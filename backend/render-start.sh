#!/bin/sh
set -eu

alembic upgrade head
celery -A app.worker.celery_app worker --loglevel=WARNING &
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
