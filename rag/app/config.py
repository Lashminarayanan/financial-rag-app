
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "financial_rag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_pass")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

REPORTS_DIR = os.getenv("REPORTS_DIR", str(ROOT / "sample_data" / "reports"))
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))

# Parsing controls
# USE_DOCLING=false  -> safest setting for MVP
# DOCLING_PREFER=true -> try Docling first if enabled
USE_DOCLING = os.getenv("USE_DOCLING", "false").strip().lower() == "true"
DOCLING_PREFER = os.getenv("DOCLING_PREFER", "false").strip().lower() == "true"

AUTO_PARSER_ROUTE = os.getenv("AUTO_PARSER_ROUTE", "true").strip().lower() == "true"
MAX_PROBE_PAGES = int(os.getenv("MAX_PROBE_PAGES", "10"))
MIN_AVG_CHARS_PER_PAGE = int(os.getenv("MIN_AVG_CHARS_PER_PAGE", "250"))
MAX_EMPTY_PAGE_RATIO = float(os.getenv("MAX_EMPTY_PAGE_RATIO", "0.30"))
TABLE_SIGNAL_RATIO_THRESHOLD = float(os.getenv("TABLE_SIGNAL_RATIO_THRESHOLD", "0.35"))
TABLE_EXTRACTION_PRIORITY = os.getenv("TABLE_EXTRACTION_PRIORITY", "true").strip().lower() == "true"