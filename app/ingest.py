# app/ingest.py
import os
import re
import uuid
import json
import hashlib
from datetime import datetime
from typing import Iterable, Dict, Any, List

import psycopg2
import psycopg2.extras as extras
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from app.utils import simple_chunk  # usa el chunker existente

load_dotenv()


# =========================
# Lectura de archivo (JSON/NDJSON)
# =========================
def iter_docs_from_file(json_path: str) -> Iterable[Dict[str, Any]]:
    """
    Devuelve objetos 'documento' admitiendo:
      A) Lista JSON: [ {...}, {...} ]
      B) Objeto único: { ... }
      C) NDJSON: una línea = un JSON
    """
    # 1) Intenta JSON completo
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for obj in data:
                yield obj
            return
        if isinstance(data, dict):
            yield data
            return
    except Exception:
        pass

    # 2) NDJSON
    with open(json_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as ex:
                raise RuntimeError(
                    f"Línea {i}: no es JSON válido. ¿Archivo mixto? Detalle: {ex}"
                ) from ex


# =========================
# Normalización documento Aconex
# =========================
META_FIELDS_ORDER = [
    "Category",
    "DocumentType",
    "DocumentStatus",
    "ReviewStatus",
    "DocumentNumber",
    "Revision",
    "Filename",
    "FileType",
    "FileSize",
    "SelectList1",
    "SelectList2",
    "SelectList3",
    "SelectList7",
    "SelectList10",
    "Confidential",
    "ConfidentialUserAccessList",
    "PlannedSubmissionDate",
    "MilestoneDate",
    "Date1",
]

def normalize_doc(obj: Dict[str, Any], default_project_id: str) -> Dict[str, Any]:
    """
    Espera objetos con:
      - DocumentId (str)
      - metadata (dict) con campos como Title, DocumentNumber, DateModified, etc.
    Construye un registro listo para tabla 'documents' y texto 'body_text' para chunking.
    """
    if "DocumentId" not in obj or not isinstance(obj.get("metadata"), dict):
        raise ValueError("Objeto no parece un documento Aconex (faltan DocumentId/metadata)")

    m = obj["metadata"]

    document_id = str(obj.get("DocumentId"))
    title = (m.get("Title") or m.get("DocumentNumber") or "Documento Aconex")[:500]
    number = (m.get("DocumentNumber") or "")[:200]
    category = m.get("Category") or ""
    doc_type = m.get("DocumentType") or ""
    status = m.get("DocumentStatus") or ""
    review_status = m.get("ReviewStatus") or ""
    revision = m.get("Revision") or ""
    filename = m.get("Filename") or ""
    file_type = m.get("FileType") or ""
    file_size = None
    try:
        if m.get("FileSize") not in (None, ""):
            file_size = int(m["FileSize"])
    except Exception:
        file_size = None

    dt_raw = m.get("DateModified") or m.get("MilestoneDate") or m.get("Date1")
    date_modified = None
    if dt_raw:
        try:
            date_modified = datetime.fromisoformat(str(dt_raw).replace("Z", "+00:00"))
        except Exception:
            date_modified = None

    # project_id: usa SelectList2 si existe; si no, el default
    project_id = obj.get("project_id") or m.get("SelectList2") or default_project_id

    # Construye cuerpo semántico con metadatos ordenados
    body_lines = [f"Título: {title}", f"DocumentId: {document_id}"]
    for k in META_FIELDS_ORDER:
        v = m.get(k)
        if v not in (None, ""):
            body_lines.append(f"{k}: {v}")
    body_text = "\n".join(body_lines)[:200_000]

    # Guarda también el raw por si luego quieres enriquecer
    raw_json = obj

    return {
        "document_id": document_id,
        "project_id": project_id,
        "title": title,
        "number": number,
        "category": category,
        "doc_type": doc_type,
        "status": status,
        "review_status": review_status,
        "revision": revision,
        "filename": filename,
        "file_type": file_type,
        "file_size": file_size,
        "date_modified": date_modified,
        "body_text": body_text,
        "raw": raw_json,
    }


# =========================
# DB & Modelo
# =========================
def connect_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada en .env")
    return psycopg2.connect(url)


def load_model() -> SentenceTransformer:
    model_name = os.environ.get(
        "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    print(f"[ingest] Cargando modelo de embeddings: {model_name}")
    model = SentenceTransformer(model_name, trust_remote_code=True)
    return model


def get_model_dim(model: SentenceTransformer) -> int:
    try:
        return model.get_sentence_embedding_dimension()
    except Exception:
        v = model.encode(["probe"], normalize_embeddings=True)[0]
        return len(v)


def ensure_schema(conn, vector_dim: int):
    """Crea extensión y tablas si no existen; ajusta dimensión de 'embedding' si difiere."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
              document_id   TEXT PRIMARY KEY,
              project_id    TEXT NOT NULL,
              title         TEXT,
              number        TEXT,
              category      TEXT,
              doc_type      TEXT,
              status        TEXT,
              review_status TEXT,
              revision      TEXT,
              filename      TEXT,
              file_type     TEXT,
              file_size     BIGINT,
              date_modified TIMESTAMPTZ,
              raw           JSONB
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
              chunk_id     UUID PRIMARY KEY,
              document_id  TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
              project_id   TEXT NOT NULL,
              title        TEXT,
              date_modified TIMESTAMPTZ,
              content      TEXT NOT NULL,
              embedding    VECTOR(%s)
            );
            """,
            (vector_dim,),
        )

        # Si la tabla ya existía con otra dimensión, la ajustamos
        cur.execute(
            """
            SELECT format_type(a.atttypid, a.atttypmod) AS type
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relname = 'document_chunks'
              AND a.attname = 'embedding'
              AND a.attnum > 0
              AND NOT a.attisdropped
            LIMIT 1;
            """
        )
        row = cur.fetchone()
        if row:
            m = re.match(r"vector\((\d+)\)", row[0] or "")
            if m and int(m.group(1)) != vector_dim:
                cur.execute(
                    f"ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector({vector_dim});"
                )

        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_proj ON documents(project_id);"
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_document_chunks_vec
            ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """
        )
    conn.commit()


# =========================
# Helpers de deduplicación y chunk_id determinista
# =========================
def dedupe_by_key(items: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """Conserva la última ocurrencia por clave dentro del lote."""
    seen = {}
    for it in items:
        k = it.get(key)
        if k is not None:
            seen[k] = it
    return list(seen.values())


def stable_chunk_id(document_id: str, content: str) -> str:
    """
    Devuelve un UUID determinista basado en (document_id + contenido del chunk).
    Evita duplicados si reingestas el mismo documento/chunk.
    """
    h = hashlib.sha1(f"{document_id}:{content}".encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, h))


# =========================
# Inserciones
# =========================
def upsert_documents(conn, docs: List[Dict[str, Any]]):
    if not docs:
        return

    # 🔐 Evita 'ON CONFLICT ... cannot affect row a second time'
    docs = dedupe_by_key(docs, "document_id")

    with conn.cursor() as cur:
        extras.execute_values(
            cur,
            """
            INSERT INTO documents (
              document_id, project_id, title, number, category, doc_type,
              status, review_status, revision, filename, file_type, file_size,
              date_modified, raw
            )
            VALUES %s
            ON CONFLICT (document_id) DO UPDATE SET
              project_id    = EXCLUDED.project_id,
              title         = EXCLUDED.title,
              number        = EXCLUDED.number,
              category      = EXCLUDED.category,
              doc_type      = EXCLUDED.doc_type,
              status        = EXCLUDED.status,
              review_status = EXCLUDED.review_status,
              revision      = EXCLUDED.revision,
              filename      = EXCLUDED.filename,
              file_type     = EXCLUDED.file_type,
              file_size     = EXCLUDED.file_size,
              date_modified = EXCLUDED.date_modified,
              raw           = EXCLUDED.raw;
            """,
            [
                (
                    d["document_id"],
                    d["project_id"],
                    d["title"],
                    d["number"],
                    d["category"],
                    d["doc_type"],
                    d["status"],
                    d["review_status"],
                    d["revision"],
                    d["filename"],
                    d["file_type"],
                    d["file_size"],
                    d["date_modified"],
                    json.dumps(d["raw"]),
                )
                for d in docs
            ],
        )
    conn.commit()


def insert_doc_chunks(conn, chunks: List[Dict[str, Any]]):
    if not chunks:
        return
    with conn.cursor() as cur:
        extras.execute_values(
            cur,
            """
            INSERT INTO document_chunks (
              chunk_id, document_id, project_id, title, date_modified, content, embedding
            )
            VALUES %s
            ON CONFLICT (chunk_id) DO NOTHING;
            """,
            [
                (
                    c["chunk_id"],
                    c["document_id"],
                    c["project_id"],
                    c["title"],
                    c["date_modified"],
                    c["content"],
                    c["embedding"],
                )
                for c in chunks
            ],
        )
    conn.commit()


# =========================
# Main
# =========================
def main(json_path: str, project_id: str, batch_size: int = 512):
    conn = connect_db()
    model = load_model()
    dim = get_model_dim(model)
    print(f"[ingest] Dimensión de embeddings: {dim}")

    ensure_schema(conn, dim)

    doc_batch: List[Dict[str, Any]] = []
    chunk_texts: List[str] = []
    chunk_meta: List[Dict[str, Any]] = []
    total = 0

    for raw in iter_docs_from_file(json_path):
        doc = normalize_doc(raw, project_id)
        doc_batch.append(doc)

        # Chunking del cuerpo (metadatos consolidados)
        for piece in simple_chunk(doc["body_text"], size=1200, overlap=200):
            chunk_meta.append(
                {
                    "chunk_id": stable_chunk_id(doc["document_id"], piece),  # determinista
                    "document_id": doc["document_id"],
                    "project_id": doc["project_id"],
                    "title": doc["title"],
                    "date_modified": doc["date_modified"],
                }
            )
            chunk_texts.append(piece)

        # Lotes
        if len(doc_batch) >= batch_size:
            # Dedup por document_id dentro del lote antes de upsert
            doc_batch = dedupe_by_key(doc_batch, "document_id")

            upsert_documents(conn, doc_batch)

            if chunk_texts:
                embs = model.encode(
                    chunk_texts, normalize_embeddings=True, convert_to_numpy=True
                )
                rows = []
                for meta, emb in zip(chunk_meta, embs):
                    r = dict(meta)
                    r["embedding"] = emb.tolist()
                    r["content"] = chunk_texts[len(rows)]
                    rows.append(r)
                insert_doc_chunks(conn, rows)

            total += len(doc_batch)
            print(f"[ingest] Procesados {total} documentos…")
            doc_batch.clear()
            chunk_texts.clear()
            chunk_meta.clear()

    # Flush final
    if doc_batch:
        doc_batch = dedupe_by_key(doc_batch, "document_id")
        upsert_documents(conn, doc_batch)

    if chunk_texts:
        embs = model.encode(chunk_texts, normalize_embeddings=True, convert_to_numpy=True)
        rows = []
        for meta, emb in zip(chunk_meta, embs):
            r = dict(meta)
            r["embedding"] = emb.tolist()
            r["content"] = chunk_texts[len(rows)]
            rows.append(r)
        insert_doc_chunks(conn, rows)

    conn.close()
    print("[ingest] Ingesta terminada ✅")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--json_path", required=True, help="Ruta al JSON/NDJSON con documentos Aconex")
    p.add_argument("--project_id", required=True, help="ID de proyecto por defecto (fallback)")
    p.add_argument("--batch_size", type=int, default=512, help="Tamaño de lote para embeddings")
    a = p.parse_args()

    main(a.json_path, a.project_id, a.batch_size)
