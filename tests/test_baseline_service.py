import pytest

from app.schemas.baseline import BaselineRequest
from app.schemas.baseline_mapping import BaselineMappingResponse
from app.services.baseline_service import (
    BaselineEvaluationConfigurationError,
    BaselineEvaluationInputError,
    evaluate_baseline,
)


def _mapping() -> BaselineMappingResponse:
    return BaselineMappingResponse.model_validate(
        {
            "success": True,
            "assessment_version": "v1.0",
            "weight_scale": "0..1",
            "items": [
                {
                    "item_id": "sql-001",
                    "item_type": "single_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "B",
                    "scoring_rule": None,
                    "skill_id": 5,
                    "skill_slug": "sql",
                    "weight": 1.0,
                },
                {
                    "item_id": "sql-002",
                    "item_type": "single_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "scoring_rule": None,
                    "skill_id": 5,
                    "skill_slug": "sql",
                    "weight": 0.8,
                },
                {
                    "item_id": "python-001",
                    "item_type": "single_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "C",
                    "scoring_rule": None,
                    "skill_id": 1,
                    "skill_slug": "python",
                    "weight": 1.0,
                },
                {
                    "item_id": "python-002",
                    "item_type": "scale",
                    "options": ["1", "2", "3", "4", "5"],
                    "correct_answer": None,
                    "scoring_rule": {
                        "1": 0.0,
                        "2": 0.25,
                        "3": 0.5,
                        "4": 0.75,
                        "5": 1.0,
                    },
                    "skill_id": 1,
                    "skill_slug": "python",
                    "weight": 0.5,
                },
            ],
        }
    )


def _request(responses: list[dict[str, str]]) -> BaselineRequest:
    return BaselineRequest.model_validate(
        {
            "student_profile_id": 1,
            "user_id": 2,
            "assessment_version": "v1.0",
            "responses": responses,
        }
    )


def test_evaluate_baseline_calculates_weighted_skill_levels_and_overall_score() -> None:
    result = evaluate_baseline(
        _request(
            [
                {"item_id": "sql-001", "answer": "B"},
                {"item_id": "sql-002", "answer": "A"},
                {"item_id": "python-001", "answer": "C"},
                {"item_id": "python-002", "answer": "4"},
            ]
        ),
        _mapping(),
    )

    assert result["algorithm_version"] == "baseline-v1.0"
    assert result["student_profile_id"] == 1
    assert result["overall_score"] == 96.21
    assert result["skills"] == [
        {
            "skill_id": 1,
            "slug": "python",
            "level": 4.58,
            "confidence": 1.0,
        },
        {
            "skill_id": 5,
            "slug": "sql",
            "level": 5.0,
            "confidence": 1.0,
        },
    ]


def test_partial_skill_response_reduces_confidence_without_counting_missing_as_wrong() -> None:
    result = evaluate_baseline(
        _request([{"item_id": "sql-001", "answer": "B"}]),
        _mapping(),
    )

    assert result["overall_score"] == 100.0
    assert result["skills"] == [
        {
            "skill_id": 5,
            "slug": "sql",
            "level": 5.0,
            "confidence": 0.5556,
        }
    ]


def test_wrong_single_choice_scores_zero() -> None:
    result = evaluate_baseline(
        _request([{"item_id": "sql-001", "answer": "A"}]),
        _mapping(),
    )

    assert result["overall_score"] == 0.0
    assert result["skills"][0]["level"] == 0.0


def test_unknown_item_id_is_rejected() -> None:
    with pytest.raises(BaselineEvaluationInputError, match="Unknown baseline item_id"):
        evaluate_baseline(
            _request([{"item_id": "unknown-001", "answer": "A"}]),
            _mapping(),
        )


def test_invalid_answer_is_rejected() -> None:
    with pytest.raises(BaselineEvaluationInputError, match="Invalid answer"):
        evaluate_baseline(
            _request([{"item_id": "sql-001", "answer": "Z"}]),
            _mapping(),
        )


def test_mapping_version_mismatch_is_rejected() -> None:
    mapping = _mapping().model_copy(update={"assessment_version": "v2.0"})

    with pytest.raises(BaselineEvaluationConfigurationError, match="version"):
        evaluate_baseline(
            _request([{"item_id": "sql-001", "answer": "B"}]),
            mapping,
        )


def test_evaluate_baseline_is_deterministic_for_identical_input() -> None:
    responses = [
        {"item_id": "sql-001", "answer": "B"},
        {"item_id": "sql-002", "answer": "A"},
        {"item_id": "python-001", "answer": "C"},
        {"item_id": "python-002", "answer": "4"},
    ]

    first = evaluate_baseline(_request(responses), _mapping())
    second = evaluate_baseline(_request(responses), _mapping())

    assert first == second
