
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.graph import build_graph
    from app.ollama_client import generate_answer_stream
else:
    from .graph import build_graph
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
    args = parser.parse_args()

    graph = build_graph()
    state = {
        "query": args.query,
        "plan": [],
        "evidence": [],
        "comparison_notes": [],
        "prompt": "",
        "verified": False,
        "warnings": [],
    }

    emit({"type": "status", "stage": "planner", "message": "Planning research steps"})
    result = graph.invoke(state)

    emit({"type": "plan", "plan": result["plan"]})

    emit({
        "type": "status",
        "stage": "retriever",
        "message": f"Retrieved {len(result['evidence'])} evidence chunks"
    })

    emit({"type": "sources", "sources": result["evidence"]})

    emit({
        "type": "status",
        "stage": "comparator",
        "message": "Prepared comparison notes"
    })
    emit({"type": "comparison", "notes": result["comparison_notes"]})

    emit({
        "type": "status",
        "stage": "verifier",
        "message": "Verification checks completed",
        "verified": result["verified"],
        "warnings": result["warnings"],
    })

    answer_parts = []
    emit({"type": "status", "stage": "summarizer", "message": "Streaming answer"})

    for token in generate_answer_stream(result["prompt"]):
        answer_parts.append(token)
        emit({"type": "token", "token": token})

    final_answer = "".join(answer_parts)
    emit({
        "type": "final",
        "answer": final_answer,
        "verified": result["verified"],
        "warnings": result["warnings"],
    })


if __name__ == "__main__":
    main()
