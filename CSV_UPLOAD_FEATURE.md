# CSV Financial Data Upload Feature

## Overview

Enhanced the document upload interface to support **CSV financial data uploads** in addition to PDF document ingestion. When a user uploads a CSV file containing financial statements (P&L, Balance Sheet, Cash Flow), the system automatically:
1. Accepts the CSV file through the UI
2. Saves it temporarily on the backend
3. Executes the Python financial data ingestion script
4. Parses the CSV and loads structured data into PostgreSQL
5. Returns real-time progress feedback to the UI

## Architecture

### Frontend Components

**IngestionPanel.tsx** (`frontend-react/src/components/IngestionPanel.tsx`)
- Added file type selector (radio buttons): PDF or CSV
- Conditional rendering based on selected file type
- CSV-specific inputs: Company Name and Stock Ticker
- Different progress indicators for PDF vs CSV uploads
- Separate upload handlers routing to appropriate endpoints

**API Functions** (`frontend-react/src/api/ingestion.ts`)
- `uploadCsv(file, onProgress)` - Uploads CSV file via XHR with progress tracking
- `streamCsvIngestion({ fileName, company, ticker }, onEvent)` - SSE stream for real-time processing logs

### Backend Services

**Routes** (`backend-enterprise/src/routes/ingestion.js`)
- **POST /api/v1/ingestion/upload-csv** - Accepts CSV file uploads (mimetype: text/csv, max 50MB)
- **POST /api/v1/ingestion/run-csv** - Executes Python ingestion script with company name and ticker parameters
- File validation: Rejects non-CSV files with error message
- SSE streaming: Real-time logs from Python worker process

**Service Gateway** (`backend-enterprise/src/services/financialCsvIngestWorkerGateway.js`)
- Spawns Python process: `python ../rag/ingest_financial_csv.py --file <path> --company <name> --ticker <symbol>`
- Captures stdout/stderr for frontend streaming
- Handles process lifecycle and cleanup

**Configuration** (`backend-enterprise/src/config.js`)
- Added `financialCsvIngestWorker` path configuration
- Default: `../rag/ingest_financial_csv.py`
- Override with env var: `FINANCIAL_CSV_INGEST_WORKER`

### Python Ingestion Script

**ingest_financial_csv.py** (`rag/ingest_financial_csv.py`)
- Already implemented (no changes needed)
- Parses CSV sections: PROFIT & LOSS, BALANCE SHEET, CASH FLOW
- Inserts data into 10-table financial data schema
- Returns success/failure messages to stdout

### Database Schema

**004_financial_data.sql** (`infra/sql/004_financial_data.sql`)
- 10 tables for financial data storage:
  - `companies` - Company master data
  - `financial_periods` - Time dimension (annual/quarterly/TTM)
  - `income_statements` - P&L data
  - `balance_sheets` - Asset/liability data
  - `cash_flows` - Cash flow statements
  - `financial_ratios` - Calculated ratios
  - `growth_metrics` - YoY/CAGR growth rates
  - `market_data` - Stock prices and market cap
  - `financial_metrics_text` - Narrative summaries with embeddings
  - `parser_metrics` - Metadata tracking

## How to Use

### 1. Start the Application

Ensure all services are running:
```powershell
# Terminal 1: PostgreSQL (Docker)
cd infra
docker-compose up

# Terminal 2: Backend
cd backend-enterprise
npm install
npm start

# Terminal 3: Frontend
cd frontend-react
npm install
npm run dev

# Terminal 4: Apply database schema
psql -h localhost -p 5433 -U rag_user -d financial_rag -f infra/sql/004_financial_data.sql
```

### 2. Upload CSV File via UI

1. Open http://localhost:5173 in browser
2. Navigate to **Ingestion** panel (bottom of page)
3. Select **📊 CSV File (Financial Data)** radio button
4. Enter company details:
   - **Company Name**: `EICHER MOTORS LTD` (or any company name)
   - **Stock Ticker**: `EICHERMOT` (or any ticker symbol)
5. Click **Choose File** and select your CSV file (e.g., `Eicher_data_sheet.csv`)
6. Click **Upload & Load Financial Data** button
7. Monitor real-time logs in the **Processing Logs** section

### 3. CSV File Format Requirements

Expected structure (as in `Eicher_data_sheet.csv`):
```csv
# Section headers (row with text):
PROFIT & LOSS
CONSOLIDATED PROFIT & LOSS OF EICHER MOTORS LTD.

# Column headers (row with dates):
Particulars,Mar-17,Mar-18,Mar-19,...,Sep-24

# Data rows:
Sales,6723,7480,8437,...,4015
Net Profit,1223,1516,1728,...,845
...

# Next section:
BALANCE SHEET
CONSOLIDATED BALANCE SHEET OF EICHER MOTORS LTD.
...
```

**Column Naming Convention**:
- Annual data: `Mar-17`, `Mar-18`, `Mar-19` (MMM-YY format)
- Quarterly data: `Sep-24`, `Jun-24`, `Mar-24` (MMM-YY format)
- Script automatically detects period type (annual vs quarterly) based on column gaps

### 4. Verify Data in Database

```sql
-- Check inserted company
SELECT * FROM companies WHERE ticker = 'EICHERMOT';

-- Count periods
SELECT period_type, COUNT(*) 
FROM financial_periods 
WHERE company_id = (SELECT company_id FROM companies WHERE ticker = 'EICHERMOT')
GROUP BY period_type;

-- Check income statement data
SELECT fp.fiscal_year, fp.quarter, is.sales, is.net_profit, is.eps
FROM income_statements is
JOIN financial_periods fp ON is.period_id = fp.period_id
WHERE fp.company_id = (SELECT company_id FROM companies WHERE ticker = 'EICHERMOT')
ORDER BY fp.period_end_date DESC
LIMIT 10;
```

## Code Flow

### Upload Phase
```
Frontend (IngestionPanel.tsx)
  → uploadCsv(file, onProgress)
    → POST /api/v1/ingestion/upload-csv
      → Multer validation (CSV only)
      → Save to config.reportsUploadDir
      → Return { fileName, savedPath }
```

### Ingestion Phase
```
Frontend (IngestionPanel.tsx)
  → streamCsvIngestion({ fileName, company, ticker })
    → POST /api/v1/ingestion/run-csv (SSE)
      → financialCsvIngestWorkerGateway.startFinancialCsvIngestWorker()
        → spawn Python process:
            python ../rag/ingest_financial_csv.py \
              --file <path> \
              --company "EICHER MOTORS LTD" \
              --ticker "EICHERMOT"
        → Stream stdout → Frontend logs
        → Stream stderr → Error display
        → Process exit → Success/failure indicator
```

## File Changes Summary

### New Files
- `backend-enterprise/src/services/financialCsvIngestWorkerGateway.js` - Python process spawner

### Modified Files
- `backend-enterprise/src/config.js` - Added `financialCsvIngestWorker` path
- `backend-enterprise/src/routes/ingestion.js` - Added `/upload-csv` and `/run-csv` endpoints
- `frontend-react/src/components/IngestionPanel.tsx` - Added file type selector, CSV inputs, dual upload logic
- `frontend-react/src/api/ingestion.ts` - Added `uploadCsv()` and `streamCsvIngestion()` functions

## Testing Checklist

- [x] **Task 1**: Backend CSV upload endpoint accepts CSV files
- [x] **Task 2**: Python ingestion script execution service spawns process correctly
- [x] **Task 3**: Frontend UI shows file type selector and CSV-specific inputs
- [x] **Task 4**: File type validation rejects non-CSV files
- [ ] **Task 5**: End-to-end test with real CSV file

### Manual Testing Steps

1. **File Type Selector**
   - Switch between PDF and CSV modes
   - Verify file input changes accept attribute
   - Verify company/ticker fields appear for CSV only

2. **CSV Upload**
   - Select valid CSV file
   - Enter company name and ticker
   - Click upload button
   - Verify progress bar shows upload percentage
   - Check logs panel for upload confirmation

3. **CSV Ingestion**
   - After upload completes, verify ingestion starts automatically
   - Check logs for:
     - "Processing financial data for: EICHER MOTORS LTD (EICHERMOT)"
     - Period insertion messages (e.g., "Inserted 10 annual periods")
     - Success message: "✅ Financial data loaded successfully into database"
   - Verify completion status changes to "Completed"

4. **Error Handling**
   - Try uploading non-CSV file (should be rejected)
   - Try uploading malformed CSV (should show error in logs)
   - Test with empty company name/ticker (should use defaults)

5. **Database Verification**
   - Run SQL queries (see "Verify Data in Database" section above)
   - Check `companies`, `financial_periods`, `income_statements` tables
   - Verify data matches CSV file content

## Troubleshooting

### CSV Upload Fails with "Only CSV files are allowed"

**Cause**: File mimetype not recognized as CSV  
**Solution**: Ensure file has `.csv` extension and mimetype is `text/csv` or `application/csv`

### Python Script Not Found Error

**Cause**: `financialCsvIngestWorker` path incorrect  
**Solution**: Check `backend-enterprise/src/config.js`, verify path: `../rag/ingest_financial_csv.py`

### Database Connection Error

**Cause**: PostgreSQL not running or schema not applied  
**Solution**:
```powershell
# Start database
cd infra
docker-compose up

# Apply schema
psql -h localhost -p 5433 -U rag_user -d financial_rag -f sql/004_financial_data.sql
```

### "Company already exists" Warning

**Cause**: Company with same ticker already in database  
**Solution**: Script updates existing company data, not an error. Or delete and re-insert:
```sql
-- Delete company and cascade to related tables
DELETE FROM companies WHERE ticker = 'EICHERMOT';
```

### CSV Parsing Fails

**Cause**: CSV structure doesn't match expected format  
**Solution**: 
- Ensure section headers: "PROFIT & LOSS", "BALANCE SHEET", "CASH FLOW"
- Verify column headers use MMM-YY format (e.g., "Mar-17", "Sep-24")
- Check for extra whitespace or special characters
- Review Python script logs for specific error messages

## Future Enhancements

1. **Auto-detect Company Name and Ticker** from CSV metadata or filename
2. **CSV Format Validation** before upload (check headers, columns)
3. **Duplicate Period Detection** and update vs insert logic
4. **Batch Upload** - Multiple CSV files at once
5. **CSV Template Download** - Provide standardized template for users
6. **Progress Indicators** - Show row-by-row insertion progress
7. **Data Preview** - Show parsed data before final insertion
8. **Undo/Rollback** - Remove uploaded data if needed

## Related Documentation

- [FINANCIAL_DATA_INTEGRATION.md](./FINANCIAL_DATA_INTEGRATION.md) - Database schema and setup
- [HYBRID_RETRIEVAL_GUIDE.md](./HYBRID_RETRIEVAL_GUIDE.md) - How financial data is queried
- [rag/ingest_financial_csv.py](./rag/ingest_financial_csv.py) - Python ingestion script source code
