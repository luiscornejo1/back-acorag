# Aconex RAG Starter (mínimo)
Sigue estos pasos:
1) docker compose up -d
2) psql $DATABASE_URL -f sql/schema.sql && psql $DATABASE_URL -f sql/indexes.sql
3) python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
4) python app/ingest.py --json_path data/aconex_emails.json --project_id PROYECTO_001
5) uvicorn app.server:app --host 0.0.0.0 --port 8000
