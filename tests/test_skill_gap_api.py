from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analyze_skill_gap_returns_expected_result() -> None:
    """The endpoint should calculate the expected readiness and skill gaps."""

    response = client.post(
        "/api/v1/skill-gap",
        json={
            "user_id": 1,
            "target_role": "Data Analyst",
            "skills": [
                {
                    "skill_name": "Python",
                    "current_level": 3,
                    "required_level": 4,
                },
                {
                    "skill_name": "SQL",
                    "current_level": 4,
                    "required_level": 4,
                },
                {
                    "skill_name": "Power BI",
                    "current_level": 2,
                    "required_level": 4,
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == 1
    assert data["target_role"] == "Data Analyst"
    assert data["readiness_score"] == 75.0
    assert data["total_skills"] == 3
    assert data["met_skills"] == 1
    assert data["skills_with_gap"] == 2

    assert data["skill_results"] == [
        {
            "skill_name": "Python",
            "current_level": 3.0,
            "required_level": 4.0,
            "importance_weight": 1.0,
            "is_critical": False,
            "gap": 1.0,
            "status": "gap",
        },
        {
            "skill_name": "SQL",
            "current_level": 4.0,
            "required_level": 4.0,
            "importance_weight": 1.0,
            "is_critical": False,
            "gap": 0.0,
            "status": "met",
        },
        {
            "skill_name": "Power BI",
            "current_level": 2.0,
            "required_level": 4.0,
            "importance_weight": 1.0,
            "is_critical": False,
            "gap": 2.0,
            "status": "gap",
        },
    ]


def test_analyze_skill_gap_rejects_invalid_skill_level() -> None:
    """The endpoint should reject skill levels outside the allowed range."""

    response = client.post(
        "/api/v1/skill-gap",
        json={
            "user_id": 1,
            "target_role": "Data Analyst",
            "skills": [
                {
                    "skill_name": "Python",
                    "current_level": 8,
                    "required_level": 4,
                }
            ],
        },
    )

    assert response.status_code == 422

def test_analyze_skill_gap_uses_importance_weights() -> None:
    """More important skills should have a larger effect on readiness."""

    response = client.post(
        "/api/v1/skill-gap",
        json={
            "user_id": 1,
            "target_role": "Data Analyst",
            "skills": [
                {
                    "skill_name": "Python",
                    "current_level": 3,
                    "required_level": 4,
                    "importance_weight": 20,
                },
                {
                    "skill_name": "SQL",
                    "current_level": 2,
                    "required_level": 4,
                    "importance_weight": 50,
                },
                {
                    "skill_name": "Power BI",
                    "current_level": 4,
                    "required_level": 4,
                    "importance_weight": 30,
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["readiness_score"] == 70.0
    assert data["total_skills"] == 3
    assert data["met_skills"] == 1
    assert data["skills_with_gap"] == 2
    assert data["skill_results"][0]["importance_weight"] == 20.0
    assert data["skill_results"][1]["importance_weight"] == 50.0
    assert data["skill_results"][2]["importance_weight"] == 30.0

def test_major_critical_skill_gap_caps_readiness_score() -> None:
    """A major gap in a critical skill should cap the readiness score."""

    response = client.post(
        "/api/v1/skill-gap",
        json={
            "user_id": 1,
            "target_role": "Data Analyst",
            "skills": [
                {
                    "skill_name": "SQL",
                    "current_level": 1,
                    "required_level": 4,
                    "importance_weight": 10,
                    "is_critical": True,
                },
                {
                    "skill_name": "Python",
                    "current_level": 5,
                    "required_level": 5,
                    "importance_weight": 45,
                    "is_critical": False,
                },
                {
                    "skill_name": "Power BI",
                    "current_level": 5,
                    "required_level": 5,
                    "importance_weight": 45,
                    "is_critical": False,
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["base_readiness_score"] == 93.88
    assert data["readiness_score"] == 60.0

    assert data["critical_skill_cap_applied"] is True
    assert data["critical_skill_readiness_cap"] == 60.0
    assert data["critical_skill_gap_count"] == 1
    assert data["critical_skill_names"] == ["SQL"]

    assert data["total_skills"] == 3
    assert data["met_skills"] == 2
    assert data["skills_with_gap"] == 1

    sql_result = data["skill_results"][0]

    assert sql_result["skill_name"] == "SQL"
    assert sql_result["current_level"] == 1.0
    assert sql_result["required_level"] == 4.0
    assert sql_result["importance_weight"] == 10.0
    assert sql_result["is_critical"] is True
    assert sql_result["gap"] == 3.0
    assert sql_result["status"] == "gap"

def test_minor_critical_skill_gap_does_not_cap_readiness_score() -> None:
    """A critical skill gap below the major threshold should not cap readiness."""

    response = client.post(
        "/api/v1/skill-gap",
        json={
            "user_id": 1,
            "target_role": "Data Analyst",
            "skills": [
                {
                    "skill_name": "SQL",
                    "current_level": 3,
                    "required_level": 4,
                    "importance_weight": 10,
                    "is_critical": True,
                },
                {
                    "skill_name": "Python",
                    "current_level": 5,
                    "required_level": 5,
                    "importance_weight": 45,
                    "is_critical": False,
                },
                {
                    "skill_name": "Power BI",
                    "current_level": 5,
                    "required_level": 5,
                    "importance_weight": 45,
                    "is_critical": False,
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["base_readiness_score"] == 97.96
    assert data["readiness_score"] == 97.96

    assert data["critical_skill_cap_applied"] is False
    assert data["critical_skill_readiness_cap"] is None
    assert data["critical_skill_gap_count"] == 0
    assert data["critical_skill_names"] == []

    assert data["total_skills"] == 3
    assert data["met_skills"] == 2
    assert data["skills_with_gap"] == 1

    sql_result = data["skill_results"][0]

    assert sql_result["skill_name"] == "SQL"
    assert sql_result["current_level"] == 3
    assert sql_result["required_level"] == 4
    assert sql_result["importance_weight"] == 10
    assert sql_result["is_critical"] is True
    assert sql_result["gap"] == 1.0
    assert sql_result["status"] == "gap"