from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_no: Optional[int] = None
    section: Optional[str] = None
    chunk_text: str
    chunk_type: str = 'text'
    table_markdown: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity: Optional[float] = None


class QueryState(BaseModel):
    query: str
    plan: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    comparison_notes: List[str] = Field(default_factory=list)
    answer: str = ''
    verified: bool = False
    warnings: List[str] = Field(default_factory=list)
