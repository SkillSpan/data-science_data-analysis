from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_skill_confidence_api_calculates_expected_score() -> None:
    response = client.post(
        "/api/v1/skill-confidence/calculate",
        json={
            "student_profile_id": 15,
            "skill_id": 7,
            "evidence": [
                {
                    "source": "assessment_test",
                    "verification_status": "verified",
                    "evidence_date": "2026-01-01",
                    "recency_factor": 1.0,
                    "reference": "assessment-1",
                },
                {
                    "source": "project_performance",
                    "verification_status": "verified",
                    "evidence_date": "2026-01-01",
                    "recency_factor": 1.0,
                    "reference": "project-1",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confidence_score"] == 65.0
    assert body["confidence_band"] == "good"
    assert body["confidence_algorithm_version"] == "skill-confidence-v1"
    assert body["evidence_weight_config_version"] == "evidence-weights-v1"
    assert body["verification_config_version"] == "evidence-verification-v1"
    assert body["recency_config_version"] == "evidence-recency-v1"


def test_skill_confidence_api_returns_no_evidence_result() -> None:
    response = client.post(
        "/api/v1/skill-confidence/calculate",
        json={
            "student_profile_id": 15,
            "skill_id": 7,
            "evidence": [],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_evidence"
    assert body["confidence_score"] == 0.0
    assert body["confidence_band"] == "low"


def test_skill_confidence_api_returns_structured_error_for_future_evidence() -> None:
    response = client.post(
        "/api/v1/skill-confidence/calculate",
        json={
            "student_profile_id": 15,
            "skill_id": 7,
            "evidence": [
                {
                    "source": "assessment_test",
                    "verification_status": "verified",
                    "evidence_date": "2099-01-01",
                    "recency_factor": 1.0,
                    "reference": "future-evidence",
                }
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "FUTURE_EVIDENCE_DATE"


def test_same_source_certificate_vector_matches_backend() -> None:
    response = client.post(
        "/api/v1/skill-confidence/calculate",
        json={
            "student_profile_id": 15,
            "skill_id": 7,
            "evidence": [
                {
                    "source": "certificate",
                    "verification_status": "verified",
                    "evidence_date": "2026-01-01",
                    "recency_factor": 1.0,
                    "reference": "certificate-A",
                },
                {
                    "source": "certificate",
                    "verification_status": "verified",
                    "evidence_date": "2026-01-01",
                    "recency_factor": 0.9,
                    "reference": "certificate-B",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confidence_score"] == 4.75
    assert body["confidence_band"] == "low"
    assert body["duplicate_evidence_detected"] is False
    assert body["distinct_evidence_count"] == 2
    assert body["source_contributions"] == [
        {
            "source": "certificate",
            "configured_weight": 0.05,
            "evidence_records": 2,
            "source_support_factor": 0.95,
            "confidence_contribution": 4.75,
        }
    ]
