import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import logging
import numpy as np

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
    """Retorna el vector como string en formato PostgreSQL"""
    model = get_model()
    v = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
    # Convertir a string PostgreSQL: '[1.23,4.56,7.89]'
    vec_str = '[' + ','.join(str(float(x)) for x in v) + ']'
    return vec_str

def semantic_search(query: str, project_id: str | None, top_k: int = 20, probes: int = 10):
    try:
        logger.info(f"🔍 [v3.0-REWRITE] Búsqueda: query='{query}', project_id={project_id}, top_k={top_k}")
        query_embedding = encode_vec_str(query)
        logger.info(f"✅ Embedding generado: {len(query_embedding)} chars")
        
        # Construir SQL simple sin CTE para evitar problemas de parámetros
        where_filter = ""
        params = []
        
        if project_id:
            where_filter = "WHERE dc.project_id = %s AND"
            params.append(project_id)
        else:
            where_filter = "WHERE"
        
        # SQL con ROW_NUMBER para evitar duplicados y ordenar correctamente por relevancia
        # Primero obtiene el chunk más relevante de cada documento, luego ordena globalmente por score
        sql = f"""
        SELECT 
          document_id,
          project_id,
          title,
          number,
          category,
          doc_type,
          revision,
          filename,
          file_type,
          date_modified,
          snippet,
          vector_score,
          text_score,
          score
        FROM (
          SELECT
            dc.document_id,
            dc.project_id,
            d.title,
            COALESCE(d.number, '') AS number,
            COALESCE(d.category, '') AS category,
            COALESCE(d.doc_type, '') AS doc_type,
            COALESCE(d.revision, '') AS revision,
            COALESCE(d.filename, '') AS filename,
            COALESCE(d.file_type, '') AS file_type,
            d.date_modified,
            dc.content AS snippet,
            (1 - (dc.embedding <=> '{query_embedding}')) AS vector_score,
            (
              ts_rank(to_tsvector('spanish', COALESCE(d.title, '')), plainto_tsquery('spanish', %s)) +
              ts_rank(to_tsvector('spanish', COALESCE(d.number, '')), plainto_tsquery('spanish', %s)) +
              ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s))
            ) AS text_score,
            (1 - (dc.embedding <=> '{query_embedding}')) * 0.7 + 
            (
              ts_rank(to_tsvector('spanish', COALESCE(d.title, '')), plainto_tsquery('spanish', %s)) +
              ts_rank(to_tsvector('spanish', COALESCE(d.number, '')), plainto_tsquery('spanish', %s)) +
              ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s))
            ) * 0.3 AS score,
            ROW_NUMBER() OVER (PARTITION BY dc.document_id ORDER BY 
              (1 - (dc.embedding <=> '{query_embedding}')) * 0.7 + 
              (
                ts_rank(to_tsvector('spanish', COALESCE(d.title, '')), plainto_tsquery('spanish', %s)) +
                ts_rank(to_tsvector('spanish', COALESCE(d.number, '')), plainto_tsquery('spanish', %s)) +
                ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s))
              ) * 0.3 DESC
            ) AS rn
          FROM document_chunks dc
          JOIN documents d ON d.document_id = dc.document_id
          {where_filter} 1=1
        ) ranked
        WHERE rn = 1
        ORDER BY score DESC
        LIMIT %s
        """
        
        # Agregar parámetros: 9 queries (3 para text_score + 3 para score + 3 para ROW_NUMBER) + top_k
        params.extend([query, query, query, query, query, query, query, query, query, top_k])
        
        logger.info(f"🔍 SQL ready - params count: {len(params)}")
        
        with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
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
