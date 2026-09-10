from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.skill import SkillLevel


class SkillMatchRequest(BaseModel):
    """Represent a request to calculate weighted Skill Match for one role version."""

    student_profile_id: int = Field(..., gt=0)
    career_role_id: int = Field(..., gt=0)
    career_role_version: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    target_role: str = Field(..., min_length=2, max_length=100)
    skills: list[SkillLevel] = Field(..., min_length=1)


class SkillMatchSkillResult(BaseModel):
    """Represent one skill contribution to the weighted Skill Match score."""

    skill_id: int = Field(..., gt=0)
    skill_name: str = Field(..., min_length=2, max_length=100)
    current_level: float = Field(..., ge=0, le=5)
    required_level: float = Field(..., ge=0, le=5)
    importance_weight: float = Field(..., gt=0, le=1)
    normalized_importance_weight: float = Field(..., ge=0, le=1)
    achieved_level: float = Field(..., ge=0, le=5)
    match_ratio: float = Field(..., ge=0, le=1)
    status: Literal["met", "partial", "not_required"]


class SkillMatchResponse(BaseModel):
    """Represent the deterministic weighted Skill Match v1 result."""

    student_profile_id: int = Field(..., gt=0)
    career_role_id: int = Field(..., gt=0)
    career_role_version: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    target_role: str = Field(..., min_length=2, max_length=100)
    algorithm_version: str = "skill-match-v1"
    weight_configuration_version: str = "career-role-config-v1"
    original_weight_total: float = Field(..., gt=0)
    normalized_weight_total: float = Field(..., gt=0, le=1)
    weighted_achieved_total: float = Field(..., ge=0)
    weighted_required_total: float = Field(..., ge=0)
    skill_match_score: float = Field(..., ge=0, le=100)
    total_skills: int = Field(..., ge=1)
    met_skills: int = Field(..., ge=0)
    partial_skills: int = Field(..., ge=0)
    not_required_skills: int = Field(..., ge=0)
    skill_results: list[SkillMatchSkillResult]
