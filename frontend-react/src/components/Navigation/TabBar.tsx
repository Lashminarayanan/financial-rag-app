import React from 'react';

export type TabId = 'research' | 'documents' | 'observability';

type Props = {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
};

export function TabBar({ activeTab, onTabChange }: Props) {
  return (
    <nav className="tab-bar">
      <button
        className={`tab-item ${activeTab === 'research' ? 'tab-active' : ''}`}
        onClick={() => onTabChange('research')}
      >
        <span className="tab-icon">🔍</span>
        <span className="tab-label">Research</span>
      </button>
      <button
        className={`tab-item ${activeTab === 'documents' ? 'tab-active' : ''}`}
        onClick={() => onTabChange('documents')}
      >
        <span className="tab-icon">📁</span>
        <span className="tab-label">Documents</span>
      </button>
      <button
        className={`tab-item ${activeTab === 'observability' ? 'tab-active' : ''}`}
        onClick={() => onTabChange('observability')}
      >
        <span className="tab-icon">📊</span>
        <span className="tab-label">Analytics</span>
      </button>
    </nav>
  );
}
