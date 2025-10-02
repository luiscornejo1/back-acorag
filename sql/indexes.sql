CREATE INDEX IF NOT EXISTS idx_email_chunks_vec
ON email_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
