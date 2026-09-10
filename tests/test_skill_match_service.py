import pytest

from app.schemas.skill_match import SkillMatchRequest
from app.services.skill_match_service import SkillMatchError, calculate_skill_match


def _request(skills: list[dict[str, object]]) -> SkillMatchRequest:
    return SkillMatchRequest(
        student_profile_id=15,
        career_role_id=3,
        career_role_version=1,
        user_id=20,
        target_role="Data Analyst",
        skills=skills,
    )


def test_weighted_skill_match_normal_case() -> None:
    result = calculate_skill_match(
        _request(
            [
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
            ]
        )
    )

    assert result["algorithm_version"] == "skill-match-v1"
    assert result["weight_configuration_version"] == "career-role-config-v1"
    assert result["skill_match_score"] == 85.0
    assert result["met_skills"] == 1
    assert result["partial_skills"] == 1


def test_current_level_above_required_is_capped_at_100() -> None:
    result = calculate_skill_match(
        _request(
            [
                {
                    "skill_id": 11,
                    "skill_name": "Python",
                    "current_level": 5,
                    "required_level": 4,
                    "importance_weight": 1.0,
                    "is_critical": False,
                }
            ]
        )
    )

    assert result["skill_match_score"] == 100.0
    assert result["skill_results"][0]["achieved_level"] == 4.0
    assert result["skill_results"][0]["match_ratio"] == 1.0
    assert result["skill_results"][0]["status"] == "met"


def test_zero_required_level_does_not_distort_score() -> None:
    result = calculate_skill_match(
        _request(
            [
                {
                    "skill_id": 11,
                    "skill_name": "Python",
                    "current_level": 0,
                    "required_level": 0,
                    "importance_weight": 0.9,
                    "is_critical": False,
                },
                {
                    "skill_id": 7,
                    "skill_name": "SQL",
                    "current_level": 2,
                    "required_level": 4,
                    "importance_weight": 0.1,
                    "is_critical": False,
                },
            ]
        )
    )

    assert result["skill_match_score"] == 50.0
    assert result["not_required_skills"] == 1
    assert result["skill_results"][0]["status"] == "not_required"


def test_all_zero_requirements_produce_full_match() -> None:
    result = calculate_skill_match(
        _request(
            [
                {
                    "skill_id": 11,
                    "skill_name": "Python",
                    "current_level": 0,
                    "required_level": 0,
                    "importance_weight": 1.0,
                    "is_critical": False,
                }
            ]
        )
    )

    assert result["weighted_required_total"] == 0.0
    assert result["skill_match_score"] == 100.0


def test_positive_weights_are_normalized_deterministically() -> None:
    result = calculate_skill_match(
        _request(
            [
                {
                    "skill_id": 7,
                    "skill_name": "SQL",
                    "current_level": 4,
                    "required_level": 4,
                    "importance_weight": 0.6,
                    "is_critical": False,
                },
                {
                    "skill_id": 11,
                    "skill_name": "Python",
                    "current_level": 2,
                    "required_level": 4,
                    "importance_weight": 0.8,
                    "is_critical": False,
                },
                {
                    "skill_id": 19,
                    "skill_name": "Power BI",
                    "current_level": 3,
                    "required_level": 3,
                    "importance_weight": 0.6,
                    "is_critical": False,
                },
            ]
        )
    )

    assert result["original_weight_total"] == 2.0
    assert result["normalized_weight_total"] == 1.0
    normalized = [item["normalized_importance_weight"] for item in result["skill_results"]]
    assert normalized == [0.3, 0.4, 0.3]


def test_duplicate_skill_ids_are_rejected() -> None:
    request = _request(
        [
            {
                "skill_id": 7,
                "skill_name": "SQL",
                "current_level": 3,
                "required_level": 4,
                "importance_weight": 0.5,
                "is_critical": False,
            },
            {
                "skill_id": 7,
                "skill_name": "SQL Duplicate",
                "current_level": 4,
                "required_level": 4,
                "importance_weight": 0.5,
                "is_critical": False,
            },
        ]
    )

    with pytest.raises(SkillMatchError) as exc_info:
        calculate_skill_match(request)

    assert exc_info.value.code == "DUPLICATE_SKILL_ID"


def test_identical_input_produces_identical_output() -> None:
    request = _request(
        [
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
        ]
    )

    assert calculate_skill_match(request) == calculate_skill_match(request)
