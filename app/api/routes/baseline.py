from fastapi import APIRouter, HTTPException, status

from app.schemas.baseline import BaselineRequest, BaselineResponse
from app.services.baseline_service import (
    BaselineEvaluationConfigurationError,
    BaselineEvaluationInputError,
    evaluate_baseline,
)


router = APIRouter(
    prefix="/api/v1/baseline",
    tags=["Baseline"],
)


@router.post(
    "",
    response_model=BaselineResponse,
    summary="Evaluate dynamic baseline assessment",
    description=(
        "Evaluate the exact Laravel-owned baseline assessment snapshot "
        "submitted in the request and return only skills actually measured."
    ),
)
def analyze_baseline(
    request: BaselineRequest,
) -> BaselineResponse:
    """Evaluate one dynamic baseline assessment snapshot."""

    try:
        result = evaluate_baseline(request)
    except (
        BaselineEvaluationInputError,
        BaselineEvaluationConfigurationError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return BaselineResponse.model_validate(result)
