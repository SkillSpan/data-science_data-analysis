from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileCompletenessFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    university_name: str | None = Field(default=None, max_length=100)
    student_university_number: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=100)
    academic_level: str | None = Field(default=None, max_length=100)
    career_status: str | None = Field(default=None, max_length=100)
    interests: list[str] | None = None
    availability: str | None = Field(default=None, max_length=100)


class ProfileCompletenessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_profile_id: int = Field(..., gt=0)
    fields: ProfileCompletenessFields


class ProfileCompletenessResponse(BaseModel):
    student_profile_id: int = Field(..., gt=0)
    algorithm_version: str = "profile-completeness-v1"
    configuration_version: str = "profile-completeness-config-v1"
    component_status: Literal["available"]
    total_fields_count: int = Field(..., ge=0)
    completed_fields_count: int = Field(..., ge=0)
    incomplete_fields_count: int = Field(..., ge=0)
    profile_completeness_score: float = Field(..., ge=0, le=100)
