from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _valid_payload() -> dict:
    return {
        "career_role_id": 1,
        "title": "Data Analyst",
        "slug": "data-analyst",
        "version": 2,
        "status": "approved",
        "effective_date": "2026-09-01",
        "skills": [
            {
                "skill_id": 1,
                "skill_name": "Python",
                "required_level": 4.0,
                "importance_weight": 0.3,
                "is_critical": True,
                "prerequisite_skill_id": None
            },
            {
                "skill_id": 2,
                "skill_name": "SQL",
                "required_level": 4.0,
                "importance_weight": 0.7,
                "is_critical": True,
                "prerequisite_skill_id": 1
            }
        ]
    }


def test_career_role_configuration_api_validates_valid_role() -> None:
    response = client.post(
        "/api/v1/career-role-configuration/validate",
        json=_valid_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["configuration_version"] == "career-role-config-v1"
    assert data["production_eligible"] is True
    assert data["prerequisite_order"] == [1, 2]
    assert data["normalized_weight_total"] == 1.0


def test_career_role_configuration_api_rejects_prerequisite_cycle() -> None:
    payload = _valid_payload()
    payload["skills"][0]["prerequisite_skill_id"] = 2

    response = client.post(
        "/api/v1/career-role-configuration/validate",
        json=payload,
    )

    assert response.status_code == 422
    assert "contain a cycle" in response.json()["detail"]


def test_career_role_configuration_api_accepts_multiple_prerequisites() -> None:
    payload = _valid_payload()
    payload["skills"].append({
        "skill_id": 3,
        "skill_name": "React",
        "required_level": 3.0,
        "importance_weight": 0.6,
        "is_critical": True,
        "prerequisites": [
            {"skill_id": 1, "slug": "python", "name": "Python"},
            {"skill_id": 2, "slug": "sql", "name": "SQL"},
        ],
    })

    response = client.post(
        "/api/v1/career-role-configuration/validate",
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["prerequisite_order"].index(1) < data["prerequisite_order"].index(3)
    assert data["prerequisite_order"].index(2) < data["prerequisite_order"].index(3)
    react = next(skill for skill in data["skills"] if skill["skill_id"] == 3)
    assert [item["skill_id"] for item in react["prerequisites"]] == [1, 2]
