# Forensic Financial Analyzer Guide

## Overview

The **Forensic Financial Analyzer** is a specialized agent that detects accounting irregularities, fraud indicators, and aggressive accounting tactics in financial statements. It goes beyond traditional financial analysis to identify patterns that may indicate manipulation or financial distress.

## Key Features

### 1. **Benford's Law Analysis**
- Analyzes first-digit frequency distribution of financial figures
- Detects potential manipulation or rounding patterns
- Chi-square statistical testing with confidence levels
- Identifies digits with largest deviations from expected frequencies

**Red Flags:**
- Chi-square statistic > 20.09 indicates significant deviation
- Unusual concentration of specific digits (e.g., too many 5s or 0s)
- Patterns suggesting systematic rounding or estimation

### 2. **Revenue Quality Assessment**
- **Days Sales Outstanding (DSO) Trend Analysis**
  - Tracks DSO growth vs. revenue growth
  - Flags channel stuffing indicators
  - Identifies collection issues

**Red Flags:**
- DSO increasing by >15 days while revenue grows
- Receivables growing faster than revenue by >15%
- Unbilled revenue accumulation patterns

### 3. **Cash Flow Quality Analysis**
- **Quality of Earnings Metrics**
  - Operating cash flow to net profit ratio
  - Accrual vs. cash earnings divergence
  - Free cash flow generation

**Red Flags:**
- Cash-to-earnings ratio < 0.5 (only 50% cash backing)
- Persistent negative operating cash flow despite profits
- Large divergence between reported earnings and cash generation

### 4. **Working Capital Manipulation Detection**
- **Inventory Analysis**
  - Inventory growth exceeding sales growth
  - Obsolescence risk indicators
  - Inventory-to-sales ratio trending

- **Receivables Monitoring**
  - Receivables growth vs. revenue growth
  - Aggressive credit policies
  - Collection effectiveness

**Red Flags:**
- Inventory growth > revenue growth + 20%
- Sudden spikes in working capital components
- Unusual end-of-quarter reversals

### 5. **Expense Capitalization Analysis**
- **Depreciation Policy Changes**
  - Depreciation rate trends
  - Useful life extension indicators
  - Capitalization vs. expensing patterns

- **Capital WIP Accumulation**
  - Long-pending project capitalization
  - Delayed asset recognition
  - Maintenance vs. growth capex

**Red Flags:**
- Depreciation rate dropping by >2% suddenly
- Capital WIP > 20% of net fixed assets
- Shifting expenses to balance sheet

## Usage

### Important: Company Detection

The forensic analyzer **automatically detects the company** from your query and only analyzes structured financial data from SQL tables. It does **NOT** search document vectors to avoid cross-contamination between companies.

**Supported Company Detection:**
- **EICHERMOT** (Eicher Motors): Queries mentioning "EICHERMOT", "Eicher Motors", or "Eicher"
- **KALYANJEWEL** (Kalyan Jewellers): Queries mentioning "KALYANJEWEL", "Kalyan Jewellers", or "Kalyan"
- **Default**: If no company is mentioned, defaults to EICHERMOT

**Examples:**
```
✅ "Run forensic analysis on EICHERMOT"           → Analyzes EICHERMOT only
✅ "Forensic analysis for Kalyan Jewellers"       → Analyzes KALYANJEWEL only
✅ "Check Eicher Motors for red flags"            → Analyzes EICHERMOT only
⚠️  "Run forensic analysis"                       → Defaults to EICHERMOT
```

### Retrieval Strategy

When you select **Forensic mode**, the system automatically sets retrieval strategy to **`structured`** (SQL-only). This means:
- ✅ Fetches data from `companies`, `income_statements`, `balance_sheets`, `cash_flows` tables
- ❌ Skips vector search of document chunks (no PDF/document context)
- 🎯 Analyzes only the specific company detected in your query

This prevents documents from other companies (e.g., Kalyan Jewellery PDFs) from appearing in your EICHERMOT forensic analysis.

### Frontend Interface

**Mode Selection:**
```javascript
// Set analysis mode to 'forensic' when calling the research endpoint
POST /api/v1/research/stream
{
  "query": "Perform forensic analysis on Eicher Motors financial statements",
  "mode": "forensic",
  "topK": 6
}
```

### Command Line

```bash
# Run forensic analysis directly via Python worker
cd rag
python -m app.query_worker \
  --query "Analyze Eicher Motors for accounting irregularities" \
  --mode forensic
```

### Example Queries

**General Forensic Audit:**
```
"Run a comprehensive forensic analysis on the company's financial statements"
"Check for accounting irregularities and red flags in the financial data"
"Perform fraud detection analysis on the financial statements"
```

**Specific Focus Areas:**
```
"Analyze revenue quality and check for channel stuffing indicators"
"Examine working capital trends for manipulation patterns"
"Review cash flow quality and earnings sustainability"
"Check for aggressive capitalization of expenses"
```

## Output Format

### Forensic Report Structure

```json
{
  "overall_risk_score": 45.3,
  "overall_verdict": "MODERATE_RISK",
  "verdict_display": "🟡 Moderate Risk",
  "critical_issues": [
    {
      "type": "DSO_SPIKE",
      "severity": "🔴 Red Flag",
      "year": 2025,
      "detail": "DSO increased by 18.5 days while revenue grew 12%. Possible channel stuffing.",
      "dso_days": 65.3,
      "revenue_growth": 12.1
    }
  ],
  "benford_law": {
    "chi_square_statistic": 18.32,
    "verdict": "MONITOR",
    "risk_level": "🟡 Monitor",
    "deviation_score": 61.1,
    "interpretation": "Slight deviation from expected distribution..."
  },
  "revenue_quality": { ... },
  "cash_flow_quality": { ... },
  "working_capital": { ... },
  "expense_capitalization": { ... }
}
```

### Risk Score Interpretation

| Score Range | Verdict | Meaning |
|-------------|---------|---------|
| 0-29 | 🟢 Low Risk | No significant red flags detected |
| 30-59 | 🟡 Moderate Risk | Some areas require monitoring |
| 60-100 | 🔴 High Risk | Multiple critical issues detected |

### Severity Levels

- **🟢 Normal**: No concerns, metrics within expected ranges
- **🟡 Monitor**: Requires attention, may have legitimate explanations
- **🔴 Red Flag**: Critical issue requiring immediate investigation

## Technical Implementation

### Architecture

```
Query Worker (forensic mode)
    ↓
Graph Workflow
    ↓ 
Query Classifier → Planner → Retriever → Financial Retriever
    ↓
Forensic Analyzer Node
    ├── query_comprehensive_forensic_data() - Fetch all financial data
    ├── comprehensive_forensic_analysis()    - Run all forensic checks
    │   ├── benford_law_analysis()
    │   ├── revenue_quality_analysis()
    │   ├── cash_flow_quality_analysis()
    │   ├── working_capital_manipulation_check()
    │   └── expense_capitalization_analysis()
    └── format_forensic_report()            - Generate readable report
    ↓
Comparator → Summarizer → Verifier
```

### Database Requirements

The forensic analyzer requires comprehensive financial data from:
- `income_statements` table (P&L metrics)
- `balance_sheets` table (working capital components)
- `cash_flows` table (operating cash flow)
- `financial_periods` table (time-series data)

**Minimum Data Requirements:**
- At least 2-3 years of annual data for trend analysis
- All three financial statements populated
- Key metrics: Sales, Profit, DSO, Inventory, Receivables, Cash Flow

### Key Files

```
rag/app/
├── forensic_analyzer.py          # Core forensic analysis functions
├── financial_repository.py       # Data fetching (added forensic queries)
├── graph.py                       # Added forensic node and mode
└── query_worker.py               # Added forensic mode support
```

## Use Cases

### 1. **Pre-Investment Due Diligence**
Run forensic analysis before making investment decisions to identify:
- Quality of earnings
- Sustainability of reported profits
- Hidden accounting risks

### 2. **Ongoing Portfolio Monitoring**
Periodic forensic audits to:
- Track changes in accounting quality
- Early detection of deteriorating practices
- Monitor management credibility

### 3. **Competitive Intelligence**
Compare forensic scores across competitors to identify:
- Companies with higher accounting quality
- Firms using aggressive tactics
- Relative transparency levels

### 4. **Activist Investor Research**
Identify potential targets with:
- Earnings manipulation patterns
- Governance concerns
- Opportunities for improvement

### 5. **Credit Risk Assessment**
Evaluate borrower creditworthiness through:
- Cash flow quality analysis
- Working capital health
- Financial distress indicators

## Limitations & Disclaimers

⚠️ **Important Considerations:**

1. **Anomalies ≠ Fraud**: Red flags indicate areas requiring investigation, not definitive proof of wrongdoing
2. **Business Context Matters**: Legitimate business changes can trigger alerts (acquisitions, industry shifts)
3. **Data Quality**: Analysis quality depends on complete, accurate financial data
4. **Minimum Sample Size**: Benford's Law requires ≥30 data points for statistical validity
5. **Industry Variations**: Some metrics vary by industry (e.g., higher DSO in B2B businesses)

**Best Practice**: Use forensic analysis as a screening tool, followed by deeper manual investigation of flagged items.

## Future Enhancements

### Planned Features

1. **Industry Benchmarking**: Compare metrics against sector peers
2. **Altman Z-Score**: Bankruptcy prediction model
3. **Beneish M-Score**: Earnings manipulation probability
4. **Related Party Transactions**: Automatic RPT detection from narratives
5. **Management Discussion Analysis**: NLP sentiment analysis on MD&A
6. **Restatement Risk Predictor**: ML model for identifying restatement probability
7. **Seasonal Adjustment**: Quarterly data analysis with seasonality correction

### Integration Opportunities

- **Alert System**: Automated notifications when risk score exceeds thresholds
- **Trend Dashboard**: Historical forensic score tracking
- **PDF Report Export**: Formatted audit reports for stakeholders
- **API Endpoints**: Programmatic access for third-party tools

## Support & Feedback

For questions or feature requests, please open an issue in the project repository or contact the development team.

---

**Version**: 1.0  
**Last Updated**: 2026-06-26  
**Status**: Production Ready ✅
