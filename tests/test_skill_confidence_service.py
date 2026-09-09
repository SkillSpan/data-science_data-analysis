from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.skill_confidence import SkillConfidenceRequest
from app.services.skill_confidence_service import (
    SkillConfidenceError,
    calculate_skill_confidence,
)


PAST_DATE = date(2026, 1, 1)


def _request(evidence: list[dict[str, object]]) -> SkillConfidenceRequest:
    return SkillConfidenceRequest(
        student_profile_id=15,
        skill_id=7,
        evidence=evidence,
    )


def test_current_assessment_and_project_confidence_is_65() -> None:
    result = calculate_skill_confidence(
        _request(
            [
                {
                    "source": "assessment_test",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "assessment-1",
                },
                {
                    "source": "project_performance",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "project-1",
                },
            ]
        )
    )

    assert result["confidence_score"] == 65.0
    assert result["confidence_band"] == "good"


def test_older_project_evidence_reduces_confidence_to_56_25() -> None:
    result = calculate_skill_confidence(
        _request(
            [
                {
                    "source": "assessment_test",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "assessment-1",
                },
                {
                    "source": "project_performance",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 0.75,
                    "reference": "project-1",
                },
            ]
        )
    )

    assert result["confidence_score"] == 56.25
    assert result["confidence_band"] == "moderate"


def test_all_sources_verified_and_current_produce_100() -> None:
    evidence = [
        {
            "source": source,
            "verification_status": "verified",
            "evidence_date": PAST_DATE,
            "recency_factor": 1.0,
            "reference": f"{source}-1",
        }
        for source in (
            "self_assessment",
            "assessment_test",
            "project_performance",
            "expert_evaluation",
            "certificate",
        )
    ]

    result = calculate_skill_confidence(_request(evidence))

    assert result["confidence_score"] == 100.0
    assert result["confidence_band"] == "high"


def test_no_evidence_produces_zero_low_confidence() -> None:
    result = calculate_skill_confidence(_request([]))

    assert result["status"] == "no_evidence"
    assert result["confidence_score"] == 0.0
    assert result["confidence_band"] == "low"
    assert result["distinct_evidence_count"] == 0


def test_rejected_evidence_contributes_zero() -> None:
    result = calculate_skill_confidence(
        _request(
            [
                {
                    "source": "assessment_test",
                    "verification_status": "rejected",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "assessment-1",
                }
            ]
        )
    )

    assert result["confidence_score"] == 0.0
    assert result["confidence_band"] == "low"


def test_pending_assessment_uses_half_verification_factor() -> None:
    result = calculate_skill_confidence(
        _request(
            [
                {
                    "source": "assessment_test",
                    "verification_status": "pending",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "assessment-1",
                }
            ]
        )
    )

    assert result["confidence_score"] == 15.0
    assert result["confidence_band"] == "low"


def test_duplicate_reference_is_not_double_counted() -> None:
    result = calculate_skill_confidence(
        _request(
            [
                {
                    "source": "assessment_test",
                    "verification_status": "verified",
                    "evidence_date": date(2025, 12, 1),
                    "recency_factor": 0.9,
                    "reference": "assessment-result-123",
                },
                {
                    "source": "assessment_test",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "assessment-result-123",
                },
            ]
        )
    )

    assert result["confidence_score"] == 30.0
    assert result["duplicate_evidence_detected"] is True
    assert result["duplicate_evidence_count"] == 1
    assert result["distinct_evidence_count"] == 1


def test_canonical_source_record_identity_takes_priority_over_reference() -> None:
    result = calculate_skill_confidence(
        _request(
            [
                {
                    "source": "project_performance",
                    "verification_status": "verified",
                    "evidence_date": date(2025, 12, 1),
                    "recency_factor": 0.75,
                    "reference": "old-reference",
                    "source_record_type": "project_evaluation",
                    "source_record_id": 44,
                },
                {
                    "source": "project_performance",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "new-reference",
                    "source_record_type": "project_evaluation",
                    "source_record_id": 44,
                },
            ]
        )
    )

    assert result["confidence_score"] == 35.0
    assert result["duplicate_evidence_count"] == 1
    assert result["distinct_evidence_count"] == 1


def test_future_evidence_date_is_rejected() -> None:
    with pytest.raises(SkillConfidenceError) as exc_info:
        calculate_skill_confidence(
            _request(
                [
                    {
                        "source": "assessment_test",
                        "verification_status": "verified",
                        "evidence_date": date(2099, 1, 1),
                        "recency_factor": 1.0,
                        "reference": "future-evidence",
                    }
                ]
            )
        )

    assert exc_info.value.code == "FUTURE_EVIDENCE_DATE"


def test_multiple_distinct_same_source_records_require_approved_confidence_aggregation() -> None:
    with pytest.raises(SkillConfidenceError) as exc_info:
        calculate_skill_confidence(
            _request(
                [
                    {
                        "source": "project_performance",
                        "verification_status": "verified",
                        "evidence_date": PAST_DATE,
                        "recency_factor": 1.0,
                        "reference": "project-A",
                    },
                    {
                        "source": "project_performance",
                        "verification_status": "verified",
                        "evidence_date": PAST_DATE,
                        "recency_factor": 0.75,
                        "reference": "project-B",
                    },
                ]
            )
        )

    assert exc_info.value.code == "SAME_SOURCE_CONFIDENCE_AGGREGATION_UNDEFINED"


def test_unapproved_recency_factor_is_rejected() -> None:
    with pytest.raises(SkillConfidenceError) as exc_info:
        calculate_skill_confidence(
            _request(
                [
                    {
                        "source": "assessment_test",
                        "verification_status": "verified",
                        "evidence_date": PAST_DATE,
                        "recency_factor": 0.82,
                        "reference": "assessment-invalid-recency",
                    }
                ]
            )
        )

    assert exc_info.value.code == "INVALID_RECENCY_FACTOR"


def test_partial_canonical_identity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SkillConfidenceRequest(
            student_profile_id=15,
            skill_id=7,
            evidence=[
                {
                    "source": "project_performance",
                    "verification_status": "verified",
                    "evidence_date": PAST_DATE,
                    "recency_factor": 1.0,
                    "reference": "project-partial-identity",
                    "source_record_type": "project_evaluation",
                }
            ],
        )
