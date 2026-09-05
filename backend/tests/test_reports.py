from pathlib import Path
from uuid import UUID, uuid4

from httpx import AsyncClient
from pypdf import PdfReader

from app.api.v1 import reports as reports_api
from app.services.pdf_reports import build_pdf
from tests.test_identity import register


async def test_report_counts_all_risks_and_matches_evaluation(client):
    from app.core.database import get_db
    from app.main import app
    from app.models.reports import Report
    from app.security.tokens import decode_access_token
    from app.services.report_data import collect_report_data
    from tests.test_evaluations import create_evaluation
    from tests.test_risks import risk_payload, setup_risk

    auth, headers, asset, threat, vulnerability = await setup_risk(
        client,
        "report-data@example.test",
        "report-data",
    )
    for index in range(12):
        payload = risk_payload(asset["id"], threat["id"], vulnerability["id"])
        payload["code"] = f"R-{index:02d}"
        result = await client.post("/api/v1/risks", headers=headers, json=payload)
        assert result.status_code == 201
    framework = (await client.get("/api/v1/frameworks", headers=headers)).json()[0]
    evaluation = await create_evaluation(client, headers, framework["id"])
    questions = (
        await client.get(
            f"/api/v1/frameworks/{framework['id']}/questions",
            headers=headers,
        )
    ).json()
    await client.put(
        f"/api/v1/evaluations/{evaluation['id']}/answers/{questions[0]['id']}",
        headers=headers,
        json={"maturity": 4},
    )
    expected = (
        await client.get(
            f"/api/v1/evaluations/{evaluation['id']}/results",
            headers=headers,
        )
    ).json()
    # Another tenant must never contribute records or scores.
    await setup_risk(client, "other-data@example.test", "other-data")
    claims = decode_access_token(auth["access_token"])
    report = Report(
        id=uuid4(),
        organization_id=UUID(claims["org"]),
        created_by=UUID(claims["sub"]),
        title="Datos reales",
        scope="Todo",
        report_type="executive",
    )
    async for db in app.dependency_overrides[get_db]():
        data = await collect_report_data(db, report)
    assert data["metrics"][1]["value"] == 12
    assert len(data["risks"]) == 12
    assert len(data["assets"]) == 1
    assert data["scores"]["current_profile"] == expected["current_profile"]
    assert data["scores"]["answered"] == 1
    assert data["scores"]["current_profile"] < 100


def test_pdf_escapes_text_and_handles_long_tables(tmp_path):
    data = report_data()
    data["title"] = "Informe <TI> & operaciones"
    data["scope"] = "Operaciones y controles. " * 80
    data["assets"] = [
        dict(data["assets"][0], name="Sistema <interno> & respaldo " * 8, code=f"ASSET-{i}")
        for i in range(45)
    ]
    path = tmp_path / "long.pdf"
    build_pdf(path, "technical", data)
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "Informe <TI> & operaciones" in text
    assert "ASSET-44" in text
    assert "No registrado" in text


def report_data() -> dict[str, object]:
    return {
        "title": "Informe de seguridad de demostración",
        "organization": "Empresa Demo, S.A.",
        "scope": "Servicios tecnológicos críticos",
        "summary": "La organización mantiene controles iniciales y debe priorizar riesgos altos.",
        "metrics": [{"label": "Activos", "value": 7}, {"label": "Riesgos", "value": 2}],
        "risks": [
            {
                "code": "R-01",
                "title": "Interrupción",
                "level": "alto",
                "score": 15,
                "strategy": "mitigar",
            }
        ],
        "assets": [{"code": "SRV-01", "name": "Servidor", "type": "server", "criticality": 5}],
    }


def test_executive_and_technical_pdfs_are_valid(tmp_path: Path) -> None:
    for report_type in ("executive", "technical"):
        path = tmp_path / f"{report_type}.pdf"
        build_pdf(path, report_type, report_data())
        reader = PdfReader(path)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        assert len(reader.pages) >= 2
        assert "SECURECOMMERCE ADVISOR" in text
        assert "Principales riesgos" in text
        if report_type == "technical":
            assert "Inventario incluido" in text


async def test_report_job_and_cross_tenant_isolation(client: AsyncClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(reports_api.generate_report, "delay", lambda _: None)
    first = await register(client, "reports@example.com", "reports-org")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    created = await client.post(
        "/api/v1/reports",
        headers=first_headers,
        json={"report_type": "executive", "title": "Informe ejecutivo", "scope": "Toda la empresa"},
    )
    assert created.status_code == 202, created.text
    assert created.json()["status"] == "pending"
    assert len((await client.get("/api/v1/reports", headers=first_headers)).json()) == 1

    second = await register(client, "other-reports@example.com", "other-reports")
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    report_id = created.json()["id"]
    assert (
        await client.get(f"/api/v1/reports/{report_id}", headers=second_headers)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/reports/{report_id}/download", headers=second_headers)
    ).status_code == 404
