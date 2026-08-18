from pydantic import BaseModel, Field


class SkillLevel(BaseModel):
    """Represent a user's level in a specific skill."""

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
        description=(
            "Normalized importance of the skill for the target career role. "
            "The value must be greater than 0 and less than or equal to 1."
        ),
    )

    is_critical: bool = Field(
        ...,
        examples=[True],
        description=(
            "Indicates whether this skill is essential for the target role. "
            "A major gap in a critical skill may limit the final readiness score."
        ),
    )
