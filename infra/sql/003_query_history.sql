-- Query History Table
-- Tracks all research queries for analytics and re-run functionality

CREATE TABLE IF NOT EXISTS query_history (
  id SERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  duration INTEGER,  -- query execution time in milliseconds
  source_count INTEGER,  -- number of evidence sources retrieved
  verified BOOLEAN,  -- whether the answer was verified
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_query_history_timestamp ON query_history(timestamp DESC);

-- Index for query text search (optional, for future features)
CREATE INDEX IF NOT EXISTS idx_query_history_query ON query_history USING gin(to_tsvector('english', query));
