import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.baseline import BaselineRequest, BaselineResponse


def _valid_request_payload() -> dict[str, object]:
    return {
        "student_profile_id": 15,
        "user_id": 20,
        "career_role_id": 3,
        "assessment_version": "backend-developer-v1",
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
        ],
        "responses": [
            {"question_id": 101, "answer": "B"},
            {"question_id": 102, "answer": "4"},
        ],
    }


def test_baseline_request_accepts_dynamic_snapshot_contract() -> None:
    request = BaselineRequest.model_validate(_valid_request_payload())

    assert request.student_profile_id == 15
    assert request.user_id == 20
    assert request.career_role_id == 3
    assert request.assessment_version == "backend-developer-v1"
    assert request.questions[0].question_id == 101
    assert request.questions[1].skill_mappings[1].skill_id == 18
    assert request.responses[0].question_id == 101


def test_baseline_request_rejects_non_integer_question_id() -> None:
    payload = _valid_request_payload()
    payload["questions"][0]["question_id"] = "101"

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_duplicate_question_ids() -> None:
    payload = _valid_request_payload()
    payload["questions"][1]["question_id"] = 101

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_duplicate_response_ids() -> None:
    payload = _valid_request_payload()
    payload["responses"] = [
        {"question_id": 101, "answer": "A"},
        {"question_id": 101, "answer": "B"},
    ]

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_response_outside_snapshot() -> None:
    payload = _valid_request_payload()
    payload["responses"] = [
        {"question_id": 999, "answer": "A"},
    ]

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_invalid_skill_mapping_weights() -> None:
    payload = _valid_request_payload()
    payload["questions"][1]["skill_mappings"][0]["weight"] = 0.7

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_duplicate_skill_mapping() -> None:
    payload = _valid_request_payload()
    payload["questions"][1]["skill_mappings"] = [
        {
            "skill_id": 7,
            "skill_slug": "python",
            "weight": 0.5,
        },
        {
            "skill_id": 7,
            "skill_slug": "python",
            "weight": 0.5,
        },
    ]

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_inconsistent_skill_slug() -> None:
    payload = _valid_request_payload()
    payload["questions"][1]["skill_mappings"][0]["skill_slug"] = "python-duplicate"

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_response_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        BaselineResponse.model_validate(
            {
                "algorithm_version": "baseline-v2.0",
                "assessment_version": "backend-developer-v1",
                "career_role_id": 3,
                "student_profile_id": 15,
                "overall_score": 60,
                "skills": [
                    {
                        "skill_id": 7,
                        "slug": "python",
                        "level": 2.5,
                        "confidence": 1.1,
                    }
                ],
            }
        )


client = TestClient(
    app,
    headers={"Authorization": "Bearer test-service-token"},
)


def test_baseline_endpoint_scores_snapshot_without_backend_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BACKEND_BASE_URL", raising=False)
    monkeypatch.delenv("BASELINE_INTERNAL_SECRET", raising=False)

    response = client.post(
        "/api/v1/baseline",
        json=_valid_request_payload(),
        headers={"X-Request-ID": "dynamic-baseline-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "dynamic-baseline-123"
    assert response.json() == {
        "algorithm_version": "baseline-v2.0",
        "assessment_version": "backend-developer-v1",
        "career_role_id": 3,
        "student_profile_id": 15,
        "overall_score": 83.33,
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
        ],
    }


def test_baseline_endpoint_rejects_invalid_answer() -> None:
    payload = _valid_request_payload()
    payload["responses"][0]["answer"] = "Z"

    response = client.post("/api/v1/baseline", json=payload)

    assert response.status_code == 422
    assert "Invalid answer" in response.json()["detail"]

def test_baseline_request_rejects_empty_questions() -> None:
    payload = _valid_request_payload()
    payload["questions"] = []
    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_empty_responses() -> None:
    payload = _valid_request_payload()
    payload["responses"] = []
    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_single_choice_without_correct_answer() -> None:
    payload = _valid_request_payload()
    payload["questions"][0]["correct_answer"] = None
    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_scale_without_complete_scoring_rule() -> None:
    payload = _valid_request_payload()
    payload["questions"][1]["scoring_rule"].pop("5")
    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_scale_score_outside_unit_interval() -> None:
    payload = _valid_request_payload()
    payload["questions"][1]["scoring_rule"]["5"] = 1.5
    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)
