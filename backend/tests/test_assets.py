from httpx import AsyncClient

from app.security.tokens import decode_access_token
from tests.test_identity import register


def asset_payload(code: str, name: str = "Servidor de facturación") -> dict[str, object]:
    return {
        "name": name,
        "internal_code": code,
        "asset_type": "server",
        "description": "Activo ficticio para pruebas",
        "owner": "Gerencia",
        "technical_owner": "Soporte",
        "location": "Ciudad de Guatemala",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "manufacturer": "Fabricante demo",
        "model": "Modelo demo",
        "exposure_level": "internal",
        "status": "active",
        "acquisition_date": "2026-01-15",
        "confidentiality_criticality": 4,
        "integrity_criticality": 5,
        "availability_criticality": 4,
        "tags": ["Facturación", "Crítico", "facturación"],
        "notes": "Datos ficticios",
        "dependency_ids": [],
    }


async def test_asset_crud_filters_and_soft_delete(client: AsyncClient) -> None:
    auth = await register(client, "admin@assets.com", "assets-org")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    created = await client.post("/api/v1/assets", headers=headers, json=asset_payload("SRV-001"))
    assert created.status_code == 201, created.text
    asset = created.json()
    assert asset["overall_criticality"] == 5
    assert asset["tags"] == ["facturación", "crítico"]

    listing = await client.get("/api/v1/assets?search=factura&criticality=5", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["pages"] == 1

    updated_payload = asset_payload("SRV-001", "Servidor actualizado")
    updated_payload["status"] = "maintenance"
    updated = await client.put(
        f"/api/v1/assets/{asset['id']}", headers=headers, json=updated_payload
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "maintenance"

    deleted = await client.delete(f"/api/v1/assets/{asset['id']}", headers=headers)
    assert deleted.status_code == 204
    missing = await client.get(f"/api/v1/assets/{asset['id']}", headers=headers)
    assert missing.status_code == 404


async def test_asset_code_is_unique_per_organization(client: AsyncClient) -> None:
    first = await register(client, "one@assets.com", "one-assets")
    second = await register(client, "two@assets.com", "two-assets")
    for auth in (first, second):
        created = await client.post(
            "/api/v1/assets",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
            json=asset_payload("SAME-001"),
        )
        assert created.status_code == 201
    duplicate = await client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {first['access_token']}"},
        json=asset_payload("SAME-001"),
    )
    assert duplicate.status_code == 409


async def test_cross_tenant_asset_access_and_org_override_are_blocked(
    client: AsyncClient,
) -> None:
    first = await register(client, "one@assets.com", "one-assets")
    second = await register(client, "two@assets.com", "two-assets")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    created = await client.post(
        "/api/v1/assets", headers=first_headers, json=asset_payload("PRIVATE-001")
    )
    asset_id = created.json()["id"]
    assert (
        await client.get(f"/api/v1/assets/{asset_id}", headers=second_headers)
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/assets/{asset_id}", headers=second_headers)
    ).status_code == 404

    malicious = asset_payload("FORGED-001")
    malicious["organization_id"] = decode_access_token(str(second["access_token"]))["org"]
    rejected = await client.post("/api/v1/assets", headers=first_headers, json=malicious)
    assert rejected.status_code == 422


async def test_dependencies_must_belong_to_same_organization(client: AsyncClient) -> None:
    first = await register(client, "one@assets.com", "one-assets")
    second = await register(client, "two@assets.com", "two-assets")
    second_asset = await client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {second['access_token']}"},
        json=asset_payload("OTHER-001"),
    )
    payload = asset_payload("OWN-001")
    payload["dependency_ids"] = [second_asset.json()["id"]]
    rejected = await client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {first['access_token']}"},
        json=payload,
    )
    assert rejected.status_code == 422


async def test_viewer_can_read_but_cannot_create_assets(client: AsyncClient) -> None:
    admin = await register(client, "admin@assets.com", "assets-org")
    viewer = await register(client, "viewer@assets.com", "viewer-org")
    org_id = decode_access_token(str(admin["access_token"]))["org"]
    await client.post(
        "/api/v1/memberships/invite",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"email": "viewer@assets.com", "full_name": "Consulta", "role_code": "viewer"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "viewer@assets.com",
            "password": "Clave-Segura-2026!",
            "organization_id": org_id,
        },
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert viewer["access_token"]
    assert (await client.get("/api/v1/assets", headers=headers)).status_code == 200
    assert (
        await client.post("/api/v1/assets", headers=headers, json=asset_payload("DENIED-001"))
    ).status_code == 403
