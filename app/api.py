from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import json
import logging
import os

from .search_core import semantic_search, get_conn
from .analytics import router as analytics_router
from .upload import upload_and_ingest

logger = logging.getLogger(__name__)

app = FastAPI(title="Aconex RAG API", version="1.0")

# Incluir router de analytics
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringe en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    project_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=50)
    probes: int = Field(default=10, ge=1, le=100)

class ChatMessage(BaseModel):
    role: str  # 'user' o 'assistant'
    content: str

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    max_context_docs: int = Field(default=15, ge=1, le=50)
    history: List[ChatMessage] = Field(default_factory=list)  # Historial de conversación

class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    context_used: str
    session_id: str  # Para trackear feedback

class FeedbackRequest(BaseModel):
    session_id: str
    rating: int = Field(..., ge=1, le=5)  # 1-5 stars o 1=👎, 5=👍
    comment: Optional[str] = None

@app.post("/search")
def search(req: SearchRequest) -> List[Dict[str, Any]]:
    try:
        rows = semantic_search(
            query=req.query,
            project_id=req.project_id,
            top_k=req.top_k,
            probes=req.probes,
        )
        
        # THRESHOLD ADAPTATIVO PARA MEJOR PRECISIÓN
        # - Si hay resultados con score > 0.5 (alta confianza), usar threshold 0.4
        # - Si no, usar threshold 0.25 (permitir resultados medianos)
        # - Siempre descartar score < 0.25 (muy irrelevantes)
        
        if not rows:
            return []
        
        max_score = max(r.get('score', 0) for r in rows)
        
        # Threshold dinámico basado en el mejor resultado
        if max_score >= 0.5:
            threshold = 0.40  # Alta precisión: solo resultados muy relevantes
        elif max_score >= 0.35:
            threshold = 0.30  # Precisión media: resultados relevantes
        else:
            threshold = 0.25  # Permitir resultados medianos si no hay mejores
        
        filtered_rows = [r for r in rows if r.get('score', 0) >= threshold]
        
        # Log para debugging
        logger.info(f"📊 Max score: {max_score:.3f}, Threshold usado: {threshold:.2f}, Resultados: {len(filtered_rows)}/{len(rows)}")
        
        return filtered_rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    try:
        # Primero buscar documentos relevantes
        rows = semantic_search(
            query=req.question,
            project_id=None,
            top_k=req.max_context_docs,
            probes=10,
        )
        
        # FILTRO DE RELEVANCIA mejorado
        relevant_rows = [r for r in rows if r.get('score', 0) > 0.20]
        
        # Detectar preguntas trampa (score muy bajo)
        max_score = max((r.get('score', 0) for r in rows), default=0)
        
        # Si no hay documentos relevantes, responder directamente
        if not relevant_rows or max_score < 0.25:
            return ChatResponse(
                question=req.question,
                answer="❌ No encuentro información relevante sobre este tema en la documentación técnica disponible. Los documentos que tengo son sobre proyectos de construcción, arquitectura, cronogramas y especificaciones técnicas. ¿Puedo ayudarte con información relacionada a estos temas?",
                sources=[],
                context_used="",
                session_id=str(uuid.uuid4())
            )
        
        # Construir contexto solo con documentos relevantes
        context_parts = []
        for i, row in enumerate(relevant_rows, 1):
            title = row.get('title', 'Sin título')
            snippet = row.get('snippet', '') or row.get('content', 'Sin contenido')
            number = row.get('number', '')
            category = row.get('category', '')
            score = row.get('score', 0)
            
            # Formato más limpio para el LLM
            context_parts.append(
                f"📄 Documento {i} (Relevancia: {score:.1%})\n"
                f"Título: {title}\n"
                f"Número: {number}\n"
                f"Categoría: {category}\n"
                f"Contenido:\n{snippet}\n"
            )
        context = "\n" + ("="*80) + "\n".join(context_parts)
        
        # Generar respuesta inteligente con Groq
        import os
        import sys
        groq_key = os.environ.get("GROQ_API_KEY")
        
        print(f"[DEBUG] GROQ_API_KEY presente: {bool(groq_key)}", file=sys.stderr)
        print(f"[DEBUG] Documentos relevantes: {len(relevant_rows)}, Max score: {max_score:.3f}", file=sys.stderr)
        
        if groq_key:
            try:
                print(f"[DEBUG] Intentando importar Groq...", file=sys.stderr)
                from groq import Groq
                print(f"[DEBUG] Groq importado exitosamente", file=sys.stderr)
                client = Groq(api_key=groq_key)
                print(f"[DEBUG] Cliente Groq creado", file=sys.stderr)
                
                system_prompt = """Eres un asistente experto en documentación técnica de construcción. Analizas documentos y das respuestas precisas, integradas y naturales.

REGLAS:
1. USA SOLO información explícita de los documentos
2. Si no hay info, admítelo claramente
3. Para preguntas irrelevantes (ej: Michael Jackson en docs de construcción): "No encuentro información sobre [tema] en estos documentos técnicos"

ESTILO DE RESPUESTA:
- INTEGRADO: "Según la documentación del proyecto X, [síntesis]..." 
- NO enumeres: "Documento 1, Documento 2, Documento 3..."
- Cita fuentes al final: "📄 [Título] ([Número])"

ESTRUCTURA:
1. Respuesta directa (1-2 frases)
2. Detalles relevantes
3. Referencias de fuentes

EJEMPLO BUENO:
"El Plan Maestro de Arquitectura (200076-CCC02-PL-AR-000400) presenta el diseño conceptual del proyecto educativo, incluyendo distribución de aulas, áreas comunes y especificaciones técnicas para construcción sismo-resistente."

EJEMPLO MALO:
"Documento 1 habla de arquitectura. Documento 2 menciona planos..."
"""
                
                # Construir mensajes con historial
                messages = [{"role": "system", "content": system_prompt}]
                
                # Agregar historial de conversación (últimos 10 mensajes para no saturar)
                for msg in req.history[-10:]:
                    messages.append({"role": msg.role, "content": msg.content})
                
                # Agregar pregunta actual con contexto
                user_prompt = f"""Pregunta: {req.question}

DOCUMENTOS DISPONIBLES:
{context}

Analiza los documentos y responde de forma integrada y natural."""
                
                messages.append({"role": "user", "content": user_prompt})
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1200,
                    top_p=0.9
                )
                print(f"[DEBUG] Respuesta recibida de Groq", file=sys.stderr)
                answer = response.choices[0].message.content
            except Exception as e:
                print(f"[ERROR] {str(e)}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                # Si falla Groq, usar respuesta básica
                answer = f"Encontré {len(rows)} documentos relevantes. Aquí está un resumen:\n\n"
                for i, row in enumerate(rows[:3], 1):
                    answer += f"{i}. {row.get('title', 'Sin título')}: {row.get('snippet', '')[:200]}...\n\n"
        else:
            # Sin OpenAI, respuesta básica con los documentos encontrados
            answer = f"Encontré {len(rows)} documentos relevantes sobre '{req.question}':\n\n"
            for i, row in enumerate(rows[:3], 1):
                title = row.get('title', 'Sin título')
                snippet = row.get('snippet', '') or row.get('content', '')
                answer += f"**{i}. {title}**\n{snippet[:300]}...\n\n"
        
        return ChatResponse(
            question=req.question,
            answer=answer,
            sources=relevant_rows,
            context_used=context,
            session_id=str(uuid.uuid4())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """Guarda feedback de usuarios sobre las respuestas del chat"""
    try:
        import psycopg2
        import os
        from datetime import datetime
        
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_feedback (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Insertar feedback
        cursor.execute(
            "INSERT INTO chat_feedback (session_id, rating, comment) VALUES (%s, %s, %s)",
            (req.session_id, req.rating, req.comment)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Gracias por tu feedback"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando feedback: {str(e)}")

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Endpoint para subir documentos nuevos y hacer ingesta automática
    
    Soporta: PDF, TXT, DOCX, JSON
    
    Ejemplo de uso con curl:
    curl -X POST "http://localhost:8000/upload" \
         -F "file=@documento.pdf" \
         -F 'metadata={"project":"Proyecto A","type":"plano"}'
    """
    try:
        # Validar tipo de archivo
        filename = file.filename
        file_ext = filename.split('.')[-1].lower()
        
        if file_ext not in ['pdf', 'txt', 'docx', 'json']:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado: {file_ext}. Usa: PDF, TXT, DOCX, JSON"
            )
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Parsear metadata si existe
        metadata_dict = None
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Metadata debe ser un JSON válido"
                )
        
        # Ingestar documento
        result = upload_and_ingest(content, filename, metadata_dict)
        
        return {
            "status": "success",
            "message": f"Documento '{filename}' ingestado exitosamente",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")

@app.post("/upload-and-query")
async def upload_and_query(
    file: UploadFile = File(...),
    question: str = Form(...),
    metadata: Optional[str] = Form(None)
):
    """
    Endpoint combinado:
    1. Sube e ingesta el documento
    2. Hace una consulta inmediatamente sobre ese documento
    
    Ejemplo de uso con curl:
    curl -X POST "http://localhost:8000/upload-and-query" \
         -F "file=@documento.pdf" \
         -F "question=¿Cuál es la fecha del cronograma?" \
         -F 'metadata={"project":"Proyecto A"}'
    """
    try:
        # 1. Subir e ingestar documento
        filename = file.filename
        file_ext = filename.split('.')[-1].lower()
        
        if file_ext not in ['pdf', 'txt', 'docx', 'json']:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado: {file_ext}"
            )
        
        content = await file.read()
        
        metadata_dict = None
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Metadata inválido")
        
        # Ingestar
        upload_result = upload_and_ingest(content, filename, metadata_dict)
        
        # 2. Hacer consulta sobre el documento recién subido
        # Buscar por el document_id específico
        rows = semantic_search(
            query=question,
            project_id=None,
            top_k=5,
            probes=10,
        )
        
        # Filtrar solo resultados del documento recién subido
        doc_id = upload_result['document_id']
        relevant_rows = [r for r in rows if r.get('document_id') == doc_id]
        
        # Si no hay resultados del nuevo documento, buscar en todos
        if not relevant_rows:
            relevant_rows = rows[:3]
        
        # Construir respuesta con LLM
        if relevant_rows:
            context_parts = []
            for i, row in enumerate(relevant_rows, 1):
                context_parts.append(
                    f"[Fragmento {i}]\n{row.get('snippet', row.get('content', ''))}"
                )
            context = "\n---\n".join(context_parts)
            
            # Usar Groq para responder
            import os
            groq_key = os.environ.get("GROQ_API_KEY")
            
            if groq_key:
                try:
                    from groq import Groq
                    client = Groq(api_key=groq_key)
                    
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": "Eres un asistente que responde preguntas basándote ÚNICAMENTE en el documento proporcionado. Si la información no está en el documento, di que no la encontraste."
                            },
                            {
                                "role": "user",
                                "content": f"Documento:\n{context}\n\nPregunta: {question}\n\nRespuesta:"
                            }
                        ],
                        temperature=0.1,
                        max_tokens=800
                    )
                    answer = response.choices[0].message.content
                except:
                    answer = f"Contenido relevante:\n\n{context[:500]}..."
            else:
                answer = f"Contenido relevante:\n\n{context[:500]}..."
        else:
            answer = "No se encontró información relevante en el documento para responder la pregunta."
        
        return {
            "status": "success",
            "upload_result": upload_result,
            "query_result": {
                "question": question,
                "answer": answer,
                "sources": relevant_rows
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/document/{document_id}/file")
def get_document_file(document_id: str):
    """
    Endpoint para obtener el archivo PDF/TXT/DOCX asociado a un documento.
    
    Si el archivo está almacenado en disco (data/pdfs_generados/), lo sirve directamente.
    Si solo existe en BD, devuelve el contenido raw como archivo descargable.
    """
    try:
        # Buscar documento en BD
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT filename, file_type, file_content 
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        filename, file_type, file_content = result
        
        # Opción 1: Servir desde disco si existe
        if filename:
            # Buscar en data/pdfs_generados/
            pdf_path = os.path.join("data", "pdfs_generados", filename)
            if os.path.exists(pdf_path):
                return FileResponse(
                    pdf_path,
                    media_type=f"application/{file_type}" if file_type else "application/pdf",
                    filename=filename
                )
        
        # Opción 2: Servir contenido file_content desde BD
        if file_content:
            media_type = {
                "pdf": "application/pdf",
                "txt": "text/plain",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "json": "application/json"
            }.get(file_type, "application/octet-stream")
            
            # Convertir a bytes si es necesario (memoryview, bytearray, etc.)
            if isinstance(file_content, (memoryview, bytearray)):
                content_bytes = bytes(file_content)
            elif isinstance(file_content, bytes):
                content_bytes = file_content
            else:
                # Si es string, convertir a bytes
                content_bytes = file_content.encode() if isinstance(file_content, str) else bytes(file_content)
            
            return Response(
                content=content_bytes,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename={filename or f'documento_{document_id}.{file_type}'}"
                }
            )
        
        # No hay archivo disponible
        raise HTTPException(
            status_code=404, 
            detail="No se encontró el archivo físico ni el contenido raw del documento"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener archivo de documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document/{document_id}/preview")
def get_document_preview(document_id: str):
    """
    Endpoint para obtener información del documento sin descargar el archivo completo.
    Útil para mostrar metadatos antes de abrir el PDF.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        document_id, 
                        title, 
                        filename, 
                        file_type, 
                        doc_type,
                        number,
                        category,
                        date_modified,
                        project_id
                    FROM documents 
                    WHERE document_id = %s
                """, (document_id,))
                result = cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        return {
            "document_id": result[0],
            "title": result[1],
            "filename": result[2],
            "file_type": result[3],
            "doc_type": result[4],
            "number": result[5],
            "category": result[6],
            "date_modified": result[7].isoformat() if result[7] else None,
            "project_id": result[8],
            "has_file": bool(result[2]),  # True si tiene filename
            "download_url": f"/document/{result[0]}/file" if result[2] else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener preview de documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
