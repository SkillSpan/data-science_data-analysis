from pydantic import BaseModel, Field


class SkillLevel(BaseModel):
    """Represent a user's level in a specific skill."""

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
        default=1.0,
        gt=0,
        le=100,
        examples=[25.0],
        description=(
            "Relative importance of the skill for the target career role. "
            "The value does not need to make all weights total 100."
        ),
    )

    is_critical: bool = Field(
    default=False,
    examples=[True],
    description=(
        "Indicates whether this skill is essential for the target role. "
        "A major gap in a critical skill may limit the final readiness score."
        ),
    )