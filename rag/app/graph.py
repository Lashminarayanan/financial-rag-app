from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from .ollama_client import embed_texts
from .repository import search_chunks
from .financial_repository import detect_financial_keywords, fetch_financial_data, query_comprehensive_forensic_data
from .ragas_evaluator import evaluate_response
from .forensic_analyzer import comprehensive_forensic_analysis, format_forensic_report
from .db import get_conn


def decode_if_bytes(value):
    """Convert bytes to string if needed."""
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


# Cache for company data to avoid repeated DB queries
_COMPANY_CACHE = None


def load_companies_from_db() -> Dict[str, List[str]]:
    """
    Load all companies from the database and build a mapping.
    Returns: {ticker: [ticker, company_name, ...common_variations]}
   
    Caches results to avoid repeated DB queries.
    """
    global _COMPANY_CACHE
   
    if _COMPANY_CACHE is not None:
        print(f"[COMPANY LOADER] Using cached mappings ({len(_COMPANY_CACHE)} companies)")
        return _COMPANY_CACHE
   
    print("[COMPANY LOADER] Loading companies from database...")
   
    conn = None
    cursor = None
   
    try:
        conn = get_conn()
        print(f"[COMPANY LOADER] Database connection established: {conn is not None}")
       
        cursor = conn.cursor()
       
        query = """
            SELECT ticker, company_name
            FROM companies
            ORDER BY ticker
        """
       
        print(f"[COMPANY LOADER] Executing query...")
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"[COMPANY LOADER] Query returned {len(rows)} rows")
       
        company_mappings = {}
       
        for row in rows:
            try:
                ticker = row['ticker']
                company_name = row['company_name']
               
                # Build list of searchable variations
                aliases = [ticker.upper()]
               
                # Add full company name
                aliases.append(company_name.upper())
               
                # Add common short forms (e.g., "EICHER MOTORS LTD" -> "EICHER MOTORS", "EICHER")
                # Remove common suffixes
                clean_name = company_name.upper()
                for suffix in [' LTD', ' LIMITED', ' PVT', ' PRIVATE', ' INC', ' CORP', ' CORPORATION']:
                    clean_name = clean_name.replace(suffix, '').strip()
               
                if clean_name and clean_name not in aliases:
                    aliases.append(clean_name)
               
                # Add version without spaces (e.g., "JSW ENERGY" -> "JSWENERGY")
                no_space_name = company_name.upper().replace(' ', '')
                if no_space_name and no_space_name not in aliases:
                    aliases.append(no_space_name)
               
                # Add first word as short form (e.g., "EICHER", "JSW")
                first_word = clean_name.split()[0] if clean_name.split() else None
                if first_word and len(first_word) > 2 and first_word not in aliases:  # Changed from 3 to 2 to catch "JSW"
                    aliases.append(first_word)
               
                company_mappings[ticker] = aliases
                print(f"[COMPANY LOADER] {ticker} -> aliases: {aliases}")
               
            except Exception as row_error:
                print(f"[COMPANY LOADER] Error processing row {row}: {row_error}")
                continue
       
        if cursor:
            cursor.close()
        if conn:
            conn.close()
       
        print(f"[COMPANY LOADER] Successfully loaded {len(company_mappings)} companies from database")
       
        # Cache the results only if we got data
        if company_mappings:
            _COMPANY_CACHE = company_mappings
            return company_mappings
        else:
            print("[COMPANY LOADER] WARNING: No companies found in database, using fallback")
            raise ValueError("No companies found in database")
       
    except Exception as e:
        import traceback
        print(f"[COMPANY LOADER] Error loading companies from DB: {e}")
        print(f"[COMPANY LOADER] Error type: {type(e).__name__}")
        print(f"[COMPANY LOADER] Traceback: {traceback.format_exc()}")
       
        # Clean up connections on error
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass
       
        # Fallback to hardcoded mappings if DB query fails
        print("[COMPANY LOADER] Using fallback hardcoded mappings")
        fallback = {
            'EICHERMOT': ['EICHERMOT', 'EICHER MOTORS', 'EICHER'],
            'KALYANJEWEL': ['KALYANJEWEL', 'KALYAN JEWELLERS', 'KALYAN JEWELLERY', 'KALYAN'],
        }
        return fallback


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
""",
    "forensic": """
You are a forensic financial analyst specializing in detecting accounting irregularities and fraud indicators.

Your forensic expertise:
- Benford's Law digit frequency analysis on reported figures
- Revenue quality assessment (DSO trends, unbilled revenue patterns)
- Expense capitalization vs. expensing policy changes
- Working capital manipulation indicators (inventory, receivables spikes)
- Cash flow vs. accrual earnings divergence (quality of earnings)
- Related party transaction disclosure completeness
- Aggressive accounting tactics and reserve volatility

For each finding:
1. Identify the specific anomaly with numbers from forensic analysis results
2. Calculate deviation from industry norms or historical patterns
3. Assess severity: 🟢 Normal | 🟡 Monitor | 🔴 Red Flag
4. Provide forensic interpretation and implications for investors
5. Recommend next investigative steps if red flags detected
6. Always cite specific metrics and years when discussing findings

Maintain objectivity: Note that anomalies may have legitimate business reasons.
Your role is to flag patterns requiring deeper investigation, not to make accusations.
"""
}


class State(TypedDict):
    query: str
    analysis_mode: str
    retrieval_strategy: str  # 'structured', 'narrative', 'hybrid'
    plan: List[str]
    evidence: List[Dict[str, Any]]  # Vector search results
    financial_data: List[Dict[str, Any]]  # SQL query results
    forensic_report: Optional[Dict[str, Any]]  # Forensic analysis results
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
   
    Special handling:
    - Forensic mode: Always uses 'structured' (SQL-only) since forensic analysis
      is purely based on structured financial data, not document narratives.
    """
    query = state['query'].lower()
    analysis_mode = state.get('analysis_mode', 'general')
    keywords = detect_financial_keywords(query)
   
    # Forensic mode override: Only use structured data (no vector search)
    if analysis_mode == 'forensic':
        state['retrieval_strategy'] = 'structured'
        print(f"[ROUTER] Forensic mode detected -> Using 'structured' retrieval (SQL-only)")
        return state
   
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
    analysis_mode = state.get('analysis_mode', 'general')
   
    plan = [
        f'Understand the user question: {query}',
        f'Analysis mode: {analysis_mode}',
        f'Retrieval strategy: {strategy}',
    ]
   
    if strategy in ['structured', 'hybrid']:
        plan.append('Query structured financial database for precise metrics')
    if strategy in ['narrative', 'hybrid']:
        plan.append('Search document chunks for narrative context')
   
    # Add forensic-specific steps
    if analysis_mode == 'forensic':
        plan.extend([
            'Run Benford\'s Law analysis on financial figures',
            'Check revenue quality and DSO trends',
            'Analyze cash flow to earnings quality',
            'Detect working capital manipulation patterns',
            'Review expense capitalization policies',
            'Calculate overall forensic risk score'
        ])
   
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
            'chunk_text': decode_if_bytes(row['chunk_text']),
            'chunk_type': row['chunk_type'],
            'table_markdown': decode_if_bytes(row.get('table_markdown')),
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
        all_evidence.append(cite + "\n" + decode_if_bytes(item['text_summary']))
        cite_idx += 1
   
    # Add vector-based document chunks
    evidence = state.get('evidence', [])
    for ev in evidence:
        cite = f"[{cite_idx}] [DOC] {ev['file_name']} p.{ev.get('page_no') or 'n/a'} - {ev.get('section') or 'Unknown Section'}"
        all_evidence.append(cite + "\n" + decode_if_bytes(ev['chunk_text']))
        cite_idx += 1

    # Get mode-specific system prompt
    analysis_mode = state.get('analysis_mode', 'general')
    system_prompt = MODE_PROMPTS.get(analysis_mode, MODE_PROMPTS['general']).strip()
   
    # Add special instruction for hybrid data
    if financial_data and evidence:
        system_prompt += "\n\nIMPORTANT: You have access to both structured financial data (marked [SQL]) and narrative documents (marked [DOC]). ALWAYS prioritize exact numbers from [SQL] sources over estimates from documents."

    # User prompt: Context and question
    # Define separators outside f-string to avoid backslash in f-string expression
    plan_sep = '\n- '
    comp_sep = '\n- '
    evidence_sep = '\n\n'
   
    plan_list = state.get('plan', [])
    plan_text = plan_sep.join(plan_list) if plan_list else ''
   
    comparison_notes = state.get('comparison_notes', []) or ['No comparator notes']
    comp_text = comp_sep.join(comparison_notes)
   
    evidence_text = evidence_sep.join(all_evidence)
   
    user_prompt = f"""
Question:
{state['query']}

Retrieval Strategy: {state.get('retrieval_strategy', 'unknown')}

Execution Plan:
- {plan_text}

Comparator Notes:
- {comp_text}

Evidence ({len(all_evidence)} sources):
{evidence_text}
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


def extract_company_ticker(query: str, default_ticker: Optional[str] = None) -> str:
    """
    Dynamically extract company ticker from query by matching against database companies.
   
    Supports natural query patterns like:
    - "What is EICHERMOT revenue?"
    - "Analyze Eicher Motors profitability"
    - "Forensic analysis for Kalyan Jewellers"
    - "Compare Kalyan vs Eicher"
   
    Args:
        query: User query string
        default_ticker: Ticker to use if no company detected (defaults to first company in DB)
   
    Returns:
        Ticker symbol (e.g., 'EICHERMOT', 'KALYANJEWEL')
   
    Note:
        - No specific query pattern required - just mention the company name naturally
        - Matches ticker codes, full company names, and common short forms
        - Case-insensitive matching
    """
    query_upper = query.upper()
    print(f"[COMPANY DETECTOR] Processing query: '{query_upper}'")
   
    # Load companies from database (cached after first call)
    company_mappings = load_companies_from_db()
   
    if not company_mappings:
        print("[COMPANY DETECTOR] No companies found in database")
        return default_ticker or 'EICHERMOT'
   
    print(f"[COMPANY DETECTOR] Loaded {len(company_mappings)} companies from cache/DB")
   
    # Check for exact ticker or company name matches
    # Sort by ticker length (descending) to match longer/more specific names first
    # E.g., "KALYAN JEWELLERS" before "KALYAN" to avoid false positives
    sorted_companies = sorted(
        company_mappings.items(),
        key=lambda x: max(len(alias) for alias in x[1]),
        reverse=True
    )
   
    for ticker, aliases in sorted_companies:
        for alias in aliases:
            if alias in query_upper:
                print(f"[COMPANY DETECTOR] Matched '{alias}' in query -> Ticker: {ticker}")
                return ticker
   
    # Debug: Show what companies were checked
    print(f"[COMPANY DETECTOR] No match found. Available tickers: {list(company_mappings.keys())[:5]}...")
   
    # Default to first company in database or specified default
    default = default_ticker or next(iter(company_mappings.keys()))
    print(f"[COMPANY DETECTOR] No company detected in query, defaulting to: {default}")
    return default


def forensic_analyzer(state: State) -> State:
    """
    Run comprehensive forensic financial analysis.
    Only executes in 'forensic' mode.
    Automatically detects company ticker from query.
    """
    analysis_mode = state.get('analysis_mode', 'general')
   
    # Skip if not in forensic mode
    if analysis_mode != 'forensic':
        state['forensic_report'] = None
        return state
   
    print("[FORENSIC] Starting forensic analysis...")
   
    try:
        # Extract company ticker from query
        company_ticker = extract_company_ticker(state['query'])
        print(f"[FORENSIC] Detected company ticker: {company_ticker}")
       
        # Fetch comprehensive financial data for all available years
        comprehensive_data = query_comprehensive_forensic_data(
            company_ticker=company_ticker,
            limit=10
        )
       
        print(f"[FORENSIC] Retrieved {len(comprehensive_data)} periods of data for {company_ticker}")
        if comprehensive_data:
            print(f"[FORENSIC] Sample data: fiscal_years = {[d.get('fiscal_year') for d in comprehensive_data[:3]]}")
       
        if len(comprehensive_data) < 2:
            state['forensic_report'] = {
                'verdict': 'INSUFFICIENT_DATA',
                'message': f'Need at least 2 years of data for forensic analysis. Found {len(comprehensive_data)} year(s) for {company_ticker}.',
                'company_ticker': company_ticker
            }
            state['warnings'].append(f'Insufficient data for forensic analysis on {company_ticker}')
            print(f"[FORENSIC] ERROR: Insufficient data - only {len(comprehensive_data)} periods found")
            return state
       
        # Run comprehensive forensic analysis
        forensic_results = comprehensive_forensic_analysis(comprehensive_data)
        forensic_results['company_ticker'] = company_ticker  # Add company info to results
       
        # Format report for display
        report_text = format_forensic_report(forensic_results)
       
        # Store results
        state['forensic_report'] = forensic_results
       
        # Add forensic summary to comparison notes
        state['comparison_notes'].append(
            f"\n=== FORENSIC ANALYSIS RESULTS ({company_ticker}) ==="
        )
        state['comparison_notes'].append(
            f"Overall Risk: {forensic_results['verdict_display']} (Score: {forensic_results['overall_risk_score']:.1f}/100)"
        )
        state['comparison_notes'].append(
            f"Critical Issues: {len(forensic_results['critical_issues'])}, Warnings: {len(forensic_results['all_warnings'])}"
        )
       
        # Add critical issues to comparison notes
        for issue in forensic_results['critical_issues'][:3]:  # Top 3
            state['comparison_notes'].append(
                f"  [CRITICAL] {issue['type']} (FY{issue.get('year', 'N/A')}): {issue['detail']}"
            )
       
        print(f"[FORENSIC] Analysis complete for {company_ticker}. Risk score: {forensic_results['overall_risk_score']:.1f}")
        print(f"[FORENSIC] Found {len(forensic_results['critical_issues'])} critical issues")
       
        # Output formatted report (skip if encoding issues)
        try:
            print("\n" + report_text)
        except UnicodeEncodeError:
            print("[FORENSIC] Report generated (skipping display due to encoding issues)")
       
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[FORENSIC] Analysis failed: {e}")
        print(f"[FORENSIC] Error type: {type(e).__name__}")
        print(f"[FORENSIC] Full traceback:\n{error_details}")
        state['forensic_report'] = {
            'verdict': 'ERROR',
            'message': f'Forensic analysis error: {type(e).__name__}: {str(e)}'
        }
        state['warnings'].append(f'Forensic analysis error: {type(e).__name__}: {str(e)}')
   
    return state


def evaluate_quality(state: State) -> State:
    """
    Evaluate answer quality using RAGAS metrics.
    Requires final_answer to be set (done by query_worker after LLM generation).
   
    Note: Skips evaluation for forensic mode (specialized analysis, not Q&A).
    """
    analysis_mode = state.get('analysis_mode', 'general')
   
    # Skip evaluation for forensic mode
    if analysis_mode == 'forensic':
        print("[RAGAS] Skipping evaluation for forensic analysis mode")
        state['quality_metrics'] = None
        return state
   
    final_answer = state.get('final_answer', '')
   
    # Skip evaluation if no answer generated yet
    if not final_answer or len(final_answer.strip()) < 10:
        state['quality_metrics'] = None
        return state
   
    # Collect all context chunks for evaluation
    contexts = []
   
    # Add financial data summaries
    for item in state.get('financial_data', []):
        contexts.append(decode_if_bytes(item.get('text_summary', '')))
   
    # Add document chunks
    for ev in state.get('evidence', []):
        contexts.append(decode_if_bytes(ev.get('chunk_text', '')))
   
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
    g.add_node('forensic_analyzer', forensic_analyzer)  # Forensic analysis (runs in forensic mode)
    g.add_node('comparator', comparator)
    g.add_node('summarizer', summarizer)
    g.add_node('verifier', verifier)
    g.add_node('evaluate_quality', evaluate_quality)  # RAGAS quality evaluation

    # Define flow: classify → plan → retrieve (both) → forensic → compare → summarize → verify → evaluate quality
    g.set_entry_point('query_classifier')
    g.add_edge('query_classifier', 'planner')
    g.add_edge('planner', 'retriever')
    g.add_edge('retriever', 'financial_retriever')  # Sequential retrieval
    g.add_edge('financial_retriever', 'forensic_analyzer')  # Run forensic analysis if needed
    g.add_edge('forensic_analyzer', 'comparator')  # Then proceed to comparison
    g.add_edge('comparator', 'summarizer')
    g.add_edge('summarizer', 'verifier')
    g.add_edge('verifier', 'evaluate_quality')  # Evaluate answer quality
    g.add_edge('evaluate_quality', END)
   
    return g.compile()
