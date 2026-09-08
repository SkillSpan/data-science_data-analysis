from collections import defaultdict

from app.schemas.baseline import BaselineRequest
from app.schemas.baseline_mapping import BaselineMappingItem, BaselineMappingResponse


ALGORITHM_VERSION = "baseline-v1.0"


class BaselineEvaluationInputError(ValueError):
    """Raised when submitted responses do not match the configured assessment."""


class BaselineEvaluationConfigurationError(RuntimeError):
    """Raised when the Backend-owned mapping cannot be scored safely."""


def _score_item(item: BaselineMappingItem, answer: str) -> float:
    """Return a normalized deterministic item score in the 0..1 range."""

    if answer not in item.options:
        raise BaselineEvaluationInputError(
            f"Invalid answer for baseline item {item.item_id}."
        )

    if item.item_type == "single_choice":
        return 1.0 if answer == item.correct_answer else 0.0

    scoring_rule = item.scoring_rule or {}
    return scoring_rule[answer]


def evaluate_baseline(
    request: BaselineRequest,
    mapping: BaselineMappingResponse,
) -> dict[str, object]:
    """Evaluate baseline responses against one validated Backend mapping."""

    if mapping.assessment_version != request.assessment_version:
        raise BaselineEvaluationConfigurationError(
            "Baseline mapping version does not match the requested assessment version."
        )

    items_by_id = {item.item_id: item for item in mapping.items}
    configured_weight_by_skill: dict[int, float] = defaultdict(float)
    slug_by_skill: dict[int, str] = {}

    for item in mapping.items:
        configured_weight_by_skill[item.skill_id] += item.weight

        existing_slug = slug_by_skill.get(item.skill_id)
        if existing_slug is not None and existing_slug != item.skill_slug:
            raise BaselineEvaluationConfigurationError(
                f"Baseline mapping contains inconsistent slugs for skill_id {item.skill_id}."
            )
        slug_by_skill[item.skill_id] = item.skill_slug

    weighted_score_by_skill: dict[int, float] = defaultdict(float)
    answered_weight_by_skill: dict[int, float] = defaultdict(float)
    total_weighted_score = 0.0
    total_answered_weight = 0.0

    for submitted in request.responses:
        item = items_by_id.get(submitted.item_id)
        if item is None:
            raise BaselineEvaluationInputError(
                f"Unknown baseline item_id: {submitted.item_id}."
            )

        item_score = _score_item(item, submitted.answer)

        if item.weight == 0:
            continue

        weighted_score = item_score * item.weight
        weighted_score_by_skill[item.skill_id] += weighted_score
        answered_weight_by_skill[item.skill_id] += item.weight
        total_weighted_score += weighted_score
        total_answered_weight += item.weight

    if total_answered_weight <= 0:
        raise BaselineEvaluationInputError(
            "Baseline responses do not contain any positively weighted scorable items."
        )

    skill_results: list[dict[str, object]] = []

    for skill_id in sorted(answered_weight_by_skill):
        answered_weight = answered_weight_by_skill[skill_id]
        configured_weight = configured_weight_by_skill[skill_id]

        if configured_weight <= 0:
            raise BaselineEvaluationConfigurationError(
                f"Baseline mapping has no positive configured weight for skill_id {skill_id}."
            )

        normalized_score = weighted_score_by_skill[skill_id] / answered_weight
        confidence = answered_weight / configured_weight

        skill_results.append(
            {
                "skill_id": skill_id,
                "slug": slug_by_skill[skill_id],
                "level": round(normalized_score * 5.0, 2),
                "confidence": round(confidence, 4),
            }
        )

    overall_score = 100.0 * total_weighted_score / total_answered_weight

    return {
        "algorithm_version": ALGORITHM_VERSION,
        "student_profile_id": request.student_profile_id,
        "overall_score": round(overall_score, 2),
        "skills": skill_results,
    }
