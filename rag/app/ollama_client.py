from __future__ import annotations

import json
import time
import requests
from typing import Generator, List
from .config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL

MAX_BATCH_SIZE = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubles each retry


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Batch-embed texts using Ollama /api/embed endpoint.
    - Splits into sub-batches of MAX_BATCH_SIZE to avoid OOM
    - Retries transient failures with exponential backoff
    - Falls back to single-text /api/embeddings if batch endpoint fails
    - Validates output count matches input count
    """
    if not texts:
        return []

    all_vectors: List[List[float]] = []

    for start in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[start:start + MAX_BATCH_SIZE]
        vectors = _embed_batch_with_retry(batch)
        all_vectors.extend(vectors)

    return all_vectors


def _embed_batch_with_retry(batch: List[str]) -> List[List[float]]:
    """Try batch endpoint with retries, fall back to single-text on persistent failure."""
    timeout = max(120, len(batch) * 30)  # scale timeout with batch size

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[INFO] Batch embedding {len(batch)} chunk(s) (attempt {attempt}) ...")
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/embed",
                json={"model": OLLAMA_EMBED_MODEL, "input": batch},
                timeout=timeout,
            )
            response.raise_for_status()
            vectors = response.json()["embeddings"]

            if len(vectors) != len(batch):
                raise ValueError(
                    f"Embedding count mismatch: sent {len(batch)}, got {len(vectors)}"
                )

            print(f"[INFO] Batch embedding complete: {len(vectors)} vectors")
            return vectors

        except (requests.RequestException, ValueError, KeyError) as exc:
            print(f"[WARN] Batch embed attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * (2 ** (attempt - 1))
                print(f"[INFO] Retrying in {wait}s ...")
                time.sleep(wait)

    # Fallback: embed one at a time
    print(f"[WARN] Batch endpoint failed after {MAX_RETRIES} attempts, falling back to single-text mode")
    return _embed_single_fallback(batch)


def _embed_single_fallback(texts: List[str]) -> List[List[float]]:
    """Fallback: embed texts one by one using /api/embeddings."""
    vectors: List[List[float]] = []
    for idx, text in enumerate(texts, start=1):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                    timeout=120,
                )
                response.raise_for_status()
                vectors.append(response.json()["embedding"])
                break
            except requests.RequestException as exc:
                print(f"[WARN] Single embed {idx} attempt {attempt} failed: {exc}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF * (2 ** (attempt - 1)))
                else:
                    raise RuntimeError(
                        f"Failed to embed chunk {idx} after {MAX_RETRIES} attempts"
                    ) from exc
    return vectors


def generate_answer_stream(system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
    """
    Generate streaming response using Ollama Chat API with system/user message roles.
    
    Args:
        system_prompt: System instructions defining the assistant's role and behavior
        user_prompt: User's question with context and evidence
    
    Yields:
        Token strings from the model's response
    """
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True
        },
        stream=True,
        timeout=600,
    )
    response.raise_for_status()
    
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)
        
        # Chat API returns content in message.content field
        if message := data.get('message'):
            if token := message.get('content'):
                yield token
        
        if data.get('done'):
            break
