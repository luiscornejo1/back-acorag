#!/usr/bin/env python3
"""
Servidor web simple para búsqueda semántica
"""
import os
import json
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

load_dotenv()

app = FastAPI(title="Aconex RAG Search", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo globalmente
print("🧠 Cargando modelo de embeddings...")
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print("✅ Modelo cargado")

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    top_k: int = 5

@app.get("/health")
def health():
    return {"status": "ok", "message": "Búsqueda semántica funcionando"}

@app.post("/search")
def search(req: SearchRequest) -> List[Dict[str, Any]]:
    """Realizar búsqueda semántica"""
    
    # Conectar a BD
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    # Generar embedding de la consulta
    query_embedding = model.encode(req.query, normalize_embeddings=True)
    
    # Construir query SQL
    sql = """
        SELECT 
            chunk_id,
            document_id,
            project_id,
            title,
            content,
            1 - (embedding <=> %s::vector) as similarity_score
        FROM document_chunks 
        WHERE 1 - (embedding <=> %s::vector) > 0.2
    """
    
    params = [query_embedding.tolist(), query_embedding.tolist()]
    
    # Agregar filtro por proyecto si se especifica
    if req.project_id:
        sql += " AND project_id = %s"
        params.append(req.project_id)
    
    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([query_embedding.tolist(), req.top_k])
    
    # Ejecutar búsqueda
    cur.execute(sql, params)
    results = cur.fetchall()
    
    # Formatear resultados
    formatted_results = []
    for chunk_id, doc_id, proj_id, title, content, score in results:
        formatted_results.append({
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "project_id": proj_id,
            "title": title,
            "content": content,
            "similarity_score": float(score)
        })
    
    conn.close()
    return formatted_results

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)