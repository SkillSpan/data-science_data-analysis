from fastapi import APIRouter, HTTPException, status

from app.schemas.baseline import BaselineRequest, BaselineResponse
from app.services.baseline_service import (
    BaselineEvaluationUnavailableError,
    evaluate_baseline,
)


router = APIRouter(
    prefix="/api/v1/baseline",
    tags=["Baseline"],
)


@router.post(
    "",
    response_model=BaselineResponse,
    summary="Evaluate baseline assessment",
    description=(
        "Evaluate a student's baseline assessment and return "
        "skill-level results once the required Backend-owned "
        "assessment mapping is available."
    ),
)
def analyze_baseline(request: BaselineRequest) -> BaselineResponse:
    """Evaluate a student's baseline assessment."""

    try:
        result = evaluate_baseline(request)
    except BaselineEvaluationUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return BaselineResponse.model_validate(result)
