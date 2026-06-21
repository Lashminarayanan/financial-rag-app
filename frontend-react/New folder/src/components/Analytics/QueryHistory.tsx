import React, { useEffect, useState } from 'react';
import { fetchQueryHistory, type QueryHistoryItem } from '../../api/queryHistory';

type Props = {
  onQuerySelect?: (query: string) => void;
};

export function QueryHistory({ onQuerySelect }: Props) {
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadHistory() {
    try {
      setLoading(true);
      setError('');
      const items = await fetchQueryHistory();
      setHistory(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  function formatDuration(ms?: number) {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }

  return (
    <div className="query-history">
      <div className="history-header">
        <h3>Recent Queries</h3>
        <button className="btn btn-secondary" onClick={loadHistory} disabled={loading}>
          {loading ? 'Loading...' : '↻ Refresh'}
        </button>
      </div>

      {error && (
        <div className="notice notice-error" style={{ marginTop: '12px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="empty-state">Loading query history...</div>
      ) : history.length === 0 ? (
        <div className="empty-state">No queries executed yet.</div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-item-header">
                <span className="history-time muted">
                  {new Date(item.timestamp).toLocaleString()}
                </span>
                <div className="history-badges">
                  {item.verified !== undefined && (
                    <span className={`pill ${item.verified ? 'pill-success' : 'pill-warn'}`}>
                      {item.verified ? '✓ Verified' : '⚠ Unverified'}
                    </span>
                  )}
                  {item.sourceCount !== undefined && (
                    <span className="pill pill-neutral">
                      {item.sourceCount} sources
                    </span>
                  )}
                </div>
              </div>
              <div className="history-query">{item.query}</div>
              <div className="history-footer">
                {item.duration !== undefined && (
                  <span className="muted">Duration: {formatDuration(item.duration)}</span>
                )}
                {onQuerySelect && (
                  <button 
                    className="btn-link"
                    onClick={() => onQuerySelect(item.query)}
                  >
                    Re-run →
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
