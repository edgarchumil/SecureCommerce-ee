import pytest
from httpx import AsyncClient

from app.models.risks import RiskLevel
from app.services.risk_engine import DEFAULT_BANDS, bands_from_setting, calculate_risk
from tests.test_assets import asset_payload
from tests.test_identity import register


def test_risk_matrix_boundaries_and_validation() -> None:
    expected = {
        1: RiskLevel.LOW,
        4: RiskLevel.LOW,
        5: RiskLevel.MEDIUM,
        9: RiskLevel.MEDIUM,
        10: RiskLevel.HIGH,
        16: RiskLevel.HIGH,
        20: RiskLevel.CRITICAL,
        25: RiskLevel.CRITICAL,
    }
    for score, level in expected.items():
        pair = next((p, i) for p in range(1, 6) for i in range(1, 6) if p * i == score)
        assert calculate_risk(*pair) == (score, level)
    with pytest.raises(ValueError):
        calculate_risk(0, 5)


def test_configurable_bands_must_cover_matrix_once() -> None:
    value = {
        "bands": [
            {"level": "low", "minimum": 1, "maximum": 5},
            {"level": "medium", "minimum": 6, "maximum": 10},
            {"level": "high", "minimum": 11, "maximum": 17},
            {"level": "critical", "minimum": 18, "maximum": 25},
        ]
    }
    bands = bands_from_setting(value)
    assert calculate_risk(1, 5, bands)[1] == RiskLevel.LOW
    assert bands_from_setting(None) == DEFAULT_BANDS
    with pytest.raises(ValueError):
        bands_from_setting({"bands": []})


async def setup_risk(client: AsyncClient, email: str, slug: str):  # type: ignore[no-untyped-def]
    auth = await register(client, email, slug)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    asset = await client.post("/api/v1/assets", headers=headers, json=asset_payload("RISK-ASSET"))
    threat = await client.post(
        "/api/v1/threats",
        headers=headers,
        json={"name": "Ransomware", "description": "Cifrado malicioso", "rating": 4},
    )
    vulnerability = await client.post(
        "/api/v1/vulnerabilities",
        headers=headers,
        json={"name": "Copias no probadas", "description": "No se restauran copias", "rating": 5},
    )
    return auth, headers, asset.json(), threat.json(), vulnerability.json()


def risk_payload(asset_id: str, threat_id: str, vulnerability_id: str) -> dict[str, object]:
    return {
        "code": "RISK-001",
        "title": "Pérdida de facturación",
        "description": "Ransomware afecta la facturación",
        "asset_id": asset_id,
        "threat_id": threat_id,
        "vulnerability_id": vulnerability_id,
        "probability": 4,
        "impact": 5,
        "existing_controls": "Antivirus básico",
        "residual_probability": 3,
        "residual_impact": 4,
        "treatment_strategy": "mitigate",
        "target_date": "2026-12-31",
        "progress": 10,
        "status": "identified",
    }


async def test_risk_crud_treatment_and_filters(client: AsyncClient) -> None:
    _, headers, asset, threat, vulnerability = await setup_risk(
        client, "risk@example.com", "risk-org"
    )
    created = await client.post(
        "/api/v1/risks",
        headers=headers,
        json=risk_payload(asset["id"], threat["id"], vulnerability["id"]),
    )
    assert created.status_code == 201, created.text
    risk = created.json()
    assert risk["inherent_score"] == 20
    assert risk["inherent_level"] == "critical"
    assert risk["residual_score"] == 12
    assert risk["residual_level"] == "high"
    listing = await client.get("/api/v1/risks?level=critical&search=factura", headers=headers)
    assert listing.json()["total"] == 1
    treatment = await client.post(
        f"/api/v1/risks/{risk['id']}/treatments",
        headers=headers,
        json={
            "action": "Configurar copias inmutables",
            "target_date": "2026-11-30",
            "progress": 25,
        },
    )
    assert treatment.status_code == 201
    assert (
        len((await client.get(f"/api/v1/risks/{risk['id']}/treatments", headers=headers)).json())
        == 1
    )
    update = risk_payload(asset["id"], threat["id"], vulnerability["id"])
    update["residual_probability"] = 1
    update["residual_impact"] = 4
    updated = await client.put(f"/api/v1/risks/{risk['id']}", headers=headers, json=update)
    assert updated.json()["residual_level"] == "low"
    assert (await client.delete(f"/api/v1/risks/{risk['id']}", headers=headers)).status_code == 204
    assert (await client.get(f"/api/v1/risks/{risk['id']}", headers=headers)).status_code == 404


async def test_cross_tenant_risk_relations_are_rejected(client: AsyncClient) -> None:
    _, first_headers, first_asset, first_threat, first_vulnerability = await setup_risk(
        client, "one@risk.com", "one-risk"
    )
    _, second_headers, second_asset, _, _ = await setup_risk(client, "two@risk.com", "two-risk")
    payload = risk_payload(second_asset["id"], first_threat["id"], first_vulnerability["id"])
    assert (
        await client.post("/api/v1/risks", headers=first_headers, json=payload)
    ).status_code == 422
    own = await client.post(
        "/api/v1/risks",
        headers=first_headers,
        json=risk_payload(first_asset["id"], first_threat["id"], first_vulnerability["id"]),
    )
    assert (
        await client.get(f"/api/v1/risks/{own.json()['id']}", headers=second_headers)
    ).status_code == 404


async def test_admin_can_change_bands_and_invalid_config_is_rejected(client: AsyncClient) -> None:
    _, headers, asset, threat, vulnerability = await setup_risk(
        client, "admin@risk.com", "admin-risk"
    )
    bands = [
        {"level": "low", "minimum": 1, "maximum": 5},
        {"level": "medium", "minimum": 6, "maximum": 10},
        {"level": "high", "minimum": 11, "maximum": 17},
        {"level": "critical", "minimum": 18, "maximum": 25},
    ]
    assert (
        await client.put("/api/v1/settings/risk-bands", headers=headers, json={"bands": bands})
    ).status_code == 204
    created = await client.post(
        "/api/v1/risks",
        headers=headers,
        json=risk_payload(asset["id"], threat["id"], vulnerability["id"]),
    )
    assert created.json()["inherent_level"] == "critical"
    assert (
        await client.put("/api/v1/settings/risk-bands", headers=headers, json={"bands": []})
    ).status_code == 422
