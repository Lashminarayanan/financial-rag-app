import { getApiBaseSync } from './config';

export async function streamResearch(
  payload: { query: string; analysisMode?: string },
  onEvent: (eventType: string, data: any) => void
) {
  const response = await fetch(`${getApiBaseSync()}/api/v1/research/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok || !response.body) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const segments = buffer.split('\n\n');
    buffer = segments.pop() || '';

    for (const block of segments) {
      const lines = block.split('\n');
      let eventType = 'message';
      let dataText = '';
      for (const line of lines) {
        if (line.startsWith('event:')) eventType = line.slice(6).trim();
        if (line.startsWith('data:')) dataText += line.slice(5).trim();
      }
      if (dataText) {
        onEvent(eventType, JSON.parse(dataText));
      }
    }
  }
}
