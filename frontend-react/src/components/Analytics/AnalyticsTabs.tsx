import React, { useState } from 'react';
import { ParserStatsPanel } from '../ParserStatsPanel';
import { QueryHistory } from './QueryHistory';

type AnalyticsTab = 'query-history' | 'parser-observability';

type Props = {
  onQuerySelect?: (query: string) => void;
};

export function AnalyticsTabs({ onQuerySelect }: Props) {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('query-history');

  return (
    <div className="workspace-tabs-container panel">
      <div className="workspace-tabs-header">
        <button
          className={`workspace-tab ${activeTab === 'query-history' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('query-history')}
        >
          <span className="workspace-tab-icon">📜</span>
          <span className="workspace-tab-label">Query History</span>
        </button>
        
        <button
          className={`workspace-tab ${activeTab === 'parser-observability' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('parser-observability')}
        >
          <span className="workspace-tab-icon">📊</span>
          <span className="workspace-tab-label">Parser Observability</span>
        </button>
      </div>

      <div className="workspace-tabs-content">
        {activeTab === 'query-history' && (
          <div className="workspace-panel-content">
            <div className="workspace-panel-header">
              <h2>Query History</h2>
              <p className="muted">Recent research queries and performance metrics</p>
            </div>
            <QueryHistory onQuerySelect={onQuerySelect} />
          </div>
        )}

        {activeTab === 'parser-observability' && (
          <div className="workspace-panel-content">
            <ParserStatsPanel />
          </div>
        )}
      </div>
    </div>
  );
}
