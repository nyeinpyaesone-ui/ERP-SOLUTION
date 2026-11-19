#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-erp_dev}"
DB_USER="${DB_USER:-devuser}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-90}"

for command_name in pg_isready redis-cli; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required command not found: $command_name" >&2
    exit 1
  fi
done

deadline=$((SECONDS + WAIT_TIMEOUT_SECONDS))
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "PostgreSQL did not become ready within ${WAIT_TIMEOUT_SECONDS}s" >&2
    exit 1
  fi
  sleep 2
done

until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -qx PONG; do
  if (( SECONDS >= deadline )); then
    echo "Redis did not become ready within ${WAIT_TIMEOUT_SECONDS}s" >&2
    exit 1
  fi
  sleep 2
done

echo "PostgreSQL and Redis are ready."
