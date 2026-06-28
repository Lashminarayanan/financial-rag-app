from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from .db import get_conn


def detect_financial_keywords(query: str) -> Dict[str, bool]:
    """
    Detect which financial metrics are mentioned in the query.
    Returns dict of metric categories and whether they're present.
    """
    query_lower = query.lower()
   
    return {
        'revenue': any(kw in query_lower for kw in ['revenue', 'sales', 'turnover', 'top line', 'topline']),
        'profit': any(kw in query_lower for kw in ['profit', 'earnings', 'net income', 'pat', 'ebitda', 'ebit', 'operating profit']),
        'eps': 'eps' in query_lower or 'earnings per share' in query_lower,
        'margin': any(kw in query_lower for kw in ['margin', 'profitability', 'npm', 'opm']),
        'ratio': any(kw in query_lower for kw in ['roe', 'roa', 'roce', 'roic', 'p/e', 'pe ratio', 'p/b', 'debt to equity', 'd/e']),
        'balance_sheet': any(kw in query_lower for kw in ['assets', 'liabilities', 'equity', 'debt', 'cash', 'inventory', 'receivables']),
        'cash_flow': any(kw in query_lower for kw in ['cash flow', 'fcf', 'free cash flow', 'ocf', 'operating cash']),
        'growth': any(kw in query_lower for kw in ['growth', 'yoy', 'year over year', 'cagr', 'trend', 'increase', 'decrease']),
        'compare': any(kw in query_lower for kw in ['compare', 'comparison', 'vs', 'versus', 'against', 'between']),
    }


def extract_year_mentions(query: str) -> List[int]:
    """Extract year mentions like FY23, FY2023, 2023, etc."""
    years = []
   
    # FY23, FY2023
    fy_matches = re.findall(r'fy\s*(\d{2,4})', query.lower())
    for match in fy_matches:
        year = int(match)
        if year < 100:  # FY23 -> 2023
            year = 2000 + year
        years.append(year)
   
    # Plain years like 2023
    year_matches = re.findall(r'\b(20\d{2})\b', query)
    years.extend([int(y) for y in year_matches])
   
    return sorted(set(years))


def query_income_statements(
    company_ticker: str = 'EICHERMOT',
    fiscal_years: Optional[List[int]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Query income statement data (P&L metrics).
   
    Returns list of dicts with fiscal_year, sales, profit, eps, margins, etc.
    """
    conn = get_conn()
    cursor = conn.cursor()
   
    try:
        query = """
            SELECT
                c.company_name,
                c.ticker,
                fp.fiscal_year,
                fp.period_type,
                i.sales,
                i.other_income,
                i.operating_profit,
                i.ebitda,
                i.profit_before_tax,
                i.tax,
                i.net_profit,
                i.eps,
                i.operating_margin_pct,
                i.net_margin_pct
            FROM income_statements i
            JOIN financial_periods fp ON i.period_id = fp.id
            JOIN companies c ON fp.company_id = c.id
            WHERE c.ticker = %s
              AND fp.period_type = 'annual'
        """
       
        params = [company_ticker]
       
        if fiscal_years:
            placeholders = ','.join(['%s'] * len(fiscal_years))
            query += f" AND fp.fiscal_year IN ({placeholders})"
            params.extend(fiscal_years)
       
        query += " ORDER BY fp.fiscal_year DESC LIMIT %s"
        params.append(limit)
       
        cursor.execute(query, params)
        rows = cursor.fetchall()
       
        results = []
        for row in rows:
            results.append({
                'company_name': row['company_name'],
                'ticker': row['ticker'],
                'fiscal_year': row['fiscal_year'],
                'period_type': row['period_type'],
                'sales': float(row['sales']) if row['sales'] else None,
                'other_income': float(row['other_income']) if row['other_income'] else None,
                'operating_profit': float(row['operating_profit']) if row['operating_profit'] else None,
                'ebitda': float(row['ebitda']) if row['ebitda'] else None,
                'profit_before_tax': float(row['profit_before_tax']) if row['profit_before_tax'] else None,
                'tax': float(row['tax']) if row['tax'] else None,
                'net_profit': float(row['net_profit']) if row['net_profit'] else None,
                'eps': float(row['eps']) if row['eps'] else None,
                'operating_margin_pct': float(row['operating_margin_pct']) if row['operating_margin_pct'] else None,
                'net_margin_pct': float(row['net_margin_pct']) if row['net_margin_pct'] else None,
            })
       
        return results
       
    finally:
        cursor.close()
        conn.close()


def query_balance_sheets(
    company_ticker: str = 'EICHERMOT',
    fiscal_years: Optional[List[int]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Query balance sheet data (assets, liabilities, equity)."""
    conn = get_conn()
    cursor = conn.cursor()
   
    try:
        query = """
            SELECT
                c.company_name,
                fp.fiscal_year,
                b.equity_share_capital,
                b.reserves,
                b.borrowings,
                b.total_liabilities,
                b.net_fixed_assets,
                b.investments,
                b.total_assets,
                b.receivables,
                b.inventory,
                b.cash_and_equivalents
            FROM balance_sheets b
            JOIN financial_periods fp ON b.period_id = fp.id
            JOIN companies c ON fp.company_id = c.id
            WHERE c.ticker = %s
              AND fp.period_type = 'annual'
        """
       
        params = [company_ticker]
       
        if fiscal_years:
            placeholders = ','.join(['%s'] * len(fiscal_years))
            query += f" AND fp.fiscal_year IN ({placeholders})"
            params.extend(fiscal_years)
       
        query += " ORDER BY fp.fiscal_year DESC LIMIT %s"
        params.append(limit)
       
        cursor.execute(query, params)
        rows = cursor.fetchall()
       
        results = []
        for row in rows:
            equity = (float(row['equity_share_capital']) if row['equity_share_capital'] else 0) + (float(row['reserves']) if row['reserves'] else 0)
            debt_to_equity = (float(row['borrowings']) / equity * 100) if (row['borrowings'] and equity > 0) else None
           
            results.append({
                'company_name': row['company_name'],
                'fiscal_year': row['fiscal_year'],
                'equity_share_capital': float(row['equity_share_capital']) if row['equity_share_capital'] else None,
                'reserves': float(row['reserves']) if row['reserves'] else None,
                'borrowings': float(row['borrowings']) if row['borrowings'] else None,
                'total_liabilities': float(row['total_liabilities']) if row['total_liabilities'] else None,
                'net_fixed_assets': float(row['net_fixed_assets']) if row['net_fixed_assets'] else None,
                'investments': float(row['investments']) if row['investments'] else None,
                'total_assets': float(row['total_assets']) if row['total_assets'] else None,
                'receivables': float(row['receivables']) if row['receivables'] else None,
                'inventory': float(row['inventory']) if row['inventory'] else None,
                'cash_and_equivalents': float(row['cash_and_equivalents']) if row['cash_and_equivalents'] else None,
                'total_equity': equity,
                'debt_to_equity_pct': debt_to_equity,
            })
       
        return results
       
    finally:
        cursor.close()
        conn.close()


def query_cash_flows(
    company_ticker: str = 'EICHERMOT',
    fiscal_years: Optional[List[int]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Query cash flow statement data."""
    conn = get_conn()
    cursor = conn.cursor()
   
    try:
        query = """
            SELECT
                c.company_name,
                fp.fiscal_year,
                cf.operating_cash_flow,
                cf.investing_cash_flow,
                cf.financing_cash_flow,
                cf.net_cash_flow,
                cf.free_cash_flow,
                cf.capex
            FROM cash_flows cf
            JOIN financial_periods fp ON cf.period_id = fp.id
            JOIN companies c ON fp.company_id = c.id
            WHERE c.ticker = %s
              AND fp.period_type = 'annual'
        """
       
        params = [company_ticker]
       
        if fiscal_years:
            placeholders = ','.join(['%s'] * len(fiscal_years))
            query += f" AND fp.fiscal_year IN ({placeholders})"
            params.extend(fiscal_years)
       
        query += " ORDER BY fp.fiscal_year DESC LIMIT %s"
        params.append(limit)
       
        cursor.execute(query, params)
        rows = cursor.fetchall()
       
        results = []
        for row in rows:
            results.append({
                'company_name': row['company_name'],
                'fiscal_year': row['fiscal_year'],
                'operating_cash_flow': float(row['operating_cash_flow']) if row['operating_cash_flow'] else None,
                'investing_cash_flow': float(row['investing_cash_flow']) if row['investing_cash_flow'] else None,
                'financing_cash_flow': float(row['financing_cash_flow']) if row['financing_cash_flow'] else None,
                'net_cash_flow': float(row['net_cash_flow']) if row['net_cash_flow'] else None,
                'free_cash_flow': float(row['free_cash_flow']) if row['free_cash_flow'] else None,
                'capex': float(row['capex']) if row['capex'] else None,
            })
       
        return results
       
    finally:
        cursor.close()
        conn.close()


def fetch_financial_data(query: str, company_ticker: str = 'EICHERMOT') -> List[Dict[str, Any]]:
    """
    Main entry point: Analyze query and fetch relevant financial data.
   
    Returns list of financial data items with metadata.
    """
    keywords = detect_financial_keywords(query)
    years = extract_year_mentions(query)
   
    financial_items = []
   
    # Income statement metrics
    if any([keywords['revenue'], keywords['profit'], keywords['eps'], keywords['margin']]):
        income_data = query_income_statements(
            company_ticker=company_ticker,
            fiscal_years=years if years else None,
            limit=5
        )
       
        for item in income_data:
            financial_items.append({
                'source_type': 'structured_sql',
                'data_category': 'income_statement',
                'fiscal_year': item['fiscal_year'],
                'company': item['company_name'],
                'metrics': item,
                'text_summary': format_income_statement(item)
            })
   
    # Balance sheet metrics
    if keywords['balance_sheet']:
        balance_data = query_balance_sheets(
            company_ticker=company_ticker,
            fiscal_years=years if years else None,
            limit=5
        )
       
        for item in balance_data:
            financial_items.append({
                'source_type': 'structured_sql',
                'data_category': 'balance_sheet',
                'fiscal_year': item['fiscal_year'],
                'company': item['company_name'],
                'metrics': item,
                'text_summary': format_balance_sheet(item)
            })
   
    # Cash flow metrics
    if keywords['cash_flow']:
        cash_data = query_cash_flows(
            company_ticker=company_ticker,
            fiscal_years=years if years else None,
            limit=5
        )
       
        for item in cash_data:
            financial_items.append({
                'source_type': 'structured_sql',
                'data_category': 'cash_flow',
                'fiscal_year': item['fiscal_year'],
                'company': item['company_name'],
                'metrics': item,
                'text_summary': format_cash_flow(item)
            })
   
    return financial_items


def format_income_statement(data: Dict) -> str:
    """Format income statement data as readable text."""
    parts = [f"FY{data['fiscal_year']} Income Statement - {data['company_name']}:"]
   
    if data['sales']:
        parts.append(f"  • Sales: ₹{data['sales']:.2f} Cr")
    if data['operating_profit']:
        parts.append(f"  • Operating Profit: ₹{data['operating_profit']:.2f} Cr")
    if data['net_profit']:
        parts.append(f"  • Net Profit: ₹{data['net_profit']:.2f} Cr")
    if data['eps']:
        parts.append(f"  • EPS: ₹{data['eps']:.2f}")
    if data['operating_margin_pct']:
        parts.append(f"  • Operating Margin: {data['operating_margin_pct']:.2f}%")
    if data['net_margin_pct']:
        parts.append(f"  • Net Margin: {data['net_margin_pct']:.2f}%")
   
    return '\n'.join(parts)


def format_balance_sheet(data: Dict) -> str:
    """Format balance sheet data as readable text."""
    parts = [f"FY{data['fiscal_year']} Balance Sheet - {data['company_name']}:"]
   
    if data['total_assets']:
        parts.append(f"  • Total Assets: ₹{data['total_assets']:.2f} Cr")
    if data['total_equity']:
        parts.append(f"  • Total Equity: ₹{data['total_equity']:.2f} Cr")
    if data['borrowings']:
        parts.append(f"  • Borrowings: ₹{data['borrowings']:.2f} Cr")
    if data['debt_to_equity_pct']:
        parts.append(f"  • Debt-to-Equity: {data['debt_to_equity_pct']:.2f}%")
    if data['cash_and_equivalents']:
        parts.append(f"  • Cash: ₹{data['cash_and_equivalents']:.2f} Cr")
   
    return '\n'.join(parts)


def format_cash_flow(data: Dict) -> str:
    """Format cash flow data as readable text."""
    parts = [f"FY{data['fiscal_year']} Cash Flow - {data['company_name']}:"]
   
    if data['operating_cash_flow']:
        parts.append(f"  • Operating Cash Flow: ₹{data['operating_cash_flow']:.2f} Cr")
    if data['free_cash_flow']:
        parts.append(f"  • Free Cash Flow: ₹{data['free_cash_flow']:.2f} Cr")
    if data['capex']:
        parts.append(f"  • Capex: ₹{data['capex']:.2f} Cr")
   
    return '\n'.join(parts)


def query_comprehensive_forensic_data(
    company_ticker: str = 'EICHERMOT',
    fiscal_years: Optional[List[int]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Query comprehensive financial data for forensic analysis.
    Joins income statement, balance sheet, and cash flow data.
   
    Returns list of dicts with all key metrics per period for forensic checks.
    """
    conn = get_conn()
    cursor = conn.cursor()
   
    try:
        query = """
            SELECT
                c.company_name,
                c.ticker,
                fp.fiscal_year,
                fp.period_type,
                -- Income Statement
                i.sales,
                i.other_income,
                i.operating_profit,
                i.net_profit,
                i.eps,
                i.depreciation,
                i.operating_margin_pct,
                i.net_margin_pct,
                -- Balance Sheet
                b.total_assets,
                b.total_liabilities,
                b.equity_share_capital,
                b.reserves,
                b.borrowings,
                b.net_fixed_assets,
                b.capital_wip,
                b.inventory,
                b.receivables,
                b.cash_and_equivalents,
                -- Cash Flow
                cf.operating_cash_flow,
                cf.free_cash_flow,
                cf.capex
            FROM financial_periods fp
            JOIN companies c ON fp.company_id = c.id
            LEFT JOIN income_statements i ON i.period_id = fp.id
            LEFT JOIN balance_sheets b ON b.period_id = fp.id
            LEFT JOIN cash_flows cf ON cf.period_id = fp.id
            WHERE c.ticker = %s
              AND fp.period_type = 'annual'
        """
       
        params = [company_ticker]
       
        if fiscal_years:
            placeholders = ','.join(['%s'] * len(fiscal_years))
            query += f" AND fp.fiscal_year IN ({placeholders})"
            params.extend(fiscal_years)
       
        query += " ORDER BY fp.fiscal_year DESC LIMIT %s"
        params.append(limit)
       
        print(f"[SQL] Executing forensic data query for ticker: {company_ticker}")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        print(f"[SQL] Query returned {len(rows)} rows")
       
        results = []
        for row in rows:
            equity = (float(row['equity_share_capital']) if row['equity_share_capital'] else 0) + (float(row['reserves']) if row['reserves'] else 0)
           
            results.append({
                'company_name': row['company_name'],
                'ticker': row['ticker'],
                'fiscal_year': row['fiscal_year'],
                'period_type': row['period_type'],
                # P&L
                'sales': float(row['sales']) if row['sales'] else None,
                'other_income': float(row['other_income']) if row['other_income'] else None,
                'operating_profit': float(row['operating_profit']) if row['operating_profit'] else None,
                'net_profit': float(row['net_profit']) if row['net_profit'] else None,
                'eps': float(row['eps']) if row['eps'] else None,
                'depreciation': float(row['depreciation']) if row['depreciation'] else None,
                'operating_margin_pct': float(row['operating_margin_pct']) if row['operating_margin_pct'] else None,
                'net_margin_pct': float(row['net_margin_pct']) if row['net_margin_pct'] else None,
                # Balance Sheet
                'total_assets': float(row['total_assets']) if row['total_assets'] else None,
                'total_liabilities': float(row['total_liabilities']) if row['total_liabilities'] else None,
                'equity_share_capital': float(row['equity_share_capital']) if row['equity_share_capital'] else None,
                'reserves': float(row['reserves']) if row['reserves'] else None,
                'borrowings': float(row['borrowings']) if row['borrowings'] else None,
                'net_fixed_assets': float(row['net_fixed_assets']) if row['net_fixed_assets'] else None,
                'capital_wip': float(row['capital_wip']) if row['capital_wip'] else None,
                'inventory': float(row['inventory']) if row['inventory'] else None,
                'receivables': float(row['receivables']) if row['receivables'] else None,
                'cash_and_equivalents': float(row['cash_and_equivalents']) if row['cash_and_equivalents'] else None,
                'total_equity': equity,
                # Cash Flow
                'operating_cash_flow': float(row['operating_cash_flow']) if row['operating_cash_flow'] else None,
                'free_cash_flow': float(row['free_cash_flow']) if row['free_cash_flow'] else None,
                'capex': float(row['capex']) if row['capex'] else None,
            })
       
        if results:
            print(f"[SQL] Sample result: FY{results[0]['fiscal_year']} - {results[0]['company_name']}")
       
        return results
       
    finally:
        cursor.close()
        conn.close()
