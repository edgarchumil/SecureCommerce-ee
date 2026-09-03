from datetime import timedelta
from uuid import uuid4

import jwt
from httpx import AsyncClient

from app.core.config import settings
from app.models.base import utc_now
from app.security.tokens import ALGORITHM


async def test_expired_and_malformed_tokens_are_rejected(client: AsyncClient) -> None:
    expired = jwt.encode(
        {
            "sub": str(uuid4()),
            "org": None,
            "role": None,
            "type": "access",
            "iat": utc_now() - timedelta(hours=2),
            "exp": utc_now() - timedelta(hours=1),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    for token in (expired, "not-a-jwt"):
        response = await client.get(
            "/api/v1/organizations/current",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Sesión inválida o expirada"


async def test_correlation_id_is_preserved_only_when_safe(client: AsyncClient) -> None:
    safe = await client.get("/api/v1/health/live", headers={"X-Correlation-ID": "trace-123"})
    assert safe.headers["X-Correlation-ID"] == "trace-123"

    unsafe = await client.get("/api/v1/health/live", headers={"X-Correlation-ID": "x" * 100})
    assert unsafe.headers["X-Correlation-ID"] != "x" * 100
    assert len(unsafe.headers["X-Correlation-ID"]) == 36


async def test_security_headers_are_present_through_proxy_contract(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"]
