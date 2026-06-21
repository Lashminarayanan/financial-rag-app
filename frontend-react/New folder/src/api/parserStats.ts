const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export async function fetchParserStats() {
  const response = await fetch(`${API_BASE_URL}/api/v1/observability/parser-stats`);

  if (!response.ok) {
    throw new Error(`Failed to load parser stats: ${response.status}`);
  }

  return response.json();
}
