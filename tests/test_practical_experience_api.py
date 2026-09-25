from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app, headers={"Authorization": "Bearer test-service-token"})


def _eligible_payload() -> dict:
    return {
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "completed",
                "team_members": [
                    {"user_id": 20, "assignment_state": "completed"}
                ],
                "submissions": [
                    {
                        "submission_id": 501,
                        "contributor_id": 20,
                        "status": "accepted"
                    }
                ],
                "evaluations": [
                    {
                        "submission_id": 501,
                        "status": "finalized"
                    }
                ]
            }
        ]
    }


def test_practical_experience_api_returns_available_score() -> None:
    response = client.post(
        "/api/v1/practical-experience",
        json=_eligible_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["algorithm_version"] == "practical-experience-v1"
    assert data["configuration_version"] == "practical-experience-config-v1"
    assert data["component_status"] == "available"
    assert data["eligible_projects_count"] == 1
    assert data["full_credit_project_count"] == 2
    assert data["practical_experience_score"] == 50.0
    assert data["eligible_project_ids"] == [101]


def test_practical_experience_api_returns_unavailable_when_no_project_is_eligible() -> None:
    payload = _eligible_payload()
    payload["projects"][0]["project_status"] = "in_progress"

    response = client.post(
        "/api/v1/practical-experience",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["component_status"] == "unavailable"
    assert data["eligible_projects_count"] == 0
    assert data["practical_experience_score"] is None
    assert data["eligible_project_ids"] == []
