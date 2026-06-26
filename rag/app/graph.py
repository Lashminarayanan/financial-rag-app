from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from .ollama_client import embed_texts
from .repository import search_chunks
from .financial_repository import detect_financial_keywords, fetch_financial_data
from .ragas_evaluator import evaluate_response


# Analyst persona system prompts
MODE_PROMPTS = {
    "general": """
You are a financial research assistant specialized in analyzing annual reports and financial documents.

Your responsibilities:
- Answer questions ONLY using the evidence provided
- Use specific numbers, percentages, and metrics from the evidence
- Include citation markers [1], [2], [3] to reference evidence sources
- If evidence is insufficient or unclear, explicitly state this
- Maintain objectivity and avoid speculation beyond the provided data
- Highlight key financial trends, risks, and insights when relevant
""",
    "revenue": """
You are a revenue analyst specializing in sales analysis and growth trends.

Your focus areas:
- Revenue figures, growth rates, and year-over-year comparisons
- Segment-wise revenue breakdown (product lines, geographies, business units)
- Revenue drivers and factors affecting sales performance
- Market share trends and competitive positioning
- Use specific numbers and percentages from evidence
- Include citation markers [1], [2], [3] for all claims
- Flag any revenue recognition concerns or irregularities
""",
    "profitability": """
You are a profitability analyst specializing in margin analysis and operational efficiency.

Your focus areas:
- Net profit, EBITDA, operating profit, and margin trends
- EPS (Earnings Per Share) growth and quality
- ROE (Return on Equity), ROA (Return on Assets), ROCE (Return on Capital Employed)
- Cost structure analysis and operational leverage
- Profitability drivers and efficiency improvements
- Use specific numbers and percentages from evidence
- Include citation markers [1], [2], [3] for all metrics
- Analyze margin expansion or contraction with reasons
""",
    "risk": """
You are a risk analyst specializing in identifying and assessing business risks.

Your focus areas:
- Identify ALL risk factors mentioned in the evidence
- Categorize risks: operational, financial, market, regulatory, ESG
- Assess potential impact and likelihood of each risk
- Highlight emerging risks or changes in risk profile
- Note management's risk mitigation strategies
- Include citation markers [1], [2], [3] for each risk
- Prioritize material risks that could impact business performance
- Flag any red flags or concerns requiring deeper investigation
""",
    "valuation": """
You are a valuation analyst specializing in equity analysis and investment metrics.

Your focus areas:
- Valuation multiples: P/E, P/B, P/S, EV/EBITDA ratios
- DCF assumptions: growth rates, margins, WACC components
- Peer comparison and relative valuation
- Intrinsic value indicators and fair value assessment
- Dividend policy and shareholder returns
- Use specific numbers from evidence for all calculations
- Include citation markers [1], [2], [3] for data points
- Highlight valuation concerns or attractive entry points
"""
}


class State(TypedDict):
    query: str
    analysis_mode: str
    retrieval_strategy: str  # 'structured', 'narrative', 'hybrid'
    plan: List[str]
    evidence: List[Dict[str, Any]]  # Vector search results
    financial_data: List[Dict[str, Any]]  # SQL query results
    comparison_notes: List[str]
    system_prompt: str
    user_prompt: str
    verified: bool
    warnings: List[str]
    final_answer: Optional[str]  # Generated answer for quality evaluation
    quality_metrics: Optional[Dict[str, float]]  # RAGAS evaluation scores


def query_classifier(state: State) -> State:
    """
    Smart router: Classify query type to determine retrieval strategy.
    - 'structured': SQL-only (precise metrics queries)
    - 'narrative': Vector-only (explanatory/contextual queries)
    - 'hybrid': Both (complex analytical queries)
    """
    query = state['query'].lower()
    keywords = detect_financial_keywords(query)
    
    # Check for metric-focused queries
    has_metrics = any([
        keywords['revenue'], keywords['profit'], keywords['eps'],
        keywords['margin'], keywords['ratio'], keywords['cash_flow']
    ])
    
    # Check for narrative/explanatory queries
    narrative_signals = any(word in query for word in [
        'why', 'how', 'explain', 'describe', 'discuss',
        'strategy', 'outlook', 'risk', 'opportunity', 'challenge',
        'management', 'business model', 'competitive'
    ])
    
    # Check for comparison/trend queries (need both data + context)
    comparison_signals = keywords['compare'] or keywords['growth'] or any(word in query for word in [
        'trend', 'compare', 'versus', 'better', 'worse', 'impact'
    ])
    
    # Decision logic
    if has_metrics and not narrative_signals:
        strategy = 'structured'  # Pure metric query → SQL only
    elif narrative_signals and not has_metrics:
        strategy = 'narrative'   # Pure explanatory query → Vector only
    else:
        strategy = 'hybrid'      # Complex query → Both sources
    
    state['retrieval_strategy'] = strategy
    print(f"[ROUTER] Query classified as: {strategy} | metrics={has_metrics}, narrative={narrative_signals}")
    return state


def planner(state: State) -> State:
    query = state['query']
    strategy = state.get('retrieval_strategy', 'hybrid')
    
    plan = [
        f'Understand the user question: {query}',
        f'Retrieval strategy: {strategy}',
    ]
    
    if strategy in ['structured', 'hybrid']:
        plan.append('Query structured financial database for precise metrics')
    if strategy in ['narrative', 'hybrid']:
        plan.append('Search document chunks for narrative context')
    
    plan.extend([
        'Compare and validate information from all sources',
        'Draft comprehensive answer with citations',
        'Verify claims are grounded in evidence',
    ])
    
    state['plan'] = plan
    return state


def retriever(state: State) -> State:
    """Vector-based document chunk retrieval."""
    strategy = state.get('retrieval_strategy', 'hybrid')
    
    # Skip vector search if strategy is 'structured' (SQL-only)
    if strategy == 'structured':
        state['evidence'] = []
        print("[RETRIEVER] Skipping vector search (structured-only strategy)")
        return state
    
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
            'source_type': 'vector_chunk',  # Mark source type
        })

    state['evidence'] = evidence
    print(f"[RETRIEVER] Retrieved {len(evidence)} vector chunks")
    return state


def financial_retriever(state: State) -> State:
    """SQL-based structured financial data retrieval."""
    strategy = state.get('retrieval_strategy', 'hybrid')
    
    # Skip SQL if strategy is 'narrative' (vector-only)
    if strategy == 'narrative':
        state['financial_data'] = []
        print("[FINANCIAL_RETRIEVER] Skipping SQL (narrative-only strategy)")
        return state
    
    try:
        financial_items = fetch_financial_data(state['query'])
        state['financial_data'] = financial_items
        print(f"[FINANCIAL_RETRIEVER] Retrieved {len(financial_items)} structured items")
    except Exception as e:
        print(f"[FINANCIAL_RETRIEVER] Error: {e}")
        state['financial_data'] = []
        state['warnings'] = state.get('warnings', []) + [f"Financial data retrieval failed: {str(e)}"]
    
    return state


def comparator(state: State) -> State:
    notes = []
    evidence = state.get('evidence', [])
    financial_data = state.get('financial_data', [])
    
    # Note evidence sources
    if evidence and financial_data:
        notes.append('Hybrid retrieval: Combining structured financial data with narrative context from documents.')
    elif financial_data and not evidence:
        notes.append('Using structured financial data only for precise metrics.')
    elif evidence and not financial_data:
        notes.append('Using document narrative only (no structured data available).')
    
    if len(evidence) >= 2:
        notes.append('Multiple document chunks retrieved; comparing narrative consistency and numerical trends.')
    
    if any(e.get('table_markdown') for e in evidence):
        notes.append('Table-derived evidence from documents is available and should be prioritized for metrics.')
    
    if len(financial_data) >= 2:
        notes.append(f'Multiple years of financial data retrieved ({len(financial_data)} periods); enable trend analysis.')
    
    state['comparison_notes'] = notes
    return state


def summarizer(state: State) -> State:
    all_evidence = []
    cite_idx = 1
    
    # Add structured financial data first (higher priority for metrics)
    financial_data = state.get('financial_data', [])
    for item in financial_data:
        cite = f"[{cite_idx}] [SQL] {item['data_category'].upper()} - FY{item['fiscal_year']}"
        all_evidence.append(cite + "\n" + item['text_summary'])
        cite_idx += 1
    
    # Add vector-based document chunks
    evidence = state.get('evidence', [])
    for ev in evidence:
        cite = f"[{cite_idx}] [DOC] {ev['file_name']} p.{ev.get('page_no') or 'n/a'} - {ev.get('section') or 'Unknown Section'}"
        all_evidence.append(cite + "\n" + ev['chunk_text'])
        cite_idx += 1

    # Get mode-specific system prompt
    analysis_mode = state.get('analysis_mode', 'general')
    system_prompt = MODE_PROMPTS.get(analysis_mode, MODE_PROMPTS['general']).strip()
    
    # Add special instruction for hybrid data
    if financial_data and evidence:
        system_prompt += "\n\nIMPORTANT: You have access to both structured financial data (marked [SQL]) and narrative documents (marked [DOC]). ALWAYS prioritize exact numbers from [SQL] sources over estimates from documents."

    # User prompt: Context and question
    user_prompt = f"""
Question:
{state['query']}

Retrieval Strategy: {state.get('retrieval_strategy', 'unknown')}

Execution Plan:
- {'\n- '.join(state.get('plan', []))}

Comparator Notes:
- {'\n- '.join(state.get('comparison_notes', []) or ['No comparator notes'])}

Evidence ({len(all_evidence)} sources):
{'\n\n'.join(all_evidence)}
""".strip()

    state['system_prompt'] = system_prompt
    state['user_prompt'] = user_prompt
    return state


def verifier(state: State) -> State:
    evidence_count = len(state.get('evidence', []))
    financial_count = len(state.get('financial_data', []))
    total_sources = evidence_count + financial_count
    
    state['verified'] = total_sources > 0
    
    warnings = []
    if total_sources == 0:
        warnings.append('No evidence retrieved from any source (vector or SQL).')
    elif evidence_count == 0 and financial_count > 0:
        warnings.append('Only structured data available; narrative context may be limited.')
    elif financial_count == 0 and evidence_count > 0:
        warnings.append('No structured financial data found; relying on document narratives only.')
    
    state['warnings'] = warnings
    return state


def evaluate_quality(state: State) -> State:
    """
    Evaluate answer quality using RAGAS metrics.
    Requires final_answer to be set (done by query_worker after LLM generation).
    """
    final_answer = state.get('final_answer', '')
    
    # Skip evaluation if no answer generated yet
    if not final_answer or len(final_answer.strip()) < 10:
        state['quality_metrics'] = None
        return state
    
    # Collect all context chunks for evaluation
    contexts = []
    
    # Add financial data summaries
    for item in state.get('financial_data', []):
        contexts.append(item.get('text_summary', ''))
    
    # Add document chunks
    for ev in state.get('evidence', []):
        contexts.append(ev.get('chunk_text', ''))
    
    # Only evaluate if we have context
    if not contexts:
        state['quality_metrics'] = None
        return state
    
    # Run RAGAS evaluation
    try:
        metrics = evaluate_response(
            query=state['query'],
            answer=final_answer,
            contexts=contexts
        )
        state['quality_metrics'] = metrics
    except Exception as e:
        print(f"Quality evaluation failed: {e}")
        state['quality_metrics'] = None
    
    return state


def build_graph():
    g = StateGraph(State)
    
    # Add nodes
    g.add_node('query_classifier', query_classifier)
    g.add_node('planner', planner)
    g.add_node('retriever', retriever)  # Vector search
    g.add_node('financial_retriever', financial_retriever)  # SQL queries
    g.add_node('comparator', comparator)
    g.add_node('summarizer', summarizer)
    g.add_node('verifier', verifier)
    g.add_node('evaluate_quality', evaluate_quality)  # RAGAS quality evaluation

    # Define flow: classify → plan → retrieve (both) → compare → summarize → verify → evaluate quality
    g.set_entry_point('query_classifier')
    g.add_edge('query_classifier', 'planner')
    g.add_edge('planner', 'retriever')
    g.add_edge('retriever', 'financial_retriever')  # Sequential retrieval
    g.add_edge('financial_retriever', 'comparator')
    g.add_edge('comparator', 'summarizer')
    g.add_edge('summarizer', 'verifier')
    g.add_edge('verifier', 'evaluate_quality')  # Evaluate answer quality
    g.add_edge('evaluate_quality', END)
    
    return g.compile()
