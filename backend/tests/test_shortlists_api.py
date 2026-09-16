from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _candidate(
    candidate_id: str,
    skill_ids: list[str],
) -> dict:
    return {
        "owner_id": candidate_id,
        "kind": "candidate",
        "experience_years": 3,
        "education_level": 0.8,
        "location": "Pune",
        "work_mode": "remote",
        "text": "Python SQL data engineering",
        "skills": [
            {
                "skill_id": skill_id,
                "proficiency": 1.0,
                "proficiency_level": "expert",
                "min_proficiency": 0.0,
                "importance": 1.0,
                "evidence": [],
            }
            for skill_id in skill_ids
        ],
    }


def test_shortlist_ranks_candidates_deterministically() -> None:
    payload = {
        "job": {
            "owner_id": "job-1",
            "kind": "job",
            "experience_years": 3,
            "education_level": 0.8,
            "location": "Pune",
            "work_mode": "remote",
            "text": "Python SQL",
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
        "candidates": [
            _candidate("candidate-weak", ["SKILL_0001"]),
            _candidate(
                "candidate-strong",
                ["SKILL_0001", "SKILL_0002"],
            ),
        ],
    }

    response = client.post(
        "/api/v1/shortlists",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        candidate["candidate_id"]
        for candidate in data["candidates"]
    ] == [
        "candidate-strong",
        "candidate-weak",
    ]

    assert data["candidates"][0]["matched_skills"] == [
        "SKILL_0001",
        "SKILL_0002",
    ]

    assert data["candidates"][0]["scoring_version"] == "v1"
    assert "skill_score" in data["candidates"][0]["explanation"]


def test_shortlist_rejects_non_candidate_profiles() -> None:
    payload = {
        "job": {
            "owner_id": "job-1",
            "kind": "job",
            "skills": [],
        },
        "candidates": [
            {
                "owner_id": "wrong-kind",
                "kind": "job",
                "skills": [],
            }
        ],
    }

    response = client.post(
        "/api/v1/shortlists",
        json=payload,
    )

    assert response.status_code == 422