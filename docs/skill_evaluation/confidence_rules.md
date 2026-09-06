# SkillSpan — Confidence Calculation Rules Specification

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Purpose:** Define how SkillSpan calculates and interprets confidence in a calculated Skill Level using evidence source weight, verification state, and evidence recency.

---

## 1. Objective

A Skill Level answers:

> How strong is the learner's demonstrated capability for this Skill?

A Confidence Score answers:

> How strongly is that Skill Level supported by available evidence?

These two values must remain separate.

A learner may have:

- a high Skill Level with low Confidence if evidence is sparse or weak;
- a moderate Skill Level with high Confidence if evidence is recent, verified, and diverse;
- a provisional result when only self-assessment exists.

This specification does **not** modify `skill-gap-v1`.

---

## 2. SRS Baseline Formula

The current SkillSpan SRS defines:

```text
Confidence(s) =
100 × SUM(weight_i × verified_i × recency_i)
/
SUM(all configured weights)
```

where:

- `weight_i` = configured evidence-source weight;
- `verified_i` = verification multiplier;
- `recency_i` = recency factor;
- denominator = sum of **all configured evidence-source weights**.

Important:

- Confidence is not the same as Skill Level.
- Missing evidence may reduce Confidence.
- Missing optional evidence must not be injected as a false Skill Level value of zero.
- Recency primarily affects Confidence, not the raw historical demonstrated Skill Level.

---

## 3. Default Evidence Source Weights

Current evaluation baseline aligned to Backend source identifiers:

| Evidence Source | Weight |
|---|---:|
| `self_assessment` | 0.10 |
| `assessment_test` | 0.30 |
| `project_performance` | 0.35 |
| `expert_evaluation` | 0.20 |
| `certificate` | 0.05 |

Configured denominator:

```text
1.00
```

If a future approved configuration uses a positive total different from `1.00`, the denominator uses the configured total consistently.

---

## 4. Verification Multipliers

The SRS establishes:

```text
verified evidence                 = 1.00
missing evidence                  = 0.00
rejected evidence                 = 0.00
expired evidence                  = 0.00
pending evidence                  = 0.50 (Approved v1 configurable default)
```

### CONF-VER-01 — Verified

Verified evidence contributes its full source weight, adjusted by recency.

### CONF-VER-02 — Rejected / Missing / Expired

These states contribute zero to the Confidence numerator.

### CONF-VER-03 — Pending

Approved v1 decision:

```text
pending_verification_factor = 0.50
```

This factor is configurable and versioned under `evidence-verification-v1`. It contributes partially to Confidence only; pending evidence must not positively contribute to the calculated Skill Level until it becomes verified.

---

## 5. Default Recency Factors

Current evaluation baseline aligned to Backend source identifiers:

| Evidence Age | Recency Factor |
|---|---:|
| `0–6 months` | 1.00 |
| `>6–12 months` | 0.90 |
| `>12–24 months` | 0.75 |
| `>24 months` | 0.60 |

Recommended version identifier:

```text
evidence-recency-v1
```

### CONF-REC-01 — Boundary Semantics

The exact timestamp boundary must be deterministic.

Recommended interpretation pending Backend date-handling confirmation:

```text
age <= 6 months            -> 1.00
6 months < age <= 12       -> 0.90
12 months < age <= 24      -> 0.75
age > 24 months            -> 0.60
```

### CONF-REC-02 — Timezone

Evidence timestamps used for recency must use ISO 8601 with timezone information or be normalized consistently before age calculation.

### CONF-REC-03 — Future Evidence Dates

Evidence dated materially in the future is invalid and must be rejected/flagged rather than treated as maximally recent.

### CONF-REC-04 — Skill-Category Overrides

Faster-changing Skill categories may use shorter approved recency windows.

Such overrides require:

- explicit configuration;
- category/domain approval;
- independent versioning;
- reproducible historical retention.

No category-specific override is assumed in this v1 baseline.

---

## 6. Confidence Interpretation Bands

The SRS defines:

| Score | Band | Interpretation |
|---:|---|---|
| `0–29` | Low | Insufficient verified evidence; result is provisional. |
| `30–59` | Moderate | Some verified evidence but limited diversity or recency. |
| `60–79` | Good | Multiple relevant and reasonably recent evidence sources. |
| `80–100` | High | Diverse, recent, verified, and practical evidence. |

Recommended machine-readable codes:

```text
low
moderate
good
high
```

Exact Backend/UI labels should be confirmed before runtime contract implementation.

---

## 7. Confidence vs Evidence Diversity

The formula indirectly rewards evidence diversity because each missing source contributes zero to the numerator while the configured denominator remains fixed.

Example:

If only `assessment_test` is verified and current:

```text
Confidence =
100 × (0.30 × 1.00 × 1.00)
/
1.00

= 30.00
```

This yields only Moderate Confidence even if the Assessment-derived Skill Level itself is high.

This behavior is intentional under the current SRS baseline.

---

## 8. Deterministic Examples

### CONF-TV-01 — Only Current Assessment Test

Input:

```text
assessment_test:
  weight = 0.30
  verified = 1.00
  recency = 1.00

all other sources:
  verification contribution = 0
```

Calculation:

```text
Confidence =
100 × 0.30
/
1.00

= 30.00
```

Expected:

```json
{
  "confidence_score": 30.00,
  "confidence_band": "moderate"
}
```

---

### CONF-TV-02 — Current Assessment + Current Project

Input:

```text
assessment_test:
  0.30 × 1.00 × 1.00 = 0.30

project_performance:
  0.35 × 1.00 × 1.00 = 0.35
```

Calculation:

```text
Confidence =
100 × (0.30 + 0.35)
/
1.00

= 65.00
```

Expected:

```json
{
  "confidence_score": 65.00,
  "confidence_band": "good"
}
```

---

### CONF-TV-03 — All Sources Current and Verified

Numerator:

```text
0.10 + 0.30 + 0.35 + 0.20 + 0.05 = 1.00
```

Expected:

```text
Confidence = 100.00
Band = high
```

---

### CONF-TV-04 — Old Project Evidence

Input:

```text
assessment_test:
  weight = 0.30
  verified = 1.00
  recency = 1.00

project_performance:
  weight = 0.35
  verified = 1.00
  recency = 0.75
```

Calculation:

```text
assessment contribution = 0.30
project contribution    = 0.2625

Confidence =
100 × (0.30 + 0.2625)
/
1.00

= 56.25
```

Expected:

```json
{
  "confidence_score": 56.25,
  "confidence_band": "moderate"
}
```

---

### CONF-TV-05 — Only Self-Assessment

Input:

```text
self_assessment:
  0.10 × 1.00 × 1.00 = 0.10
```

Expected:

```text
Confidence = 10.00
Band = low
```

This supports the SRS rule that self-assessment alone may create a provisional Skill Level but not high Confidence.

---

## 9. Missing Evidence Semantics

For Confidence:

```text
missing evidence -> numerator contribution = 0
```

For Skill Level:

```text
missing optional evidence -> excluded from available-evidence weighted denominator
```

These two denominator behaviors are intentionally different and must not be conflated.

---

## 10. Duplicate Evidence

Duplicate evidence must not increase Confidence.

If two records refer to the same underlying evidence event, they must be:

- deduplicated;
- rejected;
- or flagged according to Backend evidence rules.

Confidence must reflect distinct valid evidence, not duplicated records.

---

## 11. Multiple Records from the Same Source

Approved v1 policy for multiple valid records from the same evidence source:

```text
Same skill + same source + same reference
    -> keep only the latest/final valid record

Distinct references from the same source
    -> aggregate records within the source first
    -> use recency-aware aggregation
    -> apply the configured source weight once
```

Backend persistence contract: the current migrations expose `reference`, `source_record_type`, and `source_record_id`. Backend has confirmed `(source_record_type, source_record_id)` as the canonical source identity when both values are present. When the original source identity is unavailable, `reference` is the fallback identity used by application logic to detect the same evidence and prevent duplication. The current schema does not enforce DB-level uniqueness for the source identity; any such constraint requires a separate migration after NULL and source-record behavior are defined. This identity rule refines how "same reference" is detected and does not change the approved v1 same-source aggregation policy.

Recommended source-level aggregation:

```text
source_value = SUM(value_i * recency_i) / SUM(recency_i)
```

The source category must not gain additional configured weight simply because more evidence records exist. This prevents evidence-quantity inflation while still allowing distinct, recent evidence to influence the source-level value.

For Confidence, the source contribution is likewise capped by its configured source weight. Duplicate records must not increase Confidence.

---

## 12. Confidence Edge Cases

| Case | Required Behavior |
|---|---|
| No evidence | Confidence = `0.00`. |
| Only self-assessment | Low/provisional confidence. |
| Verified evidence with missing date | Invalid input. Backend requires `skill_evidences.evidence_date` as NOT NULL, and FastAPI must keep `evidence_date` required. No fallback recency policy is used in v1. |
| Rejected evidence | Zero confidence contribution. |
| Expired evidence | Zero verification contribution under current SRS wording. |
| Pending evidence | Use verification factor `0.50` under `evidence-verification-v1`; it contributes to Confidence only and not to Skill Level until verified. |
| Future evidence date | Reject/flag. |
| Duplicate evidence | Do not double-count. |
| Unknown source code | Reject/flag. |
| Unknown verification status | Reject/flag. |
| Recency config missing | Do not invent a factor. |
| Configured denominator = 0 | Reject configuration. |
| Confidence calculation >100 | Configuration/implementation error; reject or flag. |
| Confidence calculation <0 | Configuration/implementation error. |

---

## 13. Proposed Confidence Output

```json
{
  "skill_id": 7,
  "confidence_score": 65.0,
  "confidence_band": "good",
  "evidence_weight_config_version": "evidence-weights-v1",
  "verification_config_version": "evidence-verification-v1",
  "recency_config_version": "evidence-recency-v1",
  "confidence_algorithm_version": "skill-confidence-v1"
}
```

This is a proposed analytical output, not a claim about current Backend fields.

---

## 14. Versioning

Recommended identifiers:

```text
skill-confidence-v1
evidence-verification-v1
evidence-recency-v1
evidence-weights-v1
```

Create a new configuration/algorithm version when any material factor changes, including:

- source weights;
- verification multipliers;
- pending multiplier;
- recency windows;
- recency factors;
- band thresholds;
- same-source aggregation behavior;
- confidence formula itself.

Historical Skill Evaluations must retain the versions used.

---

## 15. Monitoring / Validation

Data Science should later monitor:

- overall confidence-score distribution;
- confidence distribution by evidence source mix;
- percentage of Skills with Low/Moderate/Good/High Confidence;
- percentage of Skills supported only by self-assessment;
- stale-evidence rates;
- pending-evidence rates;
- rejected/expired evidence rates;
- missing evidence timestamps;
- anomalous sudden shifts after configuration version changes.

These metrics feed the broader `skill_distribution_validation.md` plan.

---

## 16. Backend / Product Confirmations Required

Before runtime implementation, confirm:

- exact verification-status values;
- exact pending verification multiplier;
- whether expired is stored or derived;
- evidence timestamp used for recency;
- timezone/date semantics;
- `evidence_date` is required end-to-end; no missing-date fallback policy is used in v1;
- same-source multiple-record policy;
- whether source contribution is capped at source weight;
- whether Backend already computes any verification/recency factors;
- where each configuration version is stored;
- whether confidence bands are persisted or derived for display.

---

## 17. Definition of Done

- [x] Confidence purpose separated from Skill Level.
- [x] SRS confidence formula documented.
- [x] Verification semantics documented.
- [x] Recency factors documented.
- [x] Confidence bands documented.
- [x] Deterministic baseline vectors documented.
- [x] Missing evidence behavior documented.
- [x] Edge cases documented.
- [x] Versioning requirements documented.
- [x] Pending verification multiplier confirmed as `0.50` for v1.
- [x] Same-source aggregation policy confirmed for v1.
- [x] Missing-date behavior confirmed: `evidence_date` is required; no fallback policy in v1.
- [ ] Machine-readable config approved.
- [ ] Runtime deterministic confidence tests implemented after approval.
