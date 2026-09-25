from fastapi import APIRouter, HTTPException, status

from app.schemas.project_matching import (
    ProjectMatchingRequest,
    ProjectMatchingResponse,
)
from app.services.project_matching_service import (
    ProjectMatchingError,
    calculate_project_match,
)


router = APIRouter(
    prefix="/api/v1/project-matching",
    tags=["Project Matching"],
)


@router.post(
    "",
    response_model=ProjectMatchingResponse,
    summary="Calculate project matching recommendation",
    description=(
        "Calculate deterministic Project Matching v1 for one Laravel-provided "
        "learner/project matching snapshot."
    ),
)
def calculate_project_matching_endpoint(
    request: ProjectMatchingRequest,
) -> ProjectMatchingResponse:
    """Calculate one deterministic project recommendation."""

    try:
        result = calculate_project_match(request)
    except ProjectMatchingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": exc.code,
                "message": str(exc),
            },
        ) from exc

    return ProjectMatchingResponse.model_validate(result)