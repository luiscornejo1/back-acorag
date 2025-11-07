import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    return psycopg2.connect(url)

_model = None
def get_model():
    global _model
    if _model is None:
        name = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        _model = SentenceTransformer(name, trust_remote_code=True)
    return _model

def encode_vec_str(text: str) -> str:
    model = get_model()
    v = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
    return "[" + ",".join(f"{x:.6f}" for x in v.tolist()) + "]"

def semantic_search(query: str, project_id: str | None, top_k: int = 20, probes: int = 10):
    vec_str = encode_vec_str(query)
    
    # Búsqueda híbrida: vectorial + texto (para mejorar precisión)
    sql = f"""
    SET LOCAL ivfflat.probes = %s;
    WITH q AS ( SELECT %s::vector AS v ),
    vector_search AS (
      SELECT
        dc.document_id,
        d.title,
        COALESCE(d.number, '') AS number,
        COALESCE(d.category, '') AS category,
        COALESCE(d.doc_type, '') AS doc_type,
        COALESCE(d.revision, '') AS revision,
        COALESCE(d.filename, '') AS filename,
        d.date_modified,
        dc.content AS snippet,
        (dc.embedding <=> q.v) AS vector_score,
        -- Búsqueda de texto full-text
        ts_rank(
          to_tsvector('spanish', COALESCE(d.title, '') || ' ' || COALESCE(dc.content, '') || ' ' || COALESCE(d.number, '')),
          plainto_tsquery('spanish', %s)
        ) AS text_score
      FROM document_chunks dc
      JOIN documents d ON d.document_id = dc.document_id
      CROSS JOIN q
      {"WHERE dc.project_id = %s" if project_id else ""}
    )
    SELECT 
      *,
      -- Score combinado (70% vectorial + 30% texto)
      (1 - vector_score) * 0.7 + text_score * 0.3 AS combined_score
    FROM vector_search
    WHERE vector_score < 0.8  -- Filtrar resultados muy irrelevantes
      OR text_score > 0.01    -- O que tengan match de texto
    ORDER BY combined_score DESC
    LIMIT %s;
    """
    params = [probes, vec_str, query] + ([project_id] if project_id else []) + [top_k]
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        # Renombrar combined_score a score para compatibilidad
        for row in rows:
            row['score'] = row.get('combined_score', 0)  # Usar combined_score directamente
        return rows
