from __future__ import annotations

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from .ollama_client import embed_texts, generate_answer_stream
from .repository import search_chunks


class State(TypedDict):
    query: str
    plan: List[str]
    evidence: List[Dict[str, Any]]
    comparison_notes: List[str]
    prompt: str
    verified: bool
    warnings: List[str]


def planner(state: State) -> State:
    query = state['query']
    plan = [
        f'Understand the user question: {query}',
        'Retrieve semantically related chunks and tables',
        'Compare numerical facts or risk statements if multiple references are present',
        'Draft a concise answer with citations',
        'Verify claims are grounded in evidence',
    ]
    state['plan'] = plan
    return state


def retriever(state: State) -> State:
    vector = embed_texts([state['query']])[0]
    rows = search_chunks(vector, limit=6)

    evidence = []
    for row in rows:
        evidence.append({
            'id': str(row['id']),
            'document_id': str(row['document_id']),
            'chunk_index': row['chunk_index'],
            'page_no': row.get('page_no'),
            'section': row.get('section'),
            'chunk_text': row['chunk_text'],
            'chunk_type': row['chunk_type'],
            'table_markdown': row.get('table_markdown'),
            'metadata': row.get('metadata') or {},
            'file_name': row['file_name'],
            'similarity': float(row['similarity']) if row.get('similarity') is not None else None,
        })

    state['evidence'] = evidence
    return state


def comparator(state: State) -> State:
    notes = []
    evidence = state.get('evidence', [])
    if len(evidence) >= 2:
        notes.append('Multiple evidence chunks retrieved; compare narrative consistency and numerical trends.')
    if any(e.get('table_markdown') for e in evidence):
        notes.append('Table-derived evidence is available and should be prioritized for metrics.')
    state['comparison_notes'] = notes
    return state


def summarizer(state: State) -> State:
    evidences = []
    for idx, ev in enumerate(state.get('evidence', []), start=1):
        cite = f"[{idx}] {ev['file_name']} p.{ev.get('page_no') or 'n/a'} - {ev.get('section') or 'Unknown Section'}"
        evidences.append(cite + "\n" + ev['chunk_text'])

    prompt = f"""
You are a financial research assistant running completely offline.
Answer the question only from the evidence below.
If evidence is insufficient, explicitly say so.
Include citation markers like [1], [2], [3] in the answer.

Question:
{state['query']}

Execution plan:
- {'\n- '.join(state.get('plan', []))}

Comparator notes:
- {'\n- '.join(state.get('comparison_notes', []) or ['No comparator notes'])}

Evidence:
{'\n\n'.join(evidences)}
""".strip()
    state['prompt'] = prompt
    return state


def verifier(state: State) -> State:
    evidence_count = len(state.get('evidence', []))
    state['verified'] = evidence_count > 0
    state['warnings'] = [] if evidence_count else ['No evidence retrieved for this query.']
    return state


def build_graph():
    g = StateGraph(State)
    g.add_node('planner', planner)
    g.add_node('retriever', retriever)
    g.add_node('comparator', comparator)
    g.add_node('summarizer', summarizer)
    g.add_node('verifier', verifier)

    g.set_entry_point('planner')
    g.add_edge('planner', 'retriever')
    g.add_edge('retriever', 'comparator')
    g.add_edge('comparator', 'summarizer')
    g.add_edge('summarizer', 'verifier')
    g.add_edge('verifier', END)
    return g.compile()
