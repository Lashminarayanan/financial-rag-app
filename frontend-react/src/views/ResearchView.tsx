import React from 'react';
import { useResearchStream } from '../hooks/useResearchStream';
import { QueryComposer } from '../components/QueryComposer';
import { WorkspaceTabs } from '../components/WorkspaceTabs';
import { InsightsTable } from '../components/InsightsTable';
import { ForensicReport } from '../components/ForensicReport';

export function ResearchView() {
  const vm = useResearchStream();
 
  // Debug: Track component lifecycle
  React.useEffect(() => {
    console.log('[ResearchView] Component mounted');
    return () => console.log('[ResearchView] Component unmounting');
  }, []);
 
  // Debug: Track answer state
  React.useEffect(() => {
    console.log('[ResearchView] Answer state:', vm.answer ? `${vm.answer.length} chars` : 'empty');
  }, [vm.answer]);
 
  // Debug: Track quality metrics
  React.useEffect(() => {
    console.log('[ResearchView] Quality metrics state:', vm.qualityMetrics);
  }, [vm.qualityMetrics]);

  return (
    <div className="view-content">
      <div className="panel panel-hero">
        <QueryComposer
          query={vm.query}
          onChange={vm.setQuery}
          analysisMode={vm.analysisMode}
          onModeChange={vm.setAnalysisMode}
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
        qualityMetrics={vm.qualityMetrics}
      />

      {vm.forensicReport && <ForensicReport report={vm.forensicReport} />}

      <InsightsTable metrics={vm.metrics} />
    </div>
  );
}
