from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AssessmentReliabilitySkill(BaseModel):
    skill_id: int = Field(..., gt=0)
    confidence: float = Field(..., ge=0, le=100)


class AssessmentReliabilityBaseline(BaseModel):
    assessment_id: int = Field(..., gt=0)
    assessment_type: str = Field(..., min_length=1, max_length=100)
    assessment_version: str = Field(..., min_length=1, max_length=50)
    status: Literal["in_progress", "completed"]
    normalized_skills: list[AssessmentReliabilitySkill] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_skill_ids(self) -> "AssessmentReliabilityBaseline":
        skill_ids = [skill.skill_id for skill in self.normalized_skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("normalized_skills must not contain duplicate skill_id values")
        return self


class AssessmentReliabilityRequest(BaseModel):
    student_profile_id: int = Field(..., gt=0)
    assessment: AssessmentReliabilityBaseline | None = None


class AssessmentReliabilityResponse(BaseModel):
    student_profile_id: int = Field(..., gt=0)
    algorithm_version: str = "assessment-reliability-v1"
    configuration_version: str = "assessment-reliability-config-v1"
    component_status: Literal["available", "unavailable"]
    baseline_assessment_id: int | None = Field(default=None, gt=0)
    assessment_version: str | None = Field(default=None, min_length=1, max_length=50)
    assessed_skills_count: int = Field(..., ge=0)
    assessment_reliability_score: float | None = Field(default=None, ge=0, le=100)
