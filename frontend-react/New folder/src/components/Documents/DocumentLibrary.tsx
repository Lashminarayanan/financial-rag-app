import React, { useEffect, useState } from 'react';
import { fetchDocuments, deleteDocument, type Document } from '../../api/documents';

export function DocumentLibrary() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [deleting, setDeleting] = useState<number | null>(null);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError('');
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number, fileName: string) {
    if (!confirm(`Delete document "${fileName}"?`)) return;
    
    try {
      setDeleting(id);
      await deleteDocument(id);
      await loadDocuments();
    } catch (err) {
      alert(`Failed to delete: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setDeleting(null);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  const filteredDocs = documents.filter((doc) =>
    doc.fileName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.originalName?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="document-library">
      <div className="library-header">
        <div className="library-stats">
          <span className="stat-item">
            <strong>{documents.length}</strong> documents
          </span>
          <span className="stat-item">
            <strong>{documents.reduce((sum, d) => sum + (d.chunkCount || 0), 0)}</strong> total chunks
          </span>
        </div>
        <input
          type="search"
          className="search-input"
          placeholder="Search documents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <button className="btn btn-secondary" onClick={loadDocuments} disabled={loading}>
          {loading ? 'Loading...' : '↻ Refresh'}
        </button>
      </div>

      {error && (
        <div className="notice notice-error" style={{ marginTop: '12px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="empty-state">Loading documents...</div>
      ) : filteredDocs.length === 0 ? (
        <div className="empty-state">
          {searchTerm ? 'No documents match your search.' : 'No documents ingested yet.'}
        </div>
      ) : (
        <div className="document-grid">
          {filteredDocs.map((doc) => (
            <div key={doc.id} className="document-card">
              <div className="document-card-header">
                <div className="document-icon">📄</div>
                <div className="document-info">
                  <h3 className="document-title">{doc.fileName}</h3>
                  <p className="document-meta muted">
                    {new Date(doc.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="document-details">
                {doc.parserName && (
                  <div className="detail-row">
                    <span className="detail-label">Parser:</span>
                    <span className="badge">{doc.parserName}</span>
                  </div>
                )}
                <div className="detail-row">
                  <span className="detail-label">Chunks:</span>
                  <span>{doc.chunkCount || 'N/A'}</span>
                </div>
                {doc.pageCount && (
                  <div className="detail-row">
                    <span className="detail-label">Pages:</span>
                    <span>{doc.pageCount}</span>
                  </div>
                )}
                <div className="detail-row">
                  <span className="detail-label">Checksum:</span>
                  <code className="checksum-text">{doc.checksum.slice(0, 12)}...</code>
                </div>
              </div>
              <div className="document-actions">
                <button
                  className="btn-icon btn-delete"
                  onClick={() => handleDelete(doc.id, doc.fileName)}
                  disabled={deleting === doc.id}
                  title="Delete document"
                >
                  {deleting === doc.id ? '⏳' : '🗑️'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
