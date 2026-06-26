# Financial Data Integration Guide

## Overview

This guide explains how to store and use structured financial CSV data (like Eicher Motors financial statements) in the RAG project. The ingestion script handles **Eicher_data_sheet.csv** format with complete P&L, Balance Sheet, and Cash Flow data.

## Database Schema

### New Tables Created (`004_financial_data.sql`):

1. **companies** - Master company data (ticker, name, sector)
2. **financial_periods** - Time periods (annual/quarterly/TTM)
3. **income_statements** - P&L data (Sales, Profit, EPS, Margins, detailed expenses)
4. **balance_sheets** - Assets, Liabilities, Equity, Capital structure
5. **cash_flows** - Operating, Investing, Financing cash flows
6. **financial_ratios** - ROE, ROA, ROCE, P/E, P/B, etc.
7. **growth_metrics** - YoY, QoQ, CAGR calculations
8. **market_data** - Stock prices, market cap
9. **financial_metrics_text** - Text embeddings for semantic search

## Data Source

**Eicher_data_sheet.csv** contains:
- ✅ **PROFIT & LOSS** (Mar-17 to Mar-26) - 10 years annual data
- ✅ **Quarterly P&L** (Dec-23 to Mar-26) - Recent quarters
- ✅ **BALANCE SHEET** (Mar-17 to Mar-26) - Complete asset/liability breakdown
- ✅ **CASH FLOW** - Operating, Investing, Financing activities
- ✅ **Detailed Expenses** - Raw materials, employee costs, power & fuel, selling & admin

## Setup Instructions

### 1. Apply Database Migration

```bash
psql -U postgres -p 5433 -d financial_rag -f infra/sql/004_financial_data.sql
```

### 2. Ingest CSV Data

```bash
cd rag
python ingest_financial_csv.py --file ../Eicher_data_sheet.csv
```

*Default company name and ticker are pre-configured. Override with `--company` and `--ticker` if needed.*

### 3. Verify Data

```sql
-- Check company
SELECT * FROM companies WHERE ticker = 'EICHERMOT';

-- Check periods (annual + quarterly)
SELECT fp.*, c.company_name 
FROM financial_periods fp
JOIN companies c ON fp.company_id = c.id
ORDER BY period_end_date;

-- Check income statements
SELECT fp.fiscal_year, fp.period_type, i.sales, i.net_profit, i.eps
FROM income_statements i
JOIN financial_periods fp ON i.period_id = fp.id
WHERE fp.period_type = 'annual'
ORDER BY fp.fiscal_year DESC;

-- Check balance sheets
SELECT fp.fiscal_year, b.total_assets, b.total_liabilities, 
       b.equity_share_capital + b.reserves as equity
FROM balance_sheets b
JOIN financial_periods fp ON b.period_id = fp.id
ORDER BY fp.fiscal_year DESC;
```

## Integration with RAG - Hybrid Search

Combine SQL queries for precise metrics with vector search for context.

### Approach 1: Direct SQL Queries (Recommended for Structured Data)

```sql
-- Get 5-year revenue and profit trend
SELECT 
    fp.fiscal_year,
    i.sales,
    i.net_profit,
    i.eps,
    ROUND((i.net_profit / i.sales * 100), 2) as net_margin_pct
FROM income_statements i
JOIN financial_periods fp ON i.period_id = fp.id
WHERE fp.period_type = 'annual'
ORDER BY fp.fiscal_year DESC
LIMIT 5;

-- Quarterly performance comparison
SELECT 
    fp.fiscal_year,
    fp.quarter,
    i.sales,
    i.net_profit,
    i.operating_profit
FROM income_statements i
JOIN financial_periods fp ON i.period_id = fp.id
WHERE fp.period_type = 'quarterly'
ORDER BY fp.period_end_date DESC;

-- Balance sheet health check
SELECT 
    fp.fiscal_year,
    b.total_assets,
    b.borrowings,
    b.cash_and_equivalents,
    ROUND((b.borrowings::numeric / (b.equity_share_capital + b.reserves)) * 100, 2) as debt_to_equity_pct
FROM balance_sheets b
JOIN financial_periods fp ON b.period_id = fp.id
WHERE fp.period_type = 'annual'
ORDER BY fp.fiscal_year DESC;
```

### Approach 2: Hybrid SQL + Vector Search

1. **Query structured data** for precise metrics
2. **Retrieve context** from annual reports via vector search
3. **Combine in LLM prompt** for enriched answers

Example workflow:
```python
# 1. Get structured metrics from SQL
eps_trend = query_database("SELECT fiscal_year, eps FROM income_statements...")

# 2. Get narrative context from documents
context = vector_search("What factors influenced EPS growth?")

# 3. Combine in prompt
prompt = f"""
Financial Data:
{eps_trend}

Context from Annual Report:
{context}

Question: What drove the EPS growth from FY21 to FY24?
"""
```

## Example Use Cases

### 1. Comparative Financial Analysis
```sql
-- Compare FY24 vs FY21 (Post-COVID recovery)
WITH fy21 AS (
    SELECT sales, net_profit, operating_profit
    FROM income_statements i
    JOIN financial_periods fp ON i.period_id = fp.id
    WHERE fp.fiscal_year = 2021
),
fy24 AS (
    SELECT sales, net_profit, operating_profit
    FROM income_statements i
    JOIN financial_periods fp ON i.period_id = fp.id
    WHERE fp.fiscal_year = 2024
)
SELECT 
    ROUND(((fy24.sales - fy21.sales) / fy21.sales * 100), 2) as sales_growth_pct,
    ROUND(((fy24.net_profit - fy21.net_profit) / fy21.net_profit * 100), 2) as profit_growth_pct
FROM fy21, fy24;
```

### 2. Expense Structure Analysis
```sql
-- Raw material as % of sales over time
SELECT 
    fp.fiscal_year,
    ROUND((i.raw_material_cost / i.sales * 100), 2) as raw_material_pct,
    ROUND((i.employee_cost / i.sales * 100), 2) as employee_cost_pct
FROM income_statements i
JOIN financial_periods fp ON i.period_id = fp.id
WHERE fp.period_type = 'annual'
ORDER BY fp.fiscal_year DESC;
```

### 3. Quarterly Seasonality Detection
```sql
-- Identify seasonal patterns in quarterly sales
SELECT 
    fp.quarter,
    AVG(i.sales) as avg_quarterly_sales,
    AVG(i.net_profit) as avg_quarterly_profit
FROM income_statements i
JOIN financial_periods fp ON i.period_id = fp.id
WHERE fp.period_type = 'quarterly'
GROUP BY fp.quarter
ORDER BY fp.quarter;
```

## Next Steps

### Backend API Integration
Create endpoints to serve financial data:

```javascript
// backend-enterprise/src/routes/financial.js
router.get('/api/v1/financial/metrics/:ticker', async (req, res) => {
    const { ticker } = req.params;
    const { period_type = 'annual', limit = 5 } = req.query;
    
    const result = await db.query(`
        SELECT 
            fp.fiscal_year,
            fp.quarter,
            i.sales,
            i.net_profit,
            i.eps,
            b.total_assets
        FROM financial_periods fp
        LEFT JOIN income_statements i ON i.period_id = fp.id
        LEFT JOIN balance_sheets b ON b.period_id = fp.id
        WHERE fp.company_id = (SELECT id FROM companies WHERE ticker = $1)
          AND fp.period_type = $2
        ORDER BY fp.period_end_date DESC
        LIMIT $3
    `, [ticker, period_type, limit]);
    
    res.json(result.rows);
});
```

### Frontend Integration (InsightsTable)
Display key metrics in the Research Tab:

```typescript
// frontend-react/src/api/financial.ts
export async function getFinancialMetrics(ticker: string) {
    const response = await fetch(`/api/v1/financial/metrics/${ticker}`);
    return response.json();
}

// Update InsightsTable component to show real metrics
```

## Benefits

✅ **No LLM Hallucinations** - Exact numbers from database  
✅ **Fast Queries** - SQL retrieval vs parsing PDFs  
✅ **Time-Series Analysis** - Track trends automatically  
✅ **Structured + Unstructured** - Combine precise data with narrative context  
✅ **Quarterly Granularity** - Seasonal pattern detection  
✅ **Complete Financial Statements** - P&L, Balance Sheet, Cash Flow in one place
