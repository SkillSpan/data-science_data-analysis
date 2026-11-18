from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.readiness import ReadinessRequest
from app.services.readiness_service import ReadinessError, calculate_readiness


def payload():
    # SRS 10.5.3: independently specified 85 SM, 81.75 composite.
    pairs = [(4, 4, .25), (3, 4, .20), (4, 4, .15), (2, 4, .20), (3, 3, .15), (3, 3, .05)]
    return dict(student_profile_id=1, career_role_id=3, career_role_version=1,
                user_id=1, target_role="Data Analyst", practical_experience=70,
                assessment_reliability=80, profile_completeness=90,
                skills=[dict(skill_id=i+1, skill_name=f"Skill {i+1}", current_level=c,
                             required_level=r, importance_weight=w, is_critical=False)
                        for i, (c, r, w) in enumerate(pairs)])


def calculate(data):
    return calculate_readiness(ReadinessRequest.model_validate(data))


def test_srs_worked_example_and_reproducibility():
    data = payload()
    original = deepcopy(data)
    result = calculate(data)
    assert result["base_readiness_score"] == 85
    assert result["readiness_score"] == 81.75
    assert result["band"] == "near_ready"
    assert result == calculate(data)
    assert data == original


def test_different_required_levels_use_mean_of_ratios():
    data = payload()
    data["skills"] = [dict(skill_id=i+1, skill_name=f"Skill {i+1}", current_level=c,
                           required_level=r, importance_weight=w, is_critical=False)
                      for i, (c, r, w) in enumerate([(2,2.5,.8),(1,3,.9),(1,2.5,.7),(1,2.5,.6),(3,2.5,.5)])]
    assert calculate(data)["base_readiness_score"] == 56
    # A non-required skill must not dilute normalized role importance.
    data["skills"].append(dict(skill_id=99, skill_name="Not required", current_level=0,
                               required_level=0, importance_weight=1, is_critical=True))
    assert calculate(data)["base_readiness_score"] == 56


def test_missing_optional_component_is_not_zero():
    data = payload()
    data["practical_experience"] = None
    result = calculate(data)
    assert result["readiness_score"] == 84.69
    assert result["is_provisional"] is True
    assert "practical_experience" not in result["effective_weights"]
    data["practical_experience"] = 0
    assert calculate(data)["readiness_score"] == 67.75
    assert calculate(data)["is_provisional"] is False


def test_critical_cap_uses_ratio_and_caps_composite_only():
    data = payload()
    data["skills"] = [dict(skill_id=1, skill_name="Critical skill", current_level=1.5,
                           required_level=4, importance_weight=.01, is_critical=True),
                      dict(skill_id=2, skill_name="Other skill", current_level=5,
                           required_level=5, importance_weight=.99, is_critical=False)]
    result = calculate(data)
    assert result["base_readiness_score"] == 99.38
    assert result["readiness_score"] == 69
    assert result["critical_skill_cap_applied"] is True
    data["skills"][0]["current_level"] = 2
    assert calculate(data)["critical_skill_cap_applied"] is False
    assert calculate(data)["critical_skill_ids"] == []


def test_invalid_duplicate_or_no_required_skill():
    data = payload()
    data["skills"].append(data["skills"][0])
    with pytest.raises(ReadinessError):
        calculate(data)
    data = payload()
    for skill in data["skills"]:
        skill["required_level"] = 0
    with pytest.raises(ReadinessError):
        calculate(data)


def test_api_version_auth_and_invalid_policy():
    client = TestClient(app, headers={"Authorization": "Bearer test-service-token"})
    response = client.post("/api/v1/readiness", json=payload())
    assert response.status_code == 200
    assert response.json()["algorithm_version"] == "readiness-v2-srs13"
    assert response.json()["readiness_score"] == 81.75
    data = payload()
    data["policy"] = {"skill_match": 0, "practical_experience": 0,
                      "assessment_reliability": 0, "profile_completeness": 0}
    assert client.post("/api/v1/readiness", json=data).status_code == 422
    assert client.post("/api/v1/readiness", json=payload(), headers={"Authorization":"Bearer wrong"}).status_code == 401
