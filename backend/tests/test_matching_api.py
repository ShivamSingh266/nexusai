from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_matching_endpoint_returns_explainable_match() -> None:
    payload = {
        "candidate": {
            "owner_id": "candidate-1",
            "kind": "candidate",
            "experience_years": 4,
            "education_level": 0.8,
            "location": "Pune",
            "work_mode": "remote",
            "text": "Python SQL data engineering",
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
            "experience_years": 3,
            "education_level": 0.8,
            "location": "Pune",
            "work_mode": "remote",
            "text": "Python SQL data engineering",
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
    }

    response = client.post(
        "/api/v1/matching/profiles",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["matched_skills"] == ["SKILL_0001"]
    assert data["missing_skills"] == ["SKILL_0002"]
    assert "skill_score" in data["explanation"]
    assert "semantic_score" in data["explanation"]
    assert "experience_score" in data["explanation"]
    assert "education_score" in data["explanation"]
    assert "location_mode_score" in data["explanation"]
    assert "weights" in data["explanation"]
    assert data["scoring_version"] == "v1"