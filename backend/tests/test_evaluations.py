from httpx import AsyncClient

from app.services.evaluation_scoring import ScoredAnswer, calculate_scores
from tests.test_identity import register


async def auth_and_framework(client: AsyncClient, email: str, slug: str):  # type: ignore[no-untyped-def]
    auth = await register(client, email, slug)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    frameworks = await client.get("/api/v1/frameworks", headers=headers)
    assert frameworks.status_code == 200
    return auth, headers, frameworks.json()[0]


async def create_evaluation(client: AsyncClient, headers: dict[str, str], framework_id: str):  # type: ignore[no-untyped-def]
    response = await client.post(
        "/api/v1/evaluations",
        headers=headers,
        json={
            "framework_id": framework_id,
            "code": "EVAL-2026",
            "name": "Evaluación inicial",
            "scope": "Toda la organización ficticia",
            "target_maturity": 3,
            "asset_ids": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_weighted_scoring_includes_unanswered_questions() -> None:
    rows = [
        ScoredAnswer("GV", "Govern", "GV.OC", "Contexto", 2, 4),
        ScoredAnswer("GV", "Govern", "GV.OC", "Contexto", 1, None),
    ]
    result = calculate_scores(rows, 3)
    assert result["current_profile"] == 66.67
    assert result["target_profile"] == 75.0
    assert result["gap"] == 8.33
    assert result["answered"] == 1
    assert result["total"] == 2


async def test_nist_catalog_has_six_functions(client: AsyncClient) -> None:
    _, headers, framework = await auth_and_framework(client, "nist@example.com", "nist-org")
    response = await client.get(f"/api/v1/frameworks/{framework['id']}/questions", headers=headers)
    assert response.status_code == 200
    assert {item["function_code"] for item in response.json()} == {
        "GV",
        "ID",
        "PR",
        "DE",
        "RS",
        "RC",
    }


async def test_evaluation_answers_results_status_and_version(client: AsyncClient) -> None:
    _, headers, framework = await auth_and_framework(client, "eval@example.com", "eval-org")
    evaluation = await create_evaluation(client, headers, framework["id"])
    questions = (
        await client.get(f"/api/v1/frameworks/{framework['id']}/questions", headers=headers)
    ).json()
    for question in questions:
        saved = await client.put(
            f"/api/v1/evaluations/{evaluation['id']}/answers/{question['id']}",
            headers=headers,
            json={"maturity": 2, "comment": "Respuesta ficticia"},
        )
        assert saved.status_code == 200
    result = await client.get(f"/api/v1/evaluations/{evaluation['id']}/results", headers=headers)
    assert result.status_code == 200
    assert result.json()["current_profile"] == 50.0
    assert result.json()["gap"] == 25.0
    assert len(result.json()["by_function"]) == 6

    review = await client.patch(
        f"/api/v1/evaluations/{evaluation['id']}/status",
        headers=headers,
        json={"status": "in_review"},
    )
    assert review.status_code == 200
    approved = await client.patch(
        f"/api/v1/evaluations/{evaluation['id']}/status",
        headers=headers,
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    locked = await client.put(
        f"/api/v1/evaluations/{evaluation['id']}/answers/{questions[0]['id']}",
        headers=headers,
        json={"maturity": 4},
    )
    assert locked.status_code == 409
    version = await client.post(f"/api/v1/evaluations/{evaluation['id']}/versions", headers=headers)
    assert version.status_code == 201
    assert version.json()["version"] == 2


async def test_evaluation_and_evidence_are_tenant_scoped(client: AsyncClient) -> None:
    _, first_headers, framework = await auth_and_framework(client, "one@eval.com", "one-eval")
    _, second_headers, _ = await auth_and_framework(client, "two@eval.com", "two-eval")
    evaluation = await create_evaluation(client, first_headers, framework["id"])
    assert (
        await client.get(f"/api/v1/evaluations/{evaluation['id']}", headers=second_headers)
    ).status_code == 404
    questions = (
        await client.get(f"/api/v1/frameworks/{framework['id']}/questions", headers=first_headers)
    ).json()
    question_id = questions[0]["id"]
    await client.put(
        f"/api/v1/evaluations/{evaluation['id']}/answers/{question_id}",
        headers=first_headers,
        json={"maturity": 1},
    )
    evidence = await client.post(
        f"/api/v1/evaluations/{evaluation['id']}/answers/{question_id}/evidence",
        headers=first_headers,
        json={
            "file_name": "politica.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024,
            "sha256": "a" * 64,
        },
    )
    assert evidence.status_code == 201
    cross = await client.post(
        f"/api/v1/evaluations/{evaluation['id']}/answers/{question_id}/evidence",
        headers=second_headers,
        json={
            "file_name": "ataque.pdf",
            "content_type": "application/pdf",
            "size_bytes": 10,
            "sha256": "b" * 64,
        },
    )
    assert cross.status_code == 404
