#!/bin/sh
set -eu

# This web service has no separate Celery worker.
export REPORT_EXECUTION_MODE="${REPORT_EXECUTION_MODE:-background}"

alembic upgrade head
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
