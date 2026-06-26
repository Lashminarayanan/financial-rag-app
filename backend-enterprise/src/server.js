import { buildApp } from './app.js';
import { config } from './config.js';

const app = buildApp();
const server = app.listen(config.port, () => {
  console.log(`Enterprise backend listening on http://localhost:${config.port}`);
});

// SSE ingestion streams can run for several minutes during embedding
server.timeout = 0;         // disable socket timeout (Node.js default: 2 min)
server.keepAliveTimeout = 0;
