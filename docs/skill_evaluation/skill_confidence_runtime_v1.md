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

FastAPI remains stateless. Laravel remains responsible for persistence of the returned analytical result and historical snapshot.

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

`recency_factor` is supplied as part of the versioned evidence snapshot and validated against `evidence-recency-v1`.

The current API does not invent an `as_of_date` field or derive age boundaries from server runtime time because no such request contract is currently approved. `evidence_date` remains required for traceability and future evidence dates are rejected.

## Confidence Formula

For one retained evidence record per source:

`Confidence = 100 * SUM(source_weight * verification_factor * recency_factor) / SUM(all configured source weights)`

The final score is rounded to two decimal places and constrained to `0..100`.

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

The approved documentation requires same-source evidence to be aggregated before the source weight is applied and requires the source contribution to remain capped at its configured weight.

However, the current specification does not define a numeric Confidence aggregation formula for combining multiple distinct `verification_factor * recency_factor` values from the same source.

Therefore Runtime v1 deliberately does not invent one. If multiple distinct retained records exist for the same source, the service returns:

`SAME_SOURCE_CONFIDENCE_AGGREGATION_UNDEFINED`

A future approved numeric rule requires a versioned analytical decision before this behavior is changed.

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
- explicit rejection of undefined multiple-distinct-same-source Confidence aggregation
- API calculation behavior
- API no-evidence behavior
- structured API error response

## Compatibility and Reproducibility

The response returns all material Confidence version identifiers so Laravel can persist them with the evaluation snapshot:

- `confidence_algorithm_version`
- `evidence_weight_config_version`
- `verification_config_version`
- `recency_config_version`

Changing source weights, verification factors, recency factors, confidence bands, duplicate semantics, same-source Confidence aggregation, or the Confidence formula requires an appropriate new analytical/configuration version.
