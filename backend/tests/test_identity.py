from uuid import UUID

import pyotp
from httpx import AsyncClient

from app.models.identity import RoleCode
from app.security.passwords import hash_password, verify_password
from app.security.permissions import Permission, has_permission
from app.security.tokens import create_access_token, decode_access_token


async def register(client: AsyncClient, email: str, slug: str) -> dict[str, object]:
    from app.core.database import get_db
    from app.main import app
    from app.models.identity import Membership, Organization, User

    async for db in app.dependency_overrides[get_db]():
        user = User(email=email, full_name="Persona de Prueba",
                    password_hash=hash_password("Clave-Segura-2026!"))
        organization = Organization(name=f"Empresa {slug}", slug=slug)
        db.add_all([user, organization])
        await db.flush()
        db.add(Membership(user_id=user.id, organization_id=organization.id,
                          role_code=RoleCode.ORG_ADMIN))
        await db.commit()
    response = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "Clave-Segura-2026!",
    })
    assert response.status_code == 200, response.text
    return response.json()


async def test_register_login_and_current_organization(client: AsyncClient) -> None:
    registered = await register(client, "admin@example.test", "empresa-uno")
    payload = decode_access_token(str(registered["access_token"]))
    assert payload["role"] == "org_admin"
    assert payload["org"] is not None

    current = await client.get(
        "/api/v1/organizations/current",
        headers={"Authorization": f"Bearer {registered['access_token']}"},
    )
    assert current.status_code == 200
    assert current.json()["slug"] == "empresa-uno"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.test", "password": "Clave-Segura-2026!"},
    )
    assert login.status_code == 200
    assert login.json()["expires_in"] == 900
    assert "refresh_token" in login.cookies


async def test_invalid_login_does_not_enumerate_accounts(client: AsyncClient) -> None:
    await register(client, "admin@example.test", "empresa-uno")
    wrong_password = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.test", "password": "incorrecta"},
    )
    missing_user = await client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@example.test", "password": "incorrecta"},
    )
    assert wrong_password.status_code == missing_user.status_code == 401
    assert wrong_password.json() == missing_user.json()


async def test_refresh_is_rotated_and_reuse_is_rejected(client: AsyncClient) -> None:
    await register(client, "admin@example.test", "empresa-uno")
    first_refresh = client.cookies.get("refresh_token")
    assert first_refresh

    rotated = await client.post("/api/v1/auth/refresh", json={})
    assert rotated.status_code == 200
    assert client.cookies.get("refresh_token") != first_refresh

    client.cookies.clear()
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reused.status_code == 401


async def test_cross_tenant_access_is_rejected(client: AsyncClient) -> None:
    first = await register(client, "uno@example.test", "empresa-uno")
    second = await register(client, "dos@example.test", "empresa-dos")
    second_payload = decode_access_token(str(second["access_token"]))

    forged = dict(decode_access_token(str(first["access_token"])))
    forged_token = create_access_token(
        UUID(forged["sub"]), UUID(second_payload["org"]), forged["role"]
    )
    response = await client.get(
        "/api/v1/organizations/current",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert response.status_code == 401


def test_password_hash_and_permission_matrix() -> None:
    hashed = hash_password("Clave-Segura-2026!")
    assert hashed.startswith("$argon2id$")
    assert verify_password("Clave-Segura-2026!", hashed)
    assert not verify_password("incorrecta", hashed)
    assert has_permission(RoleCode.ORG_ADMIN, Permission.MEMBERSHIP_MANAGE)
    assert not has_permission(RoleCode.VIEWER, Permission.MEMBERSHIP_MANAGE)


async def test_membership_management_is_tenant_scoped(client: AsyncClient) -> None:
    admin = await register(client, "admin@one.com", "empresa-uno")
    await register(client, "viewer@two.com", "empresa-dos")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    invitation = await client.post(
        "/api/v1/memberships/invite",
        headers=admin_headers,
        json={
            "email": "viewer@two.com",
            "full_name": "Persona Consulta",
            "role_code": "viewer",
        },
    )
    assert invitation.status_code == 201, invitation.text
    membership_id = invitation.json()["id"]
    members = await client.get("/api/v1/memberships", headers=admin_headers)
    assert {item["email"] for item in members.json()} == {"admin@one.com", "viewer@two.com"}

    updated = await client.patch(
        f"/api/v1/memberships/{membership_id}/role",
        headers=admin_headers,
        json={"role_code": "analyst"},
    )
    assert updated.status_code == 200
    assert updated.json()["role_code"] == "analyst"
    audits = await client.get("/api/v1/audit-logs", headers=admin_headers)
    assert audits.status_code == 200
    assert "membership.role.update" in {item["action"] for item in audits.json()}


async def test_viewer_is_denied_membership_management(client: AsyncClient) -> None:
    admin = await register(client, "admin@one.com", "empresa-uno")
    viewer = await register(client, "viewer@two.com", "empresa-dos")
    org_id = decode_access_token(str(admin["access_token"]))["org"]
    await client.post(
        "/api/v1/memberships/invite",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"email": "viewer@two.com", "full_name": "Consulta", "role_code": "viewer"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "viewer@two.com",
            "password": "Clave-Segura-2026!",
            "organization_id": org_id,
        },
    )
    denied = await client.post(
        "/api/v1/memberships/invite",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"email": "new@example.com", "full_name": "Nueva Persona", "role_code": "viewer"},
    )
    assert viewer["access_token"]
    assert denied.status_code == 403


async def test_mfa_and_session_revocation(client: AsyncClient) -> None:
    registered = await register(client, "admin@example.com", "empresa-uno")
    headers = {"Authorization": f"Bearer {registered['access_token']}"}
    setup = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200
    code = pyotp.TOTP(setup.json()["secret"]).now()
    verified = await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": code})
    assert verified.status_code == 204

    requires_mfa = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Clave-Segura-2026!"},
    )
    assert requires_mfa.json()["mfa_required"] is True
    logged_in = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "Clave-Segura-2026!",
            "mfa_code": pyotp.TOTP(setup.json()["secret"]).now(),
        },
    )
    assert logged_in.status_code == 200
    sessions = await client.get(
        "/api/v1/sessions",
        headers={"Authorization": f"Bearer {logged_in.json()['access_token']}"},
    )
    active = next(item for item in sessions.json() if item["revoked_at"] is None)
    revoked = await client.delete(
        f"/api/v1/sessions/{active['id']}",
        headers={"Authorization": f"Bearer {logged_in.json()['access_token']}"},
    )
    assert revoked.status_code == 204


async def test_multi_organization_login_requires_selection_and_refresh_keeps_it(
    client: AsyncClient,
) -> None:
    first = await register(client, "admin@one.com", "empresa-uno")
    await register(client, "consultor@two.com", "empresa-dos")
    org_one = decode_access_token(str(first["access_token"]))["org"]
    invited = await client.post(
        "/api/v1/memberships/invite",
        headers={"Authorization": f"Bearer {first['access_token']}"},
        json={"email": "consultor@two.com", "full_name": "Consultor", "role_code": "analyst"},
    )
    assert invited.status_code == 201

    selection = await client.post(
        "/api/v1/auth/login",
        json={"email": "consultor@two.com", "password": "Clave-Segura-2026!"},
    )
    assert selection.status_code == 200
    assert selection.json()["organization_selection_required"] is True
    assert len(selection.json()["organizations"]) == 2

    selected = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "consultor@two.com",
            "password": "Clave-Segura-2026!",
            "organization_id": org_one,
        },
    )
    assert decode_access_token(selected.json()["access_token"])["org"] == org_one
    refreshed = await client.post("/api/v1/auth/refresh", json={})
    assert decode_access_token(refreshed.json()["access_token"])["org"] == org_one


async def test_password_recovery_is_generic_and_single_use(client: AsyncClient) -> None:
    await register(client, "admin@example.com", "empresa-uno")
    missing = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "missing@example.com"}
    )
    requested = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "admin@example.com"}
    )
    assert missing.json()["message"] == requested.json()["message"]
    token = requested.json()["development_token"]
    assert token

    confirmed = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "Nueva-Clave-2026!"},
    )
    assert confirmed.status_code == 204
    reused = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "Otra-Clave-2026!"},
    )
    assert reused.status_code == 400
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Nueva-Clave-2026!"},
    )
    assert login.status_code == 200
