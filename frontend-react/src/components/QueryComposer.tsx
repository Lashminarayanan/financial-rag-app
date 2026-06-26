import React from 'react';

type Props = {
  query: string;
  onChange: (value: string) => void;
  analysisMode: string;
  onModeChange: (mode: string) => void;
  onRun: () => void;
  onReset: () => void;
  running: boolean;
};

export function QueryComposer({ query, onChange, analysisMode, onModeChange, onRun, onReset, running }: Props) {
  return (
    <section className="panel panel-hero">
      <div className="panel-header-row">
        <div>
          {/* <p className="eyebrow">Enterprise research workspace</p> */}
          <h1>Agentic Financial Research Reporting System</h1>
          {/* <p className="muted">React UI over your working offline RAG stack. Designed as the Option C enhancement path.</p> */}
        </div>
        <div className="badge-cluster">
          <span className="badge">Offline</span>
          <span className="badge">Traceable</span>
          <span className="badge">Agentic</span>
        </div>
      </div>

      <div className="composer-row">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', flex: 1 }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <label htmlFor="analysis-mode" style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>
              👤 Analyst Persona:
            </label>
            <select
              id="analysis-mode"
              value={analysisMode}
              onChange={(e) => onModeChange(e.target.value)}
              disabled={running}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                backgroundColor: 'var(--panel)',
                color: 'inherit',
                fontSize: '0.95rem',
                cursor: 'pointer',
                minWidth: '200px'
              }}
            >
              <option value="general">🔍 General Financial Analyst</option>
              <option value="revenue">💰 Revenue Analyst</option>
              <option value="profitability">📊 Profitability Analyst</option>
              <option value="risk">⚠️ Risk Analyst</option>
              <option value="valuation">💎 Valuation Analyst</option>
            </select>
          </div>
          <textarea
            className="query-box"
            value={query}
            onChange={(e) => onChange(e.target.value)}
            rows={3}
          />
        </div>
        <div className="actions-column">
          <button className="btn btn-primary" onClick={onRun} disabled={running || !query.trim()}>{running ? 'Running...' : 'Run Research'}</button>
          <button className="btn btn-secondary" onClick={onReset} disabled={running}>Reset</button>
          <button className="btn btn-secondary" disabled>Export Report</button>
        </div>
      </div>
    </section>
  );
}
