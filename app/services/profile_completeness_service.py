from app.schemas.profile_completeness import ProfileCompletenessRequest


ALGORITHM_VERSION = "profile-completeness-v1"
CONFIGURATION_VERSION = "profile-completeness-config-v1"

_TEXT_FIELD_NAMES = (
    "university_name",
    "student_university_number",
    "specialization",
    "academic_level",
    "career_status",
    "availability",
)
TOTAL_FIELDS_COUNT = 7


def _is_non_blank_text(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def calculate_profile_completeness(
    request: ProfileCompletenessRequest,
) -> dict[str, object]:
    """Calculate deterministic Profile Completeness v1."""

    fields = request.fields

    completed_fields_count = sum(
        1
        for field_name in _TEXT_FIELD_NAMES
        if _is_non_blank_text(getattr(fields, field_name))
    )

    if fields.interests is not None and len(fields.interests) > 0:
        completed_fields_count += 1

    incomplete_fields_count = TOTAL_FIELDS_COUNT - completed_fields_count
    score = round((completed_fields_count / TOTAL_FIELDS_COUNT) * 100, 2)

    return {
        "student_profile_id": request.student_profile_id,
        "algorithm_version": ALGORITHM_VERSION,
        "configuration_version": CONFIGURATION_VERSION,
        "component_status": "available",
        "total_fields_count": TOTAL_FIELDS_COUNT,
        "completed_fields_count": completed_fields_count,
        "incomplete_fields_count": incomplete_fields_count,
        "profile_completeness_score": score,
    }
