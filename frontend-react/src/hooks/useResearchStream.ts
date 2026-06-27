import { useMemo, useState } from 'react';
import { streamResearch } from '../api/client';
import type { SourceItem, QualityMetrics } from '../types';

export function useResearchStream() {
  const [query, setQuery] = useState('Compare EPS trend, margin movement, and top risks from the annual report.');
  const [analysisMode, setAnalysisMode] = useState<string>('general');
  const [running, setRunning] = useState(false);
  const [answer, setAnswer] = useState('');
  const [plan, setPlan] = useState<string[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [statusLog, setStatusLog] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [comparison, setComparison] = useState<string[]>([]);
  const [verified, setVerified] = useState<boolean | undefined>(undefined);
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetrics | null>(null);
  const [forensicReport, setForensicReport] = useState<any>(null);

  const metrics = useMemo(() => {
    const rows = sources
      .filter((s) => !!s.table_markdown)
      .slice(0, 3)
      .map((s, idx) => ({ label: `Extracted table ${idx + 1}`, value: s.table_markdown || '' }));
    return rows;
  }, [sources]);

  async function run() {
    setRunning(true);
    setAnswer('');
    setPlan([]);
    setSources([]);
    setStatusLog([]);
    setWarnings([]);
    setErrors([]);
    setComparison([]);
    setVerified(undefined);
    setQualityMetrics(null);
    setForensicReport(null);

    try {
      await streamResearch({ query, analysisMode }, (eventType, payload) => {
        if (eventType === 'status') {
          setStatusLog((prev) => [...prev, payload.message || payload.stage || 'status']);
          if (typeof payload.verified === 'boolean') setVerified(payload.verified);
          if (Array.isArray(payload.warnings)) setWarnings(payload.warnings);
        } else if (eventType === 'plan') {
          setPlan(payload.plan || []);
        } else if (eventType === 'sources') {
          setSources(payload.sources || []);
        } else if (eventType === 'comparison') {
          setComparison(payload.notes || []);
        } else if (eventType === 'forensic') {
          console.log('[FORENSIC] Forensic report received:', payload.report);
          setForensicReport(payload.report || null);
        } else if (eventType === 'token') {
          setAnswer((prev) => prev + (payload.token || ''));
        } else if (eventType === 'final') {
          setAnswer(payload.answer || '');
          if (typeof payload.verified === 'boolean') setVerified(payload.verified);
          if (Array.isArray(payload.warnings)) setWarnings(payload.warnings);
          if (payload.quality_metrics) {
            console.log('[RAGAS] Quality metrics received:', payload.quality_metrics);
            setQualityMetrics(payload.quality_metrics);
          }
        } else if (eventType === 'quality') {
          console.log('[RAGAS] Quality event received:', payload.metrics);
          setQualityMetrics(payload.metrics || null);
        } else if (eventType === 'stderr') {
          setErrors((prev) => [...prev, payload.message || 'Unknown backend/python error']);
        } else if (eventType === 'done') {
          setStatusLog((prev) => [...prev, `Worker finished. exitCode=${payload.exitCode ?? 'n/a'} signal=${payload.signal ?? 'n/a'}`]);
        }
      });
    } catch (err) {
      setErrors((prev) => [...prev, err instanceof Error ? err.message : String(err)]);
    } finally {
      setRunning(false);
    }
  }

  function reset() {
    setAnswer('');
    setPlan([]);
    setSources([]);
    setStatusLog([]);
    setWarnings([]);
    setQualityMetrics(null);
    setForensicReport(null);
  }

  return {
    query,
    setQuery,
    analysisMode,
    setAnalysisMode,
    running,
    answer,
    plan,
    sources,
    statusLog,
    warnings,
    errors,
    comparison,
    verified,
    qualityMetrics,
    forensicReport,
    errors,
    comparison,
    verified,
    metrics,
    run,
    reset
  };
}
