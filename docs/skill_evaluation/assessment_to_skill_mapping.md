# SkillSpan — Assessment-to-Skill Mapping Specification

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Purpose:** Define how assessment results and evaluated items contribute to canonical Skill evaluations in a deterministic, versioned, auditable way.

---

## 1. Objective

SkillSpan requires an explicit mapping between assessment content and canonical skills so that an assessment score is never converted into a skill level without a documented relationship.

The mapping layer must answer:

- Which canonical skill does an assessment or assessment item measure?
- How strongly does it contribute to that skill?
- Which mapping/configuration version was used?
- How is the assessment result normalized before entering Skill Evaluation?
- How are multi-skill assessment items handled?
- What happens when a mapping is missing, invalid, retired, or ambiguous?

This document defines the mapping contract only. It does **not** modify `skill-gap-v1`.

---

## 2. SRS Baseline

The current SkillSpan requirements establish that:

- verified assessment results must be mapped to canonical skills;
- assessment results must be normalized to the approved `0.00–5.00` skill scale;
- mappings must retain enough information for reproducibility;
- project/rubric evaluations may create skill evidence only through approved mappings;
- unmapped or invalid values must not silently affect Skill Evaluation.

---

## 3. Mapping Unit

The preferred analytical mapping unit is:

```text
Assessment Item / Assessment Component
        ↓
Canonical Skill
        ↓
Contribution Weight
```

This is more precise than mapping an entire assessment to a single skill because one assessment may measure multiple skills.

When the Backend only exposes an assessment-level result, an assessment-level mapping may be used, but the granularity must be explicit and versioned.

---

## 4. Proposed Canonical Mapping Record

| Field | Type | Requirement | Purpose |
|---|---|---|---|
| `mapping_id` | positive integer / stable identifier | Required | Stable identity of the mapping record. |
| `assessment_id` | positive integer / stable identifier | Required | Assessment owning the mapped content. |
| `assessment_item_id` | positive integer or null | Conditional | Specific question/task/component when item-level mapping is supported. |
| `skill_id` | positive integer | Required | Canonical Skill identifier. |
| `contribution_weight` | decimal > 0 | Required | Relative contribution of the item/component to the mapped skill. |
| `mapping_version` | version identifier | Required | Version used for reproducibility. |
| `normalization_rule_id` | version/reference or null | Recommended | Identifies the approved source-to-0–5 conversion rule. |
| `status` | controlled value | Recommended | Active/retired/superseded semantics; exact values require confirmation. |
| `effective_from` | ISO 8601 timestamp/date or null | Optional | Effective start of the mapping version. |
| `effective_to` | ISO 8601 timestamp/date or null | Optional | Effective end if superseded/retired. |

This is a **proposed analytical contract**, not a claim about current Laravel table/field names.

---

## 5. Mapping Rules

### MAP-01 — Canonical Skill Reference

Every mapping must reference a valid canonical `skill_id`.

Free-text skill names must not be used as the analytical mapping identity.

### MAP-02 — Approved Mapping Only

Only approved and active mappings may contribute to a new Skill Evaluation.

Draft, retired, invalid, or unresolved mappings must not silently contribute.

### MAP-03 — Positive Contribution Weight

`contribution_weight` must be greater than zero.

Zero or negative mapping weights are invalid.

### MAP-04 — Multi-Skill Items

One assessment item may map to more than one canonical skill when domain experts approve that relationship.

Example:

```text
Assessment Item 42
  -> SQL               weight 0.70
  -> Data Modeling     weight 0.30
```

The mapping must not be inferred automatically from wording alone.

### MAP-05 — Weight Normalization

When multiple mappings contribute to the same analytical grouping, positive weights may be normalized to sum to `1.00` during calculation if the approved configuration does not already sum to one.

The original configured weights and the normalized weights should remain explainable.

### MAP-06 — No Mapping, No Contribution

If an assessment result or item has no approved Skill mapping, it must not contribute to a Skill Evaluation.

The system should flag the condition as a mapping/data-quality issue rather than guessing.

### MAP-07 — Version Retention

Every calculated Skill Evaluation that depends on an assessment mapping must retain or be reproducible from the mapping version used.

A mapping change must not silently rewrite historical Skill Evaluations.

### MAP-08 — Normalization Before Aggregation

Assessment values must be converted using an approved normalization rule before they enter the Skill Evaluation weighted-average calculation.

Example baseline allowed by the SRS:

```text
percentage score -> percentage / 20 -> 0.00–5.00
```

The exact rule must be versioned.

### MAP-09 — Verification State

Only assessment evidence considered valid under the approved verification rules may positively contribute to the current Skill Evaluation.

Rejected, expired, invalid, or duplicate evidence must not increase the evaluated skill level.

---

## 6. Assessment-Level vs Item-Level Mapping

### Item-Level Mapping — Preferred

Use when question/task/component results are available.

Advantages:

- precise Skill attribution;
- better explainability;
- supports assessments covering multiple skills;
- easier distribution and mapping-quality analysis.

### Assessment-Level Mapping — Allowed Fallback

Use when only an overall assessment result is available.

Required safeguards:

- explicitly mark the mapping granularity;
- define which skills receive the result;
- define contribution weights;
- retain the mapping version;
- do not pretend assessment-level mapping has item-level precision.

---

## 7. Proposed Mapping Example

```json
{
  "mapping_id": 1001,
  "assessment_id": 20,
  "assessment_item_id": 42,
  "skill_id": 7,
  "contribution_weight": 0.7,
  "mapping_version": "assessment-skill-map-v1",
  "normalization_rule_id": "percent-to-skill-v1",
  "status": "active",
  "effective_from": "2026-09-01T00:00:00Z",
  "effective_to": null
}
```

A second record may map the same item to another Skill:

```json
{
  "mapping_id": 1002,
  "assessment_id": 20,
  "assessment_item_id": 42,
  "skill_id": 11,
  "contribution_weight": 0.3,
  "mapping_version": "assessment-skill-map-v1",
  "normalization_rule_id": "percent-to-skill-v1",
  "status": "active",
  "effective_from": "2026-09-01T00:00:00Z",
  "effective_to": null
}
```

---

## 8. Deterministic Contribution Example

Assume:

```text
Assessment Item Score = 80%
Normalization rule     = percentage / 20
Normalized item value  = 4.00

Mappings:
SQL            = 0.70
Data Modeling  = 0.30
```

The evidence contribution created from this item is based on the normalized value `4.00`, while the mapping weights determine how strongly the item represents each skill in the approved assessment design.

The exact downstream aggregation with other evidence sources belongs to the Skill Evaluation algorithm specification.

---

## 9. Validation Rules

A mapping record is analytically valid when:

1. `assessment_id` exists.
2. `assessment_item_id`, when supplied, belongs to the specified assessment.
3. `skill_id` resolves to an approved canonical Skill.
4. `contribution_weight > 0`.
5. `mapping_version` is present.
6. the normalization rule is approved for the source score type.
7. active date ranges do not contradict each other.
8. superseded mappings do not remain active unintentionally.
9. duplicate active mapping records do not double-count the same assessment item and Skill.
10. ambiguous or missing Skill references are rejected/flagged.

---

## 10. Edge Cases

| Case | Required Behavior |
|---|---|
| Assessment item has no Skill mapping | Exclude from Skill Evaluation and flag mapping gap. |
| Mapping references unknown Skill | Reject/flag; do not guess. |
| Mapping weight = 0 | Reject as invalid mapping. |
| Mapping weight < 0 | Reject. |
| Multiple mappings sum to >1 | Normalize positive weights only if approved rule allows it; retain configured values. |
| Multiple mappings sum to <1 | Same rule as above; do not invent an extra Skill. |
| Same item→Skill mapping duplicated | Prevent or flag duplicate to avoid double-counting. |
| Mapping version changed | New evaluations use new version; historical evaluations retain old version. |
| Retired Skill referenced by new mapping | Reject or require approved supersession target. |
| Assessment score out of source range | Reject before normalization. |
| Missing normalization rule | Do not evaluate until an approved rule exists. |
| Only overall assessment score exists | Use explicit assessment-level mapping fallback. |

---

## 11. Data Quality Checks

The Data Science / Data Analysis workflow should be able to measure:

- percentage of assessment items with at least one approved Skill mapping;
- items mapped to multiple skills;
- duplicate mappings;
- mappings to retired/unknown Skills;
- mapping weights outside allowed rules;
- assessments with no active mapping version;
- distribution of mapped items per Skill;
- Skills receiving unusually little or excessive assessment coverage;
- failed normalization/mapping events.

These checks support later Skill-level distribution validation.

---

## 12. Versioning Proposal

Recommended independent configuration identifier:

```text
assessment-skill-map-v1
```

A new mapping version is required when changes can alter analytical results, including:

- item→Skill relationship changes;
- contribution weights change;
- an assessment item is added/removed from analytical scoring;
- mapping granularity changes;
- normalization rule reference changes.

Historical results must preserve the version used.

---

## 13. Backend / Product / Domain Confirmations Required

Before runtime implementation, confirm:

- whether current assessments expose item-level results or only overall scores;
- actual Backend identifiers for assessment and assessment items;
- existing assessment-to-Skill mapping tables/models, if any;
- who approves mappings;
- whether one item may map to multiple Skills;
- how contribution weights are stored;
- exact mapping lifecycle/status values;
- whether mapping version already exists in Backend;
- how normalization rule/version is referenced;
- whether Backend sends canonical mapped evidence to Data Science or sends raw assessment results plus mapping metadata.

---

## 14. Definition of Done

- [x] Canonical mapping direction defined.
- [x] Item-level and assessment-level mapping semantics defined.
- [x] Contribution weight rules defined.
- [x] Missing/invalid mapping behavior defined.
- [x] Versioning requirements defined.
- [x] Edge cases documented.
- [x] Data-quality validation metrics identified.
- [ ] Backend assessment schema confirmed.
- [ ] Mapping ownership/approval confirmed.
- [ ] Runtime payload contract approved.
- [ ] Deterministic mapping tests implemented after approval.
