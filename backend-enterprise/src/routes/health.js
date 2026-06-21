import { Router } from 'express';

const router = Router();

router.get('/', (_req, res) => {
  res.json({ ok: true, service: 'offline-financial-rag-backend-enterprise' });
});

export default router;
