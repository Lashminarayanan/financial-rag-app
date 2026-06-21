import React from 'react';
import { ParserStatsPanel } from '../components/ParserStatsPanel';
import { QueryHistory } from '../components/Analytics/QueryHistory';

export function ObservabilityView() {
  return (
    <div className="view-content">
      <div className="analytics-grid">
        <div className="panel panel-bottom">
          <div className="panel-header">
            <h2>Query History</h2>
            <p className="muted">Recent research queries and performance metrics</p>
          </div>
          <div className="panel-body">
            <QueryHistory />
          </div>
        </div>

        <div className="panel panel-bottom">
          <ParserStatsPanel />
        </div>
      </div>
    </div>
  );
}
