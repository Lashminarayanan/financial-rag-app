import React, { useState } from 'react';
import { ExecutionTimeline } from './ExecutionTimeline';
import { AnswerPanel } from './AnswerPanel';
import { EvidenceExplorer } from './EvidenceExplorer';
import type { QualityMetrics } from '../types';

type WorkspaceTab = 'answer' | 'timeline' | 'evidence';

type Props = {
  plan: string[];
  statusLog: string[];
  comparison: string[];
  answer: string;
  warnings: string[];
  errors: string[];
  verified: boolean;
  running: boolean;
  sources: any[];
  qualityMetrics?: QualityMetrics | null;
};

export function WorkspaceTabs({
  plan,
  statusLog,
  comparison,
  answer,
  warnings,
  errors,
  verified,
  running,
  sources,
  qualityMetrics
}: Props) {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('answer');

  // Count items for badges
  const evidenceCount = sources.length;
  const timelineSteps = plan.length + statusLog.length;

  return (
    <div className="workspace-tabs-container panel">
      <div className="workspace-tabs-header">
        <button
          className={`workspace-tab ${activeTab === 'answer' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('answer')}
        >
          <span className="workspace-tab-icon">💡</span>
          <span className="workspace-tab-label">Answer</span>
          {verified && <span className="workspace-tab-badge badge-success">✓</span>}
        </button>
        
        <button
          className={`workspace-tab ${activeTab === 'timeline' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          <span className="workspace-tab-icon">⚙️</span>
          <span className="workspace-tab-label">Execution Timeline</span>
          {timelineSteps > 0 && (
            <span className="workspace-tab-badge">{timelineSteps}</span>
          )}
        </button>
        
        <button
          className={`workspace-tab ${activeTab === 'evidence' ? 'workspace-tab-active' : ''}`}
          onClick={() => setActiveTab('evidence')}
        >
          <span className="workspace-tab-icon">📚</span>
          <span className="workspace-tab-label">Evidence Sources</span>
          {evidenceCount > 0 && (
            <span className="workspace-tab-badge">{evidenceCount}</span>
          )}
        </button>
      </div>

      <div className="workspace-tabs-content">
        {activeTab === 'answer' && (
          <AnswerPanel
            answer={answer}
            warnings={warnings}
            errors={errors}
            verified={verified}
            running={running}
            qualityMetrics={qualityMetrics}
          />
        )}
        
        {activeTab === 'timeline' && (
          <ExecutionTimeline
            plan={plan}
            statusLog={statusLog}
            comparison={comparison}
          />
        )}
        
        {activeTab === 'evidence' && (
          <EvidenceExplorer sources={sources} />
        )}
      </div>
    </div>
  );
}
