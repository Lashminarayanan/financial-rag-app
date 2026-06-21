import pg from 'pg';

const { Pool } = pg;

export const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: Number(process.env.POSTGRES_PORT || 5432),
  database: process.env.POSTGRES_DB || 'financial_rag',
  user: process.env.POSTGRES_USER || 'rag_user',
  password: process.env.POSTGRES_PASSWORD || 'rag_pass'
});
