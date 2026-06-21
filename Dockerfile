# ============================================================
# Stage 1: Build React frontend
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /build

COPY frontend-react/package.json frontend-react/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install

COPY frontend-react/tsconfig.json frontend-react/vite.config.ts frontend-react/index.html ./
COPY frontend-react/src/ ./src/

RUN npx vite build

# ============================================================
# Stage 2: Install Python dependencies
# ============================================================
FROM python:3.11-slim AS python-deps

WORKDIR /deps

COPY rag/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# Stage 3: Final runtime image
# ============================================================
FROM python:3.11-slim

# Install Node.js 20 LTS
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from Stage 2
COPY --from=python-deps /install /usr/local

# Copy RAG Python application
COPY rag/app/ /app/rag/app/

# Copy Node.js backend and install production dependencies
COPY backend-enterprise/package.json backend-enterprise/package-lock.json* /app/backend-enterprise/
WORKDIR /app/backend-enterprise
RUN npm ci --omit=dev --ignore-scripts 2>/dev/null || npm install --omit=dev

COPY backend-enterprise/src/ /app/backend-enterprise/src/

# Copy built frontend into backend's public directory
COPY --from=frontend-build /build/dist/ /app/backend-enterprise/public/

# Copy SQL init scripts (baked into image for portability)
COPY infra/sql/ /app/sql/

# Create reports directory
RUN mkdir -p /app/data/reports

WORKDIR /app

# Environment defaults (overridable at runtime)
ENV NODE_ENV=production \
    BACKEND_PORT=8080 \
    PYTHON_QUERY_WORKER=python3 \
    RAG_PYTHON_ENTRY=/app/rag/app/query_worker.py \
    RAG_INGEST_WORKER_ENTRY=/app/rag/app/ingest_worker.py \
    REPORTS_DIR=/app/data/reports \
    POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=financial_rag \
    POSTGRES_USER=rag_user \
    POSTGRES_PASSWORD=rag_pass \
    OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_CHAT_MODEL=qwen3:8b \
    OLLAMA_EMBED_MODEL=nomic-embed-text

EXPOSE 8080

CMD ["node", "/app/backend-enterprise/src/server.js"]
