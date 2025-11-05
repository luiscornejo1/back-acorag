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
    max_context_docs: int = Field(default=3, ge=1, le=10)

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
            context_parts.append(
                f"Documento {i}: {row.get('title', 'Sin título')}\n"
                f"Contenido: {row.get('snippet', 'Sin contenido')}\n"
            )
        context = "\n".join(context_parts)
        
        # Por ahora, respuesta simple (más adelante integrar LLM)
        answer = f"Basado en {len(rows)} documentos encontrados sobre '{req.question}', aquí está la información relevante."
        
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
