from datetime import UTC, datetime

from httpx import AsyncClient


async def register(client: AsyncClient, email: str, slug: str) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Persona de Prueba",
            "password": "Clave-Segura-2026!",
            "organization_name": f"Empresa {slug}",
            "organization_slug": slug,
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_incident_lifecycle_and_audit(client: AsyncClient) -> None:
    auth = await register(client, "admin@one.test", "empresa-uno")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    created = await client.post(
        "/api/v1/incidents",
        headers=headers,
        json={
            "title": "Correo sospechoso",
            "description": "Mensaje ficticio reportado por gerencia",
            "severity": "high",
            "occurred_at": datetime.now(UTC).isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    incident_id = created.json()["id"]
    updated = await client.patch(
        f"/api/v1/incidents/{incident_id}", headers=headers, json={"status": "resolved"}
    )
    assert updated.status_code == 200
    assert updated.json()["resolved_at"] is not None
    reopened = await client.patch(
        f"/api/v1/incidents/{incident_id}", headers=headers, json={"status": "investigating"}
    )
    assert reopened.json()["resolved_at"] is None
    audits = await client.get("/api/v1/audit-logs", headers=headers)
    assert {item["action"] for item in audits.json()} >= {"incident.create", "incident.update"}
    removed = await client.delete(f"/api/v1/incidents/{incident_id}", headers=headers)
    assert removed.status_code == 204
    assert (await client.get("/api/v1/incidents", headers=headers)).json() == []


async def test_incidents_are_tenant_isolated(client: AsyncClient) -> None:
    first = await register(client, "one@one.test", "empresa-uno")
    second = await register(client, "two@two.test", "empresa-dos")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    created = await client.post(
        "/api/v1/incidents",
        headers=first_headers,
        json={
            "title": "Incidente privado",
            "description": "Solo pertenece a empresa uno",
            "severity": "medium",
            "occurred_at": datetime.now(UTC).isoformat(),
        },
    )
    incident_id = created.json()["id"]
    assert (await client.get("/api/v1/incidents", headers=second_headers)).json() == []
    denied = await client.patch(
        f"/api/v1/incidents/{incident_id}", headers=second_headers, json={"status": "contained"}
    )
    assert denied.status_code == 404
    missing = await client.patch(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000",
        headers=first_headers,
        json={"status": "contained"},
    )
    assert missing.status_code == 404


async def test_users_alias_and_organization_update(client: AsyncClient) -> None:
    auth = await register(client, "admin@one.test", "empresa-uno")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    users = await client.get("/api/v1/users", headers=headers)
    assert users.status_code == 200
    assert users.json()[0]["email"] == "admin@one.test"
    updated = await client.patch(
        "/api/v1/organizations/current", headers=headers, json={"sector": "Servicios"}
    )
    assert updated.status_code == 200
    assert updated.json()["sector"] == "Servicios"
