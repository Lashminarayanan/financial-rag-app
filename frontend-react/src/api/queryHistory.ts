const API_BASE = '/api/v1';

export type QueryHistoryItem = {
  id: number;
  query: string;
  timestamp: string;
  duration?: number;
  sourceCount?: number;
  verified?: boolean;
  faithfulness_score?: number;
  relevancy_score?: number;
  precision_score?: number;
  overall_quality_score?: number;
};

export async function fetchQueryHistory(): Promise<QueryHistoryItem[]> {
  const res = await fetch(`${API_BASE}/query-history`);
  if (!res.ok) throw new Error('Failed to fetch query history');
  return res.json();
}
