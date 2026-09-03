from pathlib import Path

from httpx import AsyncClient
from pypdf import PdfReader

from app.api.v1 import reports as reports_api
from app.services.pdf_reports import build_pdf
from tests.test_identity import register


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
