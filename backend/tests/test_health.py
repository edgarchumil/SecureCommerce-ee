from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import health
from app.main import app
from app.worker import ping


def test_liveness_returns_ok_and_correlation_id() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live", headers={"X-Correlation-ID": "test-id"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"] == "test-id"


def test_openapi_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "SecureCommerce Advisor"


def test_readiness_returns_ok_when_dependencies_are_ready(monkeypatch: object) -> None:
    monkeypatch.setattr(health, "database_is_ready", AsyncMock(return_value=True))  # type: ignore[attr-defined]
    monkeypatch.setattr(health, "redis_is_ready", AsyncMock(return_value=True))  # type: ignore[attr-defined]
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_is_degraded_without_dependencies(monkeypatch: object) -> None:
    monkeypatch.setattr(health, "database_is_ready", AsyncMock(return_value=False))  # type: ignore[attr-defined]
    monkeypatch.setattr(health, "redis_is_ready", AsyncMock(return_value=False))  # type: ignore[attr-defined]
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["services"] == {
        "database": {"status": "error"},
        "redis": {"status": "error"},
    }


def test_worker_ping() -> None:
    assert ping.run() == "pong"


class FakeConnection:
    async def __aenter__(self):  # type: ignore[no-untyped-def]
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> None:
        assert statement is not None


class FakeEngine:
    def connect(self) -> FakeConnection:
        return FakeConnection()


@pytest.mark.asyncio
async def test_dependency_checks_cover_success_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "engine", FakeEngine())
    monkeypatch.setattr(health.redis_client, "ping", AsyncMock(return_value=True))
    assert await health.database_is_ready()
    assert await health.redis_is_ready()

    class BrokenEngine:
        def connect(self) -> None:
            raise RuntimeError("unavailable")

    monkeypatch.setattr(health, "engine", BrokenEngine())
    monkeypatch.setattr(health.redis_client, "ping", AsyncMock(side_effect=RuntimeError))
    assert not await health.database_is_ready()
    assert not await health.redis_is_ready()
