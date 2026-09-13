from typing import Literal

from pydantic import BaseModel, Field


class PracticalExperienceTeamMember(BaseModel):
    user_id: int = Field(..., gt=0)
    assignment_state: Literal["active", "completed", "removed"]


class PracticalExperienceSubmission(BaseModel):
    submission_id: int = Field(..., gt=0)
    contributor_id: int = Field(..., gt=0)
    status: Literal["submitted", "superseded", "under_review", "accepted"]


class PracticalExperienceEvaluation(BaseModel):
    submission_id: int = Field(..., gt=0)
    status: Literal["draft", "finalized", "moderated", "voided"]


class PracticalExperienceProject(BaseModel):
    project_id: int = Field(..., gt=0)
    project_status: Literal[
        "draft",
        "pending_review",
        "open",
        "closed",
        "in_progress",
        "completed",
        "archived",
    ]
    team_members: list[PracticalExperienceTeamMember] = Field(default_factory=list)
    submissions: list[PracticalExperienceSubmission] = Field(default_factory=list)
    evaluations: list[PracticalExperienceEvaluation] = Field(default_factory=list)


class PracticalExperienceRequest(BaseModel):
    student_profile_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    projects: list[PracticalExperienceProject] = Field(default_factory=list)


class PracticalExperienceResponse(BaseModel):
    student_profile_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    algorithm_version: str = "practical-experience-v1"
    configuration_version: str = "practical-experience-config-v1"
    component_status: Literal["available", "unavailable"]
    eligible_projects_count: int = Field(..., ge=0)
    full_credit_project_count: int = Field(..., gt=0)
    practical_experience_score: float | None = Field(default=None, ge=0, le=100)
    eligible_project_ids: list[int]
