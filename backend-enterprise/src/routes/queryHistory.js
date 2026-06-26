import express from 'express';
import { pool } from '../db.js';

const router = express.Router();

// GET /api/v1/query-history - Fetch recent query history
router.get('/', async (req, res, next) => {
  try {
    // Check if query_history table exists
    const tableCheck = await pool.query(`
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'query_history'
      ) AS exists
    `);
    
    if (!tableCheck.rows[0].exists) {
      // Return empty array if table doesn't exist yet
      return res.json([]);
    }
    
    const result = await pool.query(`
      SELECT 
        id,
        query,
        timestamp,
        duration,
        source_count AS "sourceCount",
        verified,
        faithfulness_score,
        relevancy_score,
        precision_score,
        overall_quality_score
      FROM query_history
      ORDER BY timestamp DESC
      LIMIT 50
    `);
    
    res.json(result.rows);
  } catch (err) {
    next(err);
  }
});

export default router;
