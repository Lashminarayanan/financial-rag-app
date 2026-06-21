import React from 'react';

type Metric = { label: string; value: string };

type Props = { metrics: Metric[] };

export function InsightsTable({ metrics }: Props) {
  return (
    <section className="panel panel-bottom">
      <div className="panel-header"><h2>Structured Insights</h2></div>
      <div className="panel-body">
        {metrics.length === 0 ? (
          <p className="muted">No structured table output has been emitted yet. This panel is reserved for extracted KPIs, tables, and report sections in the next enhancement cycle.</p>
        ) : (
          <div className="insights-grid">
            {metrics.map((m, idx) => (
              <div key={idx} className="insight-card">
                <strong>{m.label}</strong>
                <pre>{m.value}</pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
