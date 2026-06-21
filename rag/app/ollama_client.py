from __future__ import annotations

import json
import requests
from typing import Generator, List
from .config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL


def embed_texts(texts: List[str]) -> List[List[float]]:
    vectors: List[List[float]] = []
    total = len(texts)
 
    for idx, text in enumerate(texts, start=1):
        print(f"[INFO] Embedding chunk {idx}/{total} ...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        vectors.append(payload['embedding'])

    print(f"[INFO] Completed embeddings for {total} chunks")
    return vectors


def generate_answer_stream(prompt: str) -> Generator[str, None, None]:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_CHAT_MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=600,
    )
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)
        if token := data.get('response'):
            yield token
        if data.get('done'):
            break
