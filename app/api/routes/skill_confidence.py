from fastapi import APIRouter, HTTPException, status

from app.schemas.skill_confidence import (
    SkillConfidenceRequest,
    SkillConfidenceResponse,
)
from app.services.skill_confidence_service import (
    SkillConfidenceError,
    calculate_skill_confidence,
)


router = APIRouter(
    prefix="/api/v1/skill-confidence",
    tags=["Skill Confidence"],
)


@router.post(
    "/calculate",
    response_model=SkillConfidenceResponse,
    summary="Calculate skill confidence",
    description=(
        "Calculate deterministic Skill Confidence v1 from versioned "
        "evidence weights, verification state, and recency factors."
    ),
)
def calculate_skill_confidence_endpoint(
    request: SkillConfidenceRequest,
) -> SkillConfidenceResponse:
    """Calculate confidence for one canonical learner skill."""

    try:
        result = calculate_skill_confidence(request)
    except SkillConfidenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": exc.code,
                "message": str(exc),
            },
        ) from exc

    return SkillConfidenceResponse.model_validate(result)
