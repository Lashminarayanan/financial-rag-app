-- Add RAGAS quality metrics to query_history table
-- Phase 2: Store quality evaluation scores for each query

ALTER TABLE query_history 
ADD COLUMN IF NOT EXISTS faithfulness_score NUMERIC(4,3),
ADD COLUMN IF NOT EXISTS relevancy_score NUMERIC(4,3),
ADD COLUMN IF NOT EXISTS precision_score NUMERIC(4,3),
ADD COLUMN IF NOT EXISTS overall_quality_score NUMERIC(4,3);

-- Add index for filtering by quality
CREATE INDEX IF NOT EXISTS idx_query_history_quality 
ON query_history(overall_quality_score DESC);

-- Add comment
COMMENT ON COLUMN query_history.faithfulness_score IS 'RAGAS faithfulness metric (0-1): Answer grounded in retrieved contexts';
COMMENT ON COLUMN query_history.relevancy_score IS 'RAGAS answer relevancy metric (0-1): Answer addresses the query';
COMMENT ON COLUMN query_history.precision_score IS 'RAGAS context precision metric (0-1): Retrieved contexts are relevant';
COMMENT ON COLUMN query_history.overall_quality_score IS 'Average of all RAGAS metrics (0-1)';
