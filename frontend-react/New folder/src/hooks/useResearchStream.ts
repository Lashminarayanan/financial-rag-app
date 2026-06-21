import { useMemo, useState } from 'react';
import { streamResearch } from '../api/client';
import type { SourceItem } from '../types';

export function useResearchStream() {
  const [query, setQuery] = useState('Compare EPS trend, margin movement, and top risks from the annual report.');
  const [running, setRunning] = useState(false);
  const [answer, setAnswer] = useState('');
  const [plan, setPlan] = useState<string[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [statusLog, setStatusLog] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [comparison, setComparison] = useState<string[]>([]);
  const [verified, setVerified] = useState<boolean | undefined>(undefined);

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

    try {
      await streamResearch({ query }, (eventType, payload) => {
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
        } else if (eventType === 'token') {
          setAnswer((prev) => prev + (payload.token || ''));
        } else if (eventType === 'final') {
          setAnswer(payload.answer || '');
          if (typeof payload.verified === 'boolean') setVerified(payload.verified);
          if (Array.isArray(payload.warnings)) setWarnings(payload.warnings);
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
    setErrors([]);
    setComparison([]);
    setVerified(undefined);
  }

  return {
    query,
    setQuery,
    running,
    answer,
    plan,
    sources,
    statusLog,
    warnings,
    errors,
    comparison,
    verified,
    metrics,
    run,
    reset
  };
}
