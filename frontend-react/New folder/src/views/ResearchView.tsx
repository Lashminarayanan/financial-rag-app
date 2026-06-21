import React from 'react';
import { useResearchStream } from '../hooks/useResearchStream';
import { QueryComposer } from '../components/QueryComposer';
import { ExecutionTimeline } from '../components/ExecutionTimeline';
import { AnswerPanel } from '../components/AnswerPanel';
import { EvidenceExplorer } from '../components/EvidenceExplorer';
import { InsightsTable } from '../components/InsightsTable';

export function ResearchView() {
  const vm = useResearchStream();

  return (
    <div className="view-content">
      <div className="panel panel-hero">
        <QueryComposer
          query={vm.query}
          onChange={vm.setQuery}
          onRun={vm.run}
          onReset={vm.reset}
          running={vm.running}
        />
      </div>

      <div className="workspace-grid">
        <ExecutionTimeline 
          plan={vm.plan} 
          statusLog={vm.statusLog} 
          comparison={vm.comparison} 
        />
        <AnswerPanel 
          answer={vm.answer} 
          warnings={vm.warnings} 
          errors={vm.errors} 
          verified={vm.verified} 
          running={vm.running} 
        />
        <EvidenceExplorer sources={vm.sources} />
      </div>

      <InsightsTable metrics={vm.metrics} />
    </div>
  );
}
