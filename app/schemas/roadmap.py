from typing import Literal

from pydantic import BaseModel, Field, model_validator


RoadmapActionType = Literal[
    "assessment",
    "resource",
    "practice",
    "simulated_project",
    "real_project",
]

RoadmapPhaseName = Literal[
    "foundations",
    "core_skills",
    "applied_practice",
    "career_readiness",
]


class RoadmapLearnerSnapshot(BaseModel):
    """Represent the learner fields required for deterministic roadmap generation."""

    student_profile_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    availability: str | None = Field(default=None, max_length=100)
    weekly_availability_hours: float | None = Field(default=None, gt=0, le=168)


class RoadmapRoleSnapshot(BaseModel):
    """Represent the approved target career role selected by Laravel."""

    id: int = Field(..., gt=0)
    title: str = Field(..., min_length=2, max_length=150)
    version: int = Field(..., gt=0)


class RoadmapSkillSnapshot(BaseModel):
    """Represent one required role skill in the Laravel decision snapshot."""

    skill_id: int = Field(..., gt=0)
    skill_name: str = Field(..., min_length=2, max_length=100)
    current_level: float = Field(..., ge=0, le=5)
    required_level: float = Field(..., ge=0, le=5)
    importance_weight: float = Field(..., gt=0, le=1)
    is_critical: bool
    confidence: float = Field(..., ge=0, le=1)
    prerequisite_skill_ids: list[int] = Field(default_factory=list)
    market_demand_factor: float | None = Field(default=None, gt=0, le=2)

    @model_validator(mode="after")
    def validate_prerequisites(self) -> "RoadmapSkillSnapshot":
        if self.skill_id in self.prerequisite_skill_ids:
            raise ValueError("A roadmap skill cannot depend on itself.")
        if len(self.prerequisite_skill_ids) != len(set(self.prerequisite_skill_ids)):
            raise ValueError("Duplicate prerequisite skill ids are not allowed.")
        if any(skill_id <= 0 for skill_id in self.prerequisite_skill_ids):
            raise ValueError("Prerequisite skill ids must be positive integers.")
        return self


class RoadmapRequest(BaseModel):
    """Represent the authoritative Laravel snapshot used to generate Roadmap v1."""

    learner: RoadmapLearnerSnapshot
    role: RoadmapRoleSnapshot
    skills: list[RoadmapSkillSnapshot] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_unique_skills(self) -> "RoadmapRequest":
        skill_ids = [skill.skill_id for skill in self.skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Duplicate skill ids are not allowed in a roadmap request.")
        return self


class RoadmapAction(BaseModel):
    """Represent one deterministic roadmap action."""

    action_id: str = Field(..., min_length=1, max_length=100)
    action_type: RoadmapActionType
    title: str = Field(..., min_length=2, max_length=200)
    objective: str = Field(..., min_length=2, max_length=500)
    target_skill_id: int = Field(..., gt=0)
    target_skill_name: str = Field(..., min_length=2, max_length=100)
    prerequisite_skill_ids: list[int] = Field(default_factory=list)
    blocking_prerequisite_skill_ids: list[int] = Field(default_factory=list)
    priority_score: float = Field(..., ge=0, le=1)
    estimated_hours: float = Field(..., gt=0)
    estimated_duration_weeks: int | None = Field(default=None, gt=0)
    completion_criteria: list[str] = Field(..., min_length=1)
    explanation: list[str] = Field(..., min_length=1)


class RoadmapPhase(BaseModel):
    """Represent one of the four SRS roadmap phases."""

    phase: RoadmapPhaseName
    order: int = Field(..., ge=1, le=4)
    actions: list[RoadmapAction] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    """Represent deterministic Career Roadmap v1 output."""

    student_profile_id: int = Field(..., gt=0)
    career_role_id: int = Field(..., gt=0)
    career_role_version: int = Field(..., gt=0)
    algorithm_version: str = "roadmap-v1"
    configuration_version: str = "roadmap-config-v1"
    estimated_total_hours: float = Field(..., ge=0)
    estimated_duration_weeks: int | None = Field(default=None, ge=0)
    phases: list[RoadmapPhase]
    next_best_action_id: str | None = None
    limitations: list[str] = Field(default_factory=list)
