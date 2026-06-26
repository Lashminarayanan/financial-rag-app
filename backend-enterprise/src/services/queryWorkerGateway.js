import { spawn } from 'child_process';
import { config } from '../config.js';

export function startQueryWorker({ query, analysisMode = 'general' }) {
  const args = ['--query', query];
  if (analysisMode && analysisMode !== 'general') {
    args.push('--mode', analysisMode);
  }
  
  const worker = spawn(config.python, [config.queryWorker, ...args], {
    env: { ...process.env },
    cwd: process.cwd(),
    stdio: ['ignore', 'pipe', 'pipe']
  });
  return worker;
}
