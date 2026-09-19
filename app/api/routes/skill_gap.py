from fastapi import APIRouter, HTTPException, status

from app.schemas.skill_gap import SkillGapRequest, SkillGapResponse
from app.services.skill_gap_service import SkillGapError, calculate_skill_gap


router = APIRouter(
    prefix="/api/v1/skill-gap",
    tags=["Skill Gap"],
)


@router.post(
    "",
    response_model=SkillGapResponse,
    summary="Analyze user skill gaps",
    description=(
        "Compare the user's current skill levels with the levels required "
        "for a target career role and calculate the readiness score."
    ),
)
def analyze_skill_gap(request: SkillGapRequest) -> SkillGapResponse:
    """Analyze a user's skills against a target career role."""

    try:
        result = calculate_skill_gap(request)
    except SkillGapError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc

    return SkillGapResponse.model_validate(result)
