#!/bin/bash
set -e
# Onboard 
echo "Waiting for Postgres..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; do
  sleep 1
done

echo "Ensuring database exists: $DB_NAME"
PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -h $POSTGRES_HOST -d postgres \
  -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -h $POSTGRES_HOST -d postgres \
  -c "CREATE DATABASE \"$DB_NAME\";"

echo "Running Alembic migrations..."
alembic -c /app/app/alembic.ini upgrade head

echo "Starting Scanner Service..."
uvicorn app.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}