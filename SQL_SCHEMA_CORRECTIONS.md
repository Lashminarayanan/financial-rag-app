# SQL Schema Corrections Summary

## Changes Made

### 1. Updated `infra/sql/001_init.sql`

#### Added Missing Columns to `documents` table:
- `original_name TEXT` - Stores the original filename from file upload
- `page_count INTEGER` - Total pages in the document (from parser probe)
- `parser_name TEXT` - Parser used (pypdf or docling)
- `parser_reason TEXT` - Why this parser was chosen
- `parser_probe JSONB` - Parser quality probe metrics
- `ingestion_stats JSONB` - Ingestion statistics (chunk counts, etc.)

#### Added Parser Observability Indexes:
- `idx_documents_parser_name` - Fast lookup by parser
- `idx_documents_parser_probe` - GIN index for parser probe JSONB
- `idx_documents_ingestion_stats` - GIN index for ingestion stats JSONB

### 2. Updated `infra/sql/002_parser_observability.sql`

#### Made Backward Compatible:
- Added `ADD COLUMN IF NOT EXISTS` for all columns
- Added `original_name` and `page_count` columns for existing databases
- Kept all existing ALTER TABLE and CREATE INDEX statements
- Now safe to run on both new and existing databases

### 3. Updated `rag/app/repository.py`

#### Added `page_count` Field:
- Extracts `total_pages` from parser probe metrics
- Inserts into database during document ingestion
- Enables page count display in Document Library UI

## Schema Alignment

### Documents Table (Final Schema):
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  file_name TEXT NOT NULL,           -- Sanitized filename on disk
  original_name TEXT,                -- Original upload filename
  file_path TEXT NOT NULL,           -- Full path to PDF
  title TEXT,                        -- Extracted title
  company_name TEXT,                 -- Extracted company
  fiscal_year TEXT,                  -- Fiscal year
  checksum TEXT,                     -- SHA256 hash
  page_count INTEGER,                -- Total pages
  parser_name TEXT,                  -- 'pypdf' or 'docling'
  parser_reason TEXT,                -- Parser selection reason
  parser_probe JSONB,                -- Quality probe metrics
  ingestion_stats JSONB,             -- Chunk counts, etc.
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### What the Backend Expects:
- ✅ `id` - UUID primary key
- ✅ `fileName` (maps to file_name)
- ✅ `originalName` (maps to original_name) - Currently NULL
- ✅ `checksum` - SHA256 hash
- ✅ `pageCount` (maps to page_count) - Now populated
- ✅ `parserName` (maps to parser_name)
- ✅ `createdAt` (maps to created_at)
- ✅ `chunkCount` - Calculated via JOIN with chunks table

## Known Limitations

### `original_name` Not Currently Populated:
The ingestion flow doesn't pass the original filename from the upload endpoint to the Python worker. This field will be NULL until the ingestion flow is enhanced.

**To Fix (Future Enhancement):**
1. Modify `ingest_worker.py` to accept `--original-name` parameter
2. Update `startIngestWorker()` in backend to pass original filename
3. Update `parse_pdf()` to include original_name in document dict

## Testing

### After Running SQL Migrations:

1. **Verify Schema:**
   ```sql
   \d documents
   ```
   Should show all columns including original_name, page_count, parser_name, etc.

2. **Test Documents API:**
   ```bash
   curl http://localhost:8080/api/v1/documents
   ```
   Should return `[]` without errors

3. **Test Ingestion:**
   - Upload a PDF through the UI
   - Should see page_count populated
   - original_name will be NULL (expected)

4. **Test Document Library UI:**
   - Navigate to Documents tab
   - Should show "No documents ingested yet" instead of error
   - After ingesting, should display document cards with page count

## Migration Path

### For New Installations:
```bash
psql -U postgres -p 5433 -d financial_rag -f infra/sql/001_init.sql
psql -U postgres -p 5433 -d financial_rag -f infra/sql/002_parser_observability.sql
psql -U postgres -p 5433 -d financial_rag -f infra/sql/003_query_history.sql
```

### For Existing Databases:
```bash
# Run 002 to add missing columns
psql -U postgres -p 5433 -d financial_rag -f infra/sql/002_parser_observability.sql
```

The `ADD COLUMN IF NOT EXISTS` ensures no errors if columns already exist.

## Error Resolution

### "Failed to fetch documents" Error:
**Root Cause:** Database schema didn't match what the routes expected

**Fixed By:**
1. ✅ Added missing columns to documents table
2. ✅ Updated Python code to populate page_count
3. ✅ Made migrations backward compatible
4. ✅ Added proper indexes for performance

**Result:** Documents API now returns empty array `[]` instead of errors, and UI loads correctly.
