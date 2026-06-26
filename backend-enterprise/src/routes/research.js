import { Router } from 'express';
import { initSse, sendEvent } from '../utils/sse.js';
import { querySchema } from '../validation/querySchema.js';
import { startQueryWorker } from '../services/queryWorkerGateway.js';
import { pool } from '../db.js';

const router = Router();

router.post('/stream', (req, res) => {
  const parsed = querySchema.safeParse(req.body || {});
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }

  const { query, analysisMode = 'general' } = parsed.data;
  console.log('[INFO] /api/v1/research/stream');
  console.log('[INFO] query=', query);
  console.log('[INFO] analysisMode=', analysisMode);

  initSse(res);
  sendEvent(res, 'status', {
    type: 'status',
    stage: 'accepted',
    message: 'Query accepted by enterprise backend'
  });

  // Track query metrics
  const startTime = Date.now();
  let sourceCount = 0;
  let verified = false;
  let qualityMetrics = null;

  const worker = startQueryWorker({ query, analysisMode });
  let stdoutBuffer = '';

  const relayLine = (line) => {
    if (!line.trim()) return;
    console.log('[PYTHON STDOUT]', line);
    try {
      const payload = JSON.parse(line);
      const eventType = payload.type || 'message';
      
      // Track metrics from events
      if (eventType === 'sources' && Array.isArray(payload.sources)) {
        sourceCount = payload.sources.length;
      }
      if (eventType === 'final' && typeof payload.verified === 'boolean') {
        verified = payload.verified;
      }
      if (eventType === 'quality' && payload.metrics) {
        qualityMetrics = payload.metrics;
        console.log('[Backend Captured quality metrics:', qualityMetrics) ;
      }
      
      sendEvent(res, eventType, payload);
    } catch {
      sendEvent(res, 'log', { type: 'log', message: line });
    }
  };

  worker.stdout.on('data', (chunk) => {
    stdoutBuffer += chunk.toString();
    const parts = stdoutBuffer.split('\n');
    stdoutBuffer = parts.pop() || '';
    for (const part of parts) relayLine(part);
  });

  worker.stderr.on('data', (chunk) => {
    const msg = chunk.toString();
    console.error('[PYTHON STDERR]', msg);
    sendEvent(res, 'stderr', { type: 'stderr', message: msg });
  });

  worker.on('error', (err) => {
    console.error('[ERROR] worker spawn failed', err);
    sendEvent(res, 'stderr', { type: 'stderr', message: err.message });
    res.end();
  });

  worker.on('close', async (code, signal) => {
    if (stdoutBuffer.trim()) relayLine(stdoutBuffer);
    console.log('[INFO] worker closed code=', code, 'signal=', signal);
    
    // Log query to history
    console.log('[Backend] saving to query_history. Quality metrics:', qualityMetrics)
    const duration = Date.now() - startTime;
    try {
      await pool.query(`
        INSERT INTO query_history (
          query, 
          duration, 
          source_count, 
          verified,
          faithfulness_score,
          relevancy_score,
          precision_score,
          overall_quality_score
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      `, [
        query, 
        duration, 
        sourceCount, 
        verified,
        qualityMetrics?.faithfulness || null,
        qualityMetrics?.answer_relevancy || null,
        qualityMetrics?.context_precision || null,
        qualityMetrics?.overall_score || null
      ]);
    } catch (err) {
      console.error('[ERROR] Failed to log query history:', err.message);
    }
    
    sendEvent(res, 'done', { type: 'done', exitCode: code, signal });
    res.end();
  });

  res.on('close', () => {
    console.log('[INFO] response stream closed by client');
    if (!worker.killed) {
      worker.kill('SIGTERM');
    }
  });
});

export default router;
