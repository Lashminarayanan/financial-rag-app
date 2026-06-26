import React from 'react';
import type { QualityMetrics } from '../types';

type Props = {
  answer: string;
  warnings: string[];
  errors: string[];
  verified?: boolean;
  running: boolean;
  qualityMetrics?: QualityMetrics | null;
};

function QualityMetricBar({ label, value }: { label: string; value: number }) {
  const percentage = Math.round(value * 100);
  const width = `${percentage}%`;
  
  let colorClass = 'metric-excellent';
  if (value < 0.5) colorClass = 'metric-poor';
  else if (value < 0.7) colorClass = 'metric-fair';
  else if (value < 0.85) colorClass = 'metric-good';
  
  return (
    <div className="metric-row">
      <div className="metric-label">{label}</div>
      <div className="metric-bar-container">
        <div className={`metric-bar-fill ${colorClass}`} style={{ width }} />
      </div>
      <div className="metric-value">{percentage}%</div>
    </div>
  );
}

function getQualityLabel(score: number): string {
  if (score >= 0.85) return 'Excellent';
  if (score >= 0.70) return 'Good';
  if (score >= 0.50) return 'Fair';
  return 'Poor';
}

export function AnswerPanel({ answer, warnings, errors, verified, running, qualityMetrics }: Props) {
  // Debug logging
  React.useEffect(() => {
    if (qualityMetrics) {
      console.log('[AnswerPanel] Quality metrics:', qualityMetrics);
    }
  }, [qualityMetrics]);

  return (
    <div className="workspace-panel-content">
      <div className="workspace-panel-header">
        <div className="badge-cluster">
          <span className={`pill ${verified ? 'pill-success' : 'pill-neutral'}`}>
            {verified ? '✓ Verified' : '⏳ Verification pending'}
          </span>
          <span className={`pill ${running ? 'pill-warn' : 'pill-neutral'}`}>
            {running ? '⚡ Streaming' : 'Idle'}
          </span>
        </div>
      </div>
      
      <div className="answer-box-large">
        {answer ? <pre>{answer}</pre> : <p className="muted">The grounded answer will stream here.</p>}
      </div>
      
      {qualityMetrics && !qualityMetrics.error && qualityMetrics.overall_score > 0 && (
        <div className="quality-metrics-card">
          <div className="quality-header">
            <h4>✓ Answer Quality Assessment</h4>
            <div className={`quality-badge ${
              qualityMetrics.overall_score >= 0.85 ? 'badge-excellent' :
              qualityMetrics.overall_score >= 0.70 ? 'badge-good' :
              qualityMetrics.overall_score >= 0.50 ? 'badge-fair' : 'badge-poor'
            }`}>
              {getQualityLabel(qualityMetrics.overall_score)} ({Math.round(qualityMetrics.overall_score * 100)}%)
            </div>
          </div>
          <div className="quality-metrics-grid">
            <QualityMetricBar 
              label="Faithfulness" 
              value={qualityMetrics.faithfulness} 
            />
            <QualityMetricBar 
              label="Answer Relevancy" 
              value={qualityMetrics.answer_relevancy} 
            />
            <QualityMetricBar 
              label="Context Precision" 
              value={qualityMetrics.context_precision} 
            />
          </div>
          <p className="quality-note muted">
            <strong>Faithfulness:</strong> Answer grounded in retrieved evidence (no hallucination) |{' '}
            <strong>Relevancy:</strong> Answer addresses the query |{' '}
            <strong>Precision:</strong> Retrieved contexts are relevant
          </p>
        </div>
      )}
      
      {warnings.length > 0 && (
        <div className="notice notice-warning">
          <strong>⚠️ Warnings</strong>
          <ul className="list compact">
            {warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
      
      {errors.length > 0 && (
        <div className="notice notice-error">
          <strong>❌ Errors</strong>
          <ul className="list compact">
            {errors.map((e, i) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
