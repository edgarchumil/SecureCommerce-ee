from contextlib import asynccontextmanager
from pathlib import Path

from app import tasks
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from tests.test_identity import register


def use_test_database(monkeypatch):
    @asynccontextmanager
    async def factory():
        async for db in app.dependency_overrides[get_db]():
            yield db

    monkeypatch.setattr(tasks, "SessionFactory", factory)


async def test_background_reports_without_worker_survive_file_loss(client, monkeypatch, tmp_path):
    use_test_database(monkeypatch)
    monkeypatch.setattr(settings, "report_execution_mode", "background")
    monkeypatch.setattr(settings, "report_storage_path", str(tmp_path))

    def no_worker(*args):
        raise AssertionError("No Celery worker is required in background mode")

    monkeypatch.setattr(tasks.generate_report, "delay", no_worker)
    auth = await register(client, "cloud@example.test", "cloud")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    for kind in ["executive", "technical"]:
        response = await client.post(
            "/api/v1/reports",
            headers=headers,
            json={
                "title": "Informe en nube",
                "scope": "Toda la empresa",
                "report_type": kind,
            },
        )
        assert response.status_code == 202
        report_id = response.json()["id"]
        status = await client.get(f"/api/v1/reports/{report_id}", headers=headers)
        assert status.json()["status"] == "completed"
        for file in Path(tmp_path).rglob("*.pdf"):
            file.unlink()
        download = await client.get(f"/api/v1/reports/{report_id}/download", headers=headers)
        assert download.status_code == 200
        assert download.content.startswith(b"%PDF-")
        assert len(download.content) == status.json()["size_bytes"]


async def test_listing_recovers_old_queue_only_for_current_tenant(client, monkeypatch, tmp_path):
    use_test_database(monkeypatch)
    monkeypatch.setattr(settings, "report_storage_path", str(tmp_path))
    monkeypatch.setattr(settings, "report_execution_mode", "celery")
    monkeypatch.setattr(tasks.generate_report, "delay", lambda _: None)
    first = await register(client, "first@example.test", "first")
    second = await register(client, "second@example.test", "second")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    ids = []
    for headers in [first_headers, second_headers]:
        result = await client.post(
            "/api/v1/reports",
            headers=headers,
            json={
                "title": "Informe pendiente",
                "scope": "Toda la empresa",
                "report_type": "executive",
            },
        )
        ids.append(result.json()["id"])
    monkeypatch.setattr(settings, "report_execution_mode", "background")
    await client.get("/api/v1/reports", headers=first_headers)
    result = await client.get(f"/api/v1/reports/{ids[0]}", headers=first_headers)
    assert result.json()["status"] == "completed"
    result = await client.get(f"/api/v1/reports/{ids[1]}", headers=second_headers)
    assert result.json()["status"] == "pending"
    assert (
        await client.get(f"/api/v1/reports/{ids[0]}/download", headers=second_headers)
    ).status_code == 404
