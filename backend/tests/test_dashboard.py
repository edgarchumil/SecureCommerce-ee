from httpx import AsyncClient

from tests.test_assets import asset_payload
from tests.test_identity import register
from tests.test_risks import risk_payload


async def test_dashboard_kpis_filters_and_tenant_isolation(client: AsyncClient) -> None:
    first = await register(client, "dashboard@example.com", "dashboard-org")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    asset = await client.post(
        "/api/v1/assets", headers=first_headers, json=asset_payload("DASH-ASSET")
    )
    threat = await client.post(
        "/api/v1/threats",
        headers=first_headers,
        json={"name": "Interrupción", "description": "Amenaza operativa", "rating": 4},
    )
    vulnerability = await client.post(
        "/api/v1/vulnerabilities",
        headers=first_headers,
        json={"name": "Redundancia", "description": "Redundancia insuficiente", "rating": 5},
    )
    created = await client.post(
        "/api/v1/risks",
        headers=first_headers,
        json=risk_payload(asset.json()["id"], threat.json()["id"], vulnerability.json()["id"]),
    )
    assert created.status_code == 201

    response = await client.get("/api/v1/dashboard?asset_type=server", headers=first_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    metrics = {item["key"]: item["value"] for item in data["kpis"]}
    assert metrics["assets"] == 1
    assert metrics["risks"] == 1
    assert metrics["priority_risks"] == 1
    assert data["risks_by_level"] == [{"key": "critical", "label": "Critical", "value": 1.0}]
    assert len(data["risks_over_time"]) == 1

    second = await register(client, "other-dashboard@example.com", "other-dashboard")
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    other = await client.get("/api/v1/dashboard", headers=second_headers)
    assert {item["key"]: item["value"] for item in other.json()["kpis"]}["risks"] == 0


async def test_dashboard_rejects_inverted_date_range(client: AsyncClient) -> None:
    auth = await register(client, "dates@example.com", "dates-dashboard")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    response = await client.get(
        "/api/v1/dashboard?date_from=2026-12-31&date_to=2026-01-01", headers=headers
    )
    assert response.status_code == 422
