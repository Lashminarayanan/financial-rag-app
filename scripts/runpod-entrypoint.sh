#!/bin/bash
set -e

echo "========================================="
echo " Financial RAG - RunPod Startup"
echo "========================================="

# ─── PostgreSQL ───────────────────────────────────────────────
echo "[1/4] Starting PostgreSQL..."

# Initialize DB if not already done
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "[postgres] Initializing database cluster..."
    sudo -u postgres /usr/lib/postgresql/16/bin/initdb -D "$PGDATA"

    # Configure PostgreSQL for local trust auth
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
    echo "local all all trust" >> "$PGDATA/pg_hba.conf"
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PGDATA/postgresql.conf"
fi

# Start PostgreSQL
sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl -D "$PGDATA" -l /var/log/postgresql.log start

# Wait for PostgreSQL to be ready
echo "[postgres] Waiting for PostgreSQL..."
until sudo -u postgres pg_isready -q; do
    sleep 1
done
echo "[postgres] PostgreSQL is ready."

# Create user and database if first run
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'" | grep -q 1; then
    echo "[postgres] Creating user and database..."
    sudo -u postgres psql -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"
    sudo -u postgres psql -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};"

    # Run init SQL scripts
    echo "[postgres] Running init scripts..."
    for f in /app/sql/*.sql; do
        echo "  -> $f"
        sudo -u postgres psql -d "${POSTGRES_DB}" -f "$f"
    done
    echo "[postgres] Database initialized."
fi

# ─── Ollama ───────────────────────────────────────────────────
echo "[2/4] Starting Ollama..."

export OLLAMA_MODELS="${OLLAMA_MODELS:-/workspace/ollama}"
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "[ollama] Waiting for Ollama..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "[ollama] Ollama is ready."

# ─── Pull Models ─────────────────────────────────────────────
echo "[3/4] Pulling models (cached in /workspace/ollama)..."
ollama pull "${OLLAMA_CHAT_MODEL}" 2>&1 | tail -1
ollama pull "${OLLAMA_EMBED_MODEL}" 2>&1 | tail -1
echo "[ollama] Models ready: ${OLLAMA_CHAT_MODEL}, ${OLLAMA_EMBED_MODEL}"

# ─── Node.js App ─────────────────────────────────────────────
echo "[4/4] Starting Node.js application on port ${BACKEND_PORT}..."
echo "========================================="
echo " All services running. App: http://0.0.0.0:${BACKEND_PORT}"
echo "========================================="

# Start the Node.js app in foreground (keeps container alive)
exec node /app/backend-enterprise/src/server.js
