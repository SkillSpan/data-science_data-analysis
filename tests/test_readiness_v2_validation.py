import pytest
from pydantic import ValidationError

from app.schemas.readiness import ReadinessRequest
from app.services.readiness_service import ReadinessError, calculate_readiness


def base():
    return dict(student_profile_id=1, career_role_id=1, career_role_version=1,
                user_id=1, target_role="Analyst", skills=[dict(skill_id=1, skill_name="SQL",
                current_level=2, required_level=4, importance_weight=1, is_critical=False)])


@pytest.mark.parametrize("score", [-1, 101, float("nan"), float("inf")])
def test_invalid_component_score(score):
    with pytest.raises(ValidationError):
        ReadinessRequest.model_validate({**base(), "practical_experience": score})


def test_zero_weight_skill_does_not_contribute_and_no_required_weight_is_rejected():
    data = base()
    data["skills"].append(dict(skill_id=2, skill_name="Extra", current_level=5,
                               required_level=5, importance_weight=0, is_critical=False))
    assert calculate_readiness(ReadinessRequest.model_validate(data))["base_readiness_score"] == 50
    data["skills"][0]["importance_weight"] = 0
    with pytest.raises(ReadinessError):
        calculate_readiness(ReadinessRequest.model_validate(data))


def test_small_absolute_gap_still_triggers_critical_ratio_rule():
    data = base()
    data["skills"][0].update(current_level=.8, required_level=2,
                              importance_weight=.01, is_critical=True)
    data["skills"].append(dict(skill_id=2, skill_name="Other", current_level=5,
                               required_level=5, importance_weight=.99, is_critical=False))
    result = calculate_readiness(ReadinessRequest.model_validate(data))
    assert result["readiness_score"] == 69
    assert result["critical_skill_cap_applied"] is True


def test_unknown_policy_and_protected_features_are_rejected():
    with pytest.raises(ValidationError):
        ReadinessRequest.model_validate({**base(), "policy": {"version": "unapproved"}})
    with pytest.raises(ValidationError):
        ReadinessRequest.model_validate({**base(), "gender": "any"})
