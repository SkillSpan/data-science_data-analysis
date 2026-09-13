import pytest
from pydantic import ValidationError
from app.schemas.assessment_reliability import AssessmentReliabilityRequest
from app.services.assessment_reliability_service import calculate_assessment_reliability


def test_completed_baseline_averages_normalized_skill_confidence() -> None:
    request = AssessmentReliabilityRequest.model_validate({
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "completed",
            "normalized_skills": [
                {"skill_id": 1, "confidence": 100.0},
                {"skill_id": 2, "confidence": 80.0},
                {"skill_id": 3, "confidence": 60.0}
            ]
        }
    })

    result = calculate_assessment_reliability(request)

    assert result["algorithm_version"] == "assessment-reliability-v1"
    assert result["configuration_version"] == "assessment-reliability-config-v1"
    assert result["component_status"] == "available"
    assert result["baseline_assessment_id"] == 101
    assert result["assessment_version"] == "v1.0"
    assert result["assessed_skills_count"] == 3
    assert result["assessment_reliability_score"] == 80.0


def test_missing_assessment_is_unavailable() -> None:
    request = AssessmentReliabilityRequest(
        student_profile_id=10,
        assessment=None,
    )

    result = calculate_assessment_reliability(request)

    assert result["component_status"] == "unavailable"
    assert result["baseline_assessment_id"] is None
    assert result["assessment_version"] is None
    assert result["assessed_skills_count"] == 0
    assert result["assessment_reliability_score"] is None


def test_in_progress_baseline_is_unavailable() -> None:
    request = AssessmentReliabilityRequest.model_validate({
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "in_progress",
            "normalized_skills": [
                {"skill_id": 1, "confidence": 100.0}
            ]
        }
    })

    result = calculate_assessment_reliability(request)

    assert result["component_status"] == "unavailable"
    assert result["assessed_skills_count"] == 0
    assert result["assessment_reliability_score"] is None


def test_completed_baseline_without_normalized_skills_is_unavailable() -> None:
    request = AssessmentReliabilityRequest.model_validate({
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "completed",
            "normalized_skills": []
        }
    })

    result = calculate_assessment_reliability(request)

    assert result["component_status"] == "unavailable"
    assert result["assessed_skills_count"] == 0
    assert result["assessment_reliability_score"] is None


def test_zero_confidence_is_valid_available_data_not_missing() -> None:
    request = AssessmentReliabilityRequest.model_validate({
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "completed",
            "normalized_skills": [
                {"skill_id": 1, "confidence": 0.0},
                {"skill_id": 2, "confidence": 0.0}
            ]
        }
    })

    result = calculate_assessment_reliability(request)

    assert result["component_status"] == "available"
    assert result["assessed_skills_count"] == 2
    assert result["assessment_reliability_score"] == 0.0


def test_assessment_reliability_rounds_average_to_two_decimals() -> None:
    request = AssessmentReliabilityRequest.model_validate({
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "completed",
            "normalized_skills": [
                {"skill_id": 1, "confidence": 33.33},
                {"skill_id": 2, "confidence": 66.66},
                {"skill_id": 3, "confidence": 100.0}
            ]
        }
    })

    result = calculate_assessment_reliability(request)

    assert result["assessment_reliability_score"] == 66.66


def test_assessment_reliability_is_deterministic_for_identical_input() -> None:
    request = AssessmentReliabilityRequest.model_validate({
        "student_profile_id": 10,
        "assessment": {
            "assessment_id": 101,
            "assessment_type": "baseline",
            "assessment_version": "v1.0",
            "status": "completed",
            "normalized_skills": [
                {"skill_id": 1, "confidence": 75.0},
                {"skill_id": 2, "confidence": 50.0}
            ]
        }
    })

    first = calculate_assessment_reliability(request)
    second = calculate_assessment_reliability(request)

    assert first == second


def test_duplicate_normalized_skill_id_is_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate skill_id"):
        AssessmentReliabilityRequest.model_validate({
            "student_profile_id": 10,
            "assessment": {
                "assessment_id": 101,
                "assessment_type": "baseline",
                "assessment_version": "v1.0",
                "status": "completed",
                "normalized_skills": [
                    {"skill_id": 1, "confidence": 100.0},
                    {"skill_id": 1, "confidence": 50.0}
                ]
            }
        })
