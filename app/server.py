from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.search_core import semantic_search

app = FastAPI()

# Configurar CORS para permitir requests desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    query: str
    project_id: str | None = None
    top_k: int = 10

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/search")
def do_search(q: Query):
    # Retornar array directo para que coincida con el frontend
    return semantic_search(q.query, q.project_id, q.top_k)
