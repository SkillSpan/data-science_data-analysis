import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app

from app.schemas.baseline import (
    BaselineRequest,
    BaselineResponse,
)


def _valid_request_payload() -> dict[str, object]:
    return {
        "student_profile_id": 1,
        "user_id": 2,
        "assessment_version": "v1.0",
        "responses": [
            {"item_id": "sql-001", "answer": "B"},
        ],
    }


def test_baseline_request_accepts_valid_contract() -> None:
    request = BaselineRequest.model_validate(_valid_request_payload())

    assert request.student_profile_id == 1
    assert request.user_id == 2
    assert request.assessment_version == "v1.0"
    assert request.responses[0].item_id == "sql-001"
    assert request.responses[0].answer == "B"


def test_baseline_request_rejects_empty_responses() -> None:
    payload = _valid_request_payload()
    payload["responses"] = []

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_duplicate_item_ids() -> None:
    payload = _valid_request_payload()
    payload["responses"] = [
        {"item_id": "sql-001", "answer": "A"},
        {"item_id": "sql-001", "answer": "B"},
    ]

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_request_rejects_non_string_answer() -> None:
    payload = _valid_request_payload()
    payload["responses"] = [
        {"item_id": "sql-001", "answer": ["A", "B"]},
    ]

    with pytest.raises(ValidationError):
        BaselineRequest.model_validate(payload)


def test_baseline_response_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        BaselineResponse.model_validate(
            {
                "algorithm_version": "baseline-v1.0",
                "student_profile_id": 1,
                "overall_score": 60,
                "skills": [
                    {
                        "skill_id": 7,
                        "slug": "sql",
                        "level": 2.5,
                        "confidence": 70,
                    }
                ],
            }
        )


def test_baseline_response_rejects_overall_score_above_100() -> None:
    with pytest.raises(ValidationError):
        BaselineResponse.model_validate(
            {
                "algorithm_version": "baseline-v1.0",
                "student_profile_id": 1,
                "overall_score": 120,
                "skills": [
                    {
                        "skill_id": 7,
                        "slug": "sql",
                        "level": 2.5,
                        "confidence": 0.7,
                    }
                ],
            }
        )


client = TestClient(app)


def test_baseline_endpoint_returns_service_unavailable_without_backend_mapping() -> None:
    response = client.post(
        "/api/v1/baseline",
        json=_valid_request_payload(),
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Baseline evaluation requires Backend-owned assessment item "
            "definitions and item-to-skill mapping."
        )
    }


def test_baseline_endpoint_rejects_invalid_request_contract() -> None:
    payload = _valid_request_payload()
    payload["responses"] = []

    response = client.post("/api/v1/baseline", json=payload)

    assert response.status_code == 422
