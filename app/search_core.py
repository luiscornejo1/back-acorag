import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import logging
import numpy as np
from .query_cleaner import clean_query, should_clean_query

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
    """
    Búsqueda semántica adaptativa multinivel:
    
    1. Nivel Estricto (threshold 0.65): Solo resultados muy relevantes
    2. Nivel Medio (threshold 0.50): Resultados moderadamente relevantes
    3. Nivel Amplio (threshold 0.40): Todos los resultados disponibles
    
    El sistema automáticamente relaja los criterios si no encuentra suficientes resultados.
    """
    try:
        # Limpiar query si es conversacional
        original_query = query
        if should_clean_query(query):
            query = clean_query(query)
            logger.info(f"🧹 Query limpiada: '{original_query}' → '{query}'")
        
        logger.info(f"🔍 [ADAPTIVE-SEARCH] query='{query}', project_id={project_id}, top_k={top_k}")
        
        # Definir niveles de búsqueda (threshold, min_results_needed)
        search_levels = [
            {"name": "ESTRICTO", "threshold": 0.65, "min_results": 3},
            {"name": "MEDIO", "threshold": 0.50, "min_results": 5},
            {"name": "AMPLIO", "threshold": 0.15, "min_results": 1},  # Aumentado de 0.30 a 0.40
        ]
        
        query_embedding = encode_vec_str(query)
        logger.info(f"✅ Embedding generado")
        
        final_results = []
        level_used = None
        
        # Intentar cada nivel hasta obtener resultados suficientes
        for level in search_levels:
            logger.info(f"🎯 Intentando nivel {level['name']} (threshold >= {level['threshold']})")
            
            results = _execute_search(
                query=query,
                query_embedding=query_embedding,
                project_id=project_id,
                top_k=top_k,
                probes=probes,
                threshold=level['threshold']
            )
            
            if len(results) >= level['min_results']:
                final_results = results
                level_used = level['name']
                logger.info(f"✅ Nivel {level['name']}: {len(results)} resultados encontrados")
                break
            else:
                logger.info(f"⚠️ Nivel {level['name']}: Solo {len(results)} resultados (min: {level['min_results']}), continuando...")
        
        # Si aún no hay resultados, usar el último intento sin threshold
        if not final_results:
            logger.warning(f"⚠️ No se encontraron resultados en ningún nivel, buscando sin threshold...")
            final_results = _execute_search(
                query=query,
                query_embedding=query_embedding,
                project_id=project_id,
                top_k=top_k,
                probes=probes,
                threshold=0.0  # Sin threshold
            )
            level_used = "SIN_FILTRO"
        
        logger.info(f"📊 RESULTADO FINAL: {len(final_results)} documentos (nivel: {level_used})")
        return final_results
        
    except Exception as e:
        logger.error(f"❌ ERROR en semantic_search: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def _execute_search(query: str, query_embedding: str, project_id: str | None, 
                    top_k: int, probes: int, threshold: float = 0.0):
    """
    Ejecuta la búsqueda con un threshold específico.
    Combina similitud vectorial (70%) con búsqueda de texto completo (30%).
    """
    where_filter = ""
    params = []
    
    if project_id:
        where_filter = "WHERE dc.project_id = %s AND"
        params.append(project_id)
    else:
        where_filter = "WHERE"
    
    # Agregar threshold filter
    if threshold > 0:
        where_filter += f" (1 - (dc.embedding <=> '{query_embedding}')) >= {threshold} AND"
    
    # SQL optimizado con filtrado por threshold
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
          ts_rank(to_tsvector('spanish', REPLACE(REPLACE(REPLACE(LOWER(COALESCE(d.title, '')), '.', ' '), '_', ' '), '-', ' ')), plainto_tsquery('spanish', %s)) * 2.0 +
          ts_rank(to_tsvector('spanish', REPLACE(REPLACE(REPLACE(LOWER(COALESCE(d.number, '')), '.', ' '), '_', ' '), '-', ' ')), plainto_tsquery('spanish', %s)) +
          ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s))
        ) AS text_score,
        (1 - (dc.embedding <=> '{query_embedding}')) * 0.6 + 
        (
          ts_rank(to_tsvector('spanish', REPLACE(REPLACE(REPLACE(LOWER(COALESCE(d.title, '')), '.', ' '), '_', ' '), '-', ' ')), plainto_tsquery('spanish', %s)) * 2.0 +
          ts_rank(to_tsvector('spanish', REPLACE(REPLACE(REPLACE(LOWER(COALESCE(d.number, '')), '.', ' '), '_', ' '), '-', ' ')), plainto_tsquery('spanish', %s)) +
          ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s))
        ) * 0.4 AS score,
        ROW_NUMBER() OVER (PARTITION BY dc.document_id ORDER BY 
          (1 - (dc.embedding <=> '{query_embedding}')) * 0.6 + 
          (
            ts_rank(to_tsvector('spanish', REPLACE(REPLACE(REPLACE(LOWER(COALESCE(d.title, '')), '.', ' '), '_', ' '), '-', ' ')), plainto_tsquery('spanish', %s)) * 2.0 +
            ts_rank(to_tsvector('spanish', REPLACE(REPLACE(REPLACE(LOWER(COALESCE(d.number, '')), '.', ' '), '_', ' '), '-', ' ')), plainto_tsquery('spanish', %s)) +
            ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s))
          ) * 0.4 DESC
        ) AS rn
      FROM document_chunks dc
      JOIN documents d ON d.document_id = dc.document_id
      {where_filter} 1=1
    ) ranked
    WHERE rn = 1
    ORDER BY score DESC
    LIMIT %s
    """
    
    # Parámetros: 9 queries + top_k
    params.extend([query, query, query, query, query, query, query, query, query, top_k])
    
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"SET LOCAL ivfflat.probes = {probes};")
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
