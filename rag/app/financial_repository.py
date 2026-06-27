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
                'company_name': row[0],
                'ticker': row[1],
                'fiscal_year': row[2],
                'period_type': row[3],
                'sales': float(row[4]) if row[4] else None,
                'other_income': float(row[5]) if row[5] else None,
                'operating_profit': float(row[6]) if row[6] else None,
                'ebitda': float(row[7]) if row[7] else None,
                'profit_before_tax': float(row[8]) if row[8] else None,
                'tax': float(row[9]) if row[9] else None,
                'net_profit': float(row[10]) if row[10] else None,
                'eps': float(row[11]) if row[11] else None,
                'operating_margin_pct': float(row[12]) if row[12] else None,
                'net_margin_pct': float(row[13]) if row[13] else None,
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
            equity = (float(row[2]) if row[2] else 0) + (float(row[3]) if row[3] else 0)
            debt_to_equity = (float(row[4]) / equity * 100) if (row[4] and equity > 0) else None
            
            results.append({
                'company_name': row[0],
                'fiscal_year': row[1],
                'equity_share_capital': float(row[2]) if row[2] else None,
                'reserves': float(row[3]) if row[3] else None,
                'borrowings': float(row[4]) if row[4] else None,
                'total_liabilities': float(row[5]) if row[5] else None,
                'net_fixed_assets': float(row[6]) if row[6] else None,
                'investments': float(row[7]) if row[7] else None,
                'total_assets': float(row[8]) if row[8] else None,
                'receivables': float(row[9]) if row[9] else None,
                'inventory': float(row[10]) if row[10] else None,
                'cash_and_equivalents': float(row[11]) if row[11] else None,
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
                'company_name': row[0],
                'fiscal_year': row[1],
                'operating_cash_flow': float(row[2]) if row[2] else None,
                'investing_cash_flow': float(row[3]) if row[3] else None,
                'financing_cash_flow': float(row[4]) if row[4] else None,
                'net_cash_flow': float(row[5]) if row[5] else None,
                'free_cash_flow': float(row[6]) if row[6] else None,
                'capex': float(row[7]) if row[7] else None,
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
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            equity = (float(row[14]) if row[14] else 0) + (float(row[15]) if row[15] else 0)
            
            results.append({
                'company_name': row[0],
                'ticker': row[1],
                'fiscal_year': row[2],
                'period_type': row[3],
                # P&L
                'sales': float(row[4]) if row[4] else None,
                'other_income': float(row[5]) if row[5] else None,
                'operating_profit': float(row[6]) if row[6] else None,
                'net_profit': float(row[7]) if row[7] else None,
                'eps': float(row[8]) if row[8] else None,
                'depreciation': float(row[9]) if row[9] else None,
                'operating_margin_pct': float(row[10]) if row[10] else None,
                'net_margin_pct': float(row[11]) if row[11] else None,
                # Balance Sheet
                'total_assets': float(row[12]) if row[12] else None,
                'total_liabilities': float(row[13]) if row[13] else None,
                'equity_share_capital': float(row[14]) if row[14] else None,
                'reserves': float(row[15]) if row[15] else None,
                'borrowings': float(row[16]) if row[16] else None,
                'net_fixed_assets': float(row[17]) if row[17] else None,
                'capital_wip': float(row[18]) if row[18] else None,
                'inventory': float(row[19]) if row[19] else None,
                'receivables': float(row[20]) if row[20] else None,
                'cash_and_equivalents': float(row[21]) if row[21] else None,
                'total_equity': equity,
                # Cash Flow
                'operating_cash_flow': float(row[22]) if row[22] else None,
                'free_cash_flow': float(row[23]) if row[23] else None,
                'capex': float(row[24]) if row[24] else None,
            })
        
        return results
        
    finally:
        cursor.close()
        conn.close()
