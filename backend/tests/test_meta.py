"""Tests for API version metadata and configured CORS."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_versions_returns_active_contract_metadata():
    response = client.get("/api/v1/meta/versions")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["backend_version"] == settings.APP_VERSION
    assert body["data"]["taxonomy_version"] == settings.TAXONOMY_VERSION == "v1.2.1"
    assert body["data"]["gap_scoring_version"] == "gap-v1"
    assert body["data"]["matching"] == {
        "implemented": True,
        "version": "matching-v1",
        "weights": {
            "skill_coverage": 0.6,
            "semantic_similarity": 0.2,
            "experience": 0.1,
            "education": 0.05,
            "location_work_mode": 0.05,
        },
    }
    assert body["source_version"] == "backend-v1"
    assert body["model_version"] is None
    assert body["generated_at"]
    assert "Semantic similarity is unavailable" in body["warnings"][0]


def test_cors_allows_vite_frontend_origin():
    response = client.options(
        "/api/v1/meta/versions",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_existing_health_endpoint_remains_available():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
