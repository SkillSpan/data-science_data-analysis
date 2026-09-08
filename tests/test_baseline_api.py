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
            "Baseline mapping integration requires BACKEND_BASE_URL and "
            "BASELINE_INTERNAL_SECRET."
        )
    }


def test_baseline_endpoint_rejects_invalid_request_contract() -> None:
    payload = _valid_request_payload()
    payload["responses"] = []

    response = client.post("/api/v1/baseline", json=payload)

    assert response.status_code == 422


def test_baseline_endpoint_scores_with_backend_mapping_and_propagates_request_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.schemas.baseline_mapping import BaselineMappingResponse

    captured: dict[str, object] = {}

    mapping = BaselineMappingResponse.model_validate(
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
                }
            ],
        }
    )

    def fake_fetch_baseline_mapping(
        assessment_version: str,
        request_id: str | None = None,
    ) -> BaselineMappingResponse:
        captured["assessment_version"] = assessment_version
        captured["request_id"] = request_id
        return mapping

    monkeypatch.setattr(
        "app.api.routes.baseline.fetch_baseline_mapping",
        fake_fetch_baseline_mapping,
    )

    response = client.post(
        "/api/v1/baseline",
        json=_valid_request_payload(),
        headers={"X-Request-ID": "backend-baseline-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "backend-baseline-123"
    assert captured == {
        "assessment_version": "v1.0",
        "request_id": "backend-baseline-123",
    }
    assert response.json() == {
        "algorithm_version": "baseline-v1.0",
        "student_profile_id": 1,
        "overall_score": 100.0,
        "skills": [
            {
                "skill_id": 5,
                "slug": "sql",
                "level": 5.0,
                "confidence": 1.0,
            }
        ],
    }
