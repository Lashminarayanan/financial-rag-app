import { spawn } from 'child_process';
import { config } from '../config.js';

export function startIngestWorker({ filePath }) {
  return spawn(config.python, [config.ingestWorker, '--file', filePath], {
    env: { ...process.env },
    cwd: process.cwd(),
    stdio: ['ignore', 'pipe', 'pipe']
  });
}
