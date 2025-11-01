#!/bin/bash
# Production startup script for Atlas API
# Uses Gunicorn with Uvicorn workers for optimal performance

set -e

# Change to the API directory
cd "$(dirname "$0")/.."

# Configuration
HOST="${API_HOST:-0.0.0.0}"
PORT="${API_PORT:-8000}"
WORKERS="${API_WORKERS:-8}"
WORKER_CLASS="uvicorn.workers.UvicornWorker"
WORKER_CONNECTIONS="${WORKER_CONNECTIONS:-1000}"
MAX_REQUESTS="${MAX_REQUESTS:-10000}"
MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-1000}"
TIMEOUT="${TIMEOUT:-30}"
GRACEFUL_TIMEOUT="${GRACEFUL_TIMEOUT:-30}"

echo "Starting Atlas API in production mode..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo "Worker connections: $WORKER_CONNECTIONS"

# Start Gunicorn with Uvicorn workers using Poetry
exec poetry run gunicorn atlas_api.main:app \
  --bind "$HOST:$PORT" \
  --workers "$WORKERS" \
  --worker-class "$WORKER_CLASS" \
  --worker-connections "$WORKER_CONNECTIONS" \
  --max-requests "$MAX_REQUESTS" \
  --max-requests-jitter "$MAX_REQUESTS_JITTER" \
  --timeout "$TIMEOUT" \
  --graceful-timeout "$GRACEFUL_TIMEOUT" \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --preload

