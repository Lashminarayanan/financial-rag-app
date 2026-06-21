import React from 'react';

type Props = {
  query: string;
  onChange: (value: string) => void;
  onRun: () => void;
  onReset: () => void;
  running: boolean;
};

export function QueryComposer({ query, onChange, onRun, onReset, running }: Props) {
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
        <textarea
          className="query-box"
          value={query}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
        />
        <div className="actions-column">
          <button className="btn btn-primary" onClick={onRun} disabled={running || !query.trim()}>{running ? 'Running...' : 'Run Research'}</button>
          <button className="btn btn-secondary" onClick={onReset} disabled={running}>Reset</button>
          <button className="btn btn-secondary" disabled>Export Report</button>
        </div>
      </div>
    </section>
  );
}
