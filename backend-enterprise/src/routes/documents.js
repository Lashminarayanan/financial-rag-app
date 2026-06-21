import express from 'express';
import { pool } from '../db.js';

const router = express.Router();

// GET /api/v1/documents - List all documents
router.get('/', async (req, res, next) => {
  try {
    const result = await pool.query(`
      SELECT 
        d.id,
        d.file_name AS "fileName",
        d.original_name AS "originalName",
        d.checksum,
        d.page_count AS "pageCount",
        d.parser_name AS "parserName",
        d.created_at AS "createdAt",
        COUNT(c.id) AS "chunkCount"
      FROM documents d
      LEFT JOIN chunks c ON c.document_id = d.id
      GROUP BY d.id, d.file_name, d.original_name, d.checksum, d.page_count, d.parser_name, d.created_at
      ORDER BY d.created_at DESC
    `);
    res.json(result.rows);
  } catch (err) {
    next(err);
  }
});

// DELETE /api/v1/documents/:id - Delete a document and its chunks
router.delete('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    
    // Delete chunks first (foreign key constraint)
    await pool.query('DELETE FROM chunks WHERE document_id = $1', [id]);
    
    // Delete document
    const result = await pool.query('DELETE FROM documents WHERE id = $1 RETURNING id', [id]);
    
    if (result.rowCount === 0) {
      return res.status(404).json({ error: 'Document not found' });
    }
    
    res.json({ ok: true, message: 'Document deleted successfully' });
  } catch (err) {
    next(err);
  }
});

export default router;
