FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DEFAULT_TIMEOUT=300 PIP_RETRIES=10
WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml ./
COPY app/__init__.py ./app/__init__.py
RUN pip install --no-cache-dir .
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY render-start.sh ./render-start.sh
RUN chmod +x ./render-start.sh
RUN mkdir -p /data/reports && chown -R app:app /data

FROM base AS test
COPY tests ./tests
RUN pip install --no-cache-dir ".[dev]"
CMD ["pytest", "--cov=app", "--cov-report=term-missing"]

FROM base AS runtime
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
