from app.schemas.assessment_reliability import AssessmentReliabilityRequest


ALGORITHM_VERSION = "assessment-reliability-v1"
CONFIGURATION_VERSION = "assessment-reliability-config-v1"


def calculate_assessment_reliability(
    request: AssessmentReliabilityRequest,
) -> dict[str, object]:
    """Calculate deterministic Assessment Reliability v1."""

    assessment = request.assessment

    if (
        assessment is None
        or assessment.status != "completed"
        or not assessment.normalized_skills
    ):
        return {
            "student_profile_id": request.student_profile_id,
            "algorithm_version": ALGORITHM_VERSION,
            "configuration_version": CONFIGURATION_VERSION,
            "component_status": "unavailable",
            "baseline_assessment_id": assessment.assessment_id if assessment else None,
            "assessment_version": assessment.assessment_version if assessment else None,
            "assessed_skills_count": 0,
            "assessment_reliability_score": None,
        }

    confidences = [skill.confidence for skill in assessment.normalized_skills]
    score = round(sum(confidences) / len(confidences), 2)

    return {
        "student_profile_id": request.student_profile_id,
        "algorithm_version": ALGORITHM_VERSION,
        "configuration_version": CONFIGURATION_VERSION,
        "component_status": "available",
        "baseline_assessment_id": assessment.assessment_id,
        "assessment_version": assessment.assessment_version,
        "assessed_skills_count": len(confidences),
        "assessment_reliability_score": score,
    }
