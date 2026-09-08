import os

import httpx
from pydantic import ValidationError

from app.schemas.baseline_mapping import BaselineMappingResponse


BASELINE_ITEMS_PATH = "/api/v1/internal/baseline-items"


class BaselineMappingConfigurationError(RuntimeError):
    """Raised when Backend baseline integration configuration is missing."""


class BaselineMappingUnavailableError(RuntimeError):
    """Raised when the Backend baseline mapping endpoint cannot be reached."""


class BaselineMappingInvalidResponseError(RuntimeError):
    """Raised when the Backend returns an invalid baseline mapping contract."""


def fetch_baseline_mapping(
    assessment_version: str,
    request_id: str | None = None,
) -> BaselineMappingResponse:
    """Fetch and validate one versioned baseline mapping from Laravel."""

    backend_base_url = os.getenv("BACKEND_BASE_URL", "").strip().rstrip("/")
    internal_secret = os.getenv("BASELINE_INTERNAL_SECRET", "").strip()

    if not backend_base_url or not internal_secret:
        raise BaselineMappingConfigurationError(
            "Baseline mapping integration requires BACKEND_BASE_URL and "
            "BASELINE_INTERNAL_SECRET."
        )

    headers = {
        "Accept": "application/json",
        "X-Internal-Secret": internal_secret,
    }

    if request_id:
        headers["X-Request-ID"] = request_id

    try:
        response = httpx.get(
            f"{backend_base_url}{BASELINE_ITEMS_PATH}",
            params={"version": assessment_version},
            headers=headers,
            timeout=5.0,
        )
    except httpx.RequestError as exc:
        raise BaselineMappingUnavailableError(
            "Backend baseline mapping service is unavailable."
        ) from exc

    if response.status_code != 200:
        raise BaselineMappingUnavailableError(
            "Backend baseline mapping service returned an unexpected status."
        )

    try:
        payload = response.json()
        mapping = BaselineMappingResponse.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        raise BaselineMappingInvalidResponseError(
            "Backend baseline mapping response failed contract validation."
        ) from exc

    if mapping.assessment_version != assessment_version:
        raise BaselineMappingInvalidResponseError(
            "Backend baseline mapping assessment_version does not match the request."
        )

    return mapping
