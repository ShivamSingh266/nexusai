from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_gap_analysis_endpoint_returns_prioritized_gaps() -> None:
    payload = {
        "candidate": {
            "owner_id": "candidate-1",
            "kind": "candidate",
            "skills": [
                {
                    "skill_id": "SKILL_0001",
                    "proficiency": 1.0,
                    "proficiency_level": "expert",
                    "min_proficiency": 0.0,
                    "importance": 1.0,
                    "evidence": [],
                }
            ],
        },
        "target": {
            "owner_id": "job-1",
            "kind": "job",
            "skills": [
                {
                    "skill_id": "SKILL_0001",
                    "proficiency": 0.5,
                    "proficiency_level": "intermediate",
                    "min_proficiency": 0.5,
                    "importance": 1.0,
                    "evidence": [],
                },
                {
                    "skill_id": "SKILL_0002",
                    "proficiency": 0.5,
                    "proficiency_level": "intermediate",
                    "min_proficiency": 0.5,
                    "importance": 1.0,
                    "evidence": [],
                },
            ],
        },
        "demand_signals": {
            "SKILL_0002": {
                "demand": 2.0,
                "trend_multiplier": 1.5,
            }
        },
    }

    response = client.post(
        "/api/v1/gaps/analyze",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["gaps"]) == 1
    assert data["gaps"][0]["skill_id"] == "SKILL_0002"
    assert data["gaps"][0]["severity"] == 1.0
    assert data["gaps"][0]["priority"] == 3.0
    assert data["gaps"][0]["explanation"]