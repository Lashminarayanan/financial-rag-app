import React, { useEffect, useState } from 'react';
import { fetchParserStats } from '../api/parserStats';

type ParserRow = {
  parser_name: string | null;
  document_count: number;
  avg_chunk_count: number | string | null;
  avg_chunk_chars: number | string | null;
  avg_chars_per_page: number | string | null;
  avg_empty_page_ratio: number | string | null;
  avg_table_signal_ratio: number | string | null;
};

type RecentDoc = {
  file_name: string;
  parser_name: string | null;
  parser_reason: string | null;
  parser_probe: Record<string, any> | null;
  ingestion_stats: Record<string, any> | null;
  created_at: string;
};

type StatsResponse = {
  totalDocuments: number;
  byParser: ParserRow[];
  recentDocuments: RecentDoc[];
};

export function ParserStatsPanel() {
  const [data, setData] = useState<StatsResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      setLoading(true);
      setError('');
      const result = await fetchParserStats();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <section className="panel panel-bottom">
      <div className="panel-header split">
        <h2>Parser Observability</h2>
        <button className="btn btn-secondary" onClick={load} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="panel-body gap-md">
        {error ? <div className="notice notice-error">{error}</div> : null}

        {loading && !data ? (
          <p className="muted">Loading parser statistics...</p>
        ) : null}

        {data ? (
          <>
            <div className="stats-strip">
              <div className="stat-card">
                <div className="stat-label">Total documents</div>
                <div className="stat-value">{data.totalDocuments}</div>
              </div>

              {data.byParser.map((row, idx) => (
                <div className="stat-card" key={idx}>
                  <div className="stat-label">{row.parser_name || 'unknown'}</div>
                  <div className="stat-value">{row.document_count}</div>
                  <div className="stat-sub">
                    avg chunks: {row.avg_chunk_count ?? 'n/a'}
                  </div>
                </div>
              ))}
            </div>

            <div>
              <h3>By Parser</h3>
              <div className="simple-table">
                <div className="simple-table-row simple-table-header">
                  <div>Parser</div>
                  <div>Docs</div>
                  <div>Avg Chunks</div>
                  <div>Avg Chunk Chars</div>
                  <div>Avg Chars/Page</div>
                  <div>Empty Page Ratio</div>
                  <div>Table Signal Ratio</div>
                </div>

                {data.byParser.map((row, idx) => (
                  <div className="simple-table-row" key={idx}>
                    <div>{row.parser_name || 'unknown'}</div>
                    <div>{row.document_count}</div>
                    <div>{row.avg_chunk_count ?? 'n/a'}</div>
                    <div>{row.avg_chunk_chars ?? 'n/a'}</div>
                    <div>{row.avg_chars_per_page ?? 'n/a'}</div>
                    <div>{row.avg_empty_page_ratio ?? 'n/a'}</div>
                    <div>{row.avg_table_signal_ratio ?? 'n/a'}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3>Recent Documents</h3>
              <div className="recent-doc-list">
                {data.recentDocuments.map((doc, idx) => (
                  <article className="source-card" key={idx}>
                    <div className="source-card-header">
                      <strong>{doc.file_name}</strong>
                      <span className="source-score">{doc.parser_name || 'unknown'}</span>
                    </div>
                    <p className="meta">{doc.parser_reason || 'No parser reason recorded'}</p>
                    <p className="chunk-text">
                      avg_chars/page: {doc.parser_probe?.avg_chars_per_page ?? 'n/a'} | empty_ratio:{' '}
                      {doc.parser_probe?.empty_page_ratio ?? 'n/a'} | table_ratio:{' '}
                      {doc.parser_probe?.table_signal_ratio ?? 'n/a'}
                    </p>
                    <p className="chunk-text">
                      chunk_count: {doc.ingestion_stats?.chunk_count ?? 'n/a'} | avg_chunk_chars:{' '}
                      {doc.ingestion_stats?.avg_chunk_chars ?? 'n/a'}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}
