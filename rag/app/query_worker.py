
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.graph import build_graph, evaluate_quality
    from app.ollama_client import generate_answer_stream
else:
    from .graph import build_graph, evaluate_quality
    from .ollama_client import generate_answer_stream


def json_default(obj):
    """
    Make non-JSON-native Python types serializable.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return str(obj)


def emit(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, default=json_default) + "\n")
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--mode", default="general", choices=["general", "revenue", "profitability", "risk", "valuation", "forensic"], help="Analysis mode persona")
    args = parser.parse_args()

    graph = build_graph()
    state = {
        "query": args.query,
        "analysis_mode": args.mode,
        "retrieval_strategy": "hybrid",  # Will be set by query_classifier
        "plan": [],
        "evidence": [],
        "financial_data": [],  # NEW: Structured SQL data
        "forensic_report": None,  # NEW: Forensic analysis results
        "comparison_notes": [],
        "system_prompt": "",
        "user_prompt": "",
        "verified": False,
        "warnings": [],
    }

    emit({"type": "status", "stage": "planner", "message": "Planning research steps"})
    result = graph.invoke(state)

    emit({"type": "plan", "plan": result["plan"]})

    emit({
        "type": "status",
        "stage": "retriever",
        "message": f"Retrieved {len(result['evidence'])} document chunks + {len(result.get('financial_data', []))} structured items",
        "retrieval_strategy": result.get("retrieval_strategy", "unknown")
    })

    # Combine both evidence sources for frontend display
    all_sources = []
    
    # Add financial data first
    for item in result.get('financial_data', []):
        all_sources.append({
            'source_type': 'structured_sql',
            'data_category': item['data_category'],
            'fiscal_year': item['fiscal_year'],
            'company': item['company'],
            'metrics': item['metrics'],
            'text_summary': item['text_summary'],
            'file_name': f"{item['data_category']}_FY{item['fiscal_year']}",
            'section': 'SQL Database',
        })
    
    # Add vector evidence
    all_sources.extend(result["evidence"])
    
    emit({"type": "sources", "sources": all_sources})

    emit({
        "type": "status",
        "stage": "comparator",
        "message": "Prepared comparison notes"
    })
    emit({"type": "comparison", "notes": result["comparison_notes"]})

    # Emit forensic report if forensic mode was used
    if result.get('forensic_report'):
        emit({
            "type": "forensic",
            "report": result['forensic_report']
        })

    emit({
        "type": "status",
        "stage": "verifier",
        "message": "Verification checks completed",
        "verified": result["verified"],
        "warnings": result["warnings"],
    })

    answer_parts = []
    emit({"type": "status", "stage": "summarizer", "message": "Streaming answer"})

    for token in generate_answer_stream(result["system_prompt"], result["user_prompt"]):
        answer_parts.append(token)
        emit({"type": "token", "token": token})

    final_answer = "".join(answer_parts)
    
    # Evaluate answer quality using RAGAS
    emit({"type": "status", "stage": "quality_check", "message": "Evaluating answer quality"})
    
    # Update state with final answer for evaluation
    result['final_answer'] = final_answer
    result = evaluate_quality(result)
    
    # Emit quality metrics if available
    if result.get('quality_metrics'):
        emit({
            "type": "quality",
            "metrics": result['quality_metrics']
        })
    
    emit({
        "type": "final",
        "answer": final_answer,
        "verified": result["verified"],
        "warnings": result["warnings"],
        "quality_metrics": result.get('quality_metrics'),
    })


if __name__ == "__main__":
    main()
