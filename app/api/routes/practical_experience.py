from fastapi import APIRouter

from app.schemas.practical_experience import (
    PracticalExperienceRequest,
    PracticalExperienceResponse,
)
from app.services.practical_experience_service import calculate_practical_experience


router = APIRouter(
    prefix="/api/v1/practical-experience",
    tags=["Practical Experience"],
)


@router.post(
    "",
    response_model=PracticalExperienceResponse,
    summary="Calculate practical experience",
    description=(
        "Calculate deterministic Practical Experience v1 from eligible "
        "SkillSpan project participation records."
    ),
)
def calculate_practical_experience_endpoint(
    request: PracticalExperienceRequest,
) -> PracticalExperienceResponse:
    """Calculate Practical Experience v1 for one learner."""

    result = calculate_practical_experience(request)
    return PracticalExperienceResponse.model_validate(result)
