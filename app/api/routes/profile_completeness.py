from fastapi import APIRouter

from app.schemas.profile_completeness import (
    ProfileCompletenessRequest,
    ProfileCompletenessResponse,
)
from app.services.profile_completeness_service import calculate_profile_completeness


router = APIRouter(
    prefix="/api/v1/profile-completeness",
    tags=["Profile Completeness"],
)


@router.post(
    "",
    response_model=ProfileCompletenessResponse,
    summary="Calculate profile completeness",
    description=(
        "Calculate deterministic Profile Completeness v1 from a "
        "Backend-owned StudentProfile snapshot."
    ),
)
def calculate_profile_completeness_endpoint(
    request: ProfileCompletenessRequest,
) -> ProfileCompletenessResponse:
    """Calculate Profile Completeness v1 for one learner."""

    result = calculate_profile_completeness(request)
    return ProfileCompletenessResponse.model_validate(result)
