import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import path from 'path';
import { fileURLToPath } from 'url';
import healthRouter from './routes/health.js';
import researchRouter from './routes/research.js';
import ingestionRouter from './routes/ingestion.js';
import observabilityRouter from './routes/observability.js';
import documentsRouter from './routes/documents.js';
import queryHistoryRouter from './routes/queryHistory.js';
import { errorHandler } from './middleware/errorHandler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function buildApp() {
  const app = express();
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(cors());
  app.use(express.json({ limit: '2mb' }));

  // API routes
  app.use('/api/v1/health', healthRouter);
  app.use('/api/v1/research', researchRouter);
  app.use('/api/v1/ingestion', ingestionRouter);  
  app.use('/api/v1/observability', observabilityRouter);
  app.use('/api/v1/documents', documentsRouter);
  app.use('/api/v1/query-history', queryHistoryRouter);

  // Serve frontend static build (production)
  const publicDir = path.resolve(__dirname, '..', 'public');
  app.use(express.static(publicDir));
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api/')) return next();
    res.sendFile(path.join(publicDir, 'index.html'), (err) => {
      if (err) res.status(200).json({ ok: true, message: 'AFRRS' });
    });
  });

  app.use(errorHandler);
  return app;
}
