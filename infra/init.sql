CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  source_type VARCHAR(50) NOT NULL,
  source_name VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
  id SERIAL PRIMARY KEY,
  document_id INT REFERENCES documents(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS embeddings (
  id SERIAL PRIMARY KEY,
  chunk_id INT REFERENCES chunks(id) ON DELETE CASCADE,
  embedding VECTOR(3072)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX IF NOT EXISTS idx_chunks_trgm ON chunks USING gin (chunk_text gin_trgm_ops);

CREATE TABLE IF NOT EXISTS qa_logs (
  id SERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  trace_id VARCHAR(64) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
