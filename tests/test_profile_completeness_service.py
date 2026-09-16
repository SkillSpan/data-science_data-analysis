import pytest
from pydantic import ValidationError

from app.schemas.profile_completeness import ProfileCompletenessRequest
from app.services.profile_completeness_service import calculate_profile_completeness


def _fields(**overrides) -> dict:
    fields = {
        "university_name": "Test University",
        "student_university_number": "12345",
        "specialization": "Computer Science",
        "academic_level": "Senior",
        "career_status": "student",
        "interests": ["data-analysis"],
        "availability": "full_time",
    }
    fields.update(overrides)
    return fields


def test_complete_profile_scores_one_hundred() -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": _fields(),
    })

    result = calculate_profile_completeness(request)

    assert result["algorithm_version"] == "profile-completeness-v1"
    assert result["configuration_version"] == "profile-completeness-config-v1"
    assert result["component_status"] == "available"
    assert result["total_fields_count"] == 7
    assert result["completed_fields_count"] == 7
    assert result["incomplete_fields_count"] == 0
    assert result["profile_completeness_score"] == 100.0


def test_profile_completeness_uses_equal_weights_for_all_seven_fields() -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": _fields(
            academic_level=None,
            career_status="",
            availability="   ",
        ),
    })

    result = calculate_profile_completeness(request)

    assert result["completed_fields_count"] == 4
    assert result["incomplete_fields_count"] == 3
    assert result["profile_completeness_score"] == 57.14


@pytest.mark.parametrize(
    "field_name",
    [
        "university_name",
        "student_university_number",
        "specialization",
        "academic_level",
        "career_status",
        "availability",
    ],
)
def test_each_free_string_field_requires_non_blank_trimmed_value(field_name: str) -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": _fields(**{field_name: "   "}),
    })

    result = calculate_profile_completeness(request)

    assert result["completed_fields_count"] == 6
    assert result["profile_completeness_score"] == 85.71


def test_empty_interests_is_incomplete() -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": _fields(interests=[]),
    })

    result = calculate_profile_completeness(request)

    assert result["completed_fields_count"] == 6
    assert result["profile_completeness_score"] == 85.71


def test_nonempty_interests_is_complete() -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": _fields(interests=[""]),
    })

    result = calculate_profile_completeness(request)

    assert result["completed_fields_count"] == 7
    assert result["profile_completeness_score"] == 100.0


def test_missing_and_null_fields_are_incomplete_not_unavailable() -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": {
            "university_name": None,
            "interests": None,
        },
    })

    result = calculate_profile_completeness(request)

    assert result["component_status"] == "available"
    assert result["completed_fields_count"] == 0
    assert result["incomplete_fields_count"] == 7
    assert result["profile_completeness_score"] == 0.0


def test_profile_completeness_is_deterministic() -> None:
    request = ProfileCompletenessRequest.model_validate({
        "student_profile_id": 123,
        "fields": _fields(career_status=None),
    })

    assert calculate_profile_completeness(request) == calculate_profile_completeness(request)


def test_free_string_fields_reject_values_longer_than_backend_contract() -> None:
    with pytest.raises(ValidationError):
        ProfileCompletenessRequest.model_validate({
            "student_profile_id": 123,
            "fields": _fields(university_name="x" * 101),
        })
