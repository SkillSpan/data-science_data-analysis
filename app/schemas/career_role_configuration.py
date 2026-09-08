from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class CareerRoleSkillConfiguration(BaseModel):
    """Represent one required skill in a versioned career role."""

    skill_id: int = Field(..., gt=0)
    skill_name: str = Field(..., min_length=2, max_length=100)
    required_level: float = Field(..., ge=0, le=5)
    importance_weight: float = Field(..., gt=0, le=1)
    is_critical: bool
    prerequisite_skill_id: int | None = Field(default=None, gt=0)


class CareerRoleConfigurationRequest(BaseModel):
    """Represent a versioned career-role configuration owned by Laravel."""

    career_role_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=100)
    version: int = Field(..., gt=0)
    status: Literal["draft", "approved", "retired"]
    effective_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)
    skills: list[CareerRoleSkillConfiguration] = Field(..., min_length=1)


class NormalizedCareerRoleSkill(BaseModel):
    """Represent a validated role skill with its normalized weight."""

    skill_id: int
    normalized_importance_weight: float = Field(..., ge=0, le=1)
    prerequisite_skill_id: int | None = None


class CareerRoleConfigurationValidationResponse(BaseModel):
    """Represent the deterministic validation result for a role version."""

    configuration_version: str = "career-role-config-v1"
    career_role_id: int
    career_role_version: int
    status: Literal["draft", "approved", "retired"]
    original_weight_total: float = Field(..., gt=0)
    normalized_weight_total: float = Field(..., gt=0, le=1)
    production_eligible: bool
    prerequisite_order: list[int]
    skills: list[NormalizedCareerRoleSkill]
