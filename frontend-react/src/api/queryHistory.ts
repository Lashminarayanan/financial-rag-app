const API_BASE = '/api/v1';

export type QueryHistoryItem = {
  id: number;
  query: string;
  timestamp: string;
  duration?: number;
  sourceCount?: number;
  verified?: boolean;
};

export async function fetchQueryHistory(): Promise<QueryHistoryItem[]> {
  const res = await fetch(`${API_BASE}/query-history`);
  if (!res.ok) throw new Error('Failed to fetch query history');
  return res.json();
}
