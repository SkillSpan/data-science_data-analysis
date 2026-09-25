import logging
import os
from hmac import compare_digest
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.baseline import router as baseline_router
from app.api.routes.assessment_reliability import router as assessment_reliability_router
from app.api.routes.career_role_configuration import router as career_role_configuration_router
from app.api.routes.practical_experience import router as practical_experience_router
from app.api.routes.profile_completeness import router as profile_completeness_router
from app.api.routes.skill_gap import router as skill_gap_router
from app.api.routes.skill_match import router as skill_match_router
from app.api.routes.skill_confidence import router as skill_confidence_router


logger = logging.getLogger("uvicorn.error")


app = FastAPI(
    title="SkillSpan Intelligence Service",
    description=(
        "Data science, skill analysis, and career intelligence "
        "services for the SkillSpan platform."
    ),
    version="0.1.0",
)


def _validate_service_token(request: Request) -> JSONResponse | None:
    """Validate Laravel-to-FastAPI service authentication for API routes."""

    if not request.url.path.startswith("/api/v1/"):
        return None

    expected_token = os.getenv("DATA_SCIENCE_SERVICE_TOKEN", "").strip()

    if not expected_token:
        return JSONResponse(
            status_code=503,
            content={"detail": "Data Science service authentication is not configured."},
        )

    authorization = request.headers.get("Authorization", "")
    scheme, separator, provided_token = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not provided_token
        or not compare_digest(provided_token.strip().encode("utf-8"), expected_token.encode("utf-8"))
    ):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing service authentication token."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return None


@app.middleware("http")
async def service_token_middleware(request: Request, call_next):
    """Protect all versioned FastAPI endpoints with the shared service token."""

    authentication_error = _validate_service_token(request)

    if authentication_error is not None:
        return authentication_error

    return await call_next(request)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Preserve or generate a request ID for tracing and correlation."""

    request_id = request.headers.get("X-Request-ID")

    if request_id:
        request_id = request_id.strip()

    if not request_id:
        request_id = str(uuid4())

    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed request_id=%s method=%s path=%s status=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
    )

    return response


app.include_router(skill_gap_router)
app.include_router(assessment_reliability_router)
app.include_router(practical_experience_router)
app.include_router(profile_completeness_router)
app.include_router(skill_match_router)
app.include_router(baseline_router)
app.include_router(career_role_configuration_router)
app.include_router(skill_confidence_router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Return the current service status."""

    return {
        "status": "healthy",
        "service": "skillspan-intelligence-service",
        "version": "0.1.0",
    }


@app.get("/welcome", tags=["System"])
def welcome() -> dict[str, str]:
    """Return a welcome message for the SkillSpan service."""

    return {
        "message": "Welcome to SkillSpan",
    }
