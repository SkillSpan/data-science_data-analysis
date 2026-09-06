# SkillSpan — Algorithm & Configuration Versioning Specification

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Purpose:** Define how SkillSpan versions algorithms, configuration, mappings, taxonomy, normalization, evidence weights, confidence rules, rubrics, and validation behavior so analytical outputs remain reproducible and auditable.

---

## 1. Objective

SkillSpan decisions must remain reproducible even after business rules, mappings, weights, normalization logic, or algorithms change.

For every material Skill Evaluation, the system must be able to answer:

- Which algorithm implementation produced the result?
- Which evidence-weight configuration was used?
- Which normalization rules were used?
- Which assessment-to-skill mapping version was used?
- Which Skill taxonomy version was used?
- Which confidence and recency configuration was used?
- Which rubric version contributed evidence?
- When did the version become effective?
- Has the version since been superseded or deactivated?
- Can the historical result still be reconstructed?

Versioning is therefore part of the analytical contract, not only a release-management concern.

This document does **not** modify `skill-gap-v1`.

---

## 2. SRS Governance Baseline

SkillSpan requires:

- algorithm outputs to retain algorithm version;
- material decisions to retain configuration version;
- default weights, thresholds, caps, mappings, and recency factors to remain configurable and versioned;
- published configuration versions to be immutable or superseded through controlled versioning;
- defective configuration versions to be safely deactivated without destroying historical reproducibility;
- validation reports to record expected results, actual results, limitations, and approval;
- historical records not to be silently overwritten.

---

## 3. Versioning Domains

Skill Evaluation should distinguish the following version domains.

| Domain | Recommended Identifier | Purpose |
|---|---|---|
| Skill Evaluation algorithm | `skill-evaluation-v1` | Main orchestration/calculation behavior producing Skill Level and related explanation. |
| Skill taxonomy | `skill-taxonomy-v1` | Canonical Skill identities, aliases, lifecycle, supersession context. |
| Assessment mapping | `assessment-skill-map-v1` | Assessment/item-to-Skill contribution mappings. |
| Normalization configuration | `skill-normalization-v1` | Registry of approved source-to-0–5 rules. |
| Direct 0–5 normalization | `direct-skill-0-5-v1` | Identity normalization rule. |
| Percentage normalization | `percent-to-skill-v1` | Percentage-to-0–5 conversion rule. |
| Evidence weights | `evidence-weights-v1` | Default source weights used in Skill Level aggregation. |
| Confidence algorithm | `skill-confidence-v1` | Confidence formula semantics. |
| Verification factors | `evidence-verification-v1` | Verification-state multipliers. |
| Recency configuration | `evidence-recency-v1` | Evidence age windows and factors. |
| Rubric | Backend/domain-defined | Version of rubric used to generate project/expert evidence. |
| Distribution validation | `skill-distribution-validation-v1` | Monitoring metrics, flags, and anomaly policies. |
| Overall Skill Evaluation config bundle | `skill-evaluation-config-v1` | Optional umbrella reference tying compatible component versions together. |

Exact persisted field names remain a Backend integration decision.

---

## 4. Algorithm Version vs Configuration Version

These concepts must remain distinct.

### 4.1 Algorithm Version

Represents a change in computational logic or interpretation.

Example:

```text
skill-evaluation-v1
```

A new algorithm version is required when:

- the Skill Level formula changes;
- the evidence aggregation sequence changes;
- missing-evidence behavior changes;
- rounding semantics materially change;
- same-source aggregation logic changes;
- Confidence formula changes when bundled into the same algorithm;
- an implementation change can alter results for the same input/configuration.

### 4.2 Configuration Version

Represents approved parameter or mapping values used by an algorithm.

Examples:

```text
evidence-weights-v1
assessment-skill-map-v1
evidence-recency-v1
```

A new configuration version is required when:

- evidence weights change;
- recency windows or factors change;
- verification multipliers change;
- assessment mappings change;
- normalization mappings change;
- Skill taxonomy semantics change;
- thresholds or approved controlled values change.

The same algorithm version may therefore run with a different configuration version.

---

## 5. Recommended Version Naming Convention

Recommended baseline:

```text
<domain>-v<major>
```

Examples:

```text
skill-evaluation-v1
skill-confidence-v1
evidence-weights-v1
assessment-skill-map-v1
```

If finer release tracking becomes necessary, the team may adopt semantic-style identifiers:

```text
skill-evaluation-v1.1
skill-evaluation-v2.0
```

However, naming must remain:

- immutable once published;
- unique per analytical domain;
- human-readable;
- stored as data, not inferred only from Git branch/tag names.

Git commit/tag references may supplement but must not replace analytical version identifiers.

---

## 6. Version Lifecycle

Recommended lifecycle:

```text
draft
  ↓
validated
  ↓
approved
  ↓
active
  ↓
superseded / deactivated
```

Exact Backend enum values require confirmation.

### Draft

May change freely; must not be used for production decisions.

### Validated

Has deterministic test results and technical review.

### Approved

Authorized domain/Product/Data Science approval completed.

### Active

Eligible for new production calculations.

### Superseded

Replaced by a newer version; historical decisions continue referencing it.

### Deactivated

Must not be used for new calculations, often because of a defect or governance decision.

Deactivation must not erase historical records.

---

## 7. Immutability Rule

Once a version has produced a finalized material decision, its analytical meaning must not be silently edited in place.

Do **not**:

```text
evidence-weights-v1:
project_performance 0.35 -> 0.50
```

while keeping the same version identifier.

Instead create:

```text
evidence-weights-v2
```

Historical results must continue to point to `evidence-weights-v1`.

---

## 8. Compatibility Bundle

Because Skill Evaluation depends on several independent versions, an optional configuration bundle is recommended.

Example:

```json
{
  "skill_evaluation_config_version": "skill-evaluation-config-v1",
  "skill_taxonomy_version": "skill-taxonomy-v1",
  "assessment_skill_mapping_version": "assessment-skill-map-v1",
  "normalization_config_version": "skill-normalization-v1",
  "evidence_weight_config_version": "evidence-weights-v1",
  "verification_config_version": "evidence-verification-v1",
  "recency_config_version": "evidence-recency-v1",
  "confidence_algorithm_version": "skill-confidence-v1"
}
```

This provides one stable reference to an approved compatible set.

It does not remove the need to retain individual component versions when required for audit/reproduction.

---

## 9. Proposed Skill Evaluation Version Metadata

A material Skill Evaluation should be able to retain metadata conceptually equivalent to:

```json
{
  "skill_evaluation_algorithm_version": "skill-evaluation-v1",
  "skill_evaluation_config_version": "skill-evaluation-config-v1",
  "skill_taxonomy_version": "skill-taxonomy-v1",
  "assessment_skill_mapping_version": "assessment-skill-map-v1",
  "normalization_config_version": "skill-normalization-v1",
  "evidence_weight_config_version": "evidence-weights-v1",
  "confidence_algorithm_version": "skill-confidence-v1",
  "verification_config_version": "evidence-verification-v1",
  "recency_config_version": "evidence-recency-v1",
  "rubric_versions": [
    "project-rubric-v3"
  ],
  "calculated_at": "2026-09-02T00:00:00Z"
}
```

This is a proposed analytical representation, not a claim about current Laravel columns.

---

## 10. Input Snapshot Requirement

Version identifiers alone may be insufficient for exact historical reproduction.

A material decision should retain or reference an immutable input snapshot containing the relevant analytical inputs, such as:

```text
learner/student reference
skill_id
evidence records/references
normalized values
source types
verification states
evidence dates
mapping references
rubric references
calculation timestamp
```

The Backend remains the authoritative persistence boundary.

Data Science remains stateless unless an explicitly approved design changes that architecture.

---

## 11. Code Reference

Each production Algorithm Version should ideally retain:

```text
code_reference
```

Examples:

```text
Git commit SHA
release tag
container/image digest
deployment release identifier
```

Recommended governance record:

```json
{
  "algorithm_version": "skill-evaluation-v1",
  "code_reference": "git:<commit-sha>",
  "effective_from": "2026-09-02T00:00:00Z",
  "status": "active"
}
```

This improves reproducibility but does not replace versioned analytical configuration.

---

## 12. Effective Dates

Configuration versions may have:

```text
effective_from
effective_to
```

Rules:

1. Only one approved active version per required configuration context should apply at a calculation timestamp unless scoped overrides are explicitly supported.
2. Overlapping active effective ranges must be rejected or explicitly resolved by priority rules.
3. Historical decisions use the version effective/selected at their original calculation time.
4. Backdated configuration changes must not silently change previously finalized decisions.

---

## 13. Recalculation Rules

Recalculation must distinguish between:

### Verification Recalculation

Purpose:

```text
Confirm historical reproducibility.
```

Uses:

```text
same input snapshot
same algorithm version
same configuration versions
```

Expected:

```text
equivalent deterministic output
```

### Current Recalculation

Purpose:

```text
Generate a new current evaluation using latest approved versions.
```

Expected:

- create a new decision/evaluation version;
- preserve prior historical result;
- record reasons/version changes;
- do not overwrite the prior calculation.

---

## 14. Change Classification

### Patch-Level / Non-Analytical Change

May not require new analytical version when it cannot alter calculated results.

Examples:

- documentation typo;
- log wording;
- internal refactor proven output-equivalent;
- performance optimization with identical deterministic outputs.

Still subject to normal software release tracking.

### Material Analytical Change

Requires new analytical/configuration version.

Examples:

- formula change;
- source weight change;
- normalization change;
- confidence factor change;
- mapping change;
- taxonomy meaning change;
- rounding change affecting persisted output;
- same-source aggregation change;
- edge-case behavior change that changes output.

---

## 15. Deterministic Validation Gate

Before a new analytical version becomes active, it should pass:

1. schema validation;
2. deterministic test vectors;
3. edge-case tests;
4. reproducibility tests;
5. comparison with previous version where applicable;
6. distribution validation on available representative data;
7. documented limitations;
8. authorized approval.

Recommended validation record:

```json
{
  "validation_id": "skill-evaluation-v2-validation-001",
  "algorithm_version": "skill-evaluation-v2",
  "configuration_version": "skill-evaluation-config-v2",
  "test_vector_set": "deterministic_test_vectors.json",
  "expected_results_passed": true,
  "distribution_review_status": "passed",
  "limitations": [],
  "approved": true
}
```

---

## 16. Rollback / Deactivation

If a production version is defective:

```text
active
  ↓
deactivated
```

Then:

- stop new decisions from using it;
- activate an approved replacement/previous version according to deployment policy;
- preserve all historical decisions made with the defective version;
- record incident/rollback reason;
- identify affected decisions for review/recalculation when appropriate;
- never rewrite history silently.

---

## 17. Version-Related Edge Cases

| ID | Condition | Required Behavior |
|---|---|---|
| `VER-EC-01` | Required version missing | Reject or flag analytical contract. |
| `VER-EC-02` | Unknown version | Reject for new calculation. |
| `VER-EC-03` | Draft version used in production | Reject. |
| `VER-EC-04` | Deactivated version requested for new calculation | Reject unless explicit historical verification mode. |
| `VER-EC-05` | Version config edited in place after publication | Governance failure; create new version instead. |
| `VER-EC-06` | Effective-date overlap | Reject/require explicit resolution. |
| `VER-EC-07` | Historical version no longer active | Still allowed for historical reconstruction. |
| `VER-EC-08` | Recalculation with latest version differs from history | Store as new result/version; preserve old result. |
| `VER-EC-09` | Same snapshot + same versions gives different result | Reproducibility failure. |
| `VER-EC-10` | Code release changed but analytical output unchanged | Analytical version may remain same if equivalence is validated and governance approves. |

---

## 18. Version Compatibility Validation

A configuration bundle should reject incompatible combinations.

Example:

```text
assessment-skill-map-v2
```

might require:

```text
skill-taxonomy-v2
```

and may be incompatible with:

```text
skill-taxonomy-v1
```

Recommended compatibility check:

```json
{
  "mapping_version": "assessment-skill-map-v2",
  "requires": {
    "skill_taxonomy_version": "skill-taxonomy-v2"
  }
}
```

No component should silently substitute another version.

---

## 19. Backend Algorithm Configuration Registry

The current Laravel migrations confirm a versioned `algorithm_configurations` registry with the following fields:

```text
id
name
version
status
config
created_by
activated_at
timestamps
```

For Skill Evaluation, this table is the Backend persistence source for versioned algorithm configuration parameters such as `pending_verification_factor = 0.50`.

The registry record identifies the named/versioned configuration, while the `config` payload contains the parameters belonging to that configuration version. Exact status values, activation workflow, approval ownership, and configuration selection rules still require Backend/Product governance confirmation where not already defined.

---

## 20. Current Proposed v1 Baseline

For documentation and test-fixture purposes, the current proposed Skill Evaluation baseline is:

```text
skill_evaluation_algorithm_version  = skill-evaluation-v1
skill_taxonomy_version              = skill-taxonomy-v1
assessment_skill_mapping_version    = assessment-skill-map-v1
normalization_config_version        = skill-normalization-v1
direct_normalization_rule           = direct-skill-0-5-v1
percentage_normalization_rule       = percent-to-skill-v1
evidence_weight_config_version      = evidence-weights-v1
confidence_algorithm_version        = skill-confidence-v1
verification_config_version         = evidence-verification-v1
recency_config_version              = evidence-recency-v1
distribution_validation_version     = skill-distribution-validation-v1
```

These identifiers remain proposed Data Science specification identifiers unless a matching configuration is explicitly created and versioned in `algorithm_configurations`.

The confirmed existence of `algorithm_configurations` establishes the Backend registry mechanism, but it must not be interpreted as proof that every proposed identifier above already has a corresponding active Backend configuration record.

---

## 21. Backend Persistence and Evaluation Result Contract

### Confirmed current Backend models

The following fields are confirmed from the current Laravel migrations:

```text
skill_evidences
- id
- student_profile_id
- skill_id
- source
- value
- normalized_value
- reference
- evidence_date (NOT NULL)
- verification_status
- reviewer_id
- reviewer_notes
- recency_factor
- source_record_type
- source_record_id

skill_evaluations
- id
- student_profile_id
- skill_id
- level
- confidence
- algorithm_version
- calculated_at
- snapshot

learner_skills
- id
- learner_id -> users.id
- skill_id
- level
- confidence_score
- source_type
- algorithm_version
- configuration_version
- source_contributions
- calculated_at

algorithm_configurations
- id
- name
- version
- status
- config
- created_by
- activated_at
- timestamps
```

`skill_evidences.evidence_date` is required by the Backend schema and must remain required in the FastAPI evaluation contract.

Backend has also approved two persistence changes that are not yet present in the current migrations:

- add `configuration_id` to `skill_evaluations` as an explicit reference to the exact `algorithm_configurations` record used for the calculation;
- add `UNIQUE (learner_id, skill_id)` to `learner_skills` so the table enforces exactly one current projection row per learner and skill.

These items are approved contract changes pending Backend migration implementation.

`skill_evaluations` uses `student_profile_id`, while `learner_skills` uses `learner_id -> users.id`. The current `/api/v1/skills/matrix` read path is wired to `learner_skills`.

### Approved v1 ownership model

`skill_evaluations` is the authoritative calculated evaluation record/history. It is the audit-oriented representation of a computed skill result.

`learner_skills` is the latest/current materialized projection used by read paths such as `/skills/matrix` and by the UI. It must not become an independently calculated second source of truth.

When projecting an evaluation into `learner_skills`, Laravel must resolve the learner identity through `skill_evaluations.student_profile_id -> student_profiles.user_id -> learner_skills.learner_id`.

FastAPI remains stateless and does not write directly to the Laravel database. Laravel is responsible for persistence after receiving an evaluation result from FastAPI.

The intended persistence flow is:

```text
FastAPI calculates evaluation result
        |
        v
Laravel receives result
        |
        +--> persist SkillEvaluation authoritative result/history
        |
        +--> update/upsert learner_skills current projection
```

Laravel should persist the authoritative `skill_evaluations` record and update/upsert the corresponding `learner_skills` projection within one transaction so the history and current matrix view cannot drift during a successful evaluation write.

### Reproducibility requirement

The current migrations persist `skill_evaluations.algorithm_version` and `skill_evaluations.snapshot`, while `learner_skills` persists `algorithm_version`, `configuration_version`, and `source_contributions`.

Backend has approved the following v1 historical reproducibility contract:

- `algorithm_version` identifies the version of the calculation algorithm itself;
- `configuration_id` will be added to `skill_evaluations` as an explicit reference to the exact `algorithm_configurations` record used for the calculation;
- `snapshot` remains an immutable historical snapshot of the configuration metadata, parameters, relevant analytical inputs, and values actually used at calculation time.

`configuration_id` is an approved contract change pending Backend migration implementation. The snapshot must remain historical evidence and must not be rewritten when a configuration is later edited, superseded, deactivated, or replaced.

A representative snapshot shape is:

```json
{
  "algorithm": {
    "version": "skill-evaluation-v1"
  },
  "configuration": {
    "name": "skill_evaluation",
    "version": 3
  },
  "parameters": {
    "pending_verification_factor": 0.50
  }
}
```

Together, `algorithm_version`, `configuration_id`, and the immutable `snapshot` make `skill_evaluations` the trusted historical record for previous calculations.

A direct link such as `learner_skills.latest_skill_evaluation_id` would further improve row-level traceability between the current projection and its authoritative evaluation record. This field is not present in the current migrations and remains a Backend schema recommendation rather than an implemented contract.

---

### Backend projection integrity contract

The current migrations do not yet contain a unique constraint on `learner_skills (learner_id, skill_id)`. Backend has approved adding `UNIQUE (learner_id, skill_id)` because `learner_skills` represents the latest/current projection and must contain at most one current row per learner and skill.

This uniqueness rule is therefore an approved persistence contract change pending Backend migration implementation.

## 22. Open Decisions

The following require alignment with Backend/Product/Domain:

```text
- exact version field names
- version lifecycle enum
- approval workflow and approver roles
- effective-date selection logic
- exact code-reference strategy
- rollback/recalculation workflow
- compatibility-rule storage
- whether rubric/taxonomy versions are included directly or through a config bundle
```

---

## 23. Definition of Done

- [x] Algorithm vs configuration version distinguished.
- [x] Required Skill Evaluation version domains identified.
- [x] Recommended naming convention documented.
- [x] Immutability rules documented.
- [x] Version lifecycle documented.
- [x] Input snapshot/reproducibility requirements documented.
- [x] Verification vs current recalculation behavior documented.
- [x] Validation gate documented.
- [x] Rollback/deactivation behavior documented.
- [x] Compatibility checks documented.
- [x] Proposed v1 version baseline documented.
- [x] Backend persistence ownership contract documented (`skill_evaluations` authoritative history; `learner_skills` current projection).
- [x] Current Backend evaluation persistence schema confirmed for `skill_evidences`, `skill_evaluations`, `learner_skills`, and `algorithm_configurations`.
- [x] Projection integrity contract confirmed; `UNIQUE (learner_id, skill_id)` is approved pending Backend migration implementation.
- [x] Historical snapshot/configuration persistence contract confirmed; `configuration_id` is approved pending Backend migration implementation.
- [ ] Direct evaluation-to-projection row-level traceability remains unconfirmed; `learner_skills.latest_skill_evaluation_id` is still a recommendation.
- [ ] Version lifecycle/status values confirmed.
- [ ] Approval ownership confirmed.
- [ ] Runtime version resolution implemented after approval.
