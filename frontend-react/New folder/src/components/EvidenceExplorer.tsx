import React from 'react';
import type { SourceItem } from '../types';

type Props = { sources: SourceItem[] };

export function EvidenceExplorer({ sources }: Props) {
  return (
    <section className="panel">
      <div className="panel-header"><h2>Evidence Explorer</h2></div>
      <div className="panel-body gap-md scrollable">
        {sources.length === 0 ? (
          <p className="muted">Retrieved evidence will appear here.</p>
        ) : (
          sources.map((src, index) => (
            <article className="source-card" key={src.id || index}>
              <div className="source-card-header">
                <strong>{src.file_name || 'Document'}</strong>
                <span className="source-score">score {(src.similarity ?? 0).toFixed(3)}</span>
              </div>
              <p className="meta">Page {src.page_no ?? 'n/a'} • {src.section || 'Unknown section'}</p>
              <p className="chunk-text">{src.chunk_text}</p>
              {src.table_markdown ? <pre className="table-block">{src.table_markdown}</pre> : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}
