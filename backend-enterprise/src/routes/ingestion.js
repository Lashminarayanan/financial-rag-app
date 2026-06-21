import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import multer from 'multer';
import { z } from 'zod';
import { initSse, sendEvent } from '../utils/sse.js';
import { config } from '../config.js';
import { startIngestWorker } from '../services/ingestWorkerGateway.js';

const router = Router();
fs.mkdirSync(config.reportsUploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    cb(null, config.reportsUploadDir);
  },
  filename: (_req, file, cb) => {
    const original = file.originalname || 'uploaded.pdf';
    const safeName = original.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, safeName);
  }
});

const upload = multer({
  storage,
  fileFilter: (_req, file, cb) => {
    const isPdf = (file.mimetype === 'application/pdf') || file.originalname.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      cb(new Error('Only PDF files are allowed'));
      return;
    }
    cb(null, true);
  },
  limits: {
    fileSize: 100 * 1024 * 1024
  }
});

router.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'file is required' });
  }

  res.json({
    ok: true,
    fileName: req.file.filename,
    originalName: req.file.originalname,
    savedPath: req.file.path,
    size: req.file.size,
    uploadDir: config.reportsUploadDir
  });
});

const runSchema = z.object({
  fileName: z.string().min(1)
});

router.post('/run', (req, res) => {
  const parsed = runSchema.safeParse(req.body || {});
  if (!parsed.success) {
    return res.status(400).json({ error: parsed.error.flatten() });
  }

  const { fileName } = parsed.data;
  const filePath = path.join(config.reportsUploadDir, fileName);

  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: `Uploaded file not found: ${fileName}` });
  }

  initSse(res);
  sendEvent(res, 'status', {
    type: 'status',
    stage: 'accepted',
    message: 'Ingestion accepted by backend'
  });

  const worker = startIngestWorker({ filePath });
  let stdoutBuffer = '';

  const relayLine = (line) => {
    if (!line.trim()) return;
    try {
      const payload = JSON.parse(line);
      const eventType = payload.type || 'message';
      sendEvent(res, eventType, payload);
    } catch {
      sendEvent(res, 'log', { type: 'log', message: line });
    }
  };

  worker.stdout.on('data', (chunk) => {
    stdoutBuffer += chunk.toString();
    const parts = stdoutBuffer.split('\n');
    stdoutBuffer = parts.pop() || '';
    for (const part of parts) relayLine(part.trim());
  });

  worker.stderr.on('data', (chunk) => {
    const msg = chunk.toString();
    sendEvent(res, 'stderr', { type: 'stderr', message: msg });
  });

  worker.on('error', (err) => {
    sendEvent(res, 'stderr', { type: 'stderr', message: err.message });
    res.end();
  });

  worker.on('close', (code, signal) => {
    if (stdoutBuffer.trim()) relayLine(stdoutBuffer.trim());
    sendEvent(res, 'done', { type: 'done', exitCode: code, signal });
    res.end();
  });

  res.on('close', () => {
    if (!worker.killed) {
      worker.kill('SIGTERM');
    }
  });
});

export default router;
