from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BaselineMappingItem(BaseModel):
    # Backend-owned baseline assessment item definition.

    item_id: str = Field(..., min_length=1, max_length=100)
    item_type: Literal['single_choice', 'scale']
    options: list[str] = Field(..., min_length=1)
    correct_answer: str | None = None
    scoring_rule: dict[str, float] | None = None
    skill_id: int = Field(..., gt=0)
    skill_slug: str = Field(..., min_length=1, max_length=100)
    weight: float = Field(..., ge=0, le=1)

    @model_validator(mode='after')
    def validate_item_scoring_contract(self) -> 'BaselineMappingItem':
        if len(self.options) != len(set(self.options)):
            raise ValueError('options must contain unique values')

        if self.item_type == 'single_choice':
            if self.correct_answer is None:
                raise ValueError('single_choice items require correct_answer')
            if self.correct_answer not in self.options:
                raise ValueError('correct_answer must be present in options')
            if self.scoring_rule is not None:
                raise ValueError(
                    'single_choice items must not define scoring_rule'
                )
            return self

        if self.correct_answer is not None:
            raise ValueError('scale items must not define correct_answer')

        if not self.scoring_rule:
            raise ValueError('scale items require scoring_rule')

        if set(self.scoring_rule) != set(self.options):
            raise ValueError(
                'scale scoring_rule keys must match options exactly'
            )

        if any(
            score < 0 or score > 1
            for score in self.scoring_rule.values()
        ):
            raise ValueError(
                'scale scoring_rule values must be between 0 and 1'
            )

        return self


class BaselineMappingResponse(BaseModel):
    # Versioned baseline item mapping returned by Laravel.

    success: bool
    assessment_version: str = Field(..., min_length=1, max_length=50)
    weight_scale: Literal['0..1']
    items: list[BaselineMappingItem] = Field(..., min_length=1)

    @model_validator(mode='after')
    def validate_mapping_response(self) -> 'BaselineMappingResponse':
        if not self.success:
            raise ValueError(
                'baseline mapping response success must be true'
            )

        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError(
                'baseline mapping items must contain unique item_id values'
            )

        return self
