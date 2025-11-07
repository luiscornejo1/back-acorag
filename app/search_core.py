import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        logger.info(f"🔍 Búsqueda: query='{query}', project_id={project_id}, top_k={top_k}")
        vec_str = encode_vec_str(query)
        logger.info(f"✅ Embedding generado: {len(vec_str)} chars")
        
        # Construir WHERE clause dinámicamente
        where_clause = "WHERE dc.project_id = %s" if project_id else ""
        
        # Búsqueda híbrida: vectorial + texto (para mejorar precisión)
        sql = f"""
        WITH q AS ( SELECT %s::vector AS v )
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
          ) AS text_score,
          -- Score combinado (70% vectorial + 30% texto)
          (1 - (dc.embedding <=> q.v)) * 0.7 + ts_rank(
            to_tsvector('spanish', COALESCE(d.title, '') || ' ' || COALESCE(dc.content, '') || ' ' || COALESCE(d.number, '')),
            plainto_tsquery('spanish', %s)
          ) * 0.3 AS score
        FROM document_chunks dc
        JOIN documents d ON d.document_id = dc.document_id
        CROSS JOIN q
        {where_clause}
        ORDER BY score DESC
        LIMIT %s;
        """
        params = [vec_str, query, query] + ([project_id] if project_id else []) + [top_k]
        
        logger.info(f"📊 Ejecutando SQL con {len(params)} parámetros")
        with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Configurar ivfflat probes antes del query
            cur.execute(f"SET LOCAL ivfflat.probes = {probes};")
            cur.execute(sql, params)
            rows = cur.fetchall()
            logger.info(f"✅ Resultados obtenidos: {len(rows)} filas")
            return rows
    except Exception as e:
        logger.error(f"❌ ERROR en semantic_search: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
