from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_roadmap_generate_orders_prerequisites_first() -> None:
    payload = {
        "steps": [
            {
                "skill_id": "SKILL_C",
                "priority": 1.0,
                "prerequisites": ["SKILL_B"],
            },
            {
                "skill_id": "SKILL_B",
                "priority": 1.0,
                "prerequisites": ["SKILL_A"],
            },
            {
                "skill_id": "SKILL_A",
                "priority": 0.5,
                "prerequisites": [],
            },
        ]
    }

    response = client.post(
        "/api/v1/roadmaps/generate",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert [step["skill_id"] for step in data["steps"]] == [
        "SKILL_A",
        "SKILL_B",
        "SKILL_C",
    ]
    assert data["scoring_version"] == "v1"


def test_roadmap_generate_rejects_cycle() -> None:
    payload = {
        "steps": [
            {
                "skill_id": "SKILL_A",
                "priority": 1.0,
                "prerequisites": ["SKILL_B"],
            },
            {
                "skill_id": "SKILL_B",
                "priority": 1.0,
                "prerequisites": ["SKILL_A"],
            },
        ]
    }

    response = client.post(
        "/api/v1/roadmaps/generate",
        json=payload,
    )

    assert response.status_code == 422