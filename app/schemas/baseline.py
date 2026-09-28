from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BaselineSkillMapping(BaseModel):
    """Map one assessment question to one measured skill."""

    skill_id: int = Field(..., gt=0)
    skill_slug: str = Field(..., min_length=1, max_length=100)
    weight: float = Field(..., gt=0, le=1)


class BaselineQuestion(BaseModel):
    """Represent one question in the exact Laravel-owned assessment snapshot."""

    question_id: int = Field(..., gt=0, strict=True)
    question_type: Literal["single_choice", "scale"]
    options: list[str] = Field(..., min_length=1)
    correct_answer: str | None = None
    scoring_rule: dict[str, float] | None = None
    weight: float = Field(..., gt=0)
    skill_mappings: list[BaselineSkillMapping] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_question_contract(self) -> "BaselineQuestion":
        if len(self.options) != len(set(self.options)):
            raise ValueError("options must contain unique values")

        skill_ids = [mapping.skill_id for mapping in self.skill_mappings]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError(
                "skill_mappings must not contain duplicate skill_id values "
                "within one question"
            )

        mapping_weight_total = sum(
            mapping.weight for mapping in self.skill_mappings
        )
        if abs(mapping_weight_total - 1.0) > 1e-9:
            raise ValueError(
                "skill_mappings weights must total 1.0 for each question"
            )

        if self.question_type == "single_choice":
            if self.correct_answer is None:
                raise ValueError(
                    "single_choice questions require correct_answer"
                )
            if self.correct_answer not in self.options:
                raise ValueError(
                    "correct_answer must be present in options"
                )
            if self.scoring_rule is not None:
                raise ValueError(
                    "single_choice questions must not define scoring_rule"
                )
            return self

        if self.correct_answer is not None:
            raise ValueError(
                "scale questions must not define correct_answer"
            )

        if not self.scoring_rule:
            raise ValueError("scale questions require scoring_rule")

        if set(self.scoring_rule) != set(self.options):
            raise ValueError(
                "scale scoring_rule keys must match options exactly"
            )

        if any(
            score < 0 or score > 1
            for score in self.scoring_rule.values()
        ):
            raise ValueError(
                "scale scoring_rule values must be between 0 and 1"
            )

        return self


class BaselineQuestionResponse(BaseModel):
    """Represent one answered question in the assessment snapshot."""

    question_id: int = Field(..., gt=0, strict=True)
    answer: str = Field(..., min_length=1, max_length=1000)


class BaselineRequest(BaseModel):
    """Represent one dynamic baseline assessment request from Laravel."""

    student_profile_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    career_role_id: int = Field(..., gt=0)
    assessment_version: str = Field(..., min_length=1, max_length=100)
    questions: list[BaselineQuestion] = Field(..., min_length=1)
    responses: list[BaselineQuestionResponse] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_assessment_snapshot(self) -> "BaselineRequest":
        question_ids = [
            question.question_id for question in self.questions
        ]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError(
                "questions must contain unique question_id values"
            )

        response_ids = [
            response.question_id for response in self.responses
        ]
        if len(response_ids) != len(set(response_ids)):
            raise ValueError(
                "responses must contain unique question_id values"
            )

        unknown_response_ids = sorted(
            set(response_ids) - set(question_ids)
        )
        if unknown_response_ids:
            raise ValueError(
                "responses contain question_id values that are not present "
                "in the assessment snapshot"
            )

        slug_by_skill: dict[int, str] = {}
        for question in self.questions:
            for mapping in question.skill_mappings:
                existing_slug = slug_by_skill.get(mapping.skill_id)
                if (
                    existing_slug is not None
                    and existing_slug != mapping.skill_slug
                ):
                    raise ValueError(
                        "assessment snapshot contains inconsistent "
                        f"skill_slug values for skill_id {mapping.skill_id}"
                    )
                slug_by_skill[mapping.skill_id] = mapping.skill_slug

        return self


class BaselineSkillResult(BaseModel):
    """Represent one skill actually measured by answered questions."""

    skill_id: int = Field(..., gt=0)
    slug: str = Field(..., min_length=1, max_length=100)
    level: float = Field(..., ge=0, le=5)
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Coverage confidence for this assessment snapshot: 0..1.",
    )


class BaselineResponse(BaseModel):
    """Represent a dynamic baseline assessment result."""

    algorithm_version: str = Field(..., min_length=1, max_length=100)
    assessment_version: str = Field(..., min_length=1, max_length=100)
    career_role_id: int = Field(..., gt=0)
    student_profile_id: int = Field(..., gt=0)
    overall_score: float = Field(..., ge=0, le=100)
    skills: list[BaselineSkillResult] = Field(..., min_length=1)
