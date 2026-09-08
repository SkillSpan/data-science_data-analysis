import pytest

from app.schemas.career_role_configuration import CareerRoleConfigurationRequest
from app.services.career_role_configuration_service import (
    CareerRoleConfigurationError,
    validate_career_role_configuration,
)


def _request(*, status: str = "approved") -> CareerRoleConfigurationRequest:
    return CareerRoleConfigurationRequest(
        career_role_id=1,
        title="Data Analyst",
        slug="data-analyst",
        version=2,
        status=status,
        effective_date="2026-09-01",
        skills=[
            {
                "skill_id": 1,
                "skill_name": "Python",
                "required_level": 4.0,
                "importance_weight": 0.3,
                "is_critical": True,
                "prerequisite_skill_id": None,
            },
            {
                "skill_id": 2,
                "skill_name": "SQL",
                "required_level": 4.0,
                "importance_weight": 0.5,
                "is_critical": True,
                "prerequisite_skill_id": 1,
            },
            {
                "skill_id": 3,
                "skill_name": "Power BI",
                "required_level": 3.0,
                "importance_weight": 0.2,
                "is_critical": False,
                "prerequisite_skill_id": 2,
            },
        ],
    )


def test_valid_configuration_normalizes_weights_and_orders_prerequisites() -> None:
    result = validate_career_role_configuration(_request())

    assert result["configuration_version"] == "career-role-config-v1"
    assert result["career_role_id"] == 1
    assert result["career_role_version"] == 2
    assert result["production_eligible"] is True
    assert result["original_weight_total"] == 1.0
    assert result["normalized_weight_total"] == 1.0
    assert result["prerequisite_order"] == [1, 2, 3]

    weights = {
        skill["skill_id"]: skill["normalized_importance_weight"]
        for skill in result["skills"]
    }
    assert weights == {1: 0.3, 2: 0.5, 3: 0.2}


def test_configuration_normalizes_positive_weight_total_that_is_not_one() -> None:
    request = _request()
    request.skills[0].importance_weight = 0.6
    request.skills[1].importance_weight = 0.8
    request.skills[2].importance_weight = 0.6

    result = validate_career_role_configuration(request)

    assert result["original_weight_total"] == 2.0
    assert sum(
        skill["normalized_importance_weight"] for skill in result["skills"]
    ) == pytest.approx(1.0)


def test_draft_configuration_is_not_production_eligible() -> None:
    result = validate_career_role_configuration(_request(status="draft"))

    assert result["production_eligible"] is False



def test_duplicate_skill_id_is_rejected() -> None:
    request = _request()
    request.skills[2].skill_id = 2

    with pytest.raises(
        CareerRoleConfigurationError,
        match="duplicate skill_id",
    ):
        validate_career_role_configuration(request)


def test_self_prerequisite_is_rejected() -> None:
    request = _request()
    request.skills[0].prerequisite_skill_id = 1

    with pytest.raises(
        CareerRoleConfigurationError,
        match="cannot depend on itself",
    ):
        validate_career_role_configuration(request)


def test_missing_prerequisite_skill_is_rejected() -> None:
    request = _request()
    request.skills[1].prerequisite_skill_id = 99

    with pytest.raises(
        CareerRoleConfigurationError,
        match="not present in the same career role",
    ):
        validate_career_role_configuration(request)


def test_prerequisite_cycle_is_rejected() -> None:
    request = _request()
    request.skills[0].prerequisite_skill_id = 3

    with pytest.raises(
        CareerRoleConfigurationError,
        match="contain a cycle",
    ):
        validate_career_role_configuration(request)
