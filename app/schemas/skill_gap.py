from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.skill import SkillLevel


class SkillGapRequest(BaseModel):
    """Represent a request to analyze a user's skill gaps."""

    student_profile_id: int = Field(
        ...,
        gt=0,
        examples=[15],
        description="Backend identifier of the learner's student profile.",
    )

    career_role_id: int = Field(
        ...,
        gt=0,
        examples=[3],
        description="Backend identifier of the target career role.",
    )

    career_role_version: int = Field(
        ...,
        gt=0,
        examples=[1],
        description="Version of the target career role used for this analysis.",
    )

    user_id: int = Field(
        ...,
        gt=0,
        examples=[20],
        description="Backend identifier of the authenticated platform user.",
    )

    target_role: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Data Analyst"],
    )

    skills: list[SkillLevel] = Field(
        ...,
        min_length=1,
    )


class SkillGapResult(BaseModel):
    """Represent the gap analysis result for one skill."""

    skill_id: int = Field(
        ...,
        gt=0,
        examples=[11],
        description="Stable backend identifier of the skill.",
    )

    skill_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Python"],
    )

    current_level: float = Field(
        ...,
        ge=0,
        le=5,
        examples=[3.0],
    )

    required_level: float = Field(
        ...,
        ge=0,
        le=5,
        examples=[4.0],
    )

    importance_weight: float = Field(
        ...,
        gt=0,
        le=1,
        examples=[0.30],
    )

    is_critical: bool = Field(
        ...,
        examples=[True],
        description="Indicates whether the skill is essential for the target role.",
    )

    gap: float = Field(
        ...,
        ge=0,
        le=5,
        examples=[1.0],
    )

    status: Literal["met", "gap"] = Field(
        ...,
        examples=["gap"],
    )


class SkillGapResponse(BaseModel):
    """Represent the complete skill-gap analysis response."""

    student_profile_id: int = Field(
        ...,
        gt=0,
        examples=[15],
    )

    career_role_id: int = Field(
        ...,
        gt=0,
        examples=[3],
    )

    career_role_version: int = Field(
        ...,
        gt=0,
        examples=[1],
    )

    user_id: int = Field(
        ...,
        gt=0,
        examples=[20],
    )

    target_role: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Data Analyst"],
    )

    algorithm_version: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["skill-gap-v1"],
        description="Version of the skill-gap algorithm used for the calculation.",
    )

    base_readiness_score: float = Field(
        ...,
        ge=0,
        le=100,
        examples=[93.88],
        description=(
            "Weighted readiness score before applying critical-skill rules."
        ),
    )

    readiness_score: float = Field(
        ...,
        ge=0,
        le=100,
        examples=[75.0],
    )

    critical_skill_cap_applied: bool = Field(
        ...,
        examples=[True],
        description=(
            "Indicates whether the final readiness score was reduced "
            "because of a major gap in a critical skill."
        ),
    )

    critical_skill_readiness_cap: float | None = Field(
        default=None,
        ge=0,
        le=100,
        examples=[60.0],
        description=(
            "Maximum readiness score allowed when a major critical-skill "
            "gap exists. Null when no critical-skill cap is relevant."
        ),
    )

    critical_skill_gap_count: int = Field(
        ...,
        ge=0,
        examples=[1],
    )

    critical_skill_ids: list[int] = Field(
        default_factory=list,
        examples=[[7]],
        description=(
            "Backend identifiers of critical skills whose gaps reached "
            "the configured major-gap threshold."
        ),
    )

    critical_skill_names: list[str] = Field(
        default_factory=list,
        examples=[["SQL"]],
        description=(
            "Critical skills whose gaps reached the configured major-gap "
            "threshold."
        ),
    )

    total_skills: int = Field(
        ...,
        ge=1,
        examples=[3],
    )

    met_skills: int = Field(
        ...,
        ge=0,
        examples=[1],
    )

    skills_with_gap: int = Field(
        ...,
        ge=0,
        examples=[2],
    )

    skill_results: list[SkillGapResult]
