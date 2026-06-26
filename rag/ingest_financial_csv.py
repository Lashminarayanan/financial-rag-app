#!/usr/bin/env python3
"""
CSV Financial Data Ingestion Script
Loads structured financial data from Eicher_data_sheet.csv format into database
Handles PROFIT & LOSS, BALANCE SHEET, CASH FLOW sections with annual and quarterly data
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import os

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    import psycopg
except ImportError:
    print("Error: psycopg not installed. Run: pip install psycopg-binary")
    sys.exit(1)


def get_connection():
    """Connect to PostgreSQL"""
    return psycopg.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5433)),
        dbname=os.getenv('POSTGRES_DB', 'financial_rag'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        autocommit=False
    )


def parse_csv_value(value: str) -> Optional[float]:
    """Parse CSV value to float, handling commas and whitespace"""
    if not value or not str(value).strip():
        return None
    
    # Remove whitespace, quotes, and commas
    value = str(value).strip().strip('"').replace(',', '').replace(' ', '')
    
    # Try to convert to float
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_period_from_column(col_name: str) -> Tuple[Optional[datetime], str, Optional[int], Optional[int]]:
    """
    Parse period information from column name (e.g., 'Mar-17', 'Dec-23')
    Returns: (period_date, period_type, fiscal_year, quarter)
    """
    col_name = str(col_name).strip()
    
    # Match patterns like "Mar-17", "Dec-23"
    match = re.match(r'([A-Z][a-z]{2})-(\d{2})', col_name)
    if not match:
        return None, 'annual', None, None
    
    month_abbr, year_suffix = match.groups()
    
    # Month mapping
    months = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    month = months.get(month_abbr)
    if not month:
        return None, 'annual', None, None
    
    # Convert year (17 -> 2017, 26 -> 2026)
    year = 2000 + int(year_suffix)
    
    # Determine fiscal year and quarter (assuming March year-end)
    if month == 3:
        fiscal_year = year
        quarter = 4
        period_type = 'annual'
    elif month == 12:
        fiscal_year = year + 1
        quarter = 3
        period_type = 'quarterly'
    elif month == 9:
        fiscal_year = year + 1
        quarter = 2
        period_type = 'quarterly'
    elif month == 6:
        fiscal_year = year + 1
        quarter = 1
        period_type = 'quarterly'
    else:
        fiscal_year = year
        quarter = None
        period_type = 'quarterly'
    
    period_date = datetime(year, month, 1).date()
    
    return period_date, period_type, fiscal_year, quarter


def read_csv_sections(csv_path: Path) -> Dict[str, List[Dict]]:
    """
    Read CSV and organize data by sections (PROFIT & LOSS, BALANCE SHEET, etc.)
    Returns dict of section_name -> list of data rows
    """
    sections = {}
    current_section = None
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Read all lines
        lines = list(csv.reader(f))
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a section header
        if line and len(line) > 0:
            first_cell = str(line[0]).strip()
            
            # Detect section headers
            if 'PROFIT & LOSS' in first_cell:
                current_section = 'profit_loss'
                sections[current_section] = {'header': None, 'rows': []}
                i += 1
                continue
            elif 'BALANCE SHEET' in first_cell:
                current_section = 'balance_sheet'
                sections[current_section] = {'header': None, 'rows': []}
                i += 1
                continue
            elif 'CASH FLOW' in first_cell:
                current_section = 'cash_flow'
                sections[current_section] = {'header': None, 'rows': []}
                i += 1
                continue
            elif 'Quarters' in first_cell:
                current_section = 'quarterly'
                sections[current_section] = {'header': None, 'rows': []}
                i += 1
                continue
            
            # Check if this is a data row
            if current_section and line[0].strip():
                # If we haven't found the header yet, check if this is it
                if sections[current_section]['header'] is None:
                    if 'Report Date' in str(line[0]):
                        sections[current_section]['header'] = line
                        i += 1
                        continue
                
                # If we have a header, this is a data row
                if sections[current_section]['header'] is not None:
                    # Stop at empty rows or next section
                    if all(not str(cell).strip() for cell in line):
                        current_section = None
                    else:
                        sections[current_section]['rows'].append(line)
        
        i += 1
    
    return sections


def load_financial_data(csv_path: Path, company_name: str, ticker: str):
    """Load financial data from Eicher_data_sheet.csv format"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Insert or get company
        cursor.execute("""
            INSERT INTO companies (ticker, company_name, sector, industry, shares_outstanding)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ticker) DO UPDATE SET 
                company_name = EXCLUDED.company_name,
                shares_outstanding = EXCLUDED.shares_outstanding
            RETURNING id
        """, (ticker, company_name, 'Automotive', 'Two-Wheelers', 27.43))
        
        company_id = cursor.fetchone()[0]
        print(f"Company ID: {company_id}")
        
        # 2. Read and parse CSV sections
        sections = read_csv_sections(csv_path)
        print(f"Found {len(sections)} sections: {list(sections.keys())}")
        
        # 3. Process each section
        for section_name, section_data in sections.items():
            if not section_data['header']:
                print(f"  Skipping {section_name} - no header found")
                continue
            
            header = section_data['header']
            rows = section_data['rows']
            
            # Find period columns (Mar-17, Dec-23, etc.)
            period_columns = []
            for idx, col_name in enumerate(header):
                period_info = parse_period_from_column(col_name)
                if period_info[0] is not None:  # Valid period
                    period_columns.append((idx, col_name, period_info))
            
            print(f"\nProcessing {section_name}: {len(rows)} rows, {len(period_columns)} periods")
            
            # 4. Process each period
            for col_idx, col_name, (period_date, period_type, fiscal_year, quarter) in period_columns:
                # Insert or get period
                cursor.execute("""
                    INSERT INTO financial_periods (
                        company_id, period_end_date, period_type, fiscal_year, quarter
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (company_id, period_end_date, period_type) 
                    DO UPDATE SET fiscal_year = EXCLUDED.fiscal_year, quarter = EXCLUDED.quarter
                    RETURNING id
                """, (company_id, period_date, period_type, fiscal_year, quarter))
                
                period_id = cursor.fetchone()[0]
                
                # Build metrics dict for this period
                metrics = {}
                for row in rows:
                    if len(row) > col_idx and row[0].strip():
                        metric_name = row[0].strip()
                        metric_value = parse_csv_value(row[col_idx])
                        metrics[metric_name] = metric_value
                
                # 5. Insert data based on section type
                if section_name in ['profit_loss', 'quarterly']:
                    insert_income_statement(cursor, period_id, metrics)
                
                if section_name == 'balance_sheet':
                    insert_balance_sheet(cursor, period_id, metrics)
                
                if section_name == 'cash_flow':
                    insert_cash_flow(cursor, period_id, metrics)
                
                print(f"   {col_name} (FY{fiscal_year}{'Q'+str(quarter) if quarter else ''})")
        
        conn.commit()
        print(f"\nSuccessfully loaded financial data for {company_name}")
        
    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cursor.close()
        conn.close()


def insert_income_statement(cursor, period_id: str, metrics: Dict[str, float]):
    """Insert P&L data into income_statements table"""
    cursor.execute("""
        INSERT INTO income_statements (
            period_id, sales, raw_material_cost, change_in_inventory,
            power_fuel_cost, employee_cost, selling_admin_exp, other_expenses,
            other_income, depreciation, interest, profit_before_tax, tax,
            net_profit, operating_profit, ebitda, eps
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (period_id) DO UPDATE SET
            sales = EXCLUDED.sales,
            net_profit = EXCLUDED.net_profit,
            eps = EXCLUDED.eps
    """, (
        period_id,
        metrics.get('Sales'),
        metrics.get('Raw Material Cost'),
        metrics.get('Change in Inventory'),
        metrics.get('Power and Fuel'),
        metrics.get('Employee Cost'),
        metrics.get('Selling and admin'),
        metrics.get('Other Expenses'),
        metrics.get('Other Income'),
        metrics.get('Depreciation'),
        metrics.get('Interest'),
        metrics.get('Profit before tax'),
        metrics.get('Tax'),
        metrics.get('Net profit'),
        metrics.get('Operating Profit'),
        metrics.get('EBITDA'),
        metrics.get('EPS')
    ))


def insert_balance_sheet(cursor, period_id: str, metrics: Dict[str, float]):
    """Insert balance sheet data"""
    cursor.execute("""
        INSERT INTO balance_sheets (
            period_id, equity_share_capital, reserves, borrowings,
            other_liabilities, total_liabilities, net_fixed_assets,
            capital_wip, investments, other_assets, total_assets,
            receivables, inventory, cash_and_equivalents
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (period_id) DO UPDATE SET
            reserves = EXCLUDED.reserves,
            total_assets = EXCLUDED.total_assets
    """, (
        period_id,
        metrics.get('Equity Share Capital'),
        metrics.get('Reserves'),
        metrics.get('Borrowings'),
        metrics.get('Other Liabilities'),
        metrics.get('Total'),  # Total liabilities
        metrics.get('Net Block'),
        metrics.get('Capital Work in Progress'),
        metrics.get('Investments'),
        metrics.get('Other Assets'),
        metrics.get('Total'),  # Total assets (same metric name in CSV)
        metrics.get('Receivables'),
        metrics.get('Inventory'),
        metrics.get('Cash & Bank')
    ))


def insert_cash_flow(cursor, period_id: str, metrics: Dict[str, float]):
    """Insert cash flow data"""
    cursor.execute("""
        INSERT INTO cash_flows (
            period_id, operating_cash_flow, investing_cash_flow,
            financing_cash_flow, net_cash_flow
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (period_id) DO UPDATE SET
            operating_cash_flow = EXCLUDED.operating_cash_flow,
            net_cash_flow = EXCLUDED.net_cash_flow
    """, (
        period_id,
        metrics.get('Operating Activities'),
        metrics.get('Investing Activities'),
        metrics.get('Financing Activities'),
        metrics.get('Net Cash Flow')
    ))


def main():
    """Main ingestion function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ingest Eicher_data_sheet.csv financial data into database'
    )
    parser.add_argument('--file', required=True, help='Path to Eicher_data_sheet.csv file')
    parser.add_argument('--company', default='EICHER MOTORS LTD', help='Company name')
    parser.add_argument('--ticker', default='EICHERMOT', help='Stock ticker symbol')
    
    args = parser.parse_args()
    
    csv_path = Path(args.file)
    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("FINANCIAL DATA INGESTION")
    print("=" * 70)
    print(f"File: {csv_path}")
    print(f"Company: {args.company}")
    print(f"Ticker: {args.ticker}")
    print("=" * 70)
    
    load_financial_data(csv_path, args.company, args.ticker)
    
    print("=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()

