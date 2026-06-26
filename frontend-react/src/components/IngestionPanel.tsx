import React, { useMemo, useState } from 'react';
import { streamIngestion, uploadPdf, streamCsvIngestion, uploadCsv, type UploadResult } from '../api/ingestion';

type LogItem = { ts: string; text: string };
type FileType = 'pdf' | 'csv';

function nowLabel() {
  return new Date().toLocaleTimeString();
}

export function IngestionPanel() {
  const [fileType, setFileType] = useState<FileType>('pdf');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [companyName, setCompanyName] = useState('EICHER MOTORS LTD');
  const [ticker, setTicker] = useState('EICHERMOT');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [embeddingProgress, setEmbeddingProgress] = useState(0);
  const [embeddingCurrent, setEmbeddingCurrent] = useState(0);
  const [embeddingTotal, setEmbeddingTotal] = useState(0);
  const [chunkCount, setChunkCount] = useState<number | null>(null);
  const [parserName, setParserName] = useState('');
  const [running, setRunning] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [error, setError] = useState('');
  const [completed, setCompleted] = useState(false);

  const overallProgress = useMemo(() => {
    if (completed) return 100;
    if (embeddingTotal > 0) return Math.min(99, Math.round(30 + (embeddingProgress * 0.7)));
    return Math.min(30, uploadProgress);
  }, [uploadProgress, embeddingProgress, embeddingTotal, completed]);

  function addLog(text: string) {
    setLogs((prev) => [{ ts: nowLabel(), text }, ...prev].slice(0, 100));
  }

  async function handleUploadAndIngest() {
    if (!selectedFile) {
      setError(`Please choose a ${fileType.toUpperCase()} file first`);
      return;
    }

    setRunning(true);
    setCompleted(false);
    setError('');
    setUploadProgress(0);
    setEmbeddingProgress(0);
    setEmbeddingCurrent(0);
    setEmbeddingTotal(0);
    setChunkCount(null);
    setParserName('');
    setUploadResult(null);
    setLogs([]);

    try {
      if (fileType === 'pdf') {
        // PDF Document Ingestion
        addLog(`Uploading PDF: ${selectedFile.name}`);
        const uploaded = await uploadPdf(selectedFile, (percent) => setUploadProgress(percent));
        setUploadResult(uploaded);
        addLog(`Upload complete: ${uploaded.fileName}`);

        await streamIngestion({ fileName: uploaded.fileName }, (eventType, payload) => {
          if (eventType === 'status') {
            addLog(payload.message || payload.stage || 'status');
            if (payload.parser) setParserName(payload.parser);
            if (payload.chunkCount) setChunkCount(payload.chunkCount);
          } else if (eventType === 'progress') {
            if (payload.stage === 'embedding') {
              setEmbeddingCurrent(payload.current || 0);
              setEmbeddingTotal(payload.total || 0);
              setEmbeddingProgress(payload.percent || 0);
            }
            addLog(payload.message || 'progress');
          } else if (eventType === 'final') {
            addLog(payload.message || 'Ingestion completed successfully');
            setCompleted(true);
            if (payload.parser) setParserName(payload.parser);
            if (payload.chunkCount) setChunkCount(payload.chunkCount);
          } else if (eventType === 'stderr') {
            const msg = payload.message || 'Unknown ingestion error';
            addLog(`ERROR: ${msg}`);
            setError(msg);
          } else if (eventType === 'done') {
            addLog(`Worker finished. exitCode=${payload.exitCode ?? 'n/a'} signal=${payload.signal ?? 'n/a'}`);
          }
        });
      } else {
        // CSV Financial Data Ingestion
        addLog(`Uploading CSV: ${selectedFile.name}`);
        const uploaded = await uploadCsv(selectedFile, (percent) => setUploadProgress(percent));
        setUploadResult(uploaded);
        addLog(`Upload complete: ${uploaded.fileName}`);
        addLog(`Processing financial data for: ${companyName} (${ticker})`);

        await streamCsvIngestion({ fileName: uploaded.fileName, company: companyName, ticker }, (eventType, payload) => {
          if (eventType === 'status') {
            addLog(payload.message || payload.stage || 'status');
          } else if (eventType === 'log') {
            addLog(payload.message || 'log');
          } else if (eventType === 'stderr') {
            const msg = payload.message || 'Unknown CSV ingestion error';
            addLog(`ERROR: ${msg}`);
            setError(msg);
          } else if (eventType === 'done') {
            const success = payload.success || payload.exitCode === 0;
            if (success) {
              setCompleted(true);
              addLog('✅ Financial data loaded successfully into database');
            } else {
              setError('CSV ingestion failed');
              addLog('❌ Financial data ingestion failed');
            }
            addLog(`Worker finished. exitCode=${payload.exitCode ?? 'n/a'}`);
          }
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      addLog(`ERROR: ${msg}`);
    } finally {
      setRunning(false);
    }
  }

  return (
    <section>
      <div className="workspace-panel-header" style={{ marginBottom: '20px' }}>
        <h2>Document Upload & Ingestion</h2>
        <div className="badge-cluster">
          <span className={`pill ${running ? 'pill-warn' : completed ? 'pill-success' : 'pill-neutral'}`}>
            {running ? 'Ingestion Running' : completed ? 'Completed' : 'Idle'}
          </span>
        </div>
      </div>

      <div className="gap-md">
        {/* File Type Selector */}
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
          <label style={{ fontWeight: 500 }}>File Type:</label>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                value="pdf"
                checked={fileType === 'pdf'}
                onChange={(e) => {
                  setFileType(e.target.value as FileType);
                  setSelectedFile(null);
                  setError('');
                }}
                disabled={running}
              />
              <span>📄 PDF Document (Annual Reports)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                value="csv"
                checked={fileType === 'csv'}
                onChange={(e) => {
                  setFileType(e.target.value as FileType);
                  setSelectedFile(null);
                  setError('');
                }}
                disabled={running}
              />
              <span>📊 CSV File (Financial Data)</span>
            </label>
          </div>
        </div>

        {/* CSV-specific fields */}
        {fileType === 'csv' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label htmlFor="company-name" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                Company Name:
              </label>
              <input
                id="company-name"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                disabled={running}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--panel)',
                  color: 'inherit'
                }}
              />
            </div>
            <div>
              <label htmlFor="ticker" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                Stock Ticker:
              </label>
              <input
                id="ticker"
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                disabled={running}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--panel)',
                  color: 'inherit'
                }}
              />
            </div>
          </div>
        )}

        <div className="upload-row">
          <input
            type="file"
            accept={fileType === 'pdf' ? 'application/pdf,.pdf' : 'text/csv,.csv'}
            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
          />
          <button className="btn btn-primary" onClick={handleUploadAndIngest} disabled={running || !selectedFile}>
            {running ? 'Processing...' : fileType === 'pdf' ? 'Upload & Ingest PDF' : 'Upload & Load Financial Data'}
          </button>
        </div>

        {selectedFile ? <p className="muted">Selected file: {selectedFile.name}</p> : null}
        {uploadResult ? <p className="muted">Saved to: {uploadResult.savedPath}</p> : null}
        {error ? <div className="notice notice-error">{error}</div> : null}

        {fileType === 'pdf' && (
          <>
            <div className="progress-card">
              <div className="progress-header"><strong>Overall Progress</strong><span>{overallProgress}%</span></div>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${overallProgress}%` }} /></div>
            </div>

            <div className="progress-grid">
              <div className="progress-card">
                <div className="progress-header"><strong>Upload</strong><span>{uploadProgress}%</span></div>
                <div className="progress-track"><div className="progress-fill" style={{ width: `${uploadProgress}%` }} /></div>
              </div>
              <div className="progress-card">
                <div className="progress-header"><strong>Embedding</strong><span>{embeddingTotal > 0 ? `${embeddingCurrent}/${embeddingTotal}` : 'n/a'}</span></div>
                <div className="progress-track"><div className="progress-fill" style={{ width: `${embeddingProgress}%` }} /></div>
              </div>
            </div>

            <div className="stats-strip">
              <div className="stat-card"><div className="stat-label">Parser</div><div className="stat-value small">{parserName || 'n/a'}</div></div>
              <div className="stat-card"><div className="stat-label">Chunk Count</div><div className="stat-value small">{chunkCount ?? 'n/a'}</div></div>
              <div className="stat-card"><div className="stat-label">Uploaded File</div><div className="stat-value small">{uploadResult?.fileName || selectedFile?.name || 'n/a'}</div></div>
            </div>
          </>
        )}

        {fileType === 'csv' && (
          <div className="progress-card">
            <div className="progress-header"><strong>Upload Progress</strong><span>{uploadProgress}%</span></div>
            <div className="progress-track"><div className="progress-fill" style={{ width: `${uploadProgress}%` }} /></div>
          </div>
        )}

        <div>
          <h3>{fileType === 'pdf' ? 'Ingestion Logs' : 'Processing Logs'}</h3>
          <div className="logs-panel">
            {logs.length === 0 ? (
              <p className="muted">
                {fileType === 'pdf'
                  ? 'Upload and ingestion progress will appear here.'
                  : 'CSV processing and database insertion logs will appear here.'}
              </p>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="log-line">
                  <span className="log-ts">{log.ts}</span>
                  <span>{log.text}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
