from fastapi import APIRouter, HTTPException, status

from app.schemas.skill_match import SkillMatchRequest, SkillMatchResponse
from app.services.skill_match_service import SkillMatchError, calculate_skill_match


router = APIRouter(
    prefix="/api/v1/skill-match",
    tags=["Skill Match"],
)


@router.post(
    "",
    response_model=SkillMatchResponse,
    summary="Calculate weighted skill match",
    description=(
        "Calculate deterministic weighted Skill Match v1 for a learner "
        "against one versioned target career role."
    ),
)
def calculate_skill_match_endpoint(
    request: SkillMatchRequest,
) -> SkillMatchResponse:
    """Calculate Skill Match for one learner and target role version."""

    try:
        result = calculate_skill_match(request)
    except SkillMatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": exc.code,
                "message": str(exc),
            },
        ) from exc

    return SkillMatchResponse.model_validate(result)
