from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _complete_payload() -> dict:
    return {
        "student_profile_id": 123,
        "fields": {
            "university_name": "Test University",
            "student_university_number": "12345",
            "specialization": "Computer Science",
            "academic_level": "Senior",
            "career_status": "student",
            "interests": ["data-analysis"],
            "availability": "full_time",
        },
    }


def test_profile_completeness_api_returns_complete_profile_score() -> None:
    response = client.post(
        "/api/v1/profile-completeness",
        json=_complete_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_profile_id"] == 123
    assert data["algorithm_version"] == "profile-completeness-v1"
    assert data["configuration_version"] == "profile-completeness-config-v1"
    assert data["component_status"] == "available"
    assert data["total_fields_count"] == 7
    assert data["completed_fields_count"] == 7
    assert data["incomplete_fields_count"] == 0
    assert data["profile_completeness_score"] == 100.0


def test_profile_completeness_api_treats_missing_fields_as_incomplete() -> None:
    response = client.post(
        "/api/v1/profile-completeness",
        json={
            "student_profile_id": 123,
            "fields": {
                "university_name": "Test University",
                "interests": [],
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["component_status"] == "available"
    assert data["completed_fields_count"] == 1
    assert data["incomplete_fields_count"] == 6
    assert data["profile_completeness_score"] == 14.29


def test_profile_completeness_api_rejects_unknown_profile_fields() -> None:
    payload = _complete_payload()
    payload["fields"]["unknown_field"] = "unexpected"

    response = client.post(
        "/api/v1/profile-completeness",
        json=payload,
    )

    assert response.status_code == 422


def test_profile_completeness_api_rejects_overlong_free_string() -> None:
    payload = _complete_payload()
    payload["fields"]["availability"] = "x" * 101

    response = client.post(
        "/api/v1/profile-completeness",
        json=payload,
    )

    assert response.status_code == 422
