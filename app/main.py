from fastapi import FastAPI

from app.api.routes.skill_gap import router as skill_gap_router


app = FastAPI(
    title="SkillBridge Intelligence Service",
    description=(
        "Data science, skill analysis, and career intelligence "
        "services for the SkillBridge platform."
    ),
    version="0.1.0",
)


app.include_router(skill_gap_router)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Return the current service status."""

    return {
        "status": "healthy",
        "service": "skillbridge-intelligence-service",
        "version": "0.1.0",
    }


@app.get("/welcome", tags=["System"])
def welcome() -> dict[str, str]:
    """Return a welcome message for the SkillBridge service."""

    return {
        "message": "Welcome to SkillBridge",
    }