import React, { useState } from 'react';
import { TabBar, type TabId } from './components/Navigation/TabBar';
import { ResearchView } from './views/ResearchView';
import { DocumentsView } from './views/DocumentsView';
import { ObservabilityView } from './views/ObservabilityView';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('research');

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">Agentic Financial Research System</h1>
          <p className="app-subtitle">AI-powered research with evidence-backed insights</p>
        </div>
      </header>

      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />

      <div style={{ display: activeTab === 'research' ? 'block' : 'none' }}>
        <ResearchView />
      </div>
      <div style={{ display: activeTab === 'documents' ? 'block' : 'none' }}>
        <DocumentsView />
      </div>
      <div style={{ display: activeTab === 'observability' ? 'block' : 'none' }}>
        <ObservabilityView />
      </div>
    </div>
  );
}
