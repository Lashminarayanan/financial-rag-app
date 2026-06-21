import React from 'react';

type Props = {
  plan: string[];
  statusLog: string[];
  comparison: string[];
};

export function ExecutionTimeline({ plan, statusLog, comparison }: Props) {
  return (
    <div className="workspace-panel-content">
      <div className="timeline-grid">
        <div className="timeline-section">
          <div className="timeline-section-header">
            <h3>📋 Planned Steps</h3>
            {plan.length > 0 && <span className="badge">{plan.length} steps</span>}
          </div>
          {plan.length === 0 ? (
            <p className="muted">Plan will appear here after query execution starts</p>
          ) : (
            <ol className="list">
              {plan.map((step, index) => <li key={index}>{step}</li>)}
            </ol>
          )}
        </div>
        
        <div className="timeline-section">
          <div className="timeline-section-header">
            <h3>⚙️ Status Log</h3>
            {statusLog.length > 0 && <span className="badge">{statusLog.length} events</span>}
          </div>
          {statusLog.length === 0 ? (
            <p className="muted">Waiting for status events</p>
          ) : (
            <ul className="list compact">
              {statusLog.map((line, index) => <li key={index}>{line}</li>)}
            </ul>
          )}
        </div>
        
        <div className="timeline-section">
          <div className="timeline-section-header">
            <h3>🔍 Comparison Notes</h3>
            {comparison.length > 0 && <span className="badge">{comparison.length} notes</span>}
          </div>
          {comparison.length === 0 ? (
            <p className="muted">Comparator notes will appear here</p>
          ) : (
            <ul className="list compact">
              {comparison.map((line, index) => <li key={index}>{line}</li>)}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
