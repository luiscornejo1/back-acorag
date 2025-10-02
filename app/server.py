from fastapi import FastAPI
from pydantic import BaseModel
from app.search import search

app = FastAPI()

class Query(BaseModel):
    query: str
    project_id: str
    top_k: int = 10

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/search")
def do_search(q: Query):
    return {"results": search(q.query, q.project_id, q.top_k)}
