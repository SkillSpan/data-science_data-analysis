from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app, headers={"Authorization": "Bearer test-service-token"})


def _completed_payload() -> dict:
    return {
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "completed",
            "normalized_skills": [
                {"skill_id": 1, "confidence": 100.0},
                {"skill_id": 2, "confidence": 80.0},
                {"skill_id": 3, "confidence": 60.0}
            ]
        }
    }


def test_assessment_reliability_api_returns_available_score() -> None:
    response = client.post(
        "/api/v1/assessment-reliability",
        json=_completed_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["algorithm_version"] == "assessment-reliability-v1"
    assert data["configuration_version"] == "assessment-reliability-config-v1"
    assert data["component_status"] == "available"
    assert data["baseline_assessment_id"] == 101
    assert data["assessment_version"] == "v1.0"
    assert data["assessed_skills_count"] == 3
    assert data["assessment_reliability_score"] == 80.0


def test_assessment_reliability_api_returns_unavailable_without_assessment() -> None:
    response = client.post(
        "/api/v1/assessment-reliability",
        json={
            "student_profile_id": 10,
            "assessment": None
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["component_status"] == "unavailable"
    assert data["baseline_assessment_id"] is None
    assert data["assessment_version"] is None
    assert data["assessed_skills_count"] == 0
    assert data["assessment_reliability_score"] is None


def test_assessment_reliability_api_rejects_confidence_above_one_hundred() -> None:
    payload = _completed_payload()
    payload["assessment"]["normalized_skills"][0]["confidence"] = 101.0

    response = client.post(
        "/api/v1/assessment-reliability",
        json=payload,
    )

    assert response.status_code == 422


def test_assessment_reliability_api_rejects_duplicate_skill_ids() -> None:
    payload = _completed_payload()
    payload["assessment"]["normalized_skills"][1]["skill_id"] = 1

    response = client.post(
        "/api/v1/assessment-reliability",
        json=payload,
    )

    assert response.status_code == 422
    assert "duplicate skill_id" in response.text
