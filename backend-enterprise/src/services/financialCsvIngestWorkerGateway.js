import { spawn } from 'child_process';
import { config } from '../config.js';

/**
 * Start the Python financial CSV ingestion worker.
 * This executes ingest_financial_csv.py which parses CSV and loads into PostgreSQL.
 * 
 * @param {Object} options
 * @param {string} options.filePath - Absolute path to the uploaded CSV file
 * @param {string} [options.company] - Company name (default: EICHER MOTORS LTD)
 * @param {string} [options.ticker] - Stock ticker symbol (default: EICHERMOT)
 * @returns {ChildProcess} The spawned Python process
 */
export function startFinancialCsvIngestWorker({ filePath, company, ticker }) {
  const args = [config.financialCsvIngestWorker, '--file', filePath];
  
  if (company) {
    args.push('--company', company);
  }
  
  if (ticker) {
    args.push('--ticker', ticker);
  }
  
  return spawn(config.python, args, {
    env: { ...process.env },
    cwd: process.cwd(),
    stdio: ['ignore', 'pipe', 'pipe']
  });
}
