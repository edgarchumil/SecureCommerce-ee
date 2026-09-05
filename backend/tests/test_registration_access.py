import pytest
from sqlalchemy import select

from app.core.database import get_db
from app.main import app
from app.models.identity import Membership, RoleCode
from tests.test_identity import register


@pytest.mark.parametrize(
    "role", [None, RoleCode.VIEWER, RoleCode.ANALYST, RoleCode.ORG_ADMIN, RoleCode.SUPERADMIN]
)
async def test_registration_requires_admin_and_preserves_session(client, role):
    headers = {}
    if role is not None:
        await register(client, "creator@example.test", "creator")
        async for db in app.dependency_overrides[get_db]():
            membership = await db.scalar(select(Membership))
            membership.role_code = role
            await db.commit()
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "creator@example.test",
                "password": "Clave-Segura-2026!",
            },
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    cookie = client.cookies.get("refresh_token")
    response = await client.post(
        "/api/v1/auth/register",
        headers=headers,
        json={
            "email": "new@example.test",
            "full_name": "Nueva Administradora",
            "password": "Clave-Segura-2026!",
            "organization_name": "Nueva empresa",
            "organization_slug": "nueva-empresa",
        },
    )
    expected = (
        401 if role is None else 201 if role in (RoleCode.ORG_ADMIN, RoleCode.SUPERADMIN) else 403
    )
    assert response.status_code == expected, response.text
    assert client.cookies.get("refresh_token") == cookie
    if expected == 201:
        assert "id" in response.json()
        profile = await client.get("/api/v1/auth/me", headers=headers)
        assert profile.json()["email"] == "creator@example.test"
