from copy import deepcopy

import pytest

from app.schemas.project_matching import (
    ProjectMatchingConfiguration,
    ProjectMatchingRequest,
)
from app.services.project_matching_service import (
    ProjectMatchingError,
    calculate_project_match,
    evaluate_availability_fit,
    evaluate_career_relevance,
    evaluate_interest_match,
    evaluate_learning_value,
    evaluate_skill_compatibility,
    rank_project_matches,
)


def _payload(project_id: int = 10, request_id: str = "project-match-test") -> dict[str, object]:
    return {
        "request_id": request_id,
        "algorithm_version": "project-matching-v1",
        "configuration_version": "project-matching-config-v1",
        "project_version": 1,
        "learner": {
            "user_id": 20,
            "student_profile_id": 15,
            "availability": "full_time",
            "preferred_work_type": "remote",
            "interests": ["backend"],
            "target_career_role": {
                "id": 3,
                "title": "Backend Developer",
                "version": 1,
            },
            "current_skills": [
                {
                    "skill_id": 1,
                    "level": 3,
                    "required_level": 3,
                    "meets_requirement": True,
                },
                {
                    "skill_id": 2,
                    "level": 3,
                    "required_level": 4,
                    "meets_requirement": False,
                },
                {
                    "skill_id": 3,
                    "level": 2,
                    "required_level": 2,
                    "meets_requirement": True,
                },
            ],
        },
        "project": {
            "id": project_id,
            "version": 1,
            "type": "company_sponsored",
            "domain": "backend",
            "difficulty": 3,
            "work_mode": "remote",
            "role": "Backend Developer",
            "schedule": "full_time",
            "organization_id": 2,
            "confidentiality": "public",
        },
        "required_skills": [
            {
                "skill_id": 1,
                "skill_name": "Python",
                "minimum_level": 3,
                "is_critical_entry": True,
            },
            {
                "skill_id": 2,
                "skill_name": "SQL",
                "minimum_level": 4,
                "is_critical_entry": False,
            },
            {
                "skill_id": 3,
                "skill_name": "Git",
                "minimum_level": 2,
                "is_critical_entry": False,
            },
        ],
        "validation": {
            "eligibility_state": "eligible",
            "validation_state": "validated",
            "constraints": [],
            "skill_gaps": [],
            "authorization": "authorized",
        },
    }


def _request(payload: dict[str, object] | None = None) -> ProjectMatchingRequest:
    return ProjectMatchingRequest.model_validate(payload or _payload())


def test_vector_01_strong_full_match() -> None:
    payload = _payload()
    payload["learner"]["current_skills"][1]["level"] = 4
    payload["learner"]["current_skills"][1]["meets_requirement"] = True

    result = calculate_project_match(_request(payload))
    recommendation = result["recommendation"]

    assert recommendation["eligibility_state"] == "eligible"
    assert recommendation["matching_state"] == "scored"
    assert recommendation["factor_scores"]["skill_compatibility"] == 100.0
    assert [item["status"] for item in recommendation["skill_results"]] == [
        "met",
        "met",
        "met",
    ]


def test_vector_02_partial_skill_match() -> None:
    payload = _payload()
    payload["learner"]["current_skills"][1]["level"] = 2

    result = calculate_project_match(_request(payload))
    recommendation = result["recommendation"]

    assert recommendation["factor_scores"]["skill_compatibility"] == 83.33
    assert recommendation["skill_results"][1]["status"] == "large_gap"
    assert recommendation["score"] == 69.17


def test_vector_03_missing_non_critical_skill() -> None:
    payload = _payload()
    payload["learner"]["current_skills"] = [
        skill
        for skill in payload["learner"]["current_skills"]
        if skill["skill_id"] != 2
    ]

    result = calculate_project_match(_request(payload))
    recommendation = result["recommendation"]

    assert recommendation["eligibility_state"] == "eligible"
    assert recommendation["matching_state"] == "scored"
    assert recommendation["skill_results"][1]["status"] == "missing_non_critical"
    assert "Missing non-critical skill: SQL." in recommendation["limiting_factors"]


def test_vector_04_missing_critical_skill() -> None:
    payload = _payload()
    payload["learner"]["current_skills"] = [
        skill
        for skill in payload["learner"]["current_skills"]
        if skill["skill_id"] != 1
    ]

    result = calculate_project_match(_request(payload))
    recommendation = result["recommendation"]

    assert recommendation["score"] == 0.0
    assert recommendation["eligibility_state"] == "ineligible"
    assert recommendation["matching_state"] == "blocked"
    assert recommendation["skill_results"][0]["status"] == "missing_critical"


def test_vector_05_skill_level_below_critical_minimum() -> None:
    payload = _payload()
    payload["learner"]["current_skills"][0]["level"] = 2
    payload["learner"]["current_skills"][0]["meets_requirement"] = False

    result = calculate_project_match(_request(payload))
    recommendation = result["recommendation"]

    assert recommendation["score"] == 0.0
    assert recommendation["matching_state"] == "blocked"
    assert recommendation["skill_results"][0]["status"] == "critical_below_minimum"
    assert "Critical skill Python is 1.0 level(s) below the minimum." in recommendation["limiting_factors"]


def test_vector_06_manageable_growth_opportunity() -> None:
    request = _request()
    skill_result = evaluate_skill_compatibility(request)
    learning_result = evaluate_learning_value(skill_result)

    assert skill_result["skill_results"][1]["status"] == "manageable_gap"
    assert learning_result == {
        "learning_value_score": 50.0,
        "opportunity_count": 1,
        "evaluated_skill_count": 2,
    }


def test_vector_07_strong_career_relevance() -> None:
    result = evaluate_career_relevance(_request())

    assert result["career_relevance_score"] == 100.0
    assert result["career_relevance_state"] == "strong"
    assert result["matched_source"] == "project_role"


def test_vector_08_weak_career_relevance() -> None:
    payload = _payload()
    payload["learner"]["target_career_role"]["title"] = "Data Analyst"

    result = evaluate_career_relevance(_request(payload))

    assert result["career_relevance_score"] == 0.0
    assert result["career_relevance_state"] == "weak"


def test_vector_09_strong_interest_alignment() -> None:
    result = evaluate_interest_match(_request())

    assert result["interest_match_score"] == 100.0
    assert result["interest_match_state"] == "strong"
    assert result["matched_interest"] == "backend"


def test_vector_10_no_interest_data_uses_neutral_fallback() -> None:
    payload = _payload()
    payload["learner"].pop("interests")

    result = evaluate_interest_match(_request(payload))

    assert result["interest_match_score"] == 50.0
    assert result["interest_match_state"] == "unavailable"
    assert result["matched_interest"] is None


def test_vector_11_availability_match() -> None:
    result = evaluate_availability_fit(_request())

    assert result["availability_fit_score"] == 100.0
    assert result["availability_fit_state"] == "strong"


def test_vector_12_availability_mismatch() -> None:
    payload = _payload()
    payload["learner"]["availability"] = "part_time"
    payload["learner"]["preferred_work_type"] = "onsite"

    result = evaluate_availability_fit(_request(payload))

    assert result["availability_fit_score"] == 0.0
    assert result["availability_fit_state"] == "mismatch"


def test_vector_13_multiple_projects_have_deterministic_score_order() -> None:
    stronger = _payload(project_id=20, request_id="rank-strong")
    weaker = _payload(project_id=10, request_id="rank-weak")
    weaker["learner"]["target_career_role"]["title"] = "Data Analyst"
    weaker["learner"]["interests"] = ["data analysis"]
    weaker["learner"]["availability"] = "part_time"
    weaker["learner"]["preferred_work_type"] = "onsite"

    ranked = rank_project_matches([
        _request(weaker),
        _request(stronger),
    ])

    assert [item["project_id"] for item in ranked] == [20, 10]
    assert ranked[0]["score"] > ranked[1]["score"]


def test_vector_14_equal_scores_use_project_id_tie_breaker() -> None:
    first = _request(_payload(project_id=20, request_id="tie-20"))
    second = _request(_payload(project_id=10, request_id="tie-10"))

    ranked = rank_project_matches([first, second])

    assert [(item["project_id"], item["score"]) for item in ranked] == [
        (10, 84.58),
        (20, 84.58),
    ]


def test_vector_15_invalid_algorithm_configuration_is_rejected() -> None:
    configuration = ProjectMatchingConfiguration(
        algorithm_version="project-matching-v2",
    )

    with pytest.raises(ProjectMatchingError) as exc_info:
        calculate_project_match(_request(), configuration)

    assert exc_info.value.code == "UNSUPPORTED_ALGORITHM_VERSION"


def test_vector_16_repeated_identical_input_is_deterministic() -> None:
    request = _request()

    first = calculate_project_match(request)
    second = calculate_project_match(request)

    assert first == second


def test_configuration_rejects_invalid_weight_total() -> None:
    with pytest.raises(ValueError):
        ProjectMatchingConfiguration(
            weights={"skill_compatibility": 0.40}
        )


def test_configuration_rejects_negative_weight() -> None:
    with pytest.raises(ValueError):
        ProjectMatchingConfiguration(
            weights={"interest_match": -0.10}
        )


def test_configuration_rejects_invalid_threshold_and_critical_rule() -> None:
    with pytest.raises(ValueError):
        ProjectMatchingConfiguration(manageable_gap_max=0)

    with pytest.raises(ValueError):
        ProjectMatchingConfiguration(
            critical_entry_is_hard_constraint=False
        )


def test_service_rejects_unsupported_configuration_version() -> None:
    configuration = ProjectMatchingConfiguration(
        configuration_version="project-matching-config-v2",
    )

    with pytest.raises(ProjectMatchingError) as exc_info:
        calculate_project_match(_request(), configuration)

    assert exc_info.value.code == "UNSUPPORTED_CONFIGURATION_VERSION"
