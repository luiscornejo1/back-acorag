CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS emails (
  message_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  subject TEXT,
  from_addr TEXT,
  sent_at TIMESTAMPTZ,
  body_text TEXT
);
CREATE TABLE IF NOT EXISTS email_chunks (
  chunk_id UUID PRIMARY KEY,
  message_id TEXT NOT NULL REFERENCES emails(message_id) ON DELETE CASCADE,
  project_id TEXT NOT NULL,
  subject TEXT,
  sent_at TIMESTAMPTZ,
  content TEXT NOT NULL,
  embedding VECTOR(1024)
);
