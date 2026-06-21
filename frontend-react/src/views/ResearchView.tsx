import React from 'react';
import { useResearchStream } from '../hooks/useResearchStream';
import { QueryComposer } from '../components/QueryComposer';
import { WorkspaceTabs } from '../components/WorkspaceTabs';
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

      <WorkspaceTabs
        plan={vm.plan}
        statusLog={vm.statusLog}
        comparison={vm.comparison}
        answer={vm.answer}
        warnings={vm.warnings}
        errors={vm.errors}
        verified={vm.verified}
        running={vm.running}
        sources={vm.sources}
      />

      <InsightsTable metrics={vm.metrics} />
    </div>
  );
}
