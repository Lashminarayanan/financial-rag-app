import { spawn } from 'child_process';
import { config } from '../config.js';

export function startQueryWorker({ query }) {
  const worker = spawn(config.python, [config.queryWorker, '--query', query], {
    env: { ...process.env },
    cwd: process.cwd(),
    stdio: ['ignore', 'pipe', 'pipe']
  });
  return worker;
}
