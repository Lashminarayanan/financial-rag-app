-- Parser observability columns and indexes
-- Note: These are now created in 001_init.sql for new installations
-- This migration is kept for backward compatibility with existing databases

ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS parser_name TEXT,
  ADD COLUMN IF NOT EXISTS parser_reason TEXT,
  ADD COLUMN IF NOT EXISTS parser_probe JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS ingestion_stats JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS original_name TEXT,
  ADD COLUMN IF NOT EXISTS page_count INTEGER;

CREATE INDEX IF NOT EXISTS idx_documents_parser_name
  ON documents(parser_name);

CREATE INDEX IF NOT EXISTS idx_documents_parser_probe
  ON documents USING GIN (parser_probe);

CREATE INDEX IF NOT EXISTS idx_documents_ingestion_stats
  ON documents USING GIN (ingestion_stats);
