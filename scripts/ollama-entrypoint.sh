#!/bin/bash
set -e

# Start Ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "[entrypoint] Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 1
done
echo "[entrypoint] Ollama is ready."

# Pull models if not already present
echo "[entrypoint] Pulling models..."
ollama pull "${OLLAMA_CHAT_MODEL:-qwen3:8b}"
ollama pull "${OLLAMA_EMBED_MODEL:-nomic-embed-text}"
echo "[entrypoint] Models ready."

# Keep Ollama running
wait $OLLAMA_PID
