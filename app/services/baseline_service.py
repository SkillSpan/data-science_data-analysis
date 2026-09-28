from collections import defaultdict

from app.schemas.baseline import (
    BaselineQuestion,
    BaselineRequest,
)


ALGORITHM_VERSION = "baseline-v2.0"


class BaselineEvaluationInputError(ValueError):
    """Raised when submitted responses cannot be scored safely."""


class BaselineEvaluationConfigurationError(ValueError):
    """Raised when the submitted assessment snapshot is inconsistent."""


def _score_question(
    question: BaselineQuestion,
    answer: str,
) -> float:
    """Return a normalized deterministic question score in the 0..1 range."""

    if answer not in question.options:
        raise BaselineEvaluationInputError(
            f"Invalid answer for baseline question_id {question.question_id}."
        )

    if question.question_type == "single_choice":
        return 1.0 if answer == question.correct_answer else 0.0

    scoring_rule = question.scoring_rule or {}
    return scoring_rule[answer]


def evaluate_baseline(
    request: BaselineRequest,
) -> dict[str, object]:
    """Evaluate one exact dynamic assessment snapshot supplied by Laravel."""

    questions_by_id = {
        question.question_id: question
        for question in request.questions
    }

    configured_weight_by_skill: dict[int, float] = defaultdict(float)
    answered_weight_by_skill: dict[int, float] = defaultdict(float)
    weighted_score_by_skill: dict[int, float] = defaultdict(float)
    slug_by_skill: dict[int, str] = {}

    for question in request.questions:
        for mapping in question.skill_mappings:
            effective_weight = question.weight * mapping.weight
            configured_weight_by_skill[mapping.skill_id] += effective_weight

            existing_slug = slug_by_skill.get(mapping.skill_id)
            if (
                existing_slug is not None
                and existing_slug != mapping.skill_slug
            ):
                raise BaselineEvaluationConfigurationError(
                    "Assessment snapshot contains inconsistent slugs for "
                    f"skill_id {mapping.skill_id}."
                )
            slug_by_skill[mapping.skill_id] = mapping.skill_slug

    total_weighted_score = 0.0
    total_answered_weight = 0.0

    for submitted in request.responses:
        question = questions_by_id.get(submitted.question_id)
        if question is None:
            raise BaselineEvaluationInputError(
                f"Unknown baseline question_id: {submitted.question_id}."
            )

        question_score = _score_question(
            question,
            submitted.answer,
        )

        for mapping in question.skill_mappings:
            effective_weight = question.weight * mapping.weight
            weighted_score = question_score * effective_weight

            weighted_score_by_skill[mapping.skill_id] += weighted_score
            answered_weight_by_skill[mapping.skill_id] += effective_weight
            total_weighted_score += weighted_score
            total_answered_weight += effective_weight

    if total_answered_weight <= 0:
        raise BaselineEvaluationInputError(
            "Baseline responses do not contain any positively weighted "
            "scorable questions."
        )

    skill_results: list[dict[str, object]] = []

    for skill_id in sorted(answered_weight_by_skill):
        answered_weight = answered_weight_by_skill[skill_id]
        configured_weight = configured_weight_by_skill[skill_id]

        if answered_weight <= 0:
            continue

        if configured_weight <= 0:
            raise BaselineEvaluationConfigurationError(
                "Assessment snapshot has no positive configured weight for "
                f"skill_id {skill_id}."
            )

        normalized_score = (
            weighted_score_by_skill[skill_id]
            / answered_weight
        )
        confidence = answered_weight / configured_weight

        skill_results.append(
            {
                "skill_id": skill_id,
                "slug": slug_by_skill[skill_id],
                "level": round(normalized_score * 5.0, 2),
                "confidence": round(confidence, 4),
            }
        )

    if not skill_results:
        raise BaselineEvaluationInputError(
            "Baseline responses did not measure any skills."
        )

    overall_score = (
        100.0
        * total_weighted_score
        / total_answered_weight
    )

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "assessment_version": request.assessment_version,
        "career_role_id": request.career_role_id,
        "student_profile_id": request.student_profile_id,
        "overall_score": round(overall_score, 2),
        "skills": skill_results,
    }
