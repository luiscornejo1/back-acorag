from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from .search_core import semantic_search

app = FastAPI(title="Aconex RAG API", version="1.0")

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
        groq_key = os.environ.get("GROQ_API_KEY")
        
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                
                system_prompt = """Eres un asistente experto en documentos de construcción y arquitectura.
Tu trabajo es responder preguntas basándote ÚNICAMENTE en los documentos proporcionados.
Responde de manera clara, profesional y específica en español.
Si la información no está en los documentos, indícalo claramente.
Cita los documentos relevantes en tu respuesta."""
                
                user_prompt = f"""Pregunta: {req.question}

Documentos disponibles:
{context}

Por favor, responde la pregunta basándote en la información de los documentos proporcionados."""
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Modelo más potente de Groq
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                answer = response.choices[0].message.content
            except Exception as e:
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
            context_used=context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
