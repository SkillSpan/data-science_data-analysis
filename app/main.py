from fastapi import FastAPI

from app.api.routes.skill_gap import router as skill_gap_router


app = FastAPI(
    title="SkillSpan Intelligence Service",
    description=(
        "Data science, skill analysis, and career intelligence "
        "services for the SkillSpan platform."
    ),
    version="0.1.0",
)


app.include_router(skill_gap_router)


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
