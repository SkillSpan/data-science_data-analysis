from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.skill_match import SkillMatchRequest
from app.schemas.skill import SkillLevel


class ReadinessPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    version: Literal["readiness-policy-srs13-v1"] = "readiness-policy-srs13-v1"
    skill_match: float = Field(default=0.65, ge=0, le=1)
    practical_experience: float = Field(default=0.20, ge=0, le=1)
    assessment_reliability: float = Field(default=0.10, ge=0, le=1)
    profile_completeness: float = Field(default=0.05, ge=0, le=1)
    critical_minimum_match: float = Field(default=0.50, ge=0, le=1)
    critical_cap: float = Field(default=69, ge=0, le=100)

    @model_validator(mode="after")
    def positive_weights(self):
        if sum(getattr(self, name) for name in COMPONENT_NAMES) <= 0:
            raise ValueError("Component weights must have a positive total.")
        return self


COMPONENT_NAMES = (
    "skill_match", "practical_experience", "assessment_reliability", "profile_completeness"
)


class ReadinessSkill(SkillLevel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    importance_weight: float = Field(..., ge=0, le=1)


class ReadinessRequest(SkillMatchRequest):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    skills: list[ReadinessSkill] = Field(..., min_length=1)
    policy: ReadinessPolicy = Field(default_factory=ReadinessPolicy)
    practical_experience: float | None = Field(default=None, ge=0, le=100)
    assessment_reliability: float | None = Field(default=None, ge=0, le=100)
    profile_completeness: float | None = Field(default=None, ge=0, le=100)
