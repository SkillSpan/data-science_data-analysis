from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload() -> dict[str, object]:
    return {
        "student_profile_id": 15,
        "career_role_id": 3,
        "career_role_version": 1,
        "user_id": 20,
        "target_role": "Data Analyst",
        "skills": [
            {
                "skill_id": 7,
                "skill_name": "SQL",
                "current_level": 3,
                "required_level": 4,
                "importance_weight": 0.6,
                "is_critical": True,
            },
            {
                "skill_id": 11,
                "skill_name": "Python",
                "current_level": 4,
                "required_level": 4,
                "importance_weight": 0.4,
                "is_critical": False,
            },
        ],
    }


def test_skill_match_api_returns_weighted_match() -> None:
    response = client.post("/api/v1/skill-match", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm_version"] == "skill-match-v1"
    assert body["weight_configuration_version"] == "career-role-config-v1"
    assert body["skill_match_score"] == 85.0
    assert body["normalized_weight_total"] == 1.0
    assert body["met_skills"] == 1
    assert body["partial_skills"] == 1
    assert body["skill_results"][0]["is_critical"] is True
    assert body["skill_results"][1]["is_critical"] is False


def test_skill_match_api_caps_current_above_required_at_100() -> None:
    payload = _payload()
    payload["skills"] = [
        {
            "skill_id": 11,
            "skill_name": "Python",
            "current_level": 5,
            "required_level": 4,
            "importance_weight": 1.0,
            "is_critical": False,
        }
    ]

    response = client.post("/api/v1/skill-match", json=payload)

    assert response.status_code == 200
    assert response.json()["skill_match_score"] == 100.0


def test_skill_match_api_returns_structured_error_for_duplicate_skill() -> None:
    payload = _payload()
    payload["skills"] = [payload["skills"][0], payload["skills"][0]]

    response = client.post("/api/v1/skill-match", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "DUPLICATE_SKILL_ID"


def test_skill_match_api_rejects_invalid_weight() -> None:
    payload = _payload()
    payload["skills"][0]["importance_weight"] = 0

    response = client.post("/api/v1/skill-match", json=payload)

    assert response.status_code == 422


def test_skill_match_api_rejects_missing_role_data() -> None:
    for field_name in ("career_role_id", "target_role"):
        payload = _payload()
        payload.pop(field_name)

        response = client.post("/api/v1/skill-match", json=payload)

        assert response.status_code == 422
