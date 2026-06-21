#!/bin/bash
# Don't use set -e; handle errors explicitly to avoid S3 write failures killing the script

echo "========================================="
echo " Financial RAG - RunPod Startup"
echo "========================================="

# ─── Graceful shutdown: dump DB + PDFs to S3 network volume ──
cleanup() {
    echo "[shutdown] Saving state to /workspace/..."
    mkdir -p /workspace/postgres /workspace/reports

    # Backup database
    sudo -u postgres pg_dump -Fc -d "${POSTGRES_DB}" -f /workspace/postgres/backup.dump 2>&1 && \
        echo "[shutdown] Database backed up." || \
        echo "[shutdown] Warning: DB backup failed."

    # Backup uploaded PDFs
    if [ -d "/app/data/reports" ] && [ "$(ls -A /app/data/reports 2>/dev/null)" ]; then
        cp -r /app/data/reports/* /workspace/reports/ 2>/dev/null && \
            echo "[shutdown] PDFs backed up." || \
            echo "[shutdown] Warning: PDF backup failed."
    fi

    sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl -D "$PGDATA" stop -m fast 2>/dev/null
    kill $OLLAMA_PID 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT EXIT

# ─── Fix permissions (container disk, not S3) ────────────────
mkdir -p /var/lib/postgresql/16/data /workspace/ollama /workspace/postgres /app/data/reports /var/log/postgresql
chown -R postgres:postgres /var/lib/postgresql/16
chown postgres:postgres /var/log/postgresql
chmod 0750 /var/log/postgresql

# ─── PostgreSQL ───────────────────────────────────────────────
echo "[1/4] Starting PostgreSQL..."

# Initialize DB if not already done
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "[postgres] Initializing database cluster..."
    sudo -u postgres /usr/lib/postgresql/16/bin/initdb -D "$PGDATA"

    # Configure PostgreSQL
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
    echo "local all all trust" >> "$PGDATA/pg_hba.conf"
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PGDATA/postgresql.conf"
fi

# Start PostgreSQL
sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl -D "$PGDATA" -l /var/log/postgresql/postgresql.log start

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
fi

# ─── Restore from S3 backup if available ─────────────────────
if [ -f "/workspace/postgres/backup.dump" ]; then
    echo "[postgres] Restoring from persistent backup..."
    sudo -u postgres pg_restore --clean --if-exists -d "${POSTGRES_DB}" /workspace/postgres/backup.dump 2>&1 && \
        echo "[postgres] Restore complete." || \
        echo "[postgres] Warning: restore had non-fatal errors (normal on first run)."
fi

# Restore uploaded PDFs from S3
if [ -d "/workspace/reports" ] && [ "$(ls -A /workspace/reports 2>/dev/null)" ]; then
    echo "[postgres] Restoring uploaded PDFs..."
    cp -r /workspace/reports/* /app/data/reports/ 2>/dev/null && \
        echo "[postgres] PDFs restored." || \
        echo "[postgres] Warning: PDF restore failed."
fi
echo "[postgres] Database ready."

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

# ─── Periodic backup (every 30 min) ─────────────────────────
(while true; do
    sleep 1800
    sudo -u postgres pg_dump -Fc -d "${POSTGRES_DB}" -f /workspace/postgres/backup.dump 2>/dev/null && \
        echo "[backup] Periodic DB backup saved." || true
    # Also backup PDFs
    if [ -d "/app/data/reports" ] && [ "$(ls -A /app/data/reports 2>/dev/null)" ]; then
        mkdir -p /workspace/reports
        cp -r /app/data/reports/* /workspace/reports/ 2>/dev/null
    fi
done) &

# ─── Node.js App ─────────────────────────────────────────────
echo "[4/4] Starting Node.js application on port ${BACKEND_PORT}..."
echo "========================================="
echo " All services running. App: http://0.0.0.0:${BACKEND_PORT}"
echo "========================================="

# Start Node.js app (wait on it so trap can catch signals)
node /app/backend-enterprise/src/server.js &
NODE_PID=$!
wait $NODE_PID
