from fastapi import APIRouter, HTTPException, status

from app.schemas.roadmap import RoadmapRequest, RoadmapResponse
from app.services.roadmap_service import RoadmapError, generate_roadmap


router = APIRouter(
    prefix="/api/v1/roadmap",
    tags=["Career Roadmap"],
)


@router.post(
    "",
    response_model=RoadmapResponse,
    summary="Generate a personalized career roadmap",
    description=(
        "Generate deterministic Career Roadmap v1 from one Laravel-provided "
        "learner/role/skill snapshot. Laravel remains the source of truth for "
        "persistence, history, status, and authorization."
    ),
)
def generate_roadmap_endpoint(request: RoadmapRequest) -> RoadmapResponse:
    """Generate one deterministic roadmap result."""

    try:
        result = generate_roadmap(request)
    except RoadmapError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": exc.code,
                "message": str(exc),
            },
        ) from exc

    return RoadmapResponse.model_validate(result)
