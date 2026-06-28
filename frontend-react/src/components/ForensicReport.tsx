import React from 'react';

type ForensicReportProps = {
  report: any;
};

export function ForensicReport({ report }: ForensicReportProps) {
  if (!report) return null;

  // Handle insufficient data or error cases
  if (report.verdict === 'INSUFFICIENT_DATA' || report.verdict === 'ERROR') {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>🔬 Forensic Analysis Report</h2>
        </div>
        <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--muted)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <h3>{report.verdict === 'ERROR' ? 'Analysis Error' : 'Insufficient Data'}</h3>
          <p>{report.message || 'Unable to perform forensic analysis'}</p>
        </div>
      </section>
    );
  }

  const getRiskColor = (score: number) => {
    if (score < 30) return '#10b981'; // green
    if (score < 60) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  const getRiskIcon = (score: number) => {
    if (score < 30) return '🟢';
    if (score < 60) return '🟡';
    return '🔴';
  };

  // Safe score rendering with fallback
  const riskScore = report.overall_risk_score ?? 0;

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>🔬 Forensic Analysis Report</h2>
        {report.company_ticker && (
          <span style={{
            fontSize: '0.9rem',
            color: 'var(--muted)',
            marginLeft: '0.5rem'
          }}>
            ({report.company_ticker})
          </span>
        )}
      </div>

      {/* Overall Summary */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'var(--panel-alt)',
        borderRadius: '8px',
        marginBottom: '1.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{ fontSize: '3rem' }}>
            {getRiskIcon(riskScore)}
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.5rem' }}>
              {report.verdict_display || report.overall_verdict || 'Analysis Complete'}
            </h3>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--muted)' }}>
              Risk Score: <strong style={{ color: getRiskColor(riskScore) }}>
                {riskScore.toFixed(1)}/100
              </strong>
            </p>
          </div>
        </div>
       
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>Critical Issues</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#ef4444' }}>
              {report.critical_issues?.length || 0}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>Warnings</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#f59e0b' }}>
              {report.all_warnings?.length || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Critical Issues */}
      {report.critical_issues && Array.isArray(report.critical_issues) && report.critical_issues.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#ef4444' }}>
            🔴 Critical Issues
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {report.critical_issues.map((issue: any, idx: number) => (
              <div
                key={idx}
                style={{
                  padding: '1rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px'
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                  {issue.type || 'Issue'} {issue.year && <span style={{ color: 'var(--muted)' }}>• FY{issue.year}</span>}
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text)' }}>
                  {issue.detail || 'No details available'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Benford's Law Analysis */}
      {report.benford_law && report.benford_law.verdict !== 'INSUFFICIENT_DATA' && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
            📊 Benford's Law Analysis
          </h3>
          <div style={{
            padding: '1rem',
            backgroundColor: 'var(--panel-alt)',
            borderRadius: '6px'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '0.75rem' }}>
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>Sample Size</div>
                <div style={{ fontWeight: 600 }}>{report.benford_law.sample_size || 0} figures</div>
              </div>
              <div>
                <div style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>Chi-Square Statistic</div>
                <div style={{ fontWeight: 600 }}>
                  {typeof report.benford_law.chi_square_statistic === 'number'
                    ? report.benford_law.chi_square_statistic.toFixed(2)
                    : 'N/A'}
                </div>
              </div>
            </div>
            <div style={{ marginTop: '0.75rem', padding: '0.75rem', backgroundColor: 'var(--panel)', borderRadius: '4px' }}>
              <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>
                {report.benford_law.risk_level || 'No Assessment'}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                {report.benford_law.interpretation || 'No interpretation available'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Quality */}
      {report.revenue_quality && report.revenue_quality.verdict !== 'INSUFFICIENT_DATA' && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
            💰 Revenue Quality Analysis
          </h3>
          <div style={{
            padding: '1rem',
            backgroundColor: 'var(--panel-alt)',
            borderRadius: '6px'
          }}>
            <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>
              {report.revenue_quality.risk_level}
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
              {report.revenue_quality.summary}
            </div>
          </div>
        </div>
      )}

      {/* Cash Flow Quality */}
      {report.cash_flow_quality && report.cash_flow_quality.verdict !== 'INSUFFICIENT_DATA' && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
            💵 Cash Flow Quality Analysis
          </h3>
          <div style={{
            padding: '1rem',
            backgroundColor: 'var(--panel-alt)',
            borderRadius: '6px'
          }}>
            <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>
              {report.cash_flow_quality.risk_level}
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
              {report.cash_flow_quality.summary}
            </div>
          </div>
        </div>
      )}

      {/* Working Capital */}
      {report.working_capital && report.working_capital.verdict !== 'INSUFFICIENT_DATA' && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
            📦 Working Capital Analysis
          </h3>
          <div style={{
            padding: '1rem',
            backgroundColor: 'var(--panel-alt)',
            borderRadius: '6px'
          }}>
            <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>
              {report.working_capital.risk_level}
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
              {report.working_capital.summary}
            </div>
          </div>
        </div>
      )}

      {/* Warnings */}
      {report.all_warnings && Array.isArray(report.all_warnings) && report.all_warnings.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#f59e0b' }}>
            🟡 Warnings
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {report.all_warnings.slice(0, 5).map((warning: any, idx: number) => (
              <div
                key={idx}
                style={{
                  padding: '0.75rem',
                  backgroundColor: 'rgba(245, 158, 11, 0.1)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  borderRadius: '4px',
                  fontSize: '0.9rem'
                }}
              >
                <strong>{warning.type || 'Warning'}</strong>
                {warning.year && <span> (FY{warning.year})</span>}: {warning.detail || 'No details available'}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
