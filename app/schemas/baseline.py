from pydantic import BaseModel, Field, model_validator


class BaselineItemResponse(BaseModel):
    """Represent one answered baseline assessment item."""

    item_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["sql-001"],
        description="Stable item identifier within the assessment version.",
    )

    answer: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        examples=["B"],
        description="Baseline v1 answer value. Multi-select values are not supported.",
    )


class BaselineRequest(BaseModel):
    """Represent a baseline assessment evaluation request from Laravel."""

    student_profile_id: int = Field(
        ...,
        gt=0,
        examples=[1],
    )

    user_id: int = Field(
        ...,
        gt=0,
        examples=[2],
    )

    assessment_version: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["v1.0"],
    )

    responses: list[BaselineItemResponse] = Field(
        ...,
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_unique_item_ids(self) -> "BaselineRequest":
        """Require each item identifier to appear once per assessment request."""

        item_ids = [item.item_id for item in self.responses]

        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                "responses must contain unique item_id values within "
                "the assessment_version"
            )

        return self


class BaselineSkillResult(BaseModel):
    """Represent one skill result produced by the baseline evaluation."""

    skill_id: int = Field(
        ...,
        gt=0,
        examples=[7],
    )

    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["sql"],
    )

    level: float = Field(
        ...,
        ge=0,
        le=5,
        examples=[2.5],
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        examples=[0.7],
        description="Transport confidence scale required by Laravel: 0..1.",
    )


class BaselineResponse(BaseModel):
    """Represent the complete baseline evaluation response."""

    algorithm_version: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["baseline-v1.0"],
    )

    student_profile_id: int = Field(
        ...,
        gt=0,
        examples=[1],
    )

    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        examples=[60.0],
    )

    skills: list[BaselineSkillResult] = Field(
        ...,
        min_length=1,
    )
