"""
Servidor web simple para búsqueda semántica
Usa directamente las funciones existentes del proyecto
"""
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Importar directamente desde los módulos existentes
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.search_core import semantic_search

app = FastAPI(title="Aconex RAG Search", version="1.0")

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
    probes: int = 10

@app.get("/")
def root():
    return {
        "message": "Aconex RAG Search API",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "docs": "/docs"
        },
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "ok", "message": "Búsqueda semántica funcionando"}

@app.post("/search")
def search(req: SearchRequest) -> List[Dict[str, Any]]:
    """Realizar búsqueda semántica usando search_core existente"""
    try:
        # Si project_id es "string" (valor por defecto de Swagger), usar None
        project_id = req.project_id if req.project_id != "string" else None
        
        print(f"🔍 Búsqueda: '{req.query}', project_id: {project_id}")
        
        results = semantic_search(
            query=req.query,
            project_id=project_id,
            top_k=req.top_k,
            probes=req.probes
        )
        
        print(f"✅ Resultados: {len(results)}")
        return results
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return [{"error": str(e)}]

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor en http://localhost:8000")
    print("📊 Endpoints disponibles:")
    print("   GET  /health - Estado del servidor")
    print("   POST /search - Búsqueda semántica")
    print("   GET  /docs - Documentación automática")
    uvicorn.run(app, host="0.0.0.0", port=8000)