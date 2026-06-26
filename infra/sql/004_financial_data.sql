-- Financial Data Storage Schema
-- Extends existing RAG database to support structured financial metrics

-- 1. Companies table (master data)
CREATE TABLE IF NOT EXISTS companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker VARCHAR(20) UNIQUE NOT NULL,
  company_name TEXT NOT NULL,
  sector VARCHAR(100),
  industry VARCHAR(100),
  face_value DECIMAL(10, 2),
  shares_outstanding DECIMAL(15, 2),  -- In crores
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_companies_ticker ON companies(ticker);

-- 2. Financial Periods (for time-series data)
CREATE TABLE IF NOT EXISTS financial_periods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  period_end_date DATE NOT NULL,
  period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('annual', 'quarterly', 'ttm')),
  fiscal_year INTEGER,
  quarter INTEGER CHECK (quarter BETWEEN 1 AND 4),
  UNIQUE(company_id, period_end_date, period_type),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_financial_periods_company ON financial_periods(company_id, period_end_date DESC);

-- 3. Income Statement (P&L)
CREATE TABLE IF NOT EXISTS income_statements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_id UUID NOT NULL UNIQUE REFERENCES financial_periods(id) ON DELETE CASCADE,
  -- Revenue
  sales DECIMAL(15, 2),
  other_income DECIMAL(15, 2),
  total_revenue DECIMAL(15, 2),
  -- Expenses (detailed breakdown)
  raw_material_cost DECIMAL(15, 2),
  change_in_inventory DECIMAL(15, 2),
  power_fuel_cost DECIMAL(15, 2),
  employee_cost DECIMAL(15, 2),
  selling_admin_exp DECIMAL(15, 2),
  other_expenses DECIMAL(15, 2),
  depreciation DECIMAL(15, 2),
  interest DECIMAL(15, 2),
  total_expenses DECIMAL(15, 2),
  -- Profit
  ebitda DECIMAL(15, 2),
  operating_profit DECIMAL(15, 2),
  profit_before_tax DECIMAL(15, 2),
  tax DECIMAL(15, 2),
  net_profit DECIMAL(15, 2),
  -- Per Share
  eps DECIMAL(10, 2),
  dividend_per_share DECIMAL(10, 2),
  -- Margins (%)
  gross_margin_pct DECIMAL(5, 2),
  operating_margin_pct DECIMAL(5, 2),
  net_margin_pct DECIMAL(5, 2),
  ebitda_margin_pct DECIMAL(5, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_income_statements_period ON income_statements(period_id);

-- 4. Balance Sheet
CREATE TABLE IF NOT EXISTS balance_sheets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_id UUID NOT NULL UNIQUE REFERENCES financial_periods(id) ON DELETE CASCADE,
  -- Assets
  net_fixed_assets DECIMAL(15, 2),
  capital_wip DECIMAL(15, 2),
  investments DECIMAL(15, 2),
  inventory DECIMAL(15, 2),
  receivables DECIMAL(15, 2),
  cash_and_equivalents DECIMAL(15, 2),
  other_assets DECIMAL(15, 2),
  total_assets DECIMAL(15, 2),
  -- Liabilities
  equity_share_capital DECIMAL(15, 2),
  reserves DECIMAL(15, 2),
  total_equity DECIMAL(15, 2),
  borrowings DECIMAL(15, 2),
  other_liabilities DECIMAL(15, 2),
  total_liabilities DECIMAL(15, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_balance_sheets_period ON balance_sheets(period_id);

-- 5. Cash Flow Statement
CREATE TABLE IF NOT EXISTS cash_flows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_id UUID NOT NULL UNIQUE REFERENCES financial_periods(id) ON DELETE CASCADE,
  operating_cash_flow DECIMAL(15, 2),
  investing_cash_flow DECIMAL(15, 2),
  financing_cash_flow DECIMAL(15, 2),
  net_cash_flow DECIMAL(15, 2),
  free_cash_flow DECIMAL(15, 2),
  capex DECIMAL(15, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cash_flows_period ON cash_flows(period_id);

-- 6. Financial Ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_id UUID NOT NULL REFERENCES financial_periods(id) ON DELETE CASCADE,
  -- Profitability Ratios
  roe DECIMAL(10, 4),  -- Return on Equity
  roa DECIMAL(10, 4),  -- Return on Assets
  roce DECIMAL(10, 4), -- Return on Capital Employed
  roic DECIMAL(10, 4), -- Return on Invested Capital
  -- Valuation Ratios
  pe_ratio DECIMAL(10, 2),
  pb_ratio DECIMAL(10, 2),
  ps_ratio DECIMAL(10, 2),
  ev_ebitda DECIMAL(10, 2),
  -- Efficiency Ratios
  asset_turnover DECIMAL(10, 2),
  inventory_turnover DECIMAL(10, 2),
  receivables_days INTEGER,
  -- Liquidity Ratios
  current_ratio DECIMAL(10, 2),
  quick_ratio DECIMAL(10, 2),
  -- Leverage Ratios
  debt_to_equity DECIMAL(10, 4),
  interest_coverage DECIMAL(10, 2),
  -- Other
  dividend_yield DECIMAL(5, 2),
  payout_ratio DECIMAL(5, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_financial_ratios_period ON financial_ratios(period_id);

-- 7. Growth Metrics (YoY, QoQ comparisons)
CREATE TABLE IF NOT EXISTS growth_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_id UUID NOT NULL REFERENCES financial_periods(id) ON DELETE CASCADE,
  metric_name VARCHAR(100) NOT NULL,
  metric_value DECIMAL(15, 2),
  yoy_growth_pct DECIMAL(10, 2),
  qoq_growth_pct DECIMAL(10, 2),
  cagr_3yr DECIMAL(10, 2),
  cagr_5yr DECIMAL(10, 2),
  cagr_10yr DECIMAL(10, 2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_growth_metrics_period ON growth_metrics(period_id);
CREATE INDEX idx_growth_metrics_name ON growth_metrics(metric_name);

-- 8. Market Data (prices, market cap)
CREATE TABLE IF NOT EXISTS market_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  closing_price DECIMAL(10, 2),
  market_cap DECIMAL(15, 2),
  enterprise_value DECIMAL(15, 2),
  UNIQUE(company_id, date),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_market_data_company_date ON market_data(company_id, date DESC);

-- 9. Financial Metrics Text (for vector search)
CREATE TABLE IF NOT EXISTS financial_metrics_text (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_id UUID NOT NULL REFERENCES financial_periods(id) ON DELETE CASCADE,
  metric_category VARCHAR(100), -- 'profitability', 'growth', 'valuation', etc.
  metric_text TEXT NOT NULL,    -- Natural language description
  metric_data JSONB,             -- Structured data as JSON
  embedding VECTOR(768),         -- For semantic search
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_financial_metrics_text_period ON financial_metrics_text(period_id);
CREATE INDEX idx_financial_metrics_text_category ON financial_metrics_text(metric_category);
CREATE INDEX idx_financial_metrics_text_embedding ON financial_metrics_text 
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 10. Link financial data to ingested documents
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id),
  ADD COLUMN IF NOT EXISTS period_id UUID REFERENCES financial_periods(id);

CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company_id);
CREATE INDEX IF NOT EXISTS idx_documents_period ON documents(period_id);
