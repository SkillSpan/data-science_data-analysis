from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.baseline import BaselineRequest, BaselineResponse
from app.services.baseline_mapping_client import (
    BaselineMappingConfigurationError,
    BaselineMappingInvalidResponseError,
    BaselineMappingUnavailableError,
    fetch_baseline_mapping,
)
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
    summary="Evaluate baseline assessment",
    description=(
        "Evaluate a student's baseline assessment against the versioned "
        "Backend-owned assessment mapping and return skill-level results."
    ),
)
def analyze_baseline(
    request: BaselineRequest,
    http_request: Request,
) -> BaselineResponse:
    """Evaluate a student's baseline assessment."""

    request_id = getattr(http_request.state, "request_id", None)

    try:
        mapping = fetch_baseline_mapping(
            request.assessment_version,
            request_id=request_id,
        )
        result = evaluate_baseline(request, mapping)
    except (
        BaselineMappingConfigurationError,
        BaselineMappingUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (
        BaselineMappingInvalidResponseError,
        BaselineEvaluationConfigurationError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except BaselineEvaluationInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return BaselineResponse.model_validate(result)
