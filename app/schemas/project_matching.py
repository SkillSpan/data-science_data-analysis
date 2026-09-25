from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


InterestValue = Annotated[str, Field(min_length=1, max_length=100)]


class ProjectMatchingCurrentSkill(BaseModel):
    """Represent one learner skill supplied by the Laravel matching snapshot."""

    skill_id: int = Field(..., gt=0)
    level: float = Field(..., ge=0, le=5)
    required_level: float = Field(..., ge=0, le=5)
    meets_requirement: bool


class ProjectMatchingCareerRole(BaseModel):
    """Represent optional target-career-role context supplied by Laravel."""

    id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=150)
    version: int = Field(..., gt=0)


class ProjectMatchingLearner(BaseModel):
    """Represent learner context from ProjectMatchingPayloadBuilder."""

    user_id: int = Field(..., gt=0)
    student_profile_id: int = Field(..., gt=0)

    current_skills: list[ProjectMatchingCurrentSkill] = Field(
        default_factory=list,
    )

    availability: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    preferred_work_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    target_career_role: ProjectMatchingCareerRole | None = None

    interests: list[InterestValue] | None = None


class ProjectMatchingProject(BaseModel):
    """Represent one project candidate from the Laravel matching snapshot."""

    id: int = Field(..., gt=0)
    version: int = Field(..., gt=0)

    type: Literal[
        "simulation",
        "company_sponsored",
    ]

    domain: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    difficulty: float | None = Field(
        default=None,
        ge=0,
    )

    work_mode: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    role: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    schedule: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    organization_id: int | None = Field(
        default=None,
        gt=0,
    )

    confidentiality: Literal[
        "public",
        "restricted",
    ]


class ProjectMatchingRequiredSkill(BaseModel):
    """Represent one project skill requirement."""

    skill_id: int = Field(..., gt=0)

    skill_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    minimum_level: float = Field(
        ...,
        ge=0,
        le=5,
    )

    is_critical_entry: bool


class ProjectMatchingEligibilityConstraint(BaseModel):
    """Represent one non-skill eligibility constraint supplied by Laravel."""

    type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    value: str

    blocking: bool = False


class ProjectMatchingSkillFailure(BaseModel):
    """Represent one skill eligibility failure supplied by Laravel."""

    skill_id: int | None = Field(
        default=None,
        gt=0,
    )

    required_level: float | None = Field(
        default=None,
        ge=0,
        le=5,
    )

    learner_level: float | None = Field(
        default=None,
        ge=0,
        le=5,
    )

    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )


class ProjectMatchingValidation(BaseModel):
    """Represent authoritative validation state already calculated by Laravel."""

    eligibility_state: Literal[
        "eligible",
        "not_eligible",
    ]

    validation_state: Literal[
        "validated",
        "not_validated",
    ]

    constraints: list[
        ProjectMatchingEligibilityConstraint
        | ProjectMatchingSkillFailure
    ] = Field(default_factory=list)

    skill_gaps: list[ProjectMatchingSkillFailure] = Field(
        default_factory=list,
    )

    eligibility_reasons: list[str] | None = None

    authorization: str | None = Field(
        default=None,
        max_length=100,
    )


class ProjectMatchingRequest(BaseModel):
    """Represent the Laravel ProjectMatchingPayloadBuilder-compatible payload."""

    request_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    algorithm_version: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    configuration_version: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    project_version: int = Field(
        ...,
        gt=0,
    )

    learner: ProjectMatchingLearner

    project: ProjectMatchingProject

    required_skills: list[
        ProjectMatchingRequiredSkill
    ] = Field(default_factory=list)

    validation: ProjectMatchingValidation


class ProjectMatchingWeights(BaseModel):
    """Represent configurable Project Matching factor weights."""

    skill_compatibility: float = Field(
        default=0.35,
        ge=0,
        le=1,
    )

    learning_value: float = Field(
        default=0.25,
        ge=0,
        le=1,
    )

    career_relevance: float = Field(
        default=0.20,
        ge=0,
        le=1,
    )

    interest_match: float = Field(
        default=0.10,
        ge=0,
        le=1,
    )

    availability_fit: float = Field(
        default=0.10,
        ge=0,
        le=1,
    )

    @model_validator(mode="after")
    def validate_total_weight(self):
        total = (
            self.skill_compatibility
            + self.learning_value
            + self.career_relevance
            + self.interest_match
            + self.availability_fit
        )

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                "Project Matching scoring weights must total 1.0."
            )

        return self


class ProjectMatchingConfiguration(BaseModel):
    """Represent one deterministic, versioned Project Matching configuration."""

    algorithm_version: str = Field(
        default="project-matching-v1",
        min_length=1,
    )

    configuration_version: str = Field(
        default="project-matching-config-v1",
        min_length=1,
    )

    weights: ProjectMatchingWeights = Field(
        default_factory=ProjectMatchingWeights,
    )

    manageable_gap_max: float = Field(
        default=1.0,
        gt=0,
        le=5,
    )

    optional_factor_fallback_score: float = Field(
        default=50.0,
        ge=0,
        le=100,
    )

    critical_entry_is_hard_constraint: Literal[True] = True

class ProjectMatchingSkillResult(BaseModel):
    """Represent one deterministic project-skill compatibility result."""

    skill_id: int = Field(..., gt=0)

    skill_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    current_level: float = Field(
        ...,
        ge=0,
        le=5,
    )

    minimum_level: float = Field(
        ...,
        ge=0,
        le=5,
    )

    gap: float = Field(
        ...,
        ge=0,
        le=5,
    )

    match_ratio: float = Field(
        ...,
        ge=0,
        le=1,
    )

    is_critical_entry: bool

    status: Literal[
        "not_required",
        "met",
        "manageable_gap",
        "large_gap",
        "missing_non_critical",
        "missing_critical",
        "critical_below_minimum",
    ]


class ProjectMatchingFactorScores(BaseModel):
    """Represent the deterministic component scores before weighting."""

    skill_compatibility: float = Field(..., ge=0, le=100)
    learning_value: float = Field(..., ge=0, le=100)
    career_relevance: float = Field(..., ge=0, le=100)
    interest_match: float = Field(..., ge=0, le=100)
    availability_fit: float = Field(..., ge=0, le=100)


class ProjectMatchingWeightedContributions(BaseModel):
    """Represent each factor's contribution to the final 0-100 score."""

    skill_compatibility: float = Field(..., ge=0, le=100)
    learning_value: float = Field(..., ge=0, le=100)
    career_relevance: float = Field(..., ge=0, le=100)
    interest_match: float = Field(..., ge=0, le=100)
    availability_fit: float = Field(..., ge=0, le=100)


class ProjectRecommendationResult(BaseModel):
    """Represent one deterministic project recommendation result."""

    project_id: int = Field(..., gt=0)
    project_version: int = Field(..., gt=0)

    eligibility_state: Literal[
        "eligible",
        "ineligible",
    ]

    matching_state: Literal[
        "scored",
        "blocked",
    ]

    score: float = Field(..., ge=0, le=100)

    factor_scores: ProjectMatchingFactorScores

    weighted_contributions: ProjectMatchingWeightedContributions

    explanation: list[str] = Field(
        default_factory=list,
    )

    limiting_factors: list[str] = Field(
        default_factory=list,
    )

    skill_results: list[ProjectMatchingSkillResult] = Field(
        default_factory=list,
    )


class ProjectMatchingResponse(BaseModel):
    """Represent the deterministic Project Matching v1 API response."""

    request_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    algorithm_version: str = Field(
        default="project-matching-v1",
        min_length=1,
    )

    configuration_version: str = Field(
        default="project-matching-config-v1",
        min_length=1,
    )

    recommendation: ProjectRecommendationResult