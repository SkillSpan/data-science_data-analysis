# SkillSpan — Evidence Source Weights & Configuration Specification

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Purpose:** Define the default evidence-source weights, configuration rules, and deterministic handling of missing/invalid evidence used in Skill Evaluation.

---

## 1. Objective

SkillSpan evaluates a learner's Skill from multiple evidence sources rather than relying on a single questionnaire or self-report.

This document defines:

- the SRS-approved default evidence-source weights;
- how available evidence is re-weighted;
- which evidence may contribute;
- how evidence weights are versioned;
- what is deliberately **not** decided yet;
- edge cases and validation rules.

This document does **not** modify `skill-gap-v1`.

---

## 2. SRS-Approved Default Evidence Weights

The current SkillSpan SRS defines the following baseline:

| Evidence Source | Default Weight | Rationale |
|---|---:|---|
| `self_assessment` | 0.10 | Supports cold start but is subject to bias. |
| `assessment_test` | 0.30 | Provides standardized, verified evidence. |
| `project_performance` | 0.35 | Measures practical application and is the strongest default signal. |
| `expert_evaluation` | 0.20 | Adds professional judgment based on a rubric. |
| `verified_certificate` | 0.05 | Supports evidence but does not alone prove applied competence. |

Configured total:

```text
0.10 + 0.30 + 0.35 + 0.20 + 0.05 = 1.00
```

These are the **default configuration values**, not hard-coded constants that may never change.

---

## 3. Skill-Level Aggregation Baseline

The SRS defines the Skill Level calculation as:

```text
SkillLevel(s) =
SUM(value_i × weight_i)
/
SUM(weight_i for available valid evidence)
```

where:

- `value_i` is the evidence value normalized to the canonical `0.00–5.00` Skill scale;
- `weight_i` is the configured source weight;
- only **available valid evidence** participates in the Skill Level calculation.

The result is rounded to two decimal places and constrained to:

```text
0.00 <= skill_level <= 5.00
```

---

## 4. Missing Optional Evidence Rule

Missing optional evidence must **not** be inserted as value `0`.

Instead, the calculation re-normalizes across the evidence sources that are actually available and valid.

### Example

Available evidence:

```text
assessment_test     value = 4.0, weight = 0.30
project_performance value = 3.0, weight = 0.35
```

Unavailable:

```text
self_assessment
expert_evaluation
verified_certificate
```

Calculation:

```text
SkillLevel =
(4.0 × 0.30 + 3.0 × 0.35)
/
(0.30 + 0.35)

= 2.25 / 0.65
= 3.461538...
= 3.46
```

Missing sources contribute neither a false zero value nor their unused weight to the raw Skill Level denominator.

---

## 5. Evidence Eligibility Rules

### EWT-01 — Available

Evidence must exist and be associated with the learner and canonical Skill.

### EWT-02 — Valid

Evidence must pass the applicable source-specific validation.

Examples include:

- valid assessment result;
- finalized project/rubric evaluation;
- accepted evidence record;
- valid normalized score.

### EWT-03 — Verification State

Rejected, invalid, duplicate, or voided evidence must not positively contribute to the current Skill Evaluation.

The SRS also states that only verified, current, authorized evidence contributes positively to Skill Evaluation.

### EWT-04 — Canonical Skill Mapping

Evidence must resolve to a canonical `skill_id`.

Unmapped evidence must not be guessed into a Skill.

### EWT-05 — One Contribution per Intended Evidence Record

Duplicate evidence must not be silently double-counted.

Duplicate detection may use learner, Skill, source, reference, and timestamp attributes as defined by platform requirements.

---

## 6. Evidence Source Weight Configuration

Recommended versioned configuration representation:

```json
{
  "evidence_weight_config_version": "evidence-weights-v1",
  "weights": {
    "self_assessment": 0.10,
    "assessment_test": 0.30,
    "project_performance": 0.35,
    "expert_evaluation": 0.20,
    "verified_certificate": 0.05
  }
}
```

This is a proposed machine-readable representation, not a claim about current Backend field names.

---

## 7. Configuration Validation

A weight configuration is valid when:

1. every configured weight is numeric;
2. every weight is non-negative;
3. at least one source has a positive weight;
4. source identifiers are recognized;
5. the configuration has a version identifier;
6. duplicate source keys are not permitted;
7. changes are auditable;
8. historical evaluations preserve the version used.

The SRS allows approved positive weights to be normalized when the configured total differs from `1.00`.

Therefore:

- a positive total different from `1.00` is not automatically a mathematical failure;
- the system may normalize the configured weights;
- a zero or negative total must be rejected.

---

## 8. Distinguish Source Weight from Confidence Factors

Evidence source weight and Confidence are related but are not the same concept.

### Source Weight

Answers:

> How strongly should this type of evidence influence the calculated Skill Level?

Example:

```text
project_performance = 0.35
```

### Verification / Recency Factors

Answer:

> How strongly does the available evidence support confidence in that Skill Level?

The current confidence baseline uses source weight together with verification and recency factors.

Therefore Data Science must not multiply recency into the raw Skill Level unless a future approved configuration explicitly changes that rule.

---

## 9. Recency Boundary

Current SRS baseline:

| Evidence Age | Default Recency Factor |
|---|---:|
| `0–6 months` | 1.00 |
| `>6–12 months` | 0.90 |
| `>12–24 months` | 0.75 |
| `>24 months` | 0.60 |

Important:

- recency primarily affects **Confidence**;
- it does not automatically reduce the historical demonstrated Skill Level;
- faster-changing Skill categories may use different recency thresholds only after approved configuration/domain review.

Detailed confidence behavior belongs in `confidence_rules.md`.

---

## 10. Pending Evidence — Open Configuration Decision

The SRS defines:

```text
verified evidence -> verification factor = 1.0
rejected/missing/expired evidence -> verification factor = 0.0
pending evidence -> configurable partial value
```

However, the current SRS does **not** define the exact numeric multiplier for pending evidence.

Therefore this specification intentionally does **not** invent one.

Required decision:

```text
pending_verification_factor = TBD
```

This must be approved before deterministic confidence vectors involving pending evidence are finalized.

---

## 11. Evidence Source Canonical Codes

For Data Science configuration, stable machine-readable source codes are recommended:

```text
self_assessment
assessment_test
project_performance
expert_evaluation
verified_certificate
```

Human-readable labels may change without changing these analytical source identities.

Exact Backend source/status identifiers still require confirmation.

---

## 12. Multiple Evidence Records from the Same Source

The default SRS weights are defined by **evidence source**, but the SRS does not fully specify how multiple valid records from the same source should be collapsed before cross-source weighting.

Example:

```text
SQL:
assessment_test #1 = 3.5
assessment_test #2 = 4.2
assessment_test #3 = 4.0
```

Possible policies include:

- latest valid record;
- approved aggregation across records;
- highest-quality/final record;
- time-aware aggregation.

No policy should be silently assumed.

**Status: Backend/Product/Data Science decision required.**

Until approved, deterministic implementation must not invent an aggregation policy.

---

## 13. Evidence Weight Edge Cases

| Case | Required Behavior |
|---|---|
| No evidence exists | No demonstrated evidence; downstream behavior handled by Skill Evaluation edge-case rules. |
| Only self-assessment exists | Calculate provisional result using available valid evidence; Confidence remains low according to confidence rules. |
| Optional evidence source missing | Re-normalize across available valid evidence. |
| Evidence source weight = 0 | Source does not contribute; configuration must still retain valid positive total. |
| Negative source weight | Reject configuration. |
| All configured weights = 0 | Reject configuration. |
| Unknown source code | Reject or flag configuration/evidence. |
| Rejected evidence | Do not positively contribute. |
| Duplicate evidence | Prevent/flag; do not double-count. |
| Unmapped Skill evidence | Exclude/flag; do not guess. |
| Config version changed | New evaluations use new version; historical evaluations preserve old version. |
| Multiple valid records for one source | Apply only an approved same-source aggregation policy; otherwise require decision. |

---

## 14. Deterministic Examples

### Vector EWT-01 — All five sources available

```text
self_assessment        = 3.0
assessment_test        = 4.0
project_performance    = 3.5
expert_evaluation      = 4.5
verified_certificate   = 4.0
```

Calculation:

```text
(3.0×0.10)
+ (4.0×0.30)
+ (3.5×0.35)
+ (4.5×0.20)
+ (4.0×0.05)

= 0.30 + 1.20 + 1.225 + 0.90 + 0.20
= 3.825

denominator = 1.00

SkillLevel = 3.825 -> 3.83
```

Expected:

```json
{
  "expected_skill_level": 3.83,
  "evidence_weight_config_version": "evidence-weights-v1"
}
```

### Vector EWT-02 — Only Assessment + Project

```text
assessment_test     = 4.0
project_performance = 3.0
```

Expected:

```text
(4.0×0.30 + 3.0×0.35) / (0.30+0.35)
= 3.46
```

### Vector EWT-03 — Missing Certificate

Missing certificate is **not** treated as:

```text
verified_certificate = 0.0
```

Instead, its `0.05` is removed from the available-evidence denominator.

---

## 15. Versioning Rules

Recommended configuration version:

```text
evidence-weights-v1
```

Create a new version when:

- any source weight changes;
- a source is added or removed;
- source semantics materially change;
- same-source aggregation rules change in a way that alters output;
- verification eligibility rules materially change.

Historical Skill Evaluations must retain the configuration version used.

---

## 16. Backend / Product Confirmations Required

Before runtime implementation, confirm:

- actual Backend source codes;
- actual verification-status codes;
- whether Data Science receives individual evidence records or already-aggregated per-source values;
- policy for multiple valid records from the same source;
- exact pending-evidence verification multiplier;
- whether expired evidence is represented as a status or derived from dates/configuration;
- where evidence-weight configuration/version is stored;
- whether source weights may vary by Skill category or assessment type in the MVP.

---

## 17. Definition of Done

- [x] SRS default evidence weights documented.
- [x] Weighted Skill Level baseline documented.
- [x] Missing-evidence re-normalization rule documented.
- [x] Evidence eligibility rules documented.
- [x] Configuration validation documented.
- [x] Source weight vs Confidence distinction documented.
- [x] Initial deterministic weight examples documented.
- [ ] Backend evidence source/status codes confirmed.
- [ ] Same-source aggregation rule confirmed.
- [ ] Pending evidence multiplier confirmed.
- [ ] Machine-readable configuration approved.
- [ ] Runtime tests implemented after approval.
