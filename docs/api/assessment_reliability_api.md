# SkillSpan Assessment Reliability API Contract v1

## Overview

`assessment-reliability-v1` is the versioned Assessment Reliability component used by the future composite Readiness calculation.

This component measures the coverage reliability of the latest completed Backend-owned Baseline Assessment snapshot supplied to FastAPI. It is separate from `skill-confidence-v1`.

## Endpoint

`POST /api/v1/assessment-reliability`

## Versions

- Algorithm: `assessment-reliability-v1`
- Configuration: `assessment-reliability-config-v1`

## Source of Truth and Input Boundary

Laravel owns `BaselineAssessment` persistence and selects the relevant latest completed assessment snapshot.

FastAPI remains stateless and does not query the Backend database. The request contains the Backend-owned assessment snapshot.

The calculation consumes:

`BaselineAssessment.normalized_skills[*].confidence`

The Backend normalizes these confidence values to the `0..100` scale before sending/persisting the snapshot used by this component.

The raw FastAPI Baseline response stored in `result` uses confidence on `0..1`; `assessment-reliability-v1` does not consume that raw scale directly.

## Request

```json
{
  "student_profile_id": 10,
  "assessment": {
    "assessment_id": 101,
    "assessment_type": "baseline",
    "assessment_version": "v1.0",
    "status": "completed",
    "normalized_skills": [
      {"skill_id": 1, "confidence": 100.0},
      {"skill_id": 2, "confidence": 80.0},
      {"skill_id": 3, "confidence": 60.0}
    ]
  }
}
```

Each normalized skill requires:

- positive unique `skill_id`
- `confidence` in `0..100`

Duplicate `skill_id` values are rejected because they would silently give the same skill extra weight in the arithmetic mean.

## Eligibility

The component is available only when:

1. an assessment snapshot is supplied;
2. `status = completed`;
3. `normalized_skills` is non-empty;
4. every confidence value satisfies `0 <= confidence <= 100`;
5. normalized skill IDs are unique.

Backend is responsible for selecting the latest completed Baseline Assessment when multiple persisted assessments exist.

## Formula

```text
Assessment Reliability Score =
AVG(normalized_skills[*].confidence)
```

No additional multiplication by `100` is applied because the Backend-owned `normalized_skills` confidence scale is already `0..100`.

Example:

```text
100, 80, 60 -> 80.0
```

The final result is rounded to two decimal places.

## Missing / Unavailable Semantics

The component is `unavailable` when:

- no assessment snapshot is supplied;
- the supplied assessment is `in_progress`;
- the completed assessment contains no normalized skills.

In these cases:

```text
component_status = unavailable
assessment_reliability_score = null
```

A real confidence value of `0.0` is valid observed data and must not be interpreted as missing. A completed assessment with valid normalized skills all equal to zero therefore returns:

```text
component_status = available
assessment_reliability_score = 0.0
```

## Response

```json
{
  "student_profile_id": 10,
  "algorithm_version": "assessment-reliability-v1",
  "configuration_version": "assessment-reliability-config-v1",
  "component_status": "available",
  "baseline_assessment_id": 101,
  "assessment_version": "v1.0",
  "assessed_skills_count": 3,
  "assessment_reliability_score": 80.0
}
```

## Interpretation

Baseline confidence is an assessment-coverage signal, not correctness.

It represents how much of the positively weighted configured assessment coverage for a skill was answered. A wrong answer still counts as answered coverage.

This component must not be confused with generic Skill Confidence:

- Baseline Assessment Reliability uses Baseline coverage confidence.
- `skill-confidence-v1` uses evidence-source weights, verification, recency, and evidence aggregation.

## Determinism

Identical request data and the same configuration version must produce identical output.

The calculation uses no:

- database query
- current date
- random value
- external service call

## Relationship to Readiness

Assessment Reliability is the default `10%` component of the future multi-component Readiness algorithm.

This component remains independently versioned from composite Readiness.

## Test Coverage

Runtime tests cover:

- completed assessment arithmetic mean
- missing assessment -> unavailable
- in-progress assessment -> unavailable
- completed assessment without normalized skills -> unavailable
- valid zero confidence remains available
- deterministic identical-input behavior
- two-decimal rounding
- duplicate normalized skill IDs rejected
- API available response
- API unavailable response
- confidence above `100` rejected through the API
- duplicate normalized skill IDs rejected through the API
