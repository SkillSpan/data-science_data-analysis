from collections import defaultdict
from datetime import date

from app.schemas.skill_confidence import SkillConfidenceRequest


CONFIDENCE_ALGORITHM_VERSION = "skill-confidence-v1"
EVIDENCE_WEIGHT_CONFIG_VERSION = "evidence-weights-v1"
VERIFICATION_CONFIG_VERSION = "evidence-verification-v1"
RECENCY_CONFIG_VERSION = "evidence-recency-v1"

EVIDENCE_SOURCE_WEIGHTS = {
    "self_assessment": 0.10,
    "assessment_test": 0.30,
    "project_performance": 0.35,
    "expert_evaluation": 0.20,
    "certificate": 0.05,
}

VERIFICATION_FACTORS = {
    "pending": 0.50,
    "verified": 1.00,
    "rejected": 0.00,
    "expired": 0.00,
}

APPROVED_RECENCY_FACTORS = {1.00, 0.90, 0.75, 0.60}


class SkillConfidenceError(ValueError):
    """Represent a deterministic confidence-calculation validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _confidence_band(score: float) -> str:
    if score < 30:
        return "low"
    if score < 60:
        return "moderate"
    if score < 80:
        return "good"
    return "high"


def _evidence_identity(evidence: object, index: int) -> tuple[object, ...]:
    source_record_type = getattr(evidence, "source_record_type")
    source_record_id = getattr(evidence, "source_record_id")
    reference = getattr(evidence, "reference")
    source = getattr(evidence, "source")

    if source_record_type is not None and source_record_id is not None:
        return (source, "source_record", source_record_type, source_record_id)

    if reference is not None:
        return (source, "reference", reference)

    return (source, "unidentified", index)


def _deduplicate_evidence(request: SkillConfidenceRequest) -> tuple[list[object], int]:
    retained: dict[tuple[object, ...], tuple[int, object]] = {}
    duplicate_count = 0

    for index, evidence in enumerate(request.evidence):
        identity = _evidence_identity(evidence, index)
        previous = retained.get(identity)

        if previous is None:
            retained[identity] = (index, evidence)
            continue

        duplicate_count += 1
        previous_index, previous_evidence = previous

        if evidence.evidence_date > previous_evidence.evidence_date:
            retained[identity] = (index, evidence)
        elif evidence.evidence_date == previous_evidence.evidence_date and index > previous_index:
            retained[identity] = (index, evidence)

    distinct = [item[1] for item in sorted(retained.values(), key=lambda item: item[0])]
    return distinct, duplicate_count


def calculate_skill_confidence(request: SkillConfidenceRequest) -> dict[str, object]:
    """Calculate deterministic Skill Confidence v1 from evidence support."""

    configured_weight_total = sum(EVIDENCE_SOURCE_WEIGHTS.values())
    if configured_weight_total <= 0:
        raise SkillConfidenceError(
            "ZERO_CONFIDENCE_DENOMINATOR",
            "Configured evidence-source weights must have a positive total.",
        )

    today = date.today()
    for evidence in request.evidence:
        if evidence.evidence_date > today:
            raise SkillConfidenceError(
                "FUTURE_EVIDENCE_DATE",
                "Evidence date cannot be in the future.",
            )
        if evidence.recency_factor not in APPROVED_RECENCY_FACTORS:
            raise SkillConfidenceError(
                "INVALID_RECENCY_FACTOR",
                "Recency factor is not part of evidence-recency-v1.",
            )

    distinct_evidence, duplicate_count = _deduplicate_evidence(request)

    if not distinct_evidence:
        return {
            "student_profile_id": request.student_profile_id,
            "skill_id": request.skill_id,
            "status": "no_evidence",
            "confidence_score": 0.0,
            "confidence_band": "low",
            "confidence_algorithm_version": CONFIDENCE_ALGORITHM_VERSION,
            "evidence_weight_config_version": EVIDENCE_WEIGHT_CONFIG_VERSION,
            "verification_config_version": VERIFICATION_CONFIG_VERSION,
            "recency_config_version": RECENCY_CONFIG_VERSION,
            "configured_weight_total": round(configured_weight_total, 6),
            "duplicate_evidence_detected": False,
            "duplicate_evidence_count": 0,
            "distinct_evidence_count": 0,
            "source_contributions": [],
        }

    by_source: dict[str, list[object]] = defaultdict(list)
    for evidence in distinct_evidence:
        by_source[evidence.source].append(evidence)

    numerator = 0.0
    source_contributions: list[dict[str, object]] = []

    for source in EVIDENCE_SOURCE_WEIGHTS:
        records = by_source.get(source)
        if not records:
            continue

        record_support_factors = [
            VERIFICATION_FACTORS[evidence.verification_status]
            * evidence.recency_factor
            for evidence in records
        ]
        source_support_factor = sum(record_support_factors) / len(record_support_factors)
        configured_weight = EVIDENCE_SOURCE_WEIGHTS[source]
        weighted_support = configured_weight * source_support_factor
        numerator += weighted_support

        source_contributions.append(
            {
                "source": source,
                "configured_weight": configured_weight,
                "evidence_records": len(records),
                "source_support_factor": round(source_support_factor, 6),
                "confidence_contribution": round(
                    100 * weighted_support / configured_weight_total,
                    2,
                ),
            }
        )

    confidence_score = round(100 * numerator / configured_weight_total, 2)
    if confidence_score < 0 or confidence_score > 100:
        raise SkillConfidenceError(
            "CONFIDENCE_OUT_OF_RANGE",
            "Calculated confidence is outside the valid 0..100 range.",
        )

    return {
        "student_profile_id": request.student_profile_id,
        "skill_id": request.skill_id,
        "status": "calculated",
        "confidence_score": confidence_score,
        "confidence_band": _confidence_band(confidence_score),
        "confidence_algorithm_version": CONFIDENCE_ALGORITHM_VERSION,
        "evidence_weight_config_version": EVIDENCE_WEIGHT_CONFIG_VERSION,
        "verification_config_version": VERIFICATION_CONFIG_VERSION,
        "recency_config_version": RECENCY_CONFIG_VERSION,
        "configured_weight_total": round(configured_weight_total, 6),
        "duplicate_evidence_detected": duplicate_count > 0,
        "duplicate_evidence_count": duplicate_count,
        "distinct_evidence_count": len(distinct_evidence),
        "source_contributions": source_contributions,
    }
