from fastapi import FastAPI
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
    query: str = Field(..., min_length=2)
    project_id: Optional[str] = None
    top_k: int = 5
    probes: int = 10

@app.post("/search")
def search(req: SearchRequest) -> List[Dict[str, Any]]:
    rows = semantic_search(
        query=req.query,
        project_id=req.project_id,
        top_k=req.top_k,
        probes=req.probes,
    )
    return rows

@app.get("/health")
def health():
    return {"status": "ok"}
