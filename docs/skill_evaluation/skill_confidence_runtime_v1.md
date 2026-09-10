# SkillSpan - Skill Confidence Runtime v1

## Purpose

Document the implemented runtime boundary for deterministic Skill Confidence calculation in the FastAPI Intelligence Service.

## Runtime Version

- Confidence algorithm: `skill-confidence-v1`
- Evidence weights: `evidence-weights-v1`
- Verification factors: `evidence-verification-v1`
- Recency configuration: `evidence-recency-v1`

This runtime does not modify `skill-gap-v1`, `baseline-v1.0`, or Career Role Configuration behavior.

## API

`POST /api/v1/skill-confidence/calculate`

FastAPI remains stateless and acts as the Data Science reference/parity implementation for Skill Confidence. Laravel is the production owner of the Skill Confidence business calculation, final persistence, stored evaluation result, and learner-skill projection. The FastAPI endpoint must match Laravel 1:1 but is not the authoritative stored-result source.

## Supported Evidence Sources

- `self_assessment`
- `assessment_test`
- `project_performance`
- `expert_evaluation`
- `certificate`

## Evidence Source Weights

- `self_assessment`: `0.10`
- `assessment_test`: `0.30`
- `project_performance`: `0.35`
- `expert_evaluation`: `0.20`
- `certificate`: `0.05`

Configured denominator for v1: `1.00`.

## Verification Factors

- `verified`: `1.00`
- `pending`: `0.50`
- `rejected`: `0.00`
- `expired`: `0.00`

Pending evidence contributes to Confidence only. This runtime does not make pending evidence positively contribute to Skill Level.

## Recency Factors

The v1 runtime accepts only the approved factors:

- `1.00`
- `0.90`
- `0.75`
- `0.60`

The approved `evidence-recency-v1` calendar-month thresholds are:

- `0-6 months` -> `1.00`
- `>6-12 months` -> `0.90`
- `>12-24 months` -> `0.75`
- `>24 months` -> `0.60`

Laravel dynamically recalculates `recency_factor` from `evidence_date` at each `recalculate()` and persists the factor used in the evaluation snapshot for auditability. The FastAPI parity endpoint receives the resulting versioned `recency_factor` and validates that it belongs to `evidence-recency-v1`; it does not independently own the production recency calculation. `evidence_date` remains required for traceability and future evidence dates are rejected.

## Confidence Formula

After duplicate removal, each distinct evidence record contributes:

`record_support = verification_factor * recency_factor`

For each evidence source:

`source_support = SUM(record_support) / COUNT(distinct evidence records from that source)`

The source weight is applied exactly once:

`source_contribution = source_weight * source_support`

Final Confidence is:

`Confidence = 100 * SUM(source_contribution) / SUM(all configured source weights)`

For a source with one retained evidence record, this is equivalent to `source_weight * verification_factor * recency_factor`. The final score is rounded to two decimal places and constrained to `0..100`.

## Confidence Bands

- `0 <= score < 30`: `low`
- `30 <= score < 60`: `moderate`
- `60 <= score < 80`: `good`
- `80 <= score <= 100`: `high`

## Missing and Invalid Evidence

- no evidence -> Confidence `0.00`, band `low`, status `no_evidence`
- rejected evidence -> zero positive contribution
- expired evidence -> zero positive contribution
- pending evidence -> verification factor `0.50`
- future evidence date -> `FUTURE_EVIDENCE_DATE`
- unapproved recency factor -> `INVALID_RECENCY_FACTOR`

Schema validation rejects unknown source codes, unknown verification statuses, invalid identifiers, and missing required evidence dates.

## Duplicate Evidence Identity

Duplicate detection follows the Backend-confirmed identity rule:

1. `(source_record_type, source_record_id)` when both values are present
2. otherwise `reference`
3. when neither identity is available, records cannot be assumed to represent the same underlying evidence event

For duplicate identities, only the latest evidence date is retained. If dates are equal, the last supplied record is retained deterministically.

The response exposes:

- `duplicate_evidence_detected`
- `duplicate_evidence_count`
- `distinct_evidence_count`

Duplicates never increase Confidence.

## Multiple Distinct Records From the Same Source

The v1 same-source Confidence policy is approved and implemented in both Laravel and the FastAPI parity implementation.

After duplicate removal, all independent evidence records from the same source participate in Confidence. Each record uses `verification_factor * recency_factor`, the resulting record-support values are averaged, and the configured source weight is applied once to that source-level average.

This prevents additional independent records from multiplying the configured source weight while still allowing their verification and recency quality to influence source support.

Backend parity vector for `certificate` (`source_weight = 0.05`):

- Evidence 1: `1.00 * 1.00 = 1.00`
- Evidence 2: `1.00 * 0.90 = 0.90`
- `source_support = (1.00 + 0.90) / 2 = 0.95`
- `source_contribution = 0.05 * 0.95 = 0.0475`
- Expected final Confidence when this is the only contributing source: `4.75%`

## Deterministic Runtime Coverage

Runtime tests currently cover:

- current assessment + project -> `65.00`, `good`
- older project evidence -> `56.25`, `moderate`
- all five current verified sources -> `100.00`, `high`
- no evidence -> `0.00`, `low`
- rejected evidence -> `0.00`
- pending assessment -> `15.00`
- duplicate reference deduplication
- canonical source-record identity precedence
- future evidence rejection
- unapproved recency-factor rejection
- Backend parity vector for two distinct same-source certificate records -> `4.75`
- API calculation behavior
- API no-evidence behavior
- structured API error response

## Compatibility and Reproducibility

The FastAPI parity response returns all material Confidence version identifiers so its analytical output can be compared directly with Laravel's authoritative calculation and persisted snapshot:

- `confidence_algorithm_version`
- `evidence_weight_config_version`
- `verification_config_version`
- `recency_config_version`

Changing source weights, verification factors, recency factors, confidence bands, duplicate semantics, same-source Confidence aggregation, or the Confidence formula requires an appropriate new analytical/configuration version.
