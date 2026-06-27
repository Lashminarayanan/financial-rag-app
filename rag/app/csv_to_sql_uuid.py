#!/usr/bin/env python3
"""
Financial CSV to SQL Generator with UUID Support
Generates INSERT statements compatible with PostgreSQL UUID primary keys
"""
import csv
import re
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class FinancialCSVToSQL:
    """Generate SQL INSERT statements with UUID support"""
    
    def __init__(self):
        self.statements = defaultdict(list)
        self.companies = {}  # ticker -> UUID
        self.periods = {}    # (company_id, date, type) -> UUID
        self.income_added = set()  # Track which period_ids have income statements
        self.balance_added = set()  # Track which period_ids have balance sheets
        self.cashflow_added = set()  # Track which period_ids have cash flows
        self.market_data_added = set()  # Track market data entries
        self.all_metrics = defaultdict(lambda: defaultdict(dict))  # company_id -> date -> metrics for growth calc
    
    def parse_csv_value(self, value: str) -> Optional[float]:
        """Parse CSV value to float"""
        if not value or not str(value).strip():
            return None
        value = str(value).strip().strip('"').replace(',', '').replace(' ', '')
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def parse_period_from_column(self, col_name: str) -> Tuple:
        """Parse period from column name - supports ISO dates and abbreviated format"""
        col_name = str(col_name).strip()
        
        # Try ISO date: '2017-03-31' or '2017-03-31 00:00:00'
        match = re.match(r'(\d{4})-(\d{2})-(\d{2})', col_name)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            period_date = datetime(year, month, 1).date()
            
            if month == 3:
                return period_date, 'annual', year, 4
            elif month == 12:
                return period_date, 'quarterly', year + 1, 3
            elif month == 9:
                return period_date, 'quarterly', year + 1, 2
            elif month == 6:
                return period_date, 'quarterly', year + 1, 1
            else:
                return period_date, 'quarterly', year, None
        
        # Try abbreviated: 'Mar-17'
        match = re.match(r'([A-Z][a-z]{2})-(\d{2})', col_name)
        if match:
            months = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
                     'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
            month = months.get(match.group(1))
            year = 2000 + int(match.group(2))
            if month:
                period_date = datetime(year, month, 1).date()
                if month == 3:
                    return period_date, 'annual', year, 4
                elif month == 12:
                    return period_date, 'quarterly', year + 1, 3
                elif month == 9:
                    return period_date, 'quarterly', year + 1, 2
                elif month == 6:
                    return period_date, 'quarterly', year + 1, 1
                else:
                    return period_date, 'quarterly', year, None
        
        return None, 'annual', None, None
    
    def extract_company_info(self, csv_path: Path) -> Tuple[str, str, str, str, float, float]:
        """Extract company name, ticker, sector, industry, face_value, and shares from CSV metadata"""
        company_name = None
        ticker = None
        sector = 'Unknown'
        industry = 'Unknown'
        face_value = 1.0  # Default face value for Indian stocks
        shares_outstanding = 0.0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for line in reader:
                if len(line) >= 2:
                    key = str(line[0]).strip().upper()
                    value = str(line[1]).strip() if line[1] else ''
                    
                    if 'COMPANY NAME' in key:
                        company_name = value
                    elif 'TICKER' in key or 'SYMBOL' in key:
                        ticker = value
                    elif 'SECTOR' in key:
                        sector = value if value else 'Unknown'
                    elif 'INDUSTRY' in key:
                        industry = value if value else 'Unknown'
                    elif 'FACE VALUE' in key:
                        try:
                            face_value = float(value.replace(',', ''))
                        except:
                            face_value = 1.0
                    elif ('NUMBER OF SHARES' in key) or ('SHARES OUTSTANDING' in key):
                        try:
                            shares_outstanding = float(value.replace(',', ''))
                        except:
                            shares_outstanding = 0.0
        
        # Fallback for ticker: derive from filename
        if not ticker:
            ticker = csv_path.stem.replace(' ', '').replace('-', '').upper()[:10]
        
        # Fallback for company name
        if not company_name:
            company_name = csv_path.stem
        
        return company_name, ticker, sector, industry, face_value, shares_outstanding
    
    def read_csv_sections(self, csv_path: Path) -> Dict:
        """Read CSV and organize by sections"""
        sections = {}
        current_section = None
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = list(csv.reader(f))
        
        for i, line in enumerate(lines):
            if not line or not line[0].strip():
                continue
            
            first_cell = str(line[0]).strip()
            
            if 'PROFIT & LOSS' in first_cell:
                current_section = 'profit_loss'
                sections[current_section] = {'header': None, 'rows': []}
            elif 'BALANCE SHEET' in first_cell:
                current_section = 'balance_sheet'
                sections[current_section] = {'header': None, 'rows': []}
            elif 'CASH FLOW' in first_cell:
                current_section = 'cash_flow'
                sections[current_section] = {'header': None, 'rows': []}
            elif 'Quarters' in first_cell:
                current_section = 'quarterly'
                sections[current_section] = {'header': None, 'rows': []}
            elif 'PRICE:' in first_cell or 'PRICE' in first_cell:
                current_section = 'prices'
                sections[current_section] = {'header': None, 'rows': []}
            elif current_section:
                if sections[current_section]['header'] is None:
                    if 'Report Date' in str(line[0]):
                        sections[current_section]['header'] = line
                elif sections[current_section]['header'] is not None:
                    if all(not str(cell).strip() for cell in line):
                        current_section = None
                    else:
                        sections[current_section]['rows'].append(line)
        
        return sections
    
    def sql_value(self, value) -> str:
        """Convert Python value to SQL"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value.replace(chr(39), chr(39)+chr(39))}'"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f"'{str(value)}'"
    
    def add_company(self, ticker: str, company_name: str, sector: str = 'Unknown', 
                    industry: str = 'Unknown', face_value: float = 1.0, shares_outstanding: float = 0.0):
        """Generate company INSERT with UUID (only if not already exists)"""
        # Check if company already exists
        if ticker in self.companies:
            print(f"    ⚠ Company {ticker} already exists, reusing ID")
            return self.companies[ticker]
        
        cid = str(uuid.uuid4())
        sql = f"INSERT INTO companies (id, ticker, company_name, sector, industry, face_value, shares_outstanding)\n"
        sql += f"VALUES ('{cid}'::uuid, {self.sql_value(ticker)}, {self.sql_value(company_name)}, {self.sql_value(sector)}, {self.sql_value(industry)}, {face_value}, {shares_outstanding});"
        self.statements['companies'].append(sql)
        self.companies[ticker] = cid
        return cid
    
    def add_period(self, company_id: str, date, ptype: str, fy: int, q):
        """Generate period INSERT with UUID (only if not already exists)"""
        # Check if period already exists
        period_key = (company_id, str(date), ptype)
        if period_key in self.periods:
            return self.periods[period_key]  # Reuse existing period ID
        
        pid = str(uuid.uuid4())
        sql = f"INSERT INTO financial_periods (id, company_id, period_end_date, period_type, fiscal_year, quarter)\n"
        sql += f"VALUES ('{pid}'::uuid, '{company_id}'::uuid, {self.sql_value(str(date))}, {self.sql_value(ptype)}, {fy}, {q});"
        self.statements['financial_periods'].append(sql)
        self.periods[period_key] = pid
        return pid
    
    def add_income(self, pid: str, m: Dict):
        """Generate income_statements INSERT with UUID foreign key (prevent duplicates)"""
        if pid in self.income_added:
            return  # Skip duplicate
        
        # Handle field name variations and optional fields
        sales = m.get('Sales')
        raw_material = m.get('Raw Material Cost')
        inventory_change = m.get('Change in Inventory')
        power_fuel = m.get('Power and Fuel') or m.get('Power & Fuel')
        employee_cost = m.get('Employee Cost')
        selling_admin = m.get('Selling and admin') or m.get('Selling & Admin')
        other_expenses = m.get('Other Expenses')
        other_income = m.get('Other Income')
        depreciation = m.get('Depreciation')
        interest = m.get('Interest')
        pbt = m.get('Profit before tax') or m.get('Profit Before Tax')
        tax = m.get('Tax')
        net_profit = m.get('Net profit') or m.get('Net Profit')
        operating_profit = m.get('Operating Profit')  # May not exist in annual data
        ebitda = m.get('EBITDA')  # May not exist
        eps = m.get('EPS')  # May not exist
        
        sql = f"INSERT INTO income_statements (period_id, sales, raw_material_cost, change_in_inventory, power_fuel_cost, employee_cost, selling_admin_exp, other_expenses, other_income, depreciation, interest, profit_before_tax, tax, net_profit, operating_profit, ebitda, eps)\n"
        sql += f"VALUES ('{pid}'::uuid, {self.sql_value(sales)}, {self.sql_value(raw_material)}, {self.sql_value(inventory_change)}, {self.sql_value(power_fuel)}, {self.sql_value(employee_cost)}, {self.sql_value(selling_admin)}, {self.sql_value(other_expenses)}, {self.sql_value(other_income)}, {self.sql_value(depreciation)}, {self.sql_value(interest)}, {self.sql_value(pbt)}, {self.sql_value(tax)}, {self.sql_value(net_profit)}, {self.sql_value(operating_profit)}, {self.sql_value(ebitda)}, {self.sql_value(eps)});"
        self.statements['income_statements'].append(sql)
        self.income_added.add(pid)
    
    def add_balance(self, pid: str, m: Dict):
        """Generate balance_sheets INSERT with UUID foreign key (prevent duplicates)"""
        if pid in self.balance_added:
            return  # Skip duplicate
        
        # Calculate totals from components if 'Total' is ambiguous
        equity_share = m.get('Equity Share Capital')
        reserves = m.get('Reserves')
        borrowings = m.get('Borrowings')
        other_liabilities = m.get('Other Liabilities')
        
        # Total can appear twice in CSV (once for liabilities, once for assets)
        # Use the value from 'Total' as total_assets (last occurrence in CSV)
        total_assets = m.get('Total')
        
        # Calculate total_liabilities from components
        total_liabilities = None
        if all(v is not None for v in [equity_share, reserves, borrowings, other_liabilities]):
            total_liabilities = equity_share + reserves + borrowings + other_liabilities
        
        sql = f"INSERT INTO balance_sheets (period_id, equity_share_capital, reserves, borrowings, other_liabilities, total_liabilities, net_fixed_assets, capital_wip, investments, other_assets, total_assets, receivables, inventory, cash_and_equivalents)\n"
        sql += f"VALUES ('{pid}'::uuid, {self.sql_value(equity_share)}, {self.sql_value(reserves)}, {self.sql_value(borrowings)}, {self.sql_value(other_liabilities)}, {self.sql_value(total_liabilities)}, {self.sql_value(m.get('Net Block'))}, {self.sql_value(m.get('Capital Work in Progress'))}, {self.sql_value(m.get('Investments'))}, {self.sql_value(m.get('Other Assets'))}, {self.sql_value(total_assets)}, {self.sql_value(m.get('Receivables'))}, {self.sql_value(m.get('Inventory'))}, {self.sql_value(m.get('Cash & Bank'))});"
        self.statements['balance_sheets'].append(sql)
        self.balance_added.add(pid)
    
    def add_cashflow(self, pid: str, m: Dict):
        """Generate cash_flows INSERT with UUID foreign key (prevent duplicates)"""
        if pid in self.cashflow_added:
            return  # Skip duplicate
        
        # CSV uses full field names: "Cash from Operating Activity", etc.
        operating = m.get('Cash from Operating Activity') or m.get('Operating Activities')
        investing = m.get('Cash from Investing Activity') or m.get('Investing Activities')
        financing = m.get('Cash from Financing Activity') or m.get('Financing Activities')
        net_cash = m.get('Net Cash Flow')
        
        sql = f"INSERT INTO cash_flows (period_id, operating_cash_flow, investing_cash_flow, financing_cash_flow, net_cash_flow)\n"
        sql += f"VALUES ('{pid}'::uuid, {self.sql_value(operating)}, {self.sql_value(investing)}, {self.sql_value(financing)}, {self.sql_value(net_cash)});"
        self.statements['cash_flows'].append(sql)
        self.cashflow_added.add(pid)
    
    def add_market_data(self, company_id: str, date, closing_price: float, market_cap: float = None):
        """Generate market_data INSERT"""
        key = (company_id, str(date))
        if key in self.market_data_added:
            return
        
        sql = f"INSERT INTO market_data (company_id, date, closing_price, market_cap)\n"
        sql += f"VALUES ('{company_id}'::uuid, {self.sql_value(str(date))}, {self.sql_value(closing_price)}, {self.sql_value(market_cap)});"
        self.statements['market_data'].append(sql)
        self.market_data_added.add(key)
    
    def add_financial_ratios(self, pid: str, income_data: Dict, balance_data: Dict):
        """Generate financial_ratios INSERT with calculated ratios"""
        # Calculate ratios from financial data
        net_profit = income_data.get('Net profit') or income_data.get('Net Profit')
        total_assets = balance_data.get('Total')
        equity_capital = balance_data.get('Equity Share Capital')
        reserves = balance_data.get('Reserves')
        borrowings = balance_data.get('Borrowings')
        
        # Calculate basic ratios
        roe = None  # Return on Equity = Net Profit / Total Equity
        roa = None  # Return on Assets = Net Profit / Total Assets
        debt_to_equity = None
        
        if net_profit and equity_capital and reserves:
            total_equity = equity_capital + reserves
            if total_equity > 0:
                roe = (net_profit / total_equity) * 100
        
        if net_profit and total_assets and total_assets > 0:
            roa = (net_profit / total_assets) * 100
        
        if borrowings and equity_capital and reserves:
            total_equity = equity_capital + reserves
            if total_equity > 0:
                debt_to_equity = borrowings / total_equity
        
        # Only insert if we have at least one ratio
        if roe or roa or debt_to_equity:
            sql = f"INSERT INTO financial_ratios (period_id, roe, roa, debt_to_equity)\n"
            sql += f"VALUES ('{pid}'::uuid, {self.sql_value(roe)}, {self.sql_value(roa)}, {self.sql_value(debt_to_equity)});"
            self.statements['financial_ratios'].append(sql)
    
    def add_growth_metrics(self, pid: str, company_id: str, current_date, current_metrics: Dict, period_type: str):
        """Generate growth_metrics INSERT with YoY and QoQ calculations"""
        
        # Key metrics to track growth for
        key_metrics = {
            'Sales': 'Sales',
            'Net Profit': ['Net profit', 'Net Profit'],
            'EBITDA': 'EBITDA',
            'Operating Profit': 'Operating Profit',
            'Total Assets': 'Total'
        }
        
        for metric_name, metric_keys in key_metrics.items():
            # Get current value
            if isinstance(metric_keys, list):
                current_value = None
                for key in metric_keys:
                    current_value = current_metrics.get(key)
                    if current_value is not None:
                        break
            else:
                current_value = current_metrics.get(metric_keys)
            
            if current_value is None:
                continue
            
            # Calculate YoY growth (compare with same period last year)
            yoy_growth = None
            try:
                prev_year_date = datetime(current_date.year - 1, current_date.month, current_date.day).date()
                prev_year_metrics = self.all_metrics[company_id].get(str(prev_year_date), {})
                
                if isinstance(metric_keys, list):
                    prev_value = None
                    for key in metric_keys:
                        prev_value = prev_year_metrics.get(key)
                        if prev_value is not None:
                            break
                else:
                    prev_value = prev_year_metrics.get(metric_keys)
                
                if prev_value and prev_value != 0:
                    yoy_growth = ((current_value - prev_value) / prev_value) * 100
            except:
                pass
            
            # Calculate QoQ growth (only for quarterly data)
            qoq_growth = None
            if period_type == 'quarterly':
                try:
                    prev_quarter_date = current_date - timedelta(days=90)
                    prev_quarter_metrics = self.all_metrics[company_id].get(str(prev_quarter_date), {})
                    
                    if isinstance(metric_keys, list):
                        prev_value = None
                        for key in metric_keys:
                            prev_value = prev_quarter_metrics.get(key)
                            if prev_value is not None:
                                break
                    else:
                        prev_value = prev_quarter_metrics.get(metric_keys)
                    
                    if prev_value and prev_value != 0:
                        qoq_growth = ((current_value - prev_value) / prev_value) * 100
                except:
                    pass
            
            # Insert growth metric if we have at least one growth rate
            if yoy_growth is not None or qoq_growth is not None:
                sql = f"INSERT INTO growth_metrics (period_id, metric_name, metric_value, yoy_growth_pct, qoq_growth_pct)\n"
                sql += f"VALUES ('{pid}'::uuid, {self.sql_value(metric_name)}, {self.sql_value(current_value)}, {self.sql_value(yoy_growth)}, {self.sql_value(qoq_growth)});"
                self.statements['growth_metrics'].append(sql)
    
    def process_csv(self, csv_path: Path, company_name: str, ticker: str, 
                    sector: str = 'Unknown', industry: str = 'Unknown', 
                    face_value: float = 1.0, shares_outstanding: float = 0.0):
        """Process one CSV file"""
        print(f"\nProcessing: {csv_path.name}")
        
        company_id = self.add_company(ticker, company_name, sector, industry, face_value, shares_outstanding)
        sections = self.read_csv_sections(csv_path)
        print(f"  Found {len(sections)} sections")
        
        # Store metrics by period for ratio calculations
        period_metrics = {}  # period_id -> {income, balance, cashflow, date, type}
        
        for sec_name, sec_data in sections.items():
            if not sec_data['header']:
                continue
            
            header = sec_data['header']
            rows = sec_data['rows']
            
            # Handle PRICE section differently
            if sec_name == 'prices':
                # PRICE row has dates in same columns as other sections
                price_row = None
                for row in rows:
                    if row and 'PRICE' in str(row[0]).upper():
                        price_row = row
                        break
                
                if price_row:
                    for idx, col in enumerate(header):
                        pdate, ptype, fy, q = self.parse_period_from_column(col)
                        if pdate and idx < len(price_row):
                            price = self.parse_csv_value(price_row[idx])
                            if price and shares_outstanding > 0:
                                market_cap = price * shares_outstanding
                                self.add_market_data(company_id, pdate, price, market_cap)
                print(f"    {sec_name}: {len(rows)} rows (price data)")
                continue
            
            period_cols = []
            for idx, col in enumerate(header):
                pdate, ptype, fy, q = self.parse_period_from_column(col)
                if pdate:
                    period_cols.append((idx, col, pdate, ptype, fy, q))
            
            print(f"    {sec_name}: {len(rows)} rows, {len(period_cols)} periods")
            
            for idx, col, pdate, ptype, fy, q in period_cols:
                pid = self.add_period(company_id, pdate, ptype, fy, q)
                
                # Initialize period metrics storage
                if pid not in period_metrics:
                    period_metrics[pid] = {'income': {}, 'balance': {}, 'cashflow': {}, 'date': pdate, 'type': ptype}
                
                metrics = {}
                for row in rows:
                    if len(row) > idx and row[0].strip():
                        metrics[row[0].strip()] = self.parse_csv_value(row[idx])
                
                if sec_name in ['profit_loss', 'quarterly']:
                    self.add_income(pid, metrics)
                    period_metrics[pid]['income'] = metrics
                    # Store for growth calculations
                    self.all_metrics[company_id][str(pdate)].update(metrics)
                if sec_name == 'balance_sheet':
                    self.add_balance(pid, metrics)
                    period_metrics[pid]['balance'] = metrics
                    # Store for growth calculations
                    self.all_metrics[company_id][str(pdate)].update(metrics)
                if sec_name == 'cash_flow':
                    self.add_cashflow(pid, metrics)
                    period_metrics[pid]['cashflow'] = metrics
        
        # Generate financial ratios and growth metrics after all data is collected
        for pid, data in period_metrics.items():
            if data['income'] and data['balance']:
                self.add_financial_ratios(pid, data['income'], data['balance'])
            
            # Generate growth metrics for income statement items
            if data['income']:
                combined_metrics = {**data['income'], **data.get('balance', {})}
                self.add_growth_metrics(pid, company_id, data['date'], combined_metrics, data['type'])
    
    def process_folder(self, folder: Path):
        """Process all CSV files in folder"""
        csvs = list(Path(folder).glob('*.csv'))
        print(f"\n{'='*70}")
        print(f"Found {len(csvs)} CSV files in {folder}")
        print(f"{'='*70}")
        
        for csv_file in csvs:
            company_name, ticker, sector, industry, face_value, shares_outstanding = self.extract_company_info(csv_file)
            print(f"\n📄 {csv_file.name}")
            print(f"   Company: {company_name}")
            print(f"   Ticker: {ticker}")
            print(f"   Sector: {sector}")
            print(f"   Industry: {industry}")
           print(f"   Face Value: ₹{face_value}")
            print(f"   Shares Outstanding: {shares_outstanding} Cr")
            self.process_csv(csv_file, company_name, ticker, sector, industry, face_value, shares_outstanding)
    
    def save(self, output: Path):
        """Save all SQL statements to file"""
        with open(output, 'w', encoding='utf-8') as f:
            f.write("-- =====================================================\n")
            f.write("-- Financial Data INSERT Statements (UUID-based)\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Companies: {len(self.companies)}\n")
            f.write(f"-- Periods: {len(self.periods)}\n")
            f.write("-- =====================================================\n\n")
            
            for table in ['companies', 'financial_periods', 'income_statements', 'balance_sheets', 'cash_flows', 'market_data', 'financial_ratios', 'growth_metrics']:
                if table in self.statements:
                    f.write(f"\n-- ========== {table.upper()} ({len(self.statements[table])} records) ==========\n\n")
                    for stmt in self.statements[table]:
                        f.write(stmt + '\n\n')
        
        print(f"\n{'='*70}")
        print(f"✓ Generated SQL file: {output}")
        print(f"{'='*70}")
        print("Summary:")
        for table, stmts in sorted(self.statements.items()):
            print(f"  {table:25s} {len(stmts):5d} statements")
        print(f"{'='*70}")
        print(f"\nTo execute:")
        print(f"  psql -h localhost -p 5433 -U postgres -d financial_rag -f {output}")
        print(f"{'='*70}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch process financial CSV files and generate SQL INSERT statements',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all CSV files in a folder
  python csv_to_sql_uuid.py --folder "C:\\path\\to\\csv\\files"
  
  # Specify custom output filename
  python csv_to_sql_uuid.py --folder "C:\\data\\financials" --output all_companies.sql
  
Notes:
  - Script automatically extracts company name from CSV metadata
  - Generates UUID-based INSERT statements for all tables
  - Handles PROFIT & LOSS, BALANCE SHEET, CASH FLOW, and Quarters sections
        """
    )
    
    parser.add_argument('--folder', required=True, 
                       help='Folder containing CSV files to process')
    parser.add_argument('--output', default='financial_batch.sql',
                       help='Output SQL filename (default: financial_batch.sql)')
    
    args = parser.parse_args()
    
    folder_path = Path(args.folder)
    if not folder_path.exists():
        print(f"❌ Error: Folder not found: {folder_path}")
        sys.exit(1)
    
    if not folder_path.is_dir():
        print(f"❌ Error: Not a directory: {folder_path}")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("BATCH CSV TO SQL GENERATOR")
    print("="*70)
    
    generator = FinancialCSVToSQL()
    generator.process_folder(folder_path)
    generator.save(Path(args.output))

if __name__ == '__main__':
    main()
