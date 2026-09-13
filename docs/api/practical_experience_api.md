# SkillSpan Practical Experience API Contract v1

## Overview

`practical-experience-v1` is the versioned Practical Experience component used by the future composite Readiness calculation.

The current v1 measures verified SkillSpan project experience only. It does not claim to represent employment, internships, freelance work, or other external professional experience that is not modeled by the current Backend contract.

## Endpoint

`POST /api/v1/practical-experience`

## Versions

- Algorithm: `practical-experience-v1`
- Configuration: `practical-experience-config-v1`

## Configuration

```text
full_credit_project_count = 2
```

The configuration value is versioned and must not be treated as an unchangeable business constant.

## Input Boundary

The service is stateless and receives Backend-owned project data.

Request:

```json
{
  "student_profile_id": 10,
  "user_id": 20,
  "projects": []
}
```

Each project contains:

- `project_id`
- `project_status`
- `team_members`
- `submissions`
- `evaluations`

The calculation does not query the Backend database directly.

## Eligibility

A project is eligible only when all of the following are true:

1. `project_status = completed`
2. the target learner has a team membership with `assignment_state = completed`
3. the same learner has an accepted submission
4. that exact accepted submission has an evaluation with status `finalized` or `moderated`

An evaluation belonging to another learner or another submission must not make the project eligible.

Each distinct `project_id` is counted at most once.

## Formula

```text
Practical Experience Score =
min(eligible_projects_count / full_credit_project_count, 1) * 100
```

With the v1 configuration:

```text
0 eligible projects  -> unavailable
1 eligible project   -> 50.0
2 eligible projects  -> 100.0
3+ eligible projects -> 100.0
```

## Missing / Unavailable Semantics

If `eligible_projects_count = 0`:

```text
component_status = unavailable
practical_experience_score = null
```

The value must not be converted to `0`.

This is intentional because the current Backend does not model all possible real-world experience sources, so absence of an eligible SkillSpan project is not equivalent to proven zero practical experience.

## Response

```json
{
  "student_profile_id": 10,
  "user_id": 20,
  "algorithm_version": "practical-experience-v1",
  "configuration_version": "practical-experience-config-v1",
  "component_status": "available",
  "eligible_projects_count": 1,
  "full_credit_project_count": 2,
  "practical_experience_score": 50.0,
  "eligible_project_ids": [101]
}
```

## Determinism

Identical request data and the same configuration version must produce identical output.

The algorithm uses no:

- database query
- current date
- random value
- external service call

## Excluded Inputs in v1

The current algorithm intentionally does not use:

- project `difficulty`
- project `type`
- `Evaluation.overall_score`
- `ProfessionalRecordItem`
- external employment or internship data

These are excluded because no approved scoring contract currently exists for them.

## Relationship to Readiness

Practical Experience is the default `20%` component of the future multi-component Readiness algorithm.

This component must remain independently versioned from the composite Readiness algorithm.

## Test Coverage

Runtime tests cover:

- one eligible project -> 50%
- zero eligible projects -> unavailable
- two eligible projects -> 100%
- score capped at 100%
- duplicate `project_id` counted once
- evaluation for another submission rejected
- another learner team membership rejected
- non-accepted learner submission rejected
- non-final evaluation rejected
- deterministic identical-input behavior
- API available response
- API unavailable response
