import pytest

from app.schemas.baseline import BaselineRequest
from app.services.baseline_service import (
    BaselineEvaluationInputError,
    evaluate_baseline,
)


def _payload(
    *,
    career_role_id: int = 3,
    assessment_version: str = "backend-developer-v1",
) -> dict[str, object]:
    return {
        "student_profile_id": 15,
        "user_id": 20,
        "career_role_id": career_role_id,
        "assessment_version": assessment_version,
        "questions": [
            {
                "question_id": 101,
                "question_type": "single_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "B",
                "scoring_rule": None,
                "weight": 1.0,
                "skill_mappings": [
                    {
                        "skill_id": 7,
                        "skill_slug": "python",
                        "weight": 1.0,
                    }
                ],
            },
            {
                "question_id": 102,
                "question_type": "scale",
                "options": ["1", "2", "3", "4", "5"],
                "correct_answer": None,
                "scoring_rule": {
                    "1": 0.0,
                    "2": 0.25,
                    "3": 0.5,
                    "4": 0.75,
                    "5": 1.0,
                },
                "weight": 2.0,
                "skill_mappings": [
                    {
                        "skill_id": 7,
                        "skill_slug": "python",
                        "weight": 0.5,
                    },
                    {
                        "skill_id": 18,
                        "skill_slug": "api-development",
                        "weight": 0.5,
                    },
                ],
            },
            {
                "question_id": 103,
                "question_type": "single_choice",
                "options": ["A", "B"],
                "correct_answer": "A",
                "scoring_rule": None,
                "weight": 1.0,
                "skill_mappings": [
                    {
                        "skill_id": 30,
                        "skill_slug": "sql",
                        "weight": 1.0,
                    }
                ],
            },
        ],
        "responses": [
            {"question_id": 101, "answer": "B"},
            {"question_id": 102, "answer": "4"},
            {"question_id": 103, "answer": "A"},
        ],
    }


def _request(payload: dict[str, object] | None = None) -> BaselineRequest:
    return BaselineRequest.model_validate(payload or _payload())


def test_dynamic_baseline_calculates_skill_levels_confidence_and_overall() -> None:
    result = evaluate_baseline(_request())

    assert result == {
        "algorithm_version": "baseline-v2.0",
        "assessment_version": "backend-developer-v1",
        "career_role_id": 3,
        "student_profile_id": 15,
        "overall_score": 87.5,
        "skills": [
            {
                "skill_id": 7,
                "slug": "python",
                "level": 4.38,
                "confidence": 1.0,
            },
            {
                "skill_id": 18,
                "slug": "api-development",
                "level": 3.75,
                "confidence": 1.0,
            },
            {
                "skill_id": 30,
                "slug": "sql",
                "level": 5.0,
                "confidence": 1.0,
            },
        ],
    }


def test_unanswered_question_reduces_confidence_only_and_unmeasured_skills_are_omitted() -> None:
    payload = _payload()
    payload["responses"] = [
        {"question_id": 101, "answer": "B"},
    ]

    result = evaluate_baseline(_request(payload))

    assert result["overall_score"] == 100.0
    assert result["skills"] == [
        {
            "skill_id": 7,
            "slug": "python",
            "level": 5.0,
            "confidence": 0.5,
        }
    ]


def test_one_question_can_measure_multiple_skills() -> None:
    payload = _payload()
    payload["responses"] = [
        {"question_id": 102, "answer": "4"},
    ]

    result = evaluate_baseline(_request(payload))

    assert result["overall_score"] == 75.0
    assert result["skills"] == [
        {
            "skill_id": 7,
            "slug": "python",
            "level": 3.75,
            "confidence": 0.5,
        },
        {
            "skill_id": 18,
            "slug": "api-development",
            "level": 3.75,
            "confidence": 1.0,
        },
    ]


def test_wrong_answer_is_measured_as_zero_level_not_unanswered() -> None:
    payload = _payload()
    payload["responses"] = [
        {"question_id": 101, "answer": "A"},
    ]

    result = evaluate_baseline(_request(payload))

    assert result["overall_score"] == 0.0
    assert result["skills"] == [
        {
            "skill_id": 7,
            "slug": "python",
            "level": 0.0,
            "confidence": 0.5,
        }
    ]


def test_invalid_answer_is_rejected() -> None:
    payload = _payload()
    payload["responses"] = [
        {"question_id": 101, "answer": "Z"},
    ]

    with pytest.raises(
        BaselineEvaluationInputError,
        match="Invalid answer",
    ):
        evaluate_baseline(_request(payload))


def test_different_career_role_and_question_count_use_only_submitted_snapshot() -> None:
    payload = _payload(
        career_role_id=9,
        assessment_version="data-analyst-v3",
    )
    payload["questions"] = [
        {
            "question_id": 501,
            "question_type": "single_choice",
            "options": ["A", "B"],
            "correct_answer": "A",
            "scoring_rule": None,
            "weight": 1.0,
            "skill_mappings": [
                {
                    "skill_id": 44,
                    "skill_slug": "statistics",
                    "weight": 1.0,
                }
            ],
        }
    ]
    payload["responses"] = [
        {"question_id": 501, "answer": "A"},
    ]

    result = evaluate_baseline(_request(payload))

    assert result["career_role_id"] == 9
    assert result["assessment_version"] == "data-analyst-v3"
    assert result["overall_score"] == 100.0
    assert result["skills"] == [
        {
            "skill_id": 44,
            "slug": "statistics",
            "level": 5.0,
            "confidence": 1.0,
        }
    ]


def test_dynamic_baseline_is_deterministic_for_identical_snapshot() -> None:
    request = _request()

    first = evaluate_baseline(request)
    second = evaluate_baseline(request)

    assert first == second
