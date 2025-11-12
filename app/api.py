from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import json

from .search_core import semantic_search
from .analytics import router as analytics_router
from .upload import upload_and_ingest

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

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    max_context_docs: int = Field(default=15, ge=1, le=50)

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
        
        # FILTRO DE RELEVANCIA: Solo devolver resultados con score > 0.2 (20%)
        # Umbral más bajo para permitir más resultados en pruebas
        filtered_rows = [r for r in rows if r.get('score', 0) > 0.2]
        
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
        
        # FILTRO DE RELEVANCIA: Solo usar documentos con score > 0.05
        relevant_rows = [r for r in rows if r.get('score', 0) > 0.05]
        
        # Si no hay documentos relevantes, responder directamente
        if not relevant_rows:
            return ChatResponse(
                question=req.question,
                answer="❌ No encontré documentos relevantes para responder tu pregunta. Esta pregunta podría no estar relacionada con los documentos de construcción disponibles. ¿Puedo ayudarte con información sobre proyectos, cronogramas, especificaciones técnicas o documentos de construcción?",
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
            
            context_parts.append(
                f"[Documento {i}] (Relevancia: {score:.3f})\n"
                f"Título: {title}\n"
                f"Número: {number}\n"
                f"Categoría: {category}\n"
                f"Contenido: {snippet}\n"
            )
        context = "\n---\n".join(context_parts)
        
        # Generar respuesta inteligente con Groq
        import os
        import sys
        groq_key = os.environ.get("GROQ_API_KEY")
        
        print(f"[DEBUG] GROQ_API_KEY presente: {bool(groq_key)}", file=sys.stderr)
        print(f"[DEBUG] Longitud de key: {len(groq_key) if groq_key else 0}", file=sys.stderr)
        
        if groq_key:
            try:
                print(f"[DEBUG] Intentando importar Groq...", file=sys.stderr)
                from groq import Groq
                print(f"[DEBUG] Groq importado exitosamente", file=sys.stderr)
                client = Groq(api_key=groq_key)
                print(f"[DEBUG] Cliente Groq creado", file=sys.stderr)
                
                system_prompt = """Eres un asistente experto en documentos de construcción y arquitectura. Tu trabajo es buscar información EXCLUSIVAMENTE en los documentos proporcionados.

REGLAS ESTRICTAS - NO NEGOCIABLES:
1. ❌ NUNCA inventes información que no esté en los documentos
2. ❌ NUNCA uses conocimiento general o externo
3. ❌ NUNCA asumas o extrapoles datos que no estén explícitos
4. ✅ Si la información NO está en los documentos, responde EXACTAMENTE:
   "❌ No encontré información sobre [tema] en los documentos disponibles. Los documentos que revisé tratan sobre [temas que sí están]."
5. ✅ Si la pregunta NO tiene relación con los documentos, responde:
   "❌ Esta pregunta no está relacionada con los documentos de construcción disponibles. ¿Puedo ayudarte con información sobre los proyectos, cronogramas, especificaciones técnicas o documentos de construcción?"

CUANDO SÍ HAY INFORMACIÓN:
- Cita SIEMPRE el número de documento y título exacto
- Usa comillas para citas textuales del documento
- Menciona la categoría y fecha si están disponibles
- Si hay múltiples documentos, menciónalos todos
- Sé específico con números, fechas y nombres propios

FORMATO DE RESPUESTA:
📄 Respuesta directa y precisa
📋 Fuentes: [Documento #] - Título - Número
⚠️ Si falta información, indícalo claramente

Responde en español de forma profesional, concisa y exacta."""
                
                user_prompt = f"""Pregunta: {req.question}

DOCUMENTOS PARA ANALIZAR:
{context}

INSTRUCCIONES:
1. Lee cuidadosamente todos los documentos
2. Si la respuesta está en los documentos, responde con citas específicas
3. Si NO está en los documentos, di claramente que no hay información
4. Si la pregunta no tiene relación con construcción/arquitectura, indícalo

Respuesta:"""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Modelo más potente de Groq
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Más bajo = más determinista y menos creativo
                    max_tokens=1200,
                    top_p=0.9  # Reduce aleatoriedad
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
            sources=relevant_rows,  # Solo documentos relevantes
            context_used=context,
            session_id=str(uuid.uuid4())  # ID único para feedback
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
