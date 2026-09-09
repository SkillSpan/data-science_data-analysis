from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


EvidenceSource = Literal[
    "self_assessment",
    "assessment_test",
    "project_performance",
    "expert_evaluation",
    "certificate",
]

VerificationStatus = Literal[
    "pending",
    "verified",
    "rejected",
    "expired",
]

ConfidenceBand = Literal["low", "moderate", "good", "high"]


class SkillConfidenceEvidence(BaseModel):
    """Represent one evidence record used to support skill confidence."""

    source: EvidenceSource

    verification_status: VerificationStatus

    evidence_date: date = Field(
        ...,
        description="Required Backend evidence date used for analytical traceability.",
    )

    recency_factor: float = Field(
        ...,
        ge=0,
        le=1,
        examples=[1.0],
        description="Versioned v1 recency factor supplied with the evidence snapshot.",
    )

    reference: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Fallback evidence identity when canonical source-record identity is unavailable.",
    )

    source_record_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    source_record_id: int | None = Field(
        default=None,
        gt=0,
    )

    @model_validator(mode="after")
    def validate_canonical_identity_pair(self) -> "SkillConfidenceEvidence":
        has_type = self.source_record_type is not None
        has_id = self.source_record_id is not None

        if has_type != has_id:
            raise ValueError(
                "source_record_type and source_record_id must be provided together."
            )

        return self


class SkillConfidenceRequest(BaseModel):
    """Represent a request to calculate confidence for one canonical skill."""

    student_profile_id: int = Field(
        ...,
        gt=0,
        examples=[15],
    )

    skill_id: int = Field(
        ...,
        gt=0,
        examples=[7],
    )

    evidence: list[SkillConfidenceEvidence] = Field(
        default_factory=list,
    )


class ConfidenceSourceContribution(BaseModel):
    """Explain the analytical confidence contribution of one evidence source."""

    source: EvidenceSource

    configured_weight: float = Field(..., ge=0, le=1)

    evidence_records: int = Field(..., ge=1)

    source_support_factor: float = Field(..., ge=0, le=1)

    confidence_contribution: float = Field(..., ge=0, le=100)


class SkillConfidenceResponse(BaseModel):
    """Represent the deterministic Skill Confidence v1 result."""

    student_profile_id: int = Field(..., gt=0)

    skill_id: int = Field(..., gt=0)

    status: Literal["calculated", "no_evidence"]

    confidence_score: float = Field(..., ge=0, le=100)

    confidence_band: ConfidenceBand

    confidence_algorithm_version: str = Field(
        default="skill-confidence-v1",
    )

    evidence_weight_config_version: str = Field(
        default="evidence-weights-v1",
    )

    verification_config_version: str = Field(
        default="evidence-verification-v1",
    )

    recency_config_version: str = Field(
        default="evidence-recency-v1",
    )

    configured_weight_total: float = Field(..., gt=0)

    duplicate_evidence_detected: bool

    duplicate_evidence_count: int = Field(..., ge=0)

    distinct_evidence_count: int = Field(..., ge=0)

    source_contributions: list[ConfidenceSourceContribution] = Field(
        default_factory=list,
    )
