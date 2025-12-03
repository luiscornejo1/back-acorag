"""
Servidor mock simple para pruebas de capacidad
No requiere BD ni modelos - solo simula respuestas
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import random

app = FastAPI(title="Aconex RAG Mock Server", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    top_k: int = 5

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.get("/")
def root():
    return {
        "message": "Aconex RAG Mock API",
        "version": "1.0",
        "status": "running",
        "mode": "testing"
    }

@app.get("/health")
def health():
    """Endpoint de health check"""
    return {"status": "ok", "message": "Mock server running"}

@app.post("/search")
def search(req: SearchRequest) -> List[Dict[str, Any]]:
    """Simular búsqueda semántica con delay realista"""
    
    # Simular tiempo de procesamiento (200-500ms)
    time.sleep(random.uniform(0.2, 0.5))
    
    # Generar resultados mock
    results = []
    for i in range(req.top_k):
        results.append({
            "chunk_id": f"chunk_{i+1}",
            "document_id": f"doc_{random.randint(1,100)}",
            "project_id": req.project_id or "PROJECT_001",
            "title": f"Documento {i+1}",
            "content": f"Contenido relevante para: {req.query} - Resultado {i+1}",
            "similarity_score": round(0.95 - (i * 0.1), 2)
        })
    
    return results

@app.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    """Simular respuesta de chat RAG"""
    
    # Simular tiempo de procesamiento más largo (1-2s)
    time.sleep(random.uniform(1.0, 2.0))
    
    return {
        "response": f"Respuesta generada para: {req.message}",
        "conversation_id": req.conversation_id or f"conv_{random.randint(1000,9999)}",
        "sources": [
            {"doc_id": "doc_1", "relevance": 0.95},
            {"doc_id": "doc_2", "relevance": 0.87}
        ]
    }

@app.post("/upload")
def upload() -> Dict[str, Any]:
    """Simular upload de documento"""
    
    # Simular procesamiento de upload (2-5s)
    time.sleep(random.uniform(2.0, 5.0))
    
    return {
        "status": "success",
        "document_id": f"doc_{random.randint(1000,9999)}",
        "chunks_created": random.randint(10, 50)
    }

@app.get("/history/{conversation_id}")
def get_history(conversation_id: str) -> Dict[str, Any]:
    """Simular obtención de historial"""
    
    # Simular consulta rápida (50-150ms)
    time.sleep(random.uniform(0.05, 0.15))
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {"role": "user", "content": "Mensaje 1"},
            {"role": "assistant", "content": "Respuesta 1"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Mock Server para Pruebas de Capacidad")
    print("📊 Servidor en: http://localhost:8000")
    print("🔗 Documentación: http://localhost:8000/docs")
    print("\n⚡ Endpoints disponibles:")
    print("   GET  /health - Health check")
    print("   POST /search - Búsqueda semántica")
    print("   POST /chat - Chat RAG")
    print("   POST /upload - Upload documento")
    print("   GET  /history/{id} - Obtener historial")
    print("\n✅ Listo para pruebas de carga!\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
