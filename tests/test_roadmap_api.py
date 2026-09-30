from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
HEADERS = {
    "Authorization": "Bearer test-service-token",
    "X-Request-ID": "roadmap-test-request",
}


def payload():
    return {
        "learner": {
            "student_profile_id": 15,
            "user_id": 20,
            "availability": "part_time",
            "weekly_availability_hours": 10,
        },
        "role": {
            "id": 3,
            "title": "Backend Developer",
            "version": 2,
        },
        "skills": [
            {
                "skill_id": 1,
                "skill_name": "Python",
                "current_level": 2.0,
                "required_level": 4.0,
                "importance_weight": 0.6,
                "is_critical": True,
                "confidence": 90.0,
                "prerequisite_skill_ids": [],
            },
            {
                "skill_id": 2,
                "skill_name": "FastAPI",
                "current_level": 3.0,
                "required_level": 4.0,
                "importance_weight": 0.4,
                "is_critical": True,
                "confidence": 80.0,
                "prerequisite_skill_ids": [1],
            },
        ],
    }


def test_roadmap_api_returns_v1_contract(monkeypatch):
    monkeypatch.setenv("DATA_SCIENCE_SERVICE_TOKEN", "test-service-token")

    response = client.post("/api/v1/roadmap", json=payload(), headers=HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["student_profile_id"] == 15
    assert body["career_role_id"] == 3
    assert body["career_role_version"] == 2
    assert body["algorithm_version"] == "roadmap-v1"
    assert body["configuration_version"] == "roadmap-config-v1"
    assert "roadmap_version" not in body
    assert "status" not in body
    assert body["next_best_action_id"] is not None
    assert [phase["phase"] for phase in body["phases"]] == [
        "foundations",
        "core_skills",
        "applied_practice",
        "career_readiness",
    ]
    assert response.headers["X-Request-ID"] == "roadmap-test-request"


def test_roadmap_api_rejects_prerequisite_cycle(monkeypatch):
    monkeypatch.setenv("DATA_SCIENCE_SERVICE_TOKEN", "test-service-token")
    body = payload()
    body["skills"][0]["prerequisite_skill_ids"] = [2]

    response = client.post("/api/v1/roadmap", json=body, headers=HEADERS)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "PREREQUISITE_CYCLE"
