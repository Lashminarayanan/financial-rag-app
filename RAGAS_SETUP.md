# RAGAS Setup Instructions

## What is RAGAS?

RAGAS (Retrieval-Augmented Generation Assessment) evaluates the quality of RAG system outputs using three key metrics:
- **Faithfulness**: Answer is grounded in retrieved contexts (no hallucination)
- **Answer Relevancy**: Answer addresses the user's query
- **Context Precision**: Retrieved contexts are relevant to the query

## Current Status

**RAGAS is DISABLED by default** for performance reasons (evaluation can take 10-30 seconds per query).

## How to Enable RAGAS

### Option 1: Enable via Environment Variable

Add to your `.env` file or set in your terminal:

```bash
# Windows PowerShell
$env:ENABLE_RAGAS="true"

# Linux/Mac
export ENABLE_RAGAS=true
```

### Option 2: Install Required Dependencies

RAGAS requires additional Python packages:

```powershell
cd rag
pip install ragas>=0.1.9 datasets>=2.14.0 langchain-community>=0.0.20
```

### Option 3: Verify Installation

Check if RAGAS is working:

```powershell
python -c "from ragas import evaluate; print('RAGAS installed successfully')"
```

## Testing RAGAS

1. **Enable RAGAS**: Set `ENABLE_RAGAS=true` in environment
2. **Restart backend** (if running)
3. **Run a query** in the Research tab
4. **Check logs** for:
   - `[INFO] RAGAS evaluation is ENABLED`
   - `[INFO] Starting RAGAS evaluation...`
   - `[SUCCESS] RAGAS evaluation completed: Quality: Excellent (88%)`

## Expected Behavior

### When RAGAS is Enabled:
- Quality metrics card appears in Answer panel after query completes
- Query History shows quality badges (⭐⭐⭐⭐⭐ Excellent)
- Evaluation adds 10-30 seconds to query time

### When RAGAS is Disabled (Default):
- No quality metrics displayed
- Queries complete faster
- No evaluation overhead

## Troubleshooting

### "RAGAS not available or disabled"
- Check `ENABLE_RAGAS` environment variable
- Verify RAGAS dependencies are installed

### "RAGAS evaluation failed"
- Check Ollama is running (`ollama serve`)
- Check model is available (`ollama list`)
- Review Python console logs for detailed errors

### Quality metrics not showing in UI
- Open browser console (F12) and look for:
  - `[RAGAS] Quality metrics received:` - Backend sent metrics
  - `[AnswerPanel] Quality metrics:` - Frontend received metrics
- If you see logs but no UI, check if `overall_score > 0`

## Performance Impact

| Configuration | Query Time | Overhead |
|--------------|------------|----------|
| RAGAS Disabled | 2-5 sec | 0 sec |
| RAGAS Enabled | 15-35 sec | +10-30 sec |

For development/testing, keep RAGAS **disabled** for faster iteration.
For production/demos, enable RAGAS to showcase quality assessment.
