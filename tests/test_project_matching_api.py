from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app, headers={"Authorization": "Bearer test-service-token"})


def _payload() -> dict[str, object]:
    return {
        "request_id": "project-match-api-1",
        "algorithm_version": "project-matching-v1",
        "configuration_version": "project-matching-config-v1",
        "project_version": 1,
        "learner": {
            "user_id": 20,
            "student_profile_id": 15,
            "availability": "full_time",
            "preferred_work_type": "remote",
            "interests": ["backend"],
            "target_career_role": {
                "id": 3,
                "title": "Backend Developer",
                "version": 1,
            },
            "current_skills": [
                {
                    "skill_id": 1,
                    "level": 3,
                    "required_level": 3,
                    "meets_requirement": True,
                }
            ],
        },
        "project": {
            "id": 10,
            "version": 1,
            "type": "company_sponsored",
            "domain": "backend",
            "difficulty": 3,
            "work_mode": "remote",
            "role": "Backend Developer",
            "schedule": "full_time",
            "organization_id": 2,
            "confidentiality": "public",
        },
        "required_skills": [
            {
                "skill_id": 1,
                "skill_name": "Python",
                "minimum_level": 3,
                "is_critical_entry": True,
            }
        ],
        "validation": {
            "eligibility_state": "eligible",
            "validation_state": "validated",
            "constraints": [],
            "skill_gaps": [],
            "authorization": "authorized",
        },
    }


def test_project_matching_api_returns_deterministic_recommendation() -> None:
    response = client.post("/api/v1/project-matching", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "project-match-api-1"
    assert body["algorithm_version"] == "project-matching-v1"
    assert body["configuration_version"] == "project-matching-config-v1"
    assert body["recommendation"]["project_id"] == 10
    assert body["recommendation"]["eligibility_state"] == "eligible"
    assert body["recommendation"]["matching_state"] == "scored"
    assert body["recommendation"]["score"] == 75.0


def test_project_matching_api_blocks_missing_critical_skill() -> None:
    payload = _payload()
    payload["learner"]["current_skills"] = []

    response = client.post("/api/v1/project-matching", json=payload)

    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["eligibility_state"] == "ineligible"
    assert recommendation["matching_state"] == "blocked"
    assert recommendation["score"] == 0.0
    assert "Missing critical skill: Python." in recommendation["limiting_factors"]


def test_project_matching_api_returns_structured_project_version_error() -> None:
    payload = _payload()
    payload["project_version"] = 2

    response = client.post("/api/v1/project-matching", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "PROJECT_VERSION_MISMATCH"


def test_project_matching_api_returns_structured_duplicate_skill_error() -> None:
    payload = _payload()
    payload["required_skills"] = [
        payload["required_skills"][0],
        payload["required_skills"][0],
    ]

    response = client.post("/api/v1/project-matching", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "DUPLICATE_PROJECT_SKILL_ID"


def test_project_matching_api_rejects_invalid_project_type() -> None:
    payload = _payload()
    payload["project"]["type"] = "unsupported"

    response = client.post("/api/v1/project-matching", json=payload)

    assert response.status_code == 422


def test_project_matching_api_repeated_request_is_identical() -> None:
    payload = _payload()

    first = client.post("/api/v1/project-matching", json=payload)
    second = client.post("/api/v1/project-matching", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()

def test_project_matching_api_rejects_unsupported_request_algorithm_version() -> None:
    payload = _payload()
    payload["algorithm_version"] = "project-matching-v2"

    response = client.post("/api/v1/project-matching", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSUPPORTED_ALGORITHM_VERSION"


def test_project_matching_api_rejects_unsupported_request_configuration_version() -> None:
    payload = _payload()
    payload["configuration_version"] = "project-matching-config-v2"

    response = client.post("/api/v1/project-matching", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSUPPORTED_CONFIGURATION_VERSION"
