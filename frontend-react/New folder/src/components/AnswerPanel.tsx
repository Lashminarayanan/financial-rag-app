import React from 'react';

type Props = {
  answer: string;
  warnings: string[];
  errors: string[];
  verified?: boolean;
  running: boolean;
};

export function AnswerPanel({ answer, warnings, errors, verified, running }: Props) {
  return (
    <section className="panel">
      <div className="panel-header split">
        <h2>Answer Workspace</h2>
        <div className="badge-cluster">
          <span className={`pill ${verified ? 'pill-success' : 'pill-neutral'}`}>{verified ? 'Verifier passed' : 'Verification pending'}</span>
          <span className={`pill ${running ? 'pill-warn' : 'pill-neutral'}`}>{running ? 'Streaming' : 'Idle'}</span>
        </div>
      </div>
      <div className="panel-body gap-md">
        <div className="answer-box">
          {answer ? <pre>{answer}</pre> : <p className="muted">The grounded answer will stream here.</p>}
        </div>
        {warnings.length > 0 && (
          <div className="notice notice-warning">
            <strong>Warnings</strong>
            <ul className="list compact">
              {warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}
        {errors.length > 0 && (
          <div className="notice notice-error">
            <strong>Errors</strong>
            <ul className="list compact">
              {errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
