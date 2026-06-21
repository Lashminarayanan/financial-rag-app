from __future__ import annotations

import argparse
from pathlib import Path
from .doc_parser import parse_pdf
from .ollama_client import embed_texts
from .repository import insert_document_with_chunks


def ingest_folder(source: Path):
    pdfs = sorted(source.glob('*.pdf'))
    if not pdfs:
        print(f'No PDFs found in {source}')
        return

    for pdf in pdfs:
        print(f'Ingesting {pdf.name} ...')
        doc = parse_pdf(pdf)
        texts = [c['chunk_text'] for c in doc['chunks']]
        embeddings = embed_texts(texts)
        doc_id = insert_document_with_chunks(doc, embeddings)
        print(f'Inserted document: {pdf.name} -> {doc_id}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Folder containing PDF annual reports')
    args = parser.parse_args()
    ingest_folder(Path(args.source))


if __name__ == '__main__':
    main()
