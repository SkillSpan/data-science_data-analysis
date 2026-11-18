from copy import deepcopy

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.roadmap import RoadmapRequest
from app.services.roadmap_service import generate_roadmap


def payload(recent=True, policy="assessment-aware-v2"):
    return {
        "learner": {"student_profile_id": 13, "user_id": 30, "weekly_availability_hours": 8},
        "role": {"id": 3, "title": "Data Analyst", "version": 1},
        "action_selection_policy": policy,
        "skills": [{"skill_id": 20, "skill_name": "Statistics Fundamentals",
                    "current_level": 1, "required_level": 3, "importance_weight": .9,
                    "is_critical": True, "confidence": 30,
                    "has_recent_verified_assessment": recent}],
    }


def actions(result):
    return [action for phase in result["phases"] for action in phase["actions"]]


def test_recent_measured_gap_recommends_learning_not_another_assessment():
    data = payload()
    original = deepcopy(data)
    request = RoadmapRequest.model_validate(data)
    result = generate_roadmap(request)
    action = actions(result)[0]
    assert action["action_type"] == "resource"
    assert action["title"] == "Learn Statistics Fundamentals"
    assert action["estimated_hours"] == 16
    assert any("recent verified assessment" in reason for reason in action["explanation"])
    assert result["algorithm_version"] == "roadmap-v2"
    assert result["configuration_version"] == "roadmap-config-v2"
    assert generate_roadmap(request) == result
    assert data == original


def test_absent_or_stale_assessment_still_allows_diagnostic_action():
    assert actions(generate_roadmap(RoadmapRequest.model_validate(payload(False))))[0]["action_type"] == "assessment"


def test_legacy_policy_is_preserved_even_if_new_metadata_is_present():
    result = generate_roadmap(RoadmapRequest.model_validate(payload(policy="legacy-v1")))
    assert result["algorithm_version"] == "roadmap-v1"
    assert actions(result)[0]["action_type"] == "assessment"


def test_recent_assessment_does_not_force_every_gap_into_resource():
    data = payload()
    data["skills"][0].update(current_level=2.2, required_level=3)
    assert actions(generate_roadmap(RoadmapRequest.model_validate(data)))[0]["action_type"] == "simulated_project"


def test_met_skills_are_not_reassessed_despite_low_confidence():
    data = payload()
    data["skills"][0]["current_level"] = 3
    result = generate_roadmap(RoadmapRequest.model_validate(data))
    assert actions(result) == []
    assert result["next_best_action_id"] is None


def test_api_accepts_new_policy_and_preserves_old_default():
    client = TestClient(app, headers={"Authorization": "Bearer test-service-token"})
    response = client.post("/api/v1/roadmap", json=payload())
    assert response.status_code == 200
    assert response.json()["algorithm_version"] == "roadmap-v2"
    data = payload()
    del data["action_selection_policy"]
    del data["skills"][0]["has_recent_verified_assessment"]
    response = client.post("/api/v1/roadmap", json=data)
    assert response.status_code == 200
    assert response.json()["algorithm_version"] == "roadmap-v1"
    data["action_selection_policy"] = "unknown-policy"
    assert client.post("/api/v1/roadmap", json=data).status_code == 422
