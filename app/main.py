import logging
from uuid import uuid4

from fastapi import FastAPI, Request

from app.api.routes.baseline import router as baseline_router
from app.api.routes.career_role_configuration import router as career_role_configuration_router
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
