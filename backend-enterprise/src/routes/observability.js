import { Router } from 'express';
import { pool } from '../db.js';

const router = Router();

router.get('/parser-stats', async (_req, res, next) => {
  try {
    const summaryQuery = `
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
      ORDER BY document_count DESC
    `;

    const recentDocsQuery = `
      SELECT
          file_name,
          parser_name,
          parser_reason,
          parser_probe,
          ingestion_stats,
          created_at
      FROM documents
      ORDER BY created_at DESC
      LIMIT 10
    `;

    const totalQuery = `
      SELECT COUNT(*)::int AS total_documents
      FROM documents
    `;

    const [summaryRes, recentRes, totalRes] = await Promise.all([
      pool.query(summaryQuery),
      pool.query(recentDocsQuery),
      pool.query(totalQuery)
    ]);

    res.json({
      totalDocuments: totalRes.rows[0]?.total_documents || 0,
      byParser: summaryRes.rows,
      recentDocuments: recentRes.rows
    });
  } catch (err) {
    next(err);
  }
});

export default router;
