# SkillSpan â€” Profile Completeness Metrics & Data Contract v1.0

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product review
**Prepared:** 31 August 2026
**Scope:** Future Readiness & Personalization integration
**Does not modify:** `skill-gap-v1`

---

## 1. Executive Summary

This document defines a versioned, explainable profile-completeness metric and a canonical Backend â†’ Data Science profile payload for future SkillSpan Readiness and Personalization models.

The SRS requires learner profiles to contain education, specialization, career status, interests, availability, preferences, visibility, and consent; it also requires profile completeness to be calculated from configured required and recommended fields and returned as a percentage with missing-field explanations. The final Readiness model reserves 5% for Profile Completeness.

This specification therefore establishes:

- a configuration-driven completeness formula;
- explicit missing / invalid / not-applicable semantics;
- a canonical schema for university, specialization, academic level, career context, availability, preferences, and interests;
- privacy-safe handling of consent and visibility;
- a versioned Backend â†’ Data Science contract;
- acceptance tests for deterministic scoring and schema validation.

**Important:** This is a contract/design deliverable. It does not add Profile Completeness to the currently deployed `skill-gap-v1` algorithm and does not change its threshold/cap behavior.

---

## 2. Architecture & Ownership

```text
React Frontend
      â†“
Laravel Backend  â† authoritative Student Profile / consent / visibility
      â†“
FastAPI Intelligence Service  â† consumes trusted, normalized profile context
```

### Ownership rules

| Concern | Owner |
|---|---|
| Raw learner profile records | Laravel Backend |
| Profile field validation / persistence | Laravel Backend |
| Profile visibility / consent enforcement | Laravel Backend |
| Completeness metric definition | Data Science + Product approval |
| Completeness implementation location | Backend recommended; must be single-source and versioned |
| Future Readiness aggregation | Data Science / Intelligence |
| Future Personalization / ranking use | Data Science / Intelligence |

**Recommended implementation:** Laravel calculates and stores/exposes the canonical profile-completeness result using the approved versioned configuration, because the profile is Laravel-owned and completeness is required by profile UI as well as future intelligence. FastAPI consumes the score plus normalized profile context. If the team instead chooses FastAPI calculation, Laravel must send the raw normalized fields and no second implementation may exist in parallel.

---

## 3. Metric Definition

### 3.1 Algorithm identifier

```text
profile-completeness-v1
```

### 3.2 Formula

For every configured field `i` that is applicable to the learner:

```text
completion_i = 1  if the value is present and valid
completion_i = 0  if the value is missing or invalid
```

Then:

```text
Profile Completeness (%) =
100 Ã— Î£(weight_i Ã— completion_i) / Î£(weight_i for applicable fields)
```

### 3.3 Required behavior

1. Only **applicable** fields are included in the denominator.
2. `null` or absent means **missing**, unless the field is explicitly not applicable.
3. Empty strings are invalid and should be normalized to `null` before scoring.
4. Legitimate `0` and `false` values are **not missing**.
5. Invalid enum values are treated as invalid, not as completed.
6. Lists count as complete only when they contain at least one valid normalized item where the field requires a non-empty list.
7. The same normalized profile snapshot must always return the same score and missing-field lists.
8. Results must expose the algorithm/configuration version used.
9. No sensitive/private attribute should be added to the completeness score merely to increase prediction power.

### 3.4 Consent and visibility rule

Consent and visibility must be available to the platform for authorization and personalization eligibility, but the learner must **not receive completeness points for choosing a more permissive privacy setting**.

Therefore:

- `consent.personalization_allowed = false` is a valid value, not a missing value;
- `visibility = private` is a valid choice, not a completeness penalty;
- consent/visibility may act as **eligibility gates** for downstream use, not as positive score multipliers.

---

## 4. Proposed v1 Field Configuration

The SRS states that required and recommended fields must be configurable. The following is an **initial Data Science proposal for team approval**, not a hard-coded product rule.

### 4.1 Core fields â€” recommended default configuration

| Canonical field | Tier | Default weight | Completeness rule | Future use |
|---|---:|---:|---|---|
| `education.university` | Required | 15 | Valid normalized university object/name | Personalization, role suggestions |
| `education.specialization` | Required | 15 | Valid normalized specialization object/name | Readiness context, personalization |
| `education.academic_level` | Required | 15 | Approved controlled-vocabulary value | Personalization, roadmap context |
| `career.career_status` | Required | 10 | Approved controlled-vocabulary value | Readiness / recommendations |
| `career.primary_career_role_id` | Required | 15 | Positive approved role ID | Role-specific Readiness |
| `education.enrollment_status` | Required when applicable | 10 | Approved value; N/A excluded for graduated/non-enrolled cases | Context / eligibility |
| `availability.weekly_hours` | Recommended | 8 | Number 0â€“168; zero is valid | Roadmap / project matching |
| `preferences.preferred_work_type` | Recommended | 5 | â‰¥1 valid normalized item | Personalization / matching |
| `preferences.interests` | Recommended | 4 | â‰¥1 valid normalized item | Personalization / role suggestions |
| `preferences.other_preferences` | Recommended | 3 | Valid structured preferences object when configured | Personalization |
| **Total applicable default weight** |  | **100** | Re-normalized if any field is N/A |  |

### 4.2 Fields explicitly excluded from v1 completeness points

| Field | Reason |
|---|---|
| `consent.personalization_allowed` | Privacy choice must not be incentivized through score |
| `visibility` | Private visibility is a valid user choice |
| `graduation_date` | Conditional metadata; may be required when graduation status is true but should not globally penalize students |
| CV / certificates / portfolio files | SRS treats supporting files as recommended; completeness should not disadvantage learners without documents unless product explicitly approves it |
| Demographic / sensitive attributes | Not required for current decision model and should not be introduced casually |

### 4.3 Conditional applicability examples

- `graduation_date`: applicable only when `graduation_status == graduated/true`.
- `enrollment_status`: may be N/A for some graduates; if N/A, remove its weight from the denominator.
- Work-preference details may be N/A when the learner explicitly opts out of job/project recommendations; do not convert N/A into zero.

---

## 5. Canonical Backend â†’ Data Science Profile Context

### 5.1 Contract identifier

```text
profile-context-v1
```

### 5.2 Recommended payload fragment

```json
{
  "student_profile_id": 15,
  "profile_schema_version": "profile-context-v1",
  "profile_updated_at": "2026-08-31T13:00:00Z",
  "profile_completeness": {
    "score": 82.0,
    "algorithm_version": "profile-completeness-v1",
    "required_missing_fields": [
      "education.academic_level"
    ],
    "recommended_missing_fields": [
      "preferences.interests"
    ]
  },
  "education": {
    "university": {
      "id": 12,
      "name": "Example University"
    },
    "specialization": {
      "id": 34,
      "name": "Software Engineering"
    },
    "academic_level": "bachelor",
    "enrollment_status": "enrolled",
    "graduation_status": "not_graduated",
    "graduation_date": null
  },
  "career": {
    "career_status": "student",
    "primary_career_role_id": 3
  },
  "availability": {
    "weekly_hours": 10
  },
  "preferences": {
    "preferred_work_type": ["project", "internship"],
    "interests": ["data-analysis", "artificial-intelligence"],
    "other_preferences": {}
  },
  "visibility": "private",
  "consent": {
    "personalization_allowed": true,
    "consent_version": "privacy-2026-01"
  }
}
```

### 5.3 Contract rules

- `student_profile_id`: required positive integer; derived by Laravel from authenticated user context.
- `profile_schema_version`: required immutable contract identifier.
- `profile_updated_at`: required ISO-8601 timestamp to support snapshot/reproducibility.
- `university` and `specialization`: prefer stable IDs + display names when canonical tables exist. If Backend currently stores text only, send `id = null` and normalized `name` until canonicalization is introduced.
- `academic_level`: must use a Backend-approved controlled vocabulary, not arbitrary free text.
- `career_status`, `enrollment_status`, and `graduation_status`: controlled vocabularies owned by Backend/domain configuration.
- `weekly_hours`: numeric 0â€“168; `0` is valid and distinct from `null`.
- `preferred_work_type` / `interests`: arrays of canonical IDs/slugs where possible; remove duplicates.
- `visibility`: required policy value, but not a positive completeness weight.
- `consent.personalization_allowed`: required for use authorization; a `false` value is valid and must disable personalization use without lowering completeness.

---

## 6. Normalization Rules

### 6.1 Missing-value semantics

| Input | Meaning | Completeness |
|---|---|---|
| absent key | Missing | 0 if applicable |
| `null` | Missing / unknown | 0 if applicable |
| `""` or whitespace | Invalid â†’ normalize to `null` | 0 |
| `0` | Valid numeric zero when domain allows | Complete |
| `false` | Valid boolean false when domain allows | Complete |
| `[]` | Missing for fields requiring at least one item | 0 |
| N/A marker approved by rule | Not applicable | Excluded from denominator |

### 6.2 Text normalization

- trim leading/trailing whitespace;
- reject blank strings;
- store/display original human-readable names but prefer canonical ID/slug for analytics;
- do not perform lossy lowercasing on display names; normalized search keys may be separate.

### 6.3 Controlled vocabulary

The Backend team should provide the final allowed values for:

- `academic_level`
- `career_status`
- `enrollment_status`
- `graduation_status`
- `preferred_work_type`
- `visibility`

Data Science should not invent production enum values independently.

---

## 7. Completeness Output Contract

Recommended canonical result:

```json
{
  "score": 82.0,
  "algorithm_version": "profile-completeness-v1",
  "configuration_version": "learner-profile-config-v1",
  "completed_fields": [
    "education.university",
    "education.specialization",
    "career.career_status"
  ],
  "required_missing_fields": [
    "education.academic_level"
  ],
  "recommended_missing_fields": [
    "preferences.interests"
  ],
  "not_applicable_fields": [
    "education.graduation_date"
  ]
}
```

### Explainability requirement

A completeness score must never be returned as a naked percentage. The consumer must be able to explain **which fields are missing and why the denominator changed**.

---

## 8. Future Readiness Integration

The SRS reserves the following default components for the final Readiness Score:

```text
Skill Match              65%
Practical Experience     20%
Assessment Reliability   10%
Profile Completeness      5%
```

Profile Completeness should only be integrated into a new approved multi-component Readiness algorithm version after:

1. the profile contract is approved;
2. Backend can provide stable normalized values;
3. the metric configuration is approved;
4. practical-experience and assessment-reliability component contracts are finalized;
5. the critical-skill cap policy for the final score is formally resolved;
6. a new algorithm version is introduced.

**Do not modify `skill-gap-v1` to add the 5% component.**

---

## 9. Future Personalization Use

Profile attributes may support:

- career-role suggestions;
- learning-resource ranking;
- roadmap prioritization;
- project matching;
- availability-aware recommendations;
- preference-aware filtering.

Rules:

- only use attributes covered by active consent/policy;
- do not infer missing values as negative preferences;
- do not treat profile completeness itself as a measure of talent or employability;
- keep score explanations separate from sensitive profile attributes;
- allow personalization to be disabled while retaining core account functionality.

---

## 10. Acceptance Tests

### Metric tests

1. All applicable configured fields complete â†’ score = 100.
2. Missing required field â†’ score decreases and field appears in `required_missing_fields`.
3. Missing recommended field â†’ score decreases and field appears in `recommended_missing_fields`.
4. N/A field â†’ excluded from numerator and denominator; remaining weights re-normalize.
5. Numeric `0` on `weekly_hours` â†’ valid complete value, not missing.
6. Boolean `false` for consent choice â†’ valid value, not missing; personalization eligibility becomes false.
7. Blank string â†’ normalized to missing.
8. Invalid enum â†’ rejected/invalid and does not count as complete.
9. Duplicate interest values â†’ normalized to unique set.
10. Identical normalized input â†’ identical score and explanation.

### Contract tests

11. `student_profile_id <= 0` â†’ reject.
12. Missing `profile_schema_version` â†’ reject.
13. Invalid `profile_updated_at` â†’ reject.
14. `weekly_hours < 0` or `> 168` â†’ reject.
15. Unknown contract major version â†’ reject or route through explicit compatibility policy.
16. University/specialization object with neither ID nor valid name â†’ reject as invalid.
17. `academic_level` outside approved vocabulary â†’ reject.
18. Consent false â†’ profile may still be complete; personalization consumer must not use restricted attributes.

---

## 11. Backend Coordination Checklist

Before implementation is considered contract-ready, Backend should confirm:

- [ ] Actual current DB/API field names for university, specialization, academic level.
- [ ] Whether university/specialization are text fields or canonical related entities.
- [ ] Final enum values for academic/enrollment/graduation/career statuses.
- [ ] Final shape of availability and preferred work type.
- [ ] Final representation of interests/preferences.
- [ ] Where profile completeness is calculated and persisted.
- [ ] How completeness configuration/version is stored.
- [ ] How profile updates trigger recalculation.
- [ ] How visibility/consent are represented and enforced.
- [ ] Example Laravel response/payload for one learner.
- [ ] Validation/test results for missing/null/false/zero/N/A behavior.

---

## 12. Open Decisions Requiring Team Approval

| Decision | Recommendation | Status |
|---|---|---|
| Exact completeness weights | Use the proposed v1 weights as a starting configuration, not hard-coded constants | Pending approval |
| Calculation location | Laravel, because Student Profile is Backend-owned and UI also needs completeness | Pending team confirmation |
| Academic-level enum | Backend/domain-approved controlled vocabulary | Pending Backend |
| University/specialization canonical IDs | Prefer IDs + names; allow `id=null` during transition | Pending Backend schema confirmation |
| Minimum completeness required for Readiness | Do not invent threshold yet | Open product decision |
| Whether supporting files affect completeness | Exclude in v1 unless formally approved | Proposed |
| Final Readiness integration | New algorithm version only | Required |

---

## 13. Definition of Done for This Data Science Task

The Data Science task is complete at the contract/design level when:

- profile completeness formula and semantics are documented;
- required/recommended/applicable behavior is defined;
- proposed field configuration is documented;
- Backend â†’ Data Science profile payload is documented;
- university, specialization, and academic-level schema requirements are explicit;
- validation and edge cases are documented;
- acceptance tests are defined;
- Backend confirms its actual field mapping / enums or records any required changes;
- no unapproved changes are made to `skill-gap-v1`.

---

## 14. Source Basis

This contract is grounded in SkillSpan SRS v1.1 requirements, especially:

- **PROF-01:** learner profile includes education, specialization, career status, interests, availability, preferred work type.
- **PROF-04:** visibility and consent settings are required and access-controlled.
- **PROF-05:** completeness is calculated from configured required/recommended fields and returns percentage + missing-field explanation.
- **PROF-06:** primary career goal must be identifiable/versioned for scoring.
- **PROF-09:** graduation is profile state, not a role replacement.
- **Student Profile data model:** education, specialization, goals, interests, availability, preferences, completeness, visibility are Backend-authoritative.
- **Required Decision Data:** student profile requires education, specialization, career goal, availability, preferences, interests, completeness, consent.
- **Readiness components:** Profile Completeness is 5% of the future final Readiness model.

---

## 15. Ready-to-Send Backend Coordination Note

> We have defined a proposed `profile-completeness-v1` metric and `profile-context-v1` payload for future Readiness and Personalization. Before implementation, please confirm the actual Backend field mapping for university, specialization, academic level, enrollment/career/graduation status, availability, preferences, interests, visibility, and consent. We recommend stable IDs + display names for university/specialization where possible, controlled enum values for academic/status fields, and explicit null/N/A semantics. Please also confirm whether Profile Completeness will be calculated/persisted in Laravel using the approved versioned configuration; this is our recommended option because Laravel owns Student Profile data. No change is required to the current `skill-gap-v1` contract at this stage.
