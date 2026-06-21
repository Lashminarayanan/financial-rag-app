const API_BASE = '/api/v1';

export type Document = {
  id: number;
  fileName: string;
  originalName: string;
  checksum: string;
  pageCount?: number;
  chunkCount?: number;
  parserName?: string | null;
  createdAt: string;
};

export async function fetchDocuments(): Promise<Document[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete document');
}
