import React from 'react';
import type { SourceItem } from '../types';

type Props = { sources: SourceItem[] };

export function EvidenceExplorer({ sources }: Props) {
  return (
    <div className="workspace-panel-content">
      <div className="workspace-panel-header">
        {sources.length > 0 && (
          <span className="badge">{sources.length} source{sources.length !== 1 ? 's' : ''} retrieved</span>
        )}
      </div>
      
      <div className="evidence-grid">
        {sources.length === 0 ? (
          <p className="muted">Retrieved evidence sources will appear here after query execution.</p>
        ) : (
          sources.map((src, index) => (
            <article className="source-card" key={src.id || index}>
              <div className="source-card-header">
                <strong>{src.file_name || 'Document'}</strong>
                <span className="source-score">similarity {(src.similarity ?? 0).toFixed(3)}</span>
              </div>
              <p className="meta">Page {src.page_no ?? 'n/a'} • {src.section || 'Unknown section'}</p>
              <p className="chunk-text">{src.chunk_text}</p>
              {src.table_markdown && (
                <div className="table-block">
                  <div className="table-block-header">📊 Table Data</div>
                  <pre>{src.table_markdown}</pre>
                </div>
              )}
            </article>
          ))
        )}
      </div>
    </div>
  );
}
