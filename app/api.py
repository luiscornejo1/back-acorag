from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

from .search_core import semantic_search
from .analytics import router as analytics_router

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
        return rows
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
        
        # Construir contexto
        context_parts = []
        for i, row in enumerate(rows, 1):
            title = row.get('title', 'Sin título')
            snippet = row.get('snippet', '') or row.get('content', 'Sin contenido')
            number = row.get('number', '')
            category = row.get('category', '')
            
            context_parts.append(
                f"[Documento {i}]\n"
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
                
                system_prompt = """Eres un asistente experto en documentos de construcción y arquitectura.

INSTRUCCIONES CRÍTICAS:
1. Responde ÚNICAMENTE basándote en los documentos proporcionados
2. Si la información NO está en los documentos, di claramente: "No encontré información sobre esto en los documentos disponibles"
3. Cita SIEMPRE los documentos que uses (por número de documento y título)
4. Sé ESPECÍFICO y PRECISO - no inventes ni asumas información
5. Si encuentras contradicciones, menciónalas
6. Responde en español de forma profesional y clara

FORMATO DE RESPUESTA:
- Respuesta directa a la pregunta
- Citas de los documentos relevantes
- Si aplica, menciona números de documento, fechas, categorías"""
                
                user_prompt = f"""Pregunta del usuario: {req.question}

DOCUMENTOS DISPONIBLES:
{context}

Analiza cuidadosamente los documentos y responde la pregunta del usuario."""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Modelo más potente de Groq
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
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
            sources=rows,
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

@app.get("/health")
def health():
    return {"status": "ok"}
