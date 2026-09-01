# SkillSpan — Backend Coordination for Profile Completeness

## Purpose
Track the Backend ↔ Data Science confirmations required before profile attributes are used by future Readiness and Personalization models.

## Current Data Science Status
- Profile Completeness metric definition: **Prepared**
- Profile schema requirements: **Prepared**
- Proposed `profile-context-v1` payload contract: **Prepared**
- JSON Schema: **Prepared**
- Runtime FastAPI integration: **Not implemented yet**
- `skill-gap-v1` changes: **Not required for this task**

## Backend Confirmations Required

| Concept | Proposed Contract Field | Status |
|---|---|---|
| Student profile identifier | `student_profile_id` | Pending |
| University | `university` | Pending |
| Specialization | `specialization` | Pending |
| Academic level | `academic_level` | Pending |
| Education | `education` | Pending |
| Enrollment status | `enrollment_status` | Pending |
| Graduation status | `graduation_status` | Pending |
| Graduation date | `graduation_date` | Pending |
| Career status | `career_status` | Pending |
| Primary career goal | `primary_career_role_id` | Pending |
| Interests | `interests` | Pending |
| Availability | `availability` | Pending |
| Preferred work type / preferences | `preferences` | Pending |
| Visibility | `visibility` | Pending |
| Consent | `consent` | Pending |

## Contract Rules to Confirm
1. Whether university and specialization are strings, foreign keys, or structured objects.
2. Canonical enum values for academic/enrollment/graduation/career status.
3. Which fields are required, recommended, optional, nullable, or not applicable.
4. Whether empty strings are normalized to `null`.
5. Whether list-like fields use IDs, slugs, or names.
6. How visibility and consent are exposed without leaking restricted information.
7. Whether Backend stores/calculates completeness or only supplies authoritative attributes.
8. Whether a profile version or `updated_at` is included for reproducibility.

## Integration Boundary
- Laravel remains the source of truth for profile/business data.
- Frontend must not supply scoring attributes directly to FastAPI.
- FastAPI must not query the Laravel database directly.
- Laravel should build a trusted payload from authoritative stored profile data.
- Data Science validates the approved payload schema before future use.

## Approval Gate
Runtime implementation begins only after Backend confirms actual field names, enums/reference values, null semantics, and final payload shape.

## Definition of Done
- [x] Profile Completeness requirements defined.
- [x] Proposed profile data contract documented.
- [x] Machine-readable JSON Schema prepared.
- [ ] Backend field names confirmed.
- [ ] Backend enum/reference formats confirmed.
- [ ] Final Backend → Data Science payload approved.
- [ ] Contract validation tests added after approval.
