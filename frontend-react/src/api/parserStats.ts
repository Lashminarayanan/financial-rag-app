import { getApiBaseSync } from './config';

export async function fetchParserStats() {
  const response = await fetch(`${getApiBaseSync()}/api/v1/observability/parser-stats`);

  if (!response.ok) {
    throw new Error(`Failed to load parser stats: ${response.status}`);
  }

  return response.json();
}
