import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';

dotenv.config({ path: path.resolve(process.cwd(), '.env') });
if (!process.env.BACKEND_PORT) {
  dotenv.config({ path: path.resolve(process.cwd(), '../.env') });
}

const projectRoot = fs.existsSync(path.resolve(process.cwd(), '../rag'))
  ? path.resolve(process.cwd(), '..')
  : process.cwd();

function resolvePythonPath() {
  const explicit = process.env.PYTHON_QUERY_WORKER;
  if (explicit && (explicit === 'python' || explicit === 'python3' || fs.existsSync(explicit))) {
    return explicit;
  }
  return process.platform === 'win32' ? 'python' : 'python3';
}

function resolveProjectPath(maybeRelativePath, fallbackRelativePath) {
  const value = maybeRelativePath || fallbackRelativePath;
  if (path.isAbsolute(value)) return value;
  return path.resolve(projectRoot, value);
}

export const config = {
  port: Number(process.env.BACKEND_PORT || 8080),
  python: resolvePythonPath(),
  queryWorker: process.env.RAG_PYTHON_ENTRY || '../rag/app/query_worker.py',
  ingestWorker: process.env.RAG_INGEST_WORKER_ENTRY || '../rag/app/ingest_worker.py',
  financialCsvIngestWorker: process.env.FINANCIAL_CSV_INGEST_WORKER || 'rag/app/ingest_financial_csv.py',
  reportsUploadDir: resolveProjectPath(process.env.REPORTS_DIR, './sample_data/reports')
};
