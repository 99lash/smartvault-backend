#!/bin/sh
set -e

echo "=== SmartVault starting ==="
echo "PORT=${PORT:-8000}"
echo "DATABASE_URL prefix: $(echo $DATABASE_URL | cut -c1-30)..."

echo "=== Running migrations ==="
alembic upgrade head
echo "=== Migrations complete ==="

echo "=== Starting uvicorn on port ${PORT:-8000} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
