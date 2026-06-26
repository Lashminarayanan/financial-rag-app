from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.doc_parser import parse_pdf
    from app.ollama_client import embed_texts
    from app.repository import insert_document_with_chunks
else:
    from .doc_parser import parse_pdf
    from .ollama_client import embed_texts
    from .repository import insert_document_with_chunks


def json_default(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return str(obj)


def emit(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, default=json_default) + "\n")
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, help='Full path to uploaded PDF')
    args = parser.parse_args()

    pdf_path = Path(args.file)
    if not pdf_path.exists():
        emit({'type': 'stderr', 'message': f'File not found: {pdf_path}'})
        raise SystemExit(1)

    emit({'type': 'status', 'stage': 'starting', 'message': f'Starting ingestion for {pdf_path.name}'})

    doc = parse_pdf(pdf_path)
    parser_decision = doc.get('parser_decision', {})
    emit({
        'type': 'status',
        'stage': 'parser',
        'message': f"Selected parser: {doc.get('parser')} | {parser_decision.get('reason', '')}",
        'parser': doc.get('parser'),
        'parserDecision': parser_decision,
    })

    texts = [c['chunk_text'] for c in doc.get('chunks', [])]
    chunk_count = len(texts)
    emit({
        'type': 'status',
        'stage': 'chunking_complete',
        'message': f'Chunking complete. Total chunks: {chunk_count}',
        'chunkCount': chunk_count
    })

    embeddings = []
    total = len(texts)
    BATCH_SIZE = 10
    for i in range(0, total, BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_embeddings = embed_texts(batch)
        embeddings.extend(batch_embeddings)
        done = min(i + BATCH_SIZE, total)
        emit({
            'type': 'progress',
            'stage': 'embedding',
            'message': f'Embedded {done} of {total} chunks',
            'current': done,
            'total': total,
            'percent': round((done / total) * 100, 2) if total else 100
        })

    emit({'type': 'status', 'stage': 'persisting', 'message': 'Writing chunks and embeddings to PostgreSQL'})
    doc_id = insert_document_with_chunks(doc, embeddings)
    emit({
        'type': 'final',
        'message': 'Ingestion completed successfully',
        'fileName': doc.get('file_name'),
        'documentId': doc_id,
        'parser': doc.get('parser'),
        'chunkCount': chunk_count
    })


if __name__ == '__main__':
    main()
