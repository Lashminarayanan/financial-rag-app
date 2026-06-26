"""
RAGAS-Inspired Evaluation Module for RAG Quality Assessment
Provides metrics: faithfulness, answer_relevancy, context_precision
Uses direct Ollama API calls (no langchain dependency)
"""

import os
import json
import requests
from typing import List, Dict, Optional
from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL

# Check if RAGAS evaluation is enabled (can be disabled for performance)
ENABLE_RAGAS = os.getenv('ENABLE_RAGAS', 'false').lower() == 'true'
RAGAS_AVAILABLE = ENABLE_RAGAS

if ENABLE_RAGAS:
    print("[INFO] Quality evaluation is ENABLED (using direct Ollama API)")
else:
    print("[INFO] Quality evaluation is DISABLED (set ENABLE_RAGAS=true to enable)")


def call_ollama(prompt: str, system_prompt: str = None) -> str:
    """
    Direct Ollama API call without langchain dependency.
   
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
   
    Returns:
        LLM response text
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    messages = []
   
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
   
    messages.append({"role": "user", "content": prompt})
   
    payload = {
        "model": OLLAMA_CHAT_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0}
    }
   
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("message", {}).get("content", "")
    except Exception as e:
        print(f"[ERROR] Ollama API call failed: {e}")
        return ""


def evaluate_faithfulness(answer: str, contexts: List[str]) -> float:
    """
    Evaluate if answer is grounded in the provided contexts (no hallucination).
   
    Returns:
        Score between 0.0 and 1.0
    """
    contexts_text = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
   
    prompt = f"""Given the following contexts and an answer, determine if the answer is fully supported by the contexts.

CONTEXTS:
{contexts_text}

ANSWER:
{answer}

TASK:
Rate how well the answer is grounded in the provided contexts on a scale of 0-10.
- 10: Every statement in the answer is directly supported by the contexts
- 7-9: Most statements are supported, minor unsupported details
- 4-6: Some statements are supported, some are not
- 1-3: Most statements are not supported by contexts
- 0: Answer contains information completely contradicting or absent from contexts

Respond with ONLY a number from 0-10, nothing else."""

    response = call_ollama(prompt)
   
    try:
        score = float(response.strip())
        return min(max(score / 10.0, 0.0), 1.0)  # Normalize to 0-1
    except ValueError:
        print(f"[WARNING] Could not parse faithfulness score: {response}")
        return 0.5


def evaluate_relevancy(query: str, answer: str) -> float:
    """
    Evaluate if answer addresses the user's query.
   
    Returns:
        Score between 0.0 and 1.0
    """
    prompt = f"""Given a user query and an answer, determine how well the answer addresses the query.

USER QUERY:
{query}

ANSWER:
{answer}

TASK:
Rate how relevant and complete the answer is to the query on a scale of 0-10.
- 10: Answer directly and completely addresses the query
- 7-9: Answer addresses most aspects of the query
- 4-6: Answer partially addresses the query
- 1-3: Answer barely relates to the query
- 0: Answer is completely irrelevant

Respond with ONLY a number from 0-10, nothing else."""

    response = call_ollama(prompt)
   
    try:
        score = float(response.strip())
        return min(max(score / 10.0, 0.0), 1.0)
    except ValueError:
        print(f"[WARNING] Could not parse relevancy score: {response}")
        return 0.5


def evaluate_context_precision(query: str, contexts: List[str]) -> float:
    """
    Evaluate if retrieved contexts are relevant to the query.
   
    Returns:
        Score between 0.0 and 1.0
    """
    contexts_text = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
   
    prompt = f"""Given a user query and retrieved contexts, determine how relevant the contexts are.

USER QUERY:
{query}

CONTEXTS:
{contexts_text}

TASK:
Rate how relevant and useful these contexts are for answering the query on a scale of 0-10.
- 10: All contexts are highly relevant and useful
- 7-9: Most contexts are relevant
- 4-6: Some contexts are relevant, some are not
- 1-3: Most contexts are not relevant
- 0: Contexts are completely irrelevant

Respond with ONLY a number from 0-10, nothing else."""

    response = call_ollama(prompt)
   
    try:
        score = float(response.strip())
        return min(max(score / 10.0, 0.0), 1.0)
    except ValueError:
        print(f"[WARNING] Could not parse precision score: {response}")
        return 0.5


def evaluate_response(
    query: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> Dict[str, float]:
    """
    Evaluate RAG response quality using RAGAS metrics.
   
    Args:
        query: User's question
        answer: Generated answer
        contexts: List of retrieved text chunks
        ground_truth: Optional expected answer for recall calculation
   
    Returns:
        Dict with scores (0-1 scale):
        - faithfulness: Answer grounded in contexts (no hallucination)
        - answer_relevancy: Answer addresses the query
        - context_precision: Retrieved contexts are relevant
        - overall_score: Average of all metrics
    """
    if not RAGAS_AVAILABLE:
        print("[INFO] Skipping quality evaluation (disabled)")
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_precision': 0.0,
            'overall_score': 0.0,
            'error': 'Quality evaluation disabled'
        }
   
    if not answer or len(answer.strip()) < 10:
        print("[INFO] Skipping quality evaluation (answer too short)")
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_precision': 0.0,
            'overall_score': 0.0,
            'error': 'Answer too short'
        }
   
    if not contexts or len(contexts) == 0:
        print("[INFO] Skipping quality evaluation (no contexts)")
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_precision': 0.0,
            'overall_score': 0.0,
            'error': 'No contexts available'
        }
   
    try:
        print(f"[INFO] Starting quality evaluation (query: {len(query)} chars, answer: {len(answer)} chars, contexts: {len(contexts)})")
       
        # Evaluate each metric using direct Ollama calls
        faithfulness_score = evaluate_faithfulness(answer, contexts)
        print(f"[INFO] Faithfulness: {faithfulness_score:.2f}")
       
        relevancy_score = evaluate_relevancy(query, answer)
        print(f"[INFO] Relevancy: {relevancy_score:.2f}")
       
        precision_score = evaluate_context_precision(query, contexts)
        print(f"[INFO] Context Precision: {precision_score:.2f}")
       
        # Calculate overall score
        overall = (faithfulness_score + relevancy_score + precision_score) / 3.0
       
        metrics_result = {
            'faithfulness': faithfulness_score,
            'answer_relevancy': relevancy_score,
            'context_precision': precision_score,
            'overall_score': overall
        }
       
        print(f"[SUCCESS] Quality evaluation completed: {format_quality_metrics(metrics_result)}")
        return metrics_result
   
    except Exception as e:
        print(f"[ERROR] Quality evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_precision': 0.0,
            'overall_score': 0.0,
            'error': str(e)
        }


def get_quality_label(score: float) -> str:
    """
    Convert quality score to human-readable label.
   
    Args:
        score: Quality score (0-1)
   
    Returns:
        Label: Excellent, Good, Fair, Poor
    """
    if score >= 0.85:
        return "Excellent"
    elif score >= 0.70:
        return "Good"
    elif score >= 0.50:
        return "Fair"
    else:
        return "Poor"


def format_quality_metrics(metrics: Dict[str, float]) -> str:
    """
    Format quality metrics as readable string for logging.
   
    Args:
        metrics: Dict with quality scores
   
    Returns:
        Formatted string
    """
    overall = metrics.get('overall_score', 0.0)
    label = get_quality_label(overall)
   
    return (
        f"Quality: {label} ({overall:.1%}) | "
        f"Faithfulness: {metrics.get('faithfulness', 0.0):.1%} | "
        f"Relevancy: {metrics.get('answer_relevancy', 0.0):.1%} | "
        f"Precision: {metrics.get('context_precision', 0.0):.1%}"
    )
