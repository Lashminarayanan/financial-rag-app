import React, { useState } from 'react';
import { IngestionPanel } from '../IngestionPanel';
import { DocumentLibrary } from './DocumentLibrary';

type DocumentsTab = 'upload' | 'library';

export function DocumentsTabs() {
  const [activeTab, setActiveTab] = useState<DocumentsTab>('upload');

  return (
    <div className="workspace-tabs-container panel">
      <div className="workspace-tabs-header">
        <button
          className={`workspace-tab ${activeTab === 'upload' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <span className="workspace-tab-icon">📤</span>
          <span className="workspace-tab-label">Document Upload</span>
        </button>
        
        <button
          className={`workspace-tab ${activeTab === 'library' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('library')}
        >
          <span className="workspace-tab-icon">📚</span>
          <span className="workspace-tab-label">Document Library</span>
        </button>
      </div>

      <div className="workspace-tabs-content">
        {activeTab === 'upload' && (
          <div className="workspace-panel-content">
            <IngestionPanel />
          </div>
        )}

        {activeTab === 'library' && (
          <div className="workspace-panel-content">
            <div className="workspace-panel-header">
              <div>
                <h2>Document Library</h2>
                <p className="muted">View and manage ingested documents</p>
              </div>
            </div>
            <DocumentLibrary />
          </div>
        )}
      </div>
    </div>
  );
}
