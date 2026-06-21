# UI Refactoring - Tab-Based Navigation

## Overview

The UI has been refactored from a single-page layout to a modern tab-based navigation system, improving usability and organization of features.

## New Structure

### 🔍 Research Tab (Primary Workflow)
The main research interface for querying financial documents:
- **Query Composer**: Enter research questions
- **Execution Timeline**: View agentic workflow steps (planner → retriever → comparator → summarizer → verifier)
- **Answer Panel**: View AI-generated responses with citations
- **Evidence Explorer**: Browse retrieved source chunks with similarity scores
- **Insights Table**: Review extracted financial metrics

### 📁 Documents Tab
Document management and ingestion:
- **Ingestion Panel**: Upload and process PDF documents
  - Real-time progress tracking
  - Parser selection and monitoring
  - Chunk count visibility
- **Document Library**: View and manage ingested documents
  - Search/filter documents
  - Document metadata (parser, chunks, pages, checksum)
  - Delete documents with confirmation

### 📊 Analytics Tab
System observability and performance:
- **Query History**: Recent research queries with metrics
  - Query text and timestamp
  - Execution duration
  - Source count
  - Verification status
  - Re-run capability (coming soon)
- **Parser Stats**: Parser performance analytics
  - Document count by parser
  - Average chunk metrics
  - Recent ingestion details

## File Structure

```
frontend-react/src/
├── views/
│   ├── ResearchView.tsx          # Research tab content
│   ├── DocumentsView.tsx         # Documents tab content
│   └── ObservabilityView.tsx     # Analytics tab content
├── components/
│   ├── Navigation/
│   │   └── TabBar.tsx            # Tab navigation component
│   ├── Documents/
│   │   └── DocumentLibrary.tsx   # Document grid and management
│   ├── Analytics/
│   │   └── QueryHistory.tsx      # Query history list
│   └── [existing components...]
├── api/
│   ├── documents.ts              # Document API calls
│   ├── queryHistory.ts           # Query history API calls
│   └── [existing APIs...]
└── App.tsx                       # Main app with tab routing
```

## Backend Changes

### New API Endpoints

#### Documents
- `GET /api/v1/documents` - List all ingested documents
- `DELETE /api/v1/documents/:id` - Delete a document and its chunks

#### Query History
- `GET /api/v1/query-history` - Fetch recent query history

### Database Schema

New table: `query_history` (see `infra/sql/003_query_history.sql`)
```sql
CREATE TABLE query_history (
  id SERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  duration INTEGER,
  source_count INTEGER,
  verified BOOLEAN,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Research Route Enhancement
The `/api/v1/research/stream` endpoint now automatically logs:
- Query text
- Execution duration
- Number of sources retrieved
- Verification status

## Setup Instructions

### 1. Run Database Migration
```bash
# Apply the new query_history table
psql -U rag_user -d financial_rag -f infra/sql/003_query_history.sql
```

Or if using Docker:
```bash
docker exec -i <postgres-container> psql -U rag_user -d financial_rag < infra/sql/003_query_history.sql
```

### 2. Install Dependencies (if needed)
```bash
cd frontend-react
npm install

cd ../backend-enterprise
npm install
```

### 3. Start Services
```bash
# Start backend
cd backend-enterprise
npm run dev

# Start frontend
cd frontend-react
npm run dev
```

## Usage

### Navigating Tabs
Click on the tab icons/labels to switch between views:
- 🔍 **Research** - Run queries and analyze results
- 📁 **Documents** - Upload and manage documents
- 📊 **Analytics** - View query history and parser statistics

### Managing Documents
1. Go to **Documents** tab
2. Use **Ingestion Panel** to upload new PDFs
3. View uploaded documents in **Document Library**
4. Search documents by filename
5. Delete documents using the 🗑️ button

### Tracking Query History
1. Execute queries in the **Research** tab
2. View history in **Analytics** tab
3. See execution metrics (duration, sources, verification)

## Benefits

✅ **Improved Organization**: Related features grouped logically  
✅ **Reduced Clutter**: Focused views for specific tasks  
✅ **Better Performance**: Load only active tab content  
✅ **Enhanced UX**: Clear navigation and feature discovery  
✅ **Mobile Responsive**: Tab labels hide on small screens  

## Future Enhancements

- [ ] Query re-run from history (one-click)
- [ ] Document preview/viewer
- [ ] Bulk document operations
- [ ] Export query history
- [ ] Advanced search and filtering
- [ ] System health dashboard
- [ ] User preferences/settings tab

## Responsive Design

### Desktop (> 1200px)
- Full tab labels visible
- Three-column research grid
- Two-column analytics grid

### Tablet (860px - 1200px)
- Tab labels visible
- Single-column grids
- Stacked panels

### Mobile (< 860px)
- Tab icons only (labels hidden)
- Full-width components
- Optimized touch targets
