import React from 'react';

type Props = {
  plan: string[];
  statusLog: string[];
  comparison: string[];
};

export function ExecutionTimeline({ plan, statusLog, comparison }: Props) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Execution Timeline</h2></div>
      <div className="panel-body gap-md">
        <div>
          <h3>Planned steps</h3>
          {plan.length === 0 ? <p className="muted">Plan will appear here</p> : (
            <ol className="list">
              {plan.map((step, index) => <li key={index}>{step}</li>)}
            </ol>
          )}
        </div>
        <div>
          <h3>Status</h3>
          {statusLog.length === 0 ? <p className="muted">Waiting for status events</p> : (
            <ul className="list compact">
              {statusLog.map((line, index) => <li key={index}>{line}</li>)}
            </ul>
          )}
        </div>
        <div>
          <h3>Comparison notes</h3>
          {comparison.length === 0 ? <p className="muted">Comparator notes will appear here</p> : (
            <ul className="list compact">
              {comparison.map((line, index) => <li key={index}>{line}</li>)}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
