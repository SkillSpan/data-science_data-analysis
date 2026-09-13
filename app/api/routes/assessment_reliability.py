from fastapi import APIRouter

from app.schemas.assessment_reliability import (
    AssessmentReliabilityRequest,
    AssessmentReliabilityResponse,
)
from app.services.assessment_reliability_service import calculate_assessment_reliability


router = APIRouter(
    prefix="/api/v1/assessment-reliability",
    tags=["Assessment Reliability"],
)


@router.post(
    "",
    response_model=AssessmentReliabilityResponse,
    summary="Calculate assessment reliability",
    description=(
        "Calculate deterministic Assessment Reliability v1 from a Backend-owned "
        "BaselineAssessment normalized-skills snapshot."
    ),
)
def calculate_assessment_reliability_endpoint(
    request: AssessmentReliabilityRequest,
) -> AssessmentReliabilityResponse:
    """Calculate Assessment Reliability v1 for one learner."""

    result = calculate_assessment_reliability(request)
    return AssessmentReliabilityResponse.model_validate(result)
