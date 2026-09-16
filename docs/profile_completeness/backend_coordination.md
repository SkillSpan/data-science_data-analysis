# SkillSpan - Backend Coordination for Profile Completeness v1

## Status

Backend -> Data Science contract is approved and runtime implementation is complete.

- Algorithm version: `profile-completeness-v1`
- Configuration version: `profile-completeness-config-v1`
- FastAPI endpoint: `POST /api/v1/profile-completeness`
- Backend field contract: Confirmed
- Runtime tests: Implemented
- `skill-gap-v1` changes: Not required

## Approved StudentProfile Fields

The Backend supplies exactly these seven fields:

1. `university_name`
2. `student_university_number`
3. `specialization`
4. `academic_level`
5. `career_status`
6. `interests`
7. `availability`

All seven fields are always applicable and have equal weight (`1`).

## Completion Rules

The following six fields are free strings with Backend validation `string|max:100`:

- `university_name`
- `student_university_number`
- `specialization`
- `academic_level`
- `career_status`
- `availability`

A free-string field is complete when:

```text
value != null && trim(value) != ''
```

`Interests` is complete when:

```text
interests != null && interests != []
```

Missing or `null` fields are incomplete, not unavailable.

## Approved Backend -> FastAPI Snapshot

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

Laravel remains the source of truth for `StudentProfile` persistence and builds this trusted snapshot.
FastAPI remains stateless and does not query or mutate the Laravel database.

## Formula

```text
Profile Completeness Score =
(completed_fields_count / 7) * 100
```

The result is rounded to two decimal places.

## Composite Readiness Coordination

Backend confirmed and implemented the missing-component policy:

- unavailable components are excluded rather than converted to zero;
- remaining component weights are renormalized;
- `is_provisional = true` when any component is excluded;
- `is_provisional = false` when all components are available.

Backend also confirmed the Composite Readiness critical-skill cap:

```text
any critical skill match ratio < 0.50
-> final composite readiness capped at 69.0
```

This policy is independent from the existing `skill-gap-v1` rule:

```text
critical gap >= 2
-> skill-gap readiness cap = 60
```

## Definition of Done

- [x] Backend field names confirmed.
- [x] Backend field types and maximum lengths confirmed.
- [x] Null and blank-string semantics confirmed.
- [x] Interests completion rule confirmed.
- [x] Equal-weight configuration confirmed.
- [x] Final Backend -> Data Science payload approved.
- [x] Machine-readable JSON Schema updated.
- [x] FastAPI runtime endpoint implemented.
- [x] Service and API contract tests added.
- [x] Composite missing-component policy confirmed.
- [x] Composite critical-skill cap confirmed.
