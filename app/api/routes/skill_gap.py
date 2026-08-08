from fastapi import APIRouter

from app.schemas.skill_gap import SkillGapRequest, SkillGapResponse
from app.services.skill_gap_service import calculate_skill_gap


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

    result = calculate_skill_gap(request)

    return SkillGapResponse.model_validate(result)
