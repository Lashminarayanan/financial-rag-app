
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple

from pypdf import PdfReader

from .config import (
    USE_DOCLING,
    DOCLING_PREFER,
    AUTO_PARSER_ROUTE,
    MAX_PROBE_PAGES,
    MIN_AVG_CHARS_PER_PAGE,
    MAX_EMPTY_PAGE_RATIO,
    TABLE_SIGNAL_RATIO_THRESHOLD,
    TABLE_EXTRACTION_PRIORITY,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 250) -> List[str]:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(0, end - overlap)

    return chunks


def safe_page_text(page) -> str:
    try:
        return page.extract_text() or ""
    except Exception:
        return ""


def count_table_signals(text: str) -> int:
    """
    Approximate whether a page looks table-heavy.
    Heuristics:
    - multiple lines with several numeric tokens
    - many short dense rows that often resemble financial tables
    """
    if not text:
        return 0

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0

    numeric_lines = 0
    short_dense_lines = 0

    for line in lines:
        numbers = re.findall(r"[-+]?\d[\d,().%/-]*", line)
        if len(numbers) >= 3:
            numeric_lines += 1
        if len(line) <= 80 and len(numbers) >= 2:
            short_dense_lines += 1

    score = 0
    if numeric_lines >= 4:
        score += 1
    if short_dense_lines >= 4:
        score += 1

    return score


def probe_pdf_quality(pdf_path: Path) -> Dict:
    """
    Probe the PDF using PyPDF across a limited number of pages to determine:
    - text density
    - empty-page ratio
    - noisy extraction ratio
    - table-heavy signal
    - scanned/poor-text suspicion
    """
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    probe_pages = min(total_pages, MAX_PROBE_PAGES)

    page_lengths: List[int] = []
    empty_pages = 0
    noisy_pages = 0
    table_signal_pages = 0

    for i in range(probe_pages):
        text = safe_page_text(reader.pages[i])
        cleaned = " ".join(text.split())
        char_count = len(cleaned)

        page_lengths.append(char_count)

        if char_count < 50:
            empty_pages += 1

        if "�" in text or "\x00" in text:
            noisy_pages += 1

        if count_table_signals(text) > 0:
            table_signal_pages += 1

    avg_chars_per_page = round(sum(page_lengths) / probe_pages, 2) if probe_pages else 0.0
    empty_page_ratio = round(empty_pages / probe_pages, 3) if probe_pages else 1.0
    noisy_page_ratio = round(noisy_pages / probe_pages, 3) if probe_pages else 0.0
    table_signal_ratio = round(table_signal_pages / probe_pages, 3) if probe_pages else 0.0

    scanned_suspected = (
        avg_chars_per_page < MIN_AVG_CHARS_PER_PAGE
        or empty_page_ratio > MAX_EMPTY_PAGE_RATIO
    )

    return {
        "total_pages": total_pages,
        "probe_pages": probe_pages,
        "avg_chars_per_page": avg_chars_per_page,
        "empty_page_ratio": empty_page_ratio,
        "noisy_page_ratio": noisy_page_ratio,
        "table_signal_ratio": table_signal_ratio,
        "scanned_suspected": scanned_suspected,
    }


def choose_parser(metrics: Dict) -> Tuple[str, str]:
    """
    Decide which parser to use.

    Priority:
    1. If DOCLING_PREFER and USE_DOCLING -> force Docling
    2. If AUTO_PARSER_ROUTE is disabled -> use PyPDF baseline
    3. If text quality looks poor and Docling is enabled -> Docling
    4. If document looks table-heavy and table extraction priority is enabled -> Docling
    5. Otherwise -> PyPDF
    """
    if DOCLING_PREFER and USE_DOCLING:
        return "docling", "DOCLING_PREFER is enabled"

    if not AUTO_PARSER_ROUTE:
        return "pypdf", "AUTO_PARSER_ROUTE disabled; using PyPDF baseline"

    if metrics["scanned_suspected"] and USE_DOCLING:
        return "docling", "PyPDF text density is low or too many empty pages"

    if (
        TABLE_EXTRACTION_PRIORITY
        and metrics["table_signal_ratio"] >= TABLE_SIGNAL_RATIO_THRESHOLD
        and USE_DOCLING
    ):
        return "docling", "Document appears table-heavy and table fidelity is prioritized"

    return "pypdf", "PyPDF quality probe is acceptable for baseline extraction"


def parse_with_docling(pdf_path: Path) -> List[Dict]:
    """
    Attempt Docling-based parsing.
    If import or conversion fails, return [] so caller can fallback safely.
    """
    try:
        from docling.document_converter import DocumentConverter
    except Exception as e:
        print(f"[WARN] Docling import failed for {pdf_path.name}: {e}")
        return []

    try:
        print(f"[INFO] Trying Docling parser for {pdf_path.name} ...")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))

        markdown = result.document.export_to_markdown()
        out: List[Dict] = []

        for idx, chunk in enumerate(chunk_text(markdown)):
            out.append(
                {
                    "page_no": None,
                    "section": "Docling Extract",
                    "chunk_text": chunk,
                    "chunk_type": "text",
                    "table_markdown": None,
                    "metadata": {
                        "extractor": "docling",
                        "source_format": "markdown",
                        "chunk_index": idx,
                    },
                }
            )

        print(f"[INFO] Docling succeeded for {pdf_path.name} with {len(out)} chunks")
        return out

    except Exception as e:
        print(f"[WARN] Docling parsing failed for {pdf_path.name}: {e}")
        return []


def parse_with_pypdf(pdf_path: Path) -> List[Dict]:
    """
    Lightweight default parser using PyPDF text extraction.
    """
    print(f"[INFO] Using PyPDF parser for {pdf_path.name} ...")
    reader = PdfReader(str(pdf_path))
    out: List[Dict] = []

    for page_no, page in enumerate(reader.pages, start=1):
        text = safe_page_text(page)

        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            out.append(
                {
                    "page_no": page_no,
                    "section": f"Page {page_no}",
                    "chunk_text": chunk,
                    "chunk_type": "text",
                    "table_markdown": None,
                    "metadata": {
                        "extractor": "pypdf",
                        "page_chunk_index": idx,
                    },
                }
            )

    print(f"[INFO] PyPDF extracted {len(out)} chunks for {pdf_path.name}")
    return out


def parse_pdf(pdf_path: Path) -> Dict:
    """
    Auto-routing flow:
    1. Probe the document with PyPDF
    2. Decide whether PyPDF is sufficient
    3. If Docling is recommended and enabled, try Docling
    4. If Docling fails, safely fallback to PyPDF
    """
    probe = probe_pdf_quality(pdf_path)
    recommended_parser, reason = choose_parser(probe)

    print(
        f"[INFO] Parser decision for {pdf_path.name}: "
        f"{recommended_parser.upper()} | reason={reason} | metrics={probe}"
    )

    parser = "pypdf"
    chunks: List[Dict] = []

    if recommended_parser == "docling" and USE_DOCLING:
        chunks = parse_with_docling(pdf_path)
        if chunks:
            parser = "docling"
        else:
            print(f"[WARN] Falling back to PyPDF for {pdf_path.name}")
            chunks = parse_with_pypdf(pdf_path)
            parser = "pypdf"
    else:
        chunks = parse_with_pypdf(pdf_path)
        parser = "pypdf"

    return {
        "file_name": pdf_path.name,
        "file_path": str(pdf_path.resolve()),
        "title": pdf_path.stem,
        "company_name": pdf_path.stem.split("_")[0] if "_" in pdf_path.stem else pdf_path.stem,
        "fiscal_year": None,
        "checksum": sha256_file(pdf_path),
        "parser": parser,
        "parser_decision": {
            "recommended_parser": recommended_parser,
            "reason": reason,
            "probe_metrics": probe,
        },
        "chunks": chunks,
    }