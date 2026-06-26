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
