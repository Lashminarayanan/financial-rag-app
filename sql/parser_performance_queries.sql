-- 1) Parser usage summary
SELECT
    parser_name,
    COUNT(*) AS document_count,
    ROUND(AVG((ingestion_stats->>'chunk_count')::numeric), 2) AS avg_chunk_count,
    ROUND(AVG((ingestion_stats->>'avg_chunk_chars')::numeric), 2) AS avg_chunk_chars,
    ROUND(AVG((parser_probe->>'avg_chars_per_page')::numeric), 2) AS avg_chars_per_page,
    ROUND(AVG((parser_probe->>'empty_page_ratio')::numeric), 3) AS avg_empty_page_ratio,
    ROUND(AVG((parser_probe->>'table_signal_ratio')::numeric), 3) AS avg_table_signal_ratio
FROM documents
GROUP BY parser_name
ORDER BY document_count DESC;

-- 2) Document-level parser decision audit
SELECT
    file_name,
    parser_name,
    parser_reason,
    parser_probe->>'avg_chars_per_page' AS avg_chars_per_page,
    parser_probe->>'empty_page_ratio' AS empty_page_ratio,
    parser_probe->>'table_signal_ratio' AS table_signal_ratio,
    ingestion_stats->>'chunk_count' AS chunk_count
FROM documents
ORDER BY created_at DESC;

-- 3) Documents where PyPDF looked weak
SELECT
    file_name,
    parser_name,
    parser_probe->>'avg_chars_per_page' AS avg_chars_per_page,
    parser_probe->>'empty_page_ratio' AS empty_page_ratio,
    parser_probe->>'scanned_suspected' AS scanned_suspected,
    parser_reason
FROM documents
WHERE
    (parser_probe->>'avg_chars_per_page')::numeric < 250
    OR (parser_probe->>'empty_page_ratio')::numeric > 0.30
ORDER BY created_at DESC;

-- 4) Table-heavy document candidates
SELECT
    file_name,
    parser_name,
    parser_probe->>'table_signal_ratio' AS table_signal_ratio,
    ingestion_stats->>'table_chunk_count' AS table_chunk_count,
    parser_reason
FROM documents
WHERE (parser_probe->>'table_signal_ratio')::numeric >= 0.35
ORDER BY (parser_probe->>'table_signal_ratio')::numeric DESC;

-- 5) Compare chunk distribution across documents
SELECT
    file_name,
    parser_name,
    (ingestion_stats->>'chunk_count')::int AS chunk_count,
    (ingestion_stats->>'avg_chunk_chars')::numeric AS avg_chunk_chars
FROM documents
ORDER BY (ingestion_stats->>'chunk_count')::int DESC;

-- 6) Recent ingestion observability view
SELECT
    created_at,
    file_name,
    parser_name,
    parser_reason,
    parser_probe,
    ingestion_stats
FROM documents
ORDER BY created_at DESC
LIMIT 20;
