# Sprint 2 Learner Intelligence Coverage Audit

**Status:** 2026-09-19

## Implemented and Tested

- Skill Gap v1: non-negative gaps, current above required, required zero, validation, duplicate skills, critical-gap cap 60, determinism.
- Skill Match v1: weighted scoring, cap 100, weight normalization, required zero, missing role data validation, duplicate skills, determinism.
- Career Role Config v1: versioned configuration, prerequisite validation, cycles, deterministic ordering.
- Skill Confidence v1: evidence weights, verification, recency, deduplication, rejected evidence, no evidence, determinism.
- Assessment Reliability v1: available/unavailable behavior and determinism.
- Practical Experience v1: eligible-project rules, unavailable behavior, determinism.
- Profile Completeness v1: approved seven-field contract and determinism.
- Baseline v1: deterministic identical-input behavior.
- Fairness: analytical request schemas are guarded against protected-attribute decision inputs.

## Sprint 2 Test Vectors

- Normal case: covered.
- No evidence: covered.
- Self-assessment only: documented as SE-TV-003; broader Skill Level runtime awaits approved contract.
- Missing optional evidence: documented as SE-TV-002; missing evidence is not injected as zero.
- Current > required: covered.
- Current = required: covered.
- Required = 0: covered.
- Critical deficiency: covered for Skill Gap; Composite Readiness cap is separate.
- Invalid weights: covered.
- Missing role data: covered.
- Prerequisite cycle: covered.
- Availability changes: pending Roadmap contract.
- Role changes: pending Roadmap/Readiness contract.
- Configuration changes: versioning documented; runtime registry resolution pending.

## Pending Contracts

### Composite Readiness
Approved business rules are known: Skill Match 65%, Practical Experience 20%, Assessment Reliability 10%, Profile Completeness 5%. Unavailable components are excluded and remaining weights renormalized; result becomes provisional. Critical skill match ratio below 0.50 caps Composite Readiness at 69. FastAPI runtime waits for the exact Backend request/response and version contract.

### Career Roadmap / Next Best Action
No approved FastAPI runtime contract yet for phases, actions, effort, duration, availability changes, role changes, or Next Best Action.

### Sprint 2 Profile Delta
The deployed profile-completeness-v1 stays frozen. Sprint 2 requests student_number instead of student_university_number and adds country. Exact Backend snapshot, scoring, applicability, and compatibility remain pending.

### Runtime Configuration Registry
Version identifiers exist and career-role-config-v1 is validated. Backend registry binding, runtime version resolution, lifecycle statuses, approval ownership, and configuration_id persistence remain pending.

## Validation Baseline

134 passed, 1 known Starlette TestClient/httpx deprecation warning.

## Closure Boundary

All currently approved and implementable Sprint 2 Data Science work is covered by runtime tests or deterministic specification vectors. Remaining work must wait for confirmed Backend/Product contracts rather than being inferred.

## Algorithm and Configuration Inventory

- Baseline: `baseline-v1.0`.
- Skill Gap: `skill-gap-v1`.
- Skill Match: `skill-match-v1`, using `career-role-config-v1` for role weights.
- Career Role Configuration: `career-role-config-v1`.
- Skill Confidence: `skill-confidence-v1`.
- Evidence weights: `evidence-weights-v1`.
- Verification factors: `evidence-verification-v1`.
- Evidence recency: `evidence-recency-v1`.
- Assessment Reliability: `assessment-reliability-v1` with `assessment-reliability-config-v1`.
- Practical Experience: `practical-experience-v1` with `practical-experience-config-v1`.
- Profile Completeness: `profile-completeness-v1` with `profile-completeness-config-v1`.

These identifiers describe the current analytical implementations or documented v1 configuration identities. They do not imply that every configuration identifier is already dynamically resolved from the Backend configuration registry at runtime.

## Service Ownership Boundary

- Laravel remains the source of truth for database persistence, learner identity, authorization, transactional data, assessment definitions, mappings, role configuration persistence, and authoritative historical results.
- FastAPI remains stateless and owns deterministic analytical calculation and validation only.
- FastAPI must not query or mutate the Laravel database directly.
- The frontend must not call FastAPI directly; analytical requests flow through Laravel.
- Missing optional analytical evidence must not be silently converted into demonstrated zero unless an approved algorithm explicitly defines that behavior.
- Existing algorithm versions must not be silently changed while implementing pending Sprint 2 contracts.

## Reopen Triggers for Pending Work

Pending items become implementation-ready only when the corresponding contract is confirmed:

1. Composite Readiness: exact Backend request schema, response schema, algorithm/configuration version identifiers, and persistence handoff.
2. Career Roadmap / Next Best Action: approved roadmap inputs, outputs, phases, actions, ordering, effort, duration, availability behavior, and recalculation rules.
3. Sprint 2 Profile Delta: canonical `student_number` migration rule, country representation, scoring/applicability decision, compatibility policy, and exact Backend snapshot.
4. Runtime Configuration Registry: active-version selection rules, lifecycle/status values, approval ownership, registry binding, and persistence of the exact configuration reference used.

Until those triggers are satisfied, the pending items remain intentionally blocked rather than partially implemented from assumptions.
