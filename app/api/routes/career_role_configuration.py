from fastapi import APIRouter, HTTPException, status

from app.schemas.career_role_configuration import (
    CareerRoleConfigurationRequest,
    CareerRoleConfigurationValidationResponse,
)
from app.services.career_role_configuration_service import (
    CareerRoleConfigurationError,
    validate_career_role_configuration,
)


router = APIRouter(
    prefix="/api/v1/career-role-configuration",
    tags=["Career Role Configuration"],
)


@router.post(
    "/validate",
    response_model=CareerRoleConfigurationValidationResponse,
    summary="Validate career role configuration",
    description=(
        "Validate role metadata, skills, importance weights, "
        "critical flags, and prerequisite relationships."
    ),
)
def validate_career_role_configuration_endpoint(
    request: CareerRoleConfigurationRequest,
) -> CareerRoleConfigurationValidationResponse:
    """Validate a Laravel-owned career-role configuration."""

    try:
        result = validate_career_role_configuration(request)
    except CareerRoleConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return CareerRoleConfigurationValidationResponse.model_validate(result)
