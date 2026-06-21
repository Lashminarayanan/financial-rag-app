CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY,
  file_name TEXT NOT NULL,
  original_name TEXT,
  file_path TEXT NOT NULL,
  title TEXT,
  company_name TEXT,
  fiscal_year TEXT,
  checksum TEXT,
  page_count INTEGER,
  parser_name TEXT,
  parser_reason TEXT,
  parser_probe JSONB DEFAULT '{}'::jsonb,
  ingestion_stats JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS chunks (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  page_no INT,
  section TEXT,
  chunk_text TEXT NOT NULL,
  chunk_type TEXT DEFAULT 'text',
  table_markdown TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  embedding VECTOR(768),
  created_at TIMESTAMPTZ DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_cosine ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- Indexes for parser observability
CREATE INDEX IF NOT EXISTS idx_documents_parser_name ON documents(parser_name);
CREATE INDEX IF NOT EXISTS idx_documents_parser_probe ON documents USING GIN (parser_probe);
CREATE INDEX IF NOT EXISTS idx_documents_ingestion_stats ON documents USING GIN (ingestion_stats);
