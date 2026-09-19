# Sprint 2 Student Profile Contract Delta

## Status

Pending Backend contract confirmation. No runtime change is applied to `profile-completeness-v1` by this document.

## Approved Sprint 2 Profile Changes

The updated Sprint 2 SRS/profile scope requires the learner profile to use:

- `student_number` instead of `student_university_number`
- `university_name`
- `country`

These changes apply to the Student Profile contract. They do not automatically change the existing Profile Completeness v1 scoring contract.

## Existing Profile Completeness v1 Contract

The currently approved and deployed `profile-completeness-v1` / `profile-completeness-config-v1` contract remains frozen at seven equal-weight fields:

1. `university_name`
2. `student_university_number`
3. `specialization`
4. `academic_level`
5. `career_status`
6. `interests`
7. `availability`

Changing field names or adding `country` to the score would change the approved contract and therefore requires explicit Backend coordination and versioning.

## Backend Decisions Required

Before FastAPI runtime changes are made, Backend must confirm:

1. The canonical replacement field is exactly `student_number`.
2. Whether old `student_university_number` remains temporarily supported for backward compatibility or is migrated completely.
3. The exact representation of `country` (free text, canonical ID, ISO code, or another controlled value).
4. Validation rules and maximum lengths for `student_number` and `country`.
5. Whether `country` is always applicable to every learner profile.
6. Whether `country` participates in Profile Completeness scoring.
7. Whether `student_number` remains part of Profile Completeness scoring after the rename.
8. The exact Backend -> FastAPI profile snapshot after the Sprint 2 profile migration.

## Versioning Rule

If the scoring fields or scoring denominator change, the existing v1 contract must not be silently modified. A new approved configuration and, where required, algorithm/API contract version must be introduced.

If the change is only a transport/schema rename with identical scoring semantics, backward compatibility and migration behavior must still be explicitly agreed with Backend before implementation.

## Current Data Science Decision

Until Backend confirms the above contract:

- keep `profile-completeness-v1` behavior unchanged;
- do not add `country` to the 7-field denominator;
- do not replace `student_university_number` in the deployed v1 request schema;
- treat the Sprint 2 Student Profile change as a pending integration delta;
- continue other Sprint 2 intelligence work independently where it does not depend on this unresolved profile contract.
