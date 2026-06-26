import { getApiBaseSync } from './config';

export type UploadResult = {
  ok: boolean;
  fileName: string;
  originalName: string;
  savedPath: string;
  size: number;
  uploadDir: string;
  fileType?: string;
};

export function uploadPdf(file: File, onProgress: (percent: number) => void): Promise<UploadResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${getApiBaseSync()}/api/v1/ingestion/upload`);

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const percent = Math.round((event.loaded / event.total) * 100);
      onProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('Upload failed'));

    const form = new FormData();
    form.append('file', file);
    xhr.send(form);
  });
}

export function uploadCsv(file: File, onProgress: (percent: number) => void): Promise<UploadResult> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${getApiBaseSync()}/api/v1/ingestion/upload-csv`);

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const percent = Math.round((event.loaded / event.total) * 100);
      onProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`CSV upload failed with status ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('CSV upload failed'));

    const form = new FormData();
    form.append('file', file);
    xhr.send(form);
  });
}

export async function streamCsvIngestion(
  payload: { fileName: string; company?: string; ticker?: string },
  onEvent: (eventType: string, data: any) => void
) {
  const response = await fetch(`${getApiBaseSync()}/api/v1/ingestion/run-csv`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`CSV ingestion request failed with status ${response.status}`);
  }
  if (!response.body) {
    throw new Error('Streaming response body is not available');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      if (buffer.trim()) processSseBuffer(buffer, onEvent);
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const normalized = buffer.replace(/\r\n/g, '\n');
    const blocks = normalized.split('\n\n');
    buffer = blocks.pop() || '';

    for (const block of blocks) {
      processSseBlock(block, onEvent);
    }
  }
}

export async function streamIngestion(payload: { fileName: string }, onEvent: (eventType: string, data: any) => void) {
  const response = await fetch(`${getApiBaseSync()}/api/v1/ingestion/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Ingestion request failed with status ${response.status}`);
  }
  if (!response.body) {
    throw new Error('Streaming response body is not available');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      if (buffer.trim()) processSseBuffer(buffer, onEvent);
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const normalized = buffer.replace(/\r\n/g, '\n');
    const blocks = normalized.split('\n\n');
    buffer = blocks.pop() || '';

    for (const block of blocks) {
      processSseBlock(block, onEvent);
    }
  }
}

function processSseBuffer(rawBuffer: string, onEvent: (eventType: string, data: any) => void) {
  const normalized = rawBuffer.replace(/\r\n/g, '\n');
  const blocks = normalized.split('\n\n');
  for (const block of blocks) {
    if (block.trim()) processSseBlock(block, onEvent);
  }
}

function processSseBlock(block: string, onEvent: (eventType: string, data: any) => void) {
  const lines = block.split('\n');
  let eventType = 'message';
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith('event:')) eventType = line.slice(6).trim();
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
  }

  const dataText = dataLines.join('\n').trim();
  if (!dataText) return;
  onEvent(eventType, JSON.parse(dataText));
}
