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
        "report_id": "demo-2026",
        "prepared_by": "Analista Demo",
        "company": {
            "slug": "empresa-demo",
            "sector": "Comercio",
            "size": "MIPYME",
            "country": "GT",
            "is_active": True,
        },
        "asset_count": 7,
        "risk_count": 2,
        "answered_controls": 12,
        "evidence_count": 4,
        "maturity_percent": 50.0,
        "metrics": [
            {"label": "Activos registrados", "value": 7},
            {"label": "Riesgos identificados", "value": 2},
            {"label": "Madurez NIST CSF 2.0", "value": "50.0%"},
            {"label": "Evidencias", "value": 4},
        ],
        "risk_distribution": {"critical": 1, "high": 1, "medium": 0, "low": 0},
        "maturity_functions": [{"code": "GV", "name": "Gobernar", "percent": 50.0, "answers": 12}],
        "risks": [
            {
                "code": "R-01",
                "title": "Interrupción",
                "level": "alto",
                "score": 15,
                "strategy": "mitigar",
                "residual_score": 8,
                "status": "in_treatment",
                "progress": 35,
            }
        ],
        "assets": [
            {
                "code": "SRV-01",
                "name": "Servidor",
                "type": "server",
                "criticality": 5,
                "owner": "TI",
                "exposure": "internal",
            }
        ],
        "recommendations": [
            {
                "action": "Aplicar MFA",
                "responsible": "TI",
                "target_date": "2026-09-30",
                "progress": 35,
            }
        ],
    }


def test_executive_and_technical_pdfs_are_valid(tmp_path: Path) -> None:
    for report_type in ("executive", "technical"):
        path = tmp_path / f"{report_type}.pdf"
        build_pdf(path, report_type, report_data())
        reader = PdfReader(path)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        assert len(reader.pages) >= 2
        assert "SECURECOMMERCE ADVISOR" in text
        assert "Riesgos prioritarios" in text
        assert "Perfil de la empresa" in text
        assert "Trazabilidad y alcance" in text
        if report_type == "technical":
            assert "Anexo técnico" in text


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
