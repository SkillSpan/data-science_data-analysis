# SkillSpan — Skill-Level Normalization Rules Specification

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Purpose:** Define deterministic rules for converting heterogeneous assessment/evidence values into the canonical SkillSpan `0.00–5.00` skill scale.

---

## 1. Objective

SkillSpan consumes evidence from different sources that may use different scoring systems, such as:

- direct skill levels;
- percentage-based assessments;
- rubric scores;
- certificate/evidence states;
- project performance scores;
- self-assessment levels.

Before evidence can contribute to Skill Evaluation, each source value must be converted into the canonical SkillSpan skill scale:

```text
0.00 <= normalized_skill_value <= 5.00
```

Normalization must be explicit, deterministic, versioned, and auditable.

This document does **not** modify `skill-gap-v1`.

---

## 2. Canonical Skill Scale

The approved SkillSpan scale is:

| Level | Label | Interpretation |
|---:|---|---|
| `0` | Not Demonstrated | No valid evidence or no demonstrated capability. |
| `1` | Awareness | Recognizes basic concepts and terminology. |
| `2` | Beginner | Can complete simple guided tasks. |
| `3` | Intermediate | Can complete standard tasks with limited support. |
| `4` | Advanced | Can solve complex tasks independently and justify decisions. |
| `5` | Expert | Can design, optimize, mentor, and handle unfamiliar complex scenarios. |

Normalized values may be decimal values between the anchor levels.

Examples:

```text
2.50
3.75
4.20
```

---

## 3. General Normalization Principles

### NORM-01 — Approved Rule Required

A raw source value must not enter Skill Evaluation unless an approved normalization rule exists for that source/value type.

### NORM-02 — Versioned Rule

Every normalization method that can affect analytical output must have a version identifier.

Example:

```text
percent-to-skill-v1
```

### NORM-03 — Validate Before Transform

The raw source value must be validated against its source range before conversion.

Example:

```text
percentage = 110
```

must be rejected before applying a `/20` conversion.

### NORM-04 — Canonical Output Range

The normalized result must satisfy:

```text
0.00 <= value <= 5.00
```

Out-of-range normalized values are invalid unless a specifically approved clipping rule exists.

### NORM-05 — No Silent Guessing

Unknown score formats, unsupported enums, text values, or missing mappings must not be converted heuristically.

They must be rejected or flagged as unmapped.

### NORM-06 — Reproducibility

The normalized evidence record or Skill Evaluation must preserve enough information to reproduce the conversion, including:

- raw value;
- raw scale/type;
- normalization rule/version;
- normalized value.

---

## 4. Direct 0–5 Skill Values

If a source already uses the approved SkillSpan `0–5` scale:

```text
normalized_value = raw_value
```

Validation:

```text
0.00 <= raw_value <= 5.00
```

Examples:

| Raw | Normalized |
|---:|---:|
| `0` | `0.00` |
| `2` | `2.00` |
| `3.5` | `3.50` |
| `5` | `5.00` |

Invalid:

```text
-1
5.01
8
```

---

## 5. Percentage-Based Assessments

The SRS provides an approved example mapping:

```text
normalized_value = percentage / 20
```

Recommended version identifier:

```text
percent-to-skill-v1
```

Valid source range:

```text
0 <= percentage <= 100
```

Examples:

| Percentage | Normalized Skill Value |
|---:|---:|
| `0` | `0.00` |
| `20` | `1.00` |
| `40` | `2.00` |
| `50` | `2.50` |
| `60` | `3.00` |
| `75` | `3.75` |
| `80` | `4.00` |
| `90` | `4.50` |
| `100` | `5.00` |

Important: `/20` is the current SRS-approved example/baseline. If Product/Domain later approves a nonlinear assessment mapping, it must receive a new normalization version.

---

## 6. Generic Linear Scale Conversion

For an approved numeric source scale `[source_min, source_max]`, a generic linear conversion to `[0,5]` may be defined as:

```text
normalized =
5 × (raw_value - source_min)
/
(source_max - source_min)
```

This rule must not be automatically applied to every scale.

It is only valid when:

1. the source scale is confirmed to be ordinal/interval in a way that supports linear conversion;
2. Product/Domain approves the mapping;
3. the normalization rule is versioned.

Example for a hypothetical approved `0–10` scale:

```text
normalized = raw / 2
```

Raw `7.5`:

```text
7.5 / 2 = 3.75
```

---

## 7. Rubric-Based Scores

Rubric evaluations may use:

- criterion-level scores;
- weighted dimensions;
- overall rubric percentages;
- source-specific score ranges.

The normalization path must be explicit.

Preferred sequence:

```text
Rubric criterion scores
        ↓
Approved rubric aggregation
        ↓
Rubric overall score
        ↓
Approved normalization rule
        ↓
0.00–5.00 skill value
```

The Skill Evaluation layer must not re-invent the rubric aggregation formula.

Required references should include:

```text
rubric_version
normalization_rule_version
skill_mapping_version
```

---

## 8. Binary / Pass-Fail Evidence

Approved v1 decision:

```text
Pass/Fail -> Skill Level normalization is OUT OF MVP
```

No binary-to-`0-5` normalization rule will be implemented in the MVP. A `pass`, `fail`, `true`, `false`, `completed`, or similar binary outcome must not be converted into a Skill Level unless a future approved requirement defines a versioned mapping.

If introduced later, it must be treated as a new requirement with a new normalization/configuration version rather than silently changing `skill-normalization-v1`.

## 9. Certificates

Approved v1 policy:

A verified certificate is a supporting evidence source, but certificate presence alone does not imply a specific proficiency level.

```text
Certificate with approved source-specific proficiency mapping
    -> normalize the mapped level to 0.00-5.00

Certificate without approved proficiency mapping
    -> do not create or invent a Skill Level
    -> may support Confidence as verified evidence
```

Therefore SkillSpan will not use a fixed default such as `certificate = 3.0`.

The configured `verified_certificate` source weight remains separate from certificate-to-proficiency normalization. A certificate contributes to Skill Level only when it carries an approved normalized proficiency value; otherwise it is supporting verified evidence for Confidence.

## 10. Self-Assessment

Self-assessment is expected to use the canonical `0–5` scale.

Therefore:

```text
normalized_value = submitted self-assessment level
```

subject to:

```text
0 <= level <= 5
```

Self-assessment has lower evidence weight and should not by itself create high confidence.

---

## 11. Project Performance

Project performance may produce Skill Evidence through approved rubric mappings.

The normalization sequence should therefore be:

```text
Finalized project evaluation
        ↓
Approved rubric/dimension mapping
        ↓
Approved score aggregation
        ↓
Canonical skill mapping
        ↓
Normalization to 0–5
```

Project completion alone is not enough to infer a skill value.

A finalized, mapped evaluation is required.

---

## 12. Rounding Rules

Canonical normalized evidence values should be represented with sufficient precision for deterministic calculation.

Recommended rule:

```text
- perform calculations using full internal precision;
- round normalized display/persisted analytical values to 2 decimal places where the contract requires it;
- round the final SkillLevel to 2 decimal places.
```

Do not repeatedly round intermediate arithmetic unless specifically required.

Example:

```text
77 / 20 = 3.85
```

No issue.

For repeating values:

```text
2 / 3 × 5 = 3.333333...
```

retain calculation precision and round the contracted output:

```text
3.33
```

---

## 13. Null, Missing, and Zero Semantics

These values must be distinguished:

### Missing / Null

Means no usable value was supplied.

Behavior:

```text
do not normalize;
do not inject artificial zero;
handle according to evidence availability rules.
```

### Numeric Zero

A valid value when the source scale allows zero.

Example:

```text
assessment percentage = 0
normalized_value = 0.00
```

This is different from missing evidence.

### Empty String

For numeric score fields:

```text
"" -> invalid / missing according to input validation
```

It must not be silently converted to zero.

---

## 14. Proposed Normalization Record

```json
{
  "source_type": "assessment_test",
  "raw_value": 80,
  "raw_scale": "percentage_0_100",
  "normalization_rule_version": "percent-to-skill-v1",
  "normalized_value": 4.0
}
```

This is an analytical representation, not a claim about current Backend fields.

---

## 15. Normalization Rule Registry

Recommended future configuration structure:

```json
{
  "normalization_config_version": "skill-normalization-v1",
  "rules": [
    {
      "rule_id": "direct-skill-0-5-v1",
      "source_scale": "skill_0_5",
      "method": "identity",
      "source_min": 0,
      "source_max": 5
    },
    {
      "rule_id": "percent-to-skill-v1",
      "source_scale": "percentage_0_100",
      "method": "divide",
      "divisor": 20,
      "source_min": 0,
      "source_max": 100
    }
  ]
}
```

This should be stored as versioned configuration rather than hidden constants.

---

## 16. Edge Cases

| Case | Required Behavior |
|---|---|
| Percentage = `101` | Reject before normalization. |
| Percentage = `-5` | Reject. |
| Direct skill level = `5.5` | Reject. |
| Raw numeric value is missing | Do not normalize; treat as unavailable evidence. |
| Raw numeric value is `0` | Accept if zero is valid for the source scale. |
| Unknown source scale | Reject/flag; no guessing. |
| Normalization version missing | Reject where reproducibility requires it. |
| Binary result without approved mapping | Do not generate skill value. |
| Certificate with no level mapping | Do not infer precise proficiency from certificate presence alone. |
| Rubric version unavailable | Do not generate mapped Skill Evidence. |
| Mapping yields >5 | Reject unless explicit approved clipping exists. |
| Mapping yields <0 | Reject. |
| Same evidence normalized twice under different versions | Preserve versioned results; do not silently overwrite history. |

---

## 17. Deterministic Test Vectors

### NORM-TV-01 — Direct 0–5

Input:

```json
{
  "raw_value": 3.5,
  "raw_scale": "skill_0_5",
  "rule": "direct-skill-0-5-v1"
}
```

Expected:

```json
{
  "normalized_value": 3.50
}
```

### NORM-TV-02 — Percentage 80

Input:

```json
{
  "raw_value": 80,
  "raw_scale": "percentage_0_100",
  "rule": "percent-to-skill-v1"
}
```

Expected:

```json
{
  "normalized_value": 4.00
}
```

### NORM-TV-03 — Percentage 75

Expected:

```text
75 / 20 = 3.75
```

### NORM-TV-04 — Percentage 100

Expected:

```text
100 / 20 = 5.00
```

### NORM-TV-05 — Invalid Percentage

Input:

```text
120
```

Expected:

```text
validation_error
```

No clipping to `5.00`.

### NORM-TV-06 — Missing Value

Input:

```text
null
```

Expected:

```text
no normalized value;
evidence unavailable;
do not substitute 0.00.
```

---

## 18. Distribution Validation Implications

Normalization quality should later be validated by monitoring:

- normalized values outside `0–5`;
- excessive concentration at `0` or `5`;
- unexpected spikes at exact integer levels;
- source-specific distributions;
- normalization failures;
- unmapped source score types;
- before/after changes when a normalization version is updated.

Detailed distribution monitoring belongs in `skill_distribution_validation.md`.

---

## 19. Versioning Rules

Recommended configuration versions:

```text
skill-normalization-v1
direct-skill-0-5-v1
percent-to-skill-v1
```

Create a new version if:

- formula changes;
- source range changes;
- rounding behavior materially changes;
- threshold/bucket mapping replaces linear mapping;
- source-specific meaning changes;
- rubric score conversion changes.

Historical evaluations must retain the normalization version used.

---

## 20. Backend / Product / Domain Confirmations Required

Before runtime implementation, confirm:

- which score formats the Backend currently exposes for assessments;
- whether item-level assessment results are percentages, points, or already normalized;
- actual self-assessment scale and field type;
- project/rubric score ranges;
- certificate score/level formats, if any;
- whether Backend performs any normalization before calling Data Science;
- where normalization rule/version will be stored;
- whether binary/pass-fail evidence should ever map to a proficiency level;
- exact rounding/persistence expectations.

---

## 21. Definition of Done

- [x] Canonical `0–5` target scale documented.
- [x] Direct 0–5 normalization defined.
- [x] Percentage `/20` baseline defined.
- [x] Generic linear conversion guarded by approval requirement.
- [x] Null vs zero semantics defined.
- [x] Unsupported/binary/certificate cases protected from silent inference.
- [x] Rounding behavior documented.
- [x] Deterministic normalization vectors documented.
- [x] Versioning rules documented.
- [ ] Backend raw score formats confirmed.
- [ ] Rubric normalization contract confirmed.
- [x] Certificate normalization policy confirmed for v1: no fixed level; approved proficiency mapping only.
- [ ] Machine-readable normalization config approved.
- [ ] Runtime normalization tests implemented after approval.
