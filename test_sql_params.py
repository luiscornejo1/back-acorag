#!/usr/bin/env python3
"""Test to count SQL placeholders"""

query_embedding = '[0.1,0.2,0.3]'  # fake embedding
where_clause = ""  # sin project_id

sql = f"""
WITH ranked AS (
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
      ts_rank(to_tsvector('spanish', COALESCE(d.title, '')), plainto_tsquery('spanish', %s)) * 3.0 +
      ts_rank(to_tsvector('spanish', COALESCE(d.number, '')), plainto_tsquery('spanish', %s)) * 2.0 +
      ts_rank(to_tsvector('spanish', COALESCE(dc.content, '')), plainto_tsquery('spanish', %s)) * 1.0
    ) AS text_score_raw
  FROM document_chunks dc
  JOIN documents d ON d.document_id = dc.document_id
  {where_clause}
)
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
  CASE 
    WHEN MAX(text_score_raw) OVER () > 0 
    THEN text_score_raw / NULLIF(MAX(text_score_raw) OVER (), 0)
    ELSE 0 
  END AS text_score,
  (vector_score * 0.70) + 
  (CASE 
    WHEN MAX(text_score_raw) OVER () > 0 
    THEN text_score_raw / NULLIF(MAX(text_score_raw) OVER (), 0)
    ELSE 0 
  END * 0.30) AS score
FROM ranked
ORDER BY score DESC 
LIMIT %s
"""

count = sql.count('%s')
print(f"✅ Total de placeholders '%s' en el SQL: {count}")
print(f"\n📝 Parámetros que debemos pasar: ['query', 'query', 'query', top_k]")
print(f"   Cantidad de parámetros: 4")
print(f"\n{'✅ MATCH' if count == 4 else '❌ MISMATCH'}")

# Buscar todos los %s
import re
matches = list(re.finditer(r'%s', sql))
print(f"\n🔍 Ubicaciones de %s:")
for i, match in enumerate(matches, 1):
    start = max(0, match.start() - 40)
    end = min(len(sql), match.end() + 40)
    context = sql[start:end].replace('\n', ' ')
    print(f"  {i}. ...{context}...")
