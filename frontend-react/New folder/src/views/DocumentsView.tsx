import React from 'react';
import { IngestionPanel } from '../components/IngestionPanel';
import { DocumentLibrary } from '../components/Documents/DocumentLibrary';

export function DocumentsView() {
  return (
    <div className="view-content">
      <div className="panel panel-bottom">
        <IngestionPanel />
      </div>
      
      <div className="panel panel-bottom">
        <div className="panel-header">
          <h2>Document Library</h2>
          <p className="muted">View and manage ingested documents</p>
        </div>
        <div className="panel-body">
          <DocumentLibrary />
        </div>
      </div>
    </div>
  );
}
