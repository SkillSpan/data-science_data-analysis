# Profile Completeness v1 — Final Contract

## Status

Approved contract between Backend and Data Science.

- Algorithm version: `profile-completeness-v1`
- Configuration version: `profile-completeness-config-v1`

## Ownership Boundary

Laravel owns `StudentProfile` persistence and sends the profile snapshot.

FastAPI is stateless and calculates Profile Completeness only from the supplied snapshot. It does not query or mutate the Backend database.

## Input

```json
{
  "student_profile_id": 123,
  "fields": {
    "university_name": "Test University",
    "student_university_number": "12345",
    "specialization": "Computer Science",
    "academic_level": "Senior",
    "career_status": "student",
    "interests": ["data-analysis"],
    "availability": "full_time"
  }
}
```

## Fields

All seven fields are always applicable and have equal weight (`1`):

1. `university_name`
2. `student_university_number`
3. `specialization`
4. `academic_level`
5. `career_status`
6. `interests`
7. `availability`

There are no conditional fields and no section/group weighting in v1.

## Completion Rules

For the six free-string fields:

```text
value != null && trim(value) != ''
```

The six free-string fields are:

- `university_name`
- `student_university_number`
- `specialization`
- `academic_level`
- `career_status`
- `availability`

Each free-string field follows the Backend contract maximum length of 100 characters.

For `interests`:

```text
interests != null && interests != []
```

A non-empty array counts as complete. v1 does not inspect the semantic content of individual interest strings.

Missing fields and explicit `null` values are incomplete, not unavailable.

## Formula

All fields have equal weight, therefore:

```text
Profile Completeness Score =
(completed_fields_count / 7) * 100
```

The result is rounded to two decimal places.

Examples:

```text
7 / 7 -> 100.00
6 / 7 -> 85.71
4 / 7 -> 57.14
1 / 7 -> 14.29
0 / 7 -> 0.00
```

## Component Status

For every valid request, the component is:

```text
component_status = available
```

An incomplete profile is valid observed data and produces a score between `0` and `100`.

It must not be converted into `unavailable`.

## Privacy and Fairness

No fields in the approved v1 configuration are protected or sensitive attributes used to rank the learner.

No additional fields may be introduced into the score without a new approved configuration version.

## Determinism

The calculation uses no database query, current date, random value, or external service.

Identical input under the same configuration version must produce identical output.

## Relationship to Composite Readiness

Profile Completeness is the default `5%` component of Composite Readiness.

Composite-level behavior is outside this algorithm. The approved Composite Readiness policies are:

- unavailable components are excluded and remaining weights are renormalized;
- the final result is marked provisional when a component is excluded;
- if any critical skill match ratio is below `0.50`, Composite Readiness is capped at `69.0`.

The Composite cap is independent from the `skill-gap-v1` rule:

```text
critical gap >= 2 -> skill-gap readiness cap = 60
```
