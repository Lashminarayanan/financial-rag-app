import { buildApp } from './app.js';
import { config } from './config.js';

const app = buildApp();
app.listen(config.port, () => {
  console.log(`Enterprise backend listening on http://localhost:${config.port}`);
});
