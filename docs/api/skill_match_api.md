# SkillSpan Skill Match API Contract v1

## Overview

`skill-match-v1` is the versioned weighted Skill Match component used to compare evaluated learner skill levels with the requirements of one target career-role version.

It is intentionally separate from `skill-gap-v1`. The existing Skill Gap algorithm and its critical-skill readiness cap are not modified by this component.

## Endpoint

`POST /api/v1/skill-match`

## Versions

- Algorithm: `skill-match-v1`
- Role weight configuration: `career-role-config-v1`

## Input Boundary

Skill Match receives already-evaluated `current_level` values on the approved `0..5` scale together with role requirements and importance weights.

Evidence aggregation is upstream of Skill Match. Missing optional evidence must not be injected here as a false `current_level = 0`. Skill Evaluation excludes unavailable optional evidence from its available-evidence denominator and produces the evaluated level supplied to Skill Match.

## Skill Input Rules

For every skill:

- `skill_id` must be positive and unique within the request.
- `current_level` must be within `0..5`.
- `required_level` must be within `0..5`.
- `importance_weight` must satisfy `0 < weight <= 1`.
- `current_level > required_level` is valid and must not produce more than 100% match.
- `required_level = 0` is valid and does not contribute to the weighted-required denominator.

## Weight Normalization

Configured positive weights are preserved and normalized deterministically according to `career-role-config-v1`:

```text
normalized_weight = importance_weight / SUM(importance_weight)
```

A positive total different from `1.00` is normalized rather than treated as an error.

## Calculation

For every skill:

```text
achieved_level = min(current_level, required_level)
```

For skills with `required_level > 0`:

```text
match_ratio = achieved_level / required_level
```

For `required_level = 0`, `match_ratio = 1.00` and the skill is marked `not_required`.

Weighted totals:

```text
weighted_achieved_total = SUM(achieved_level * normalized_weight)
weighted_required_total = SUM(required_level * normalized_weight)
```

Final Skill Match:

```text
if weighted_required_total == 0:
    skill_match_score = 100.00
else:
    skill_match_score = 100 * weighted_achieved_total / weighted_required_total
```

The final result is rounded to two decimal places and capped at `100.00`.

## Status Semantics

- `met`: required level is positive and the learner meets or exceeds it.
- `partial`: required level is positive and the learner is below it.
- `not_required`: required level is zero.

## Determinism

Identical request data and the same configuration version must produce identical analytical output.

No current date, random value, database query, or external service is used in `skill-match-v1` calculation.

## Relationship to Readiness

The SRS reserves Skill Match as the `65%` default component of the future multi-component Readiness algorithm.

Do not add Practical Experience, Assessment Reliability, Profile Completeness, or critical-skill readiness caps to `skill-match-v1`. Those belong to the separate versioned Readiness algorithm.

## Test Coverage

Runtime tests cover:

- normal weighted learner
- current level above required level
- Skill Match capped at 100%
- required level equal to zero
- all requirements equal to zero
- deterministic positive-weight normalization
- invalid importance weight rejection
- duplicate skill rejection
- identical-input determinism
- API success and semantic-error behavior

## Compatibility

`skill-match-v1` is an independent analytical component. It does not change `skill-gap-v1`, `baseline-v1.0`, `skill-confidence-v1`, or `career-role-config-v1` behavior.
