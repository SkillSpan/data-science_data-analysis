# SkillSpan — Skill Evaluation Edge Cases Matrix

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Purpose:** Define deterministic behavior for abnormal, incomplete, ambiguous, stale, duplicated, invalid, or version-sensitive inputs affecting Skill Evaluation.

---

## 1. Objective

Skill Evaluation must fail safely and predictably.

Edge-case handling must ensure that the system does not:

- fabricate a Skill Level;
- silently convert missing evidence to zero;
- double-count duplicate evidence;
- guess unknown Skill mappings;
- overwrite historical results after algorithm/configuration changes;
- treat rejected or invalid evidence as positive evidence;
- use unsupported normalization rules;
- produce outputs outside approved ranges.

This document consolidates Skill Evaluation-specific edge cases from the SRS and the supporting Data Science specifications.

It does **not** modify `skill-gap-v1`.

---

## 2. Edge-Case Principles

### EC-P01 — Deterministic Behavior

The same validated input and the same algorithm/configuration versions must produce the same output.

### EC-P02 — Fail Closed on Invalid Analytical Inputs

Invalid mappings, unsupported normalization rules, invalid score ranges, or unknown canonical identifiers must be rejected or flagged rather than guessed.

### EC-P03 — Missing Is Not Zero

No evidence and demonstrated level `0.00` are analytically different states.

### EC-P04 — Historical Reproducibility

Algorithm, taxonomy, mapping, rubric, normalization, evidence-weight, confidence, and configuration versions must remain traceable when they materially affect the result.

### EC-P05 — No Silent History Rewrite

Corrected or superseded evaluations create controlled revisions; prior results remain auditable.

### EC-P06 — Explanation Required

Where an edge case changes, blocks, limits, or makes a result provisional, the reason should be represented in the analytical explanation or validation output.

---

# 3. Canonical Skill / Taxonomy Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-SKL-01` | `skill_id` missing | Reject analytical input. | `MISSING_SKILL_ID` |
| `EC-SKL-02` | `skill_id <= 0` | Reject. | `INVALID_SKILL_ID` |
| `EC-SKL-03` | Unknown canonical Skill | Reject/flag; do not create Skill automatically. | `UNKNOWN_SKILL` |
| `EC-SKL-04` | Free-text Skill name without canonical mapping | Do not infer analytical identity. | `UNMAPPED_SKILL` |
| `EC-SKL-05` | Alias maps to multiple active Skills | Do not guess; require disambiguation/review. | `AMBIGUOUS_SKILL_ALIAS` |
| `EC-SKL-06` | Retired Skill referenced by historical evaluation | Preserve historical reference. | valid historical record |
| `EC-SKL-07` | Retired Skill used in new mapping | Reject or require approved supersession target. | `RETIRED_SKILL_MAPPING` |
| `EC-SKL-08` | Skill supersedes itself | Reject taxonomy configuration. | `INVALID_SUPERSESSION` |
| `EC-SKL-09` | Supersession cycle | Reject taxonomy publication/configuration. | `SUPERSESSION_CYCLE` |
| `EC-SKL-10` | Taxonomy version missing | Reject where required for reproducibility. | `MISSING_TAXONOMY_VERSION` |

---

# 4. Assessment-to-Skill Mapping Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-MAP-01` | Assessment item has no approved Skill mapping | Exclude from Skill Evaluation and flag mapping gap. | `FAILED_MAPPING` |
| `EC-MAP-02` | Mapping references unknown Skill | Reject mapping. | `UNKNOWN_SKILL` |
| `EC-MAP-03` | Mapping weight = `0` | Reject mapping as non-contributing/invalid under current contract. | `INVALID_MAPPING_WEIGHT` |
| `EC-MAP-04` | Mapping weight < `0` | Reject. | `INVALID_MAPPING_WEIGHT` |
| `EC-MAP-05` | Duplicate active item→Skill mapping | Prevent/flag duplicate contribution. | `DUPLICATE_MAPPING` |
| `EC-MAP-06` | One item maps to multiple Skills | Allowed only when explicitly approved with contribution weights. | valid multi-skill mapping |
| `EC-MAP-07` | Positive mapping weights do not sum to `1.00` | Normalize only if approved configuration allows; preserve configured values. | normalized mapping weights |
| `EC-MAP-08` | Mapping version changed | New evaluations use new version; historical evaluations retain prior version. | versioned result |
| `EC-MAP-09` | Assessment item belongs to a different assessment | Reject mapping. | `ASSESSMENT_ITEM_MISMATCH` |
| `EC-MAP-10` | Assessment exposes only overall score | Use explicit assessment-level fallback mapping; do not pretend item-level precision. | valid fallback |
| `EC-MAP-11` | Mapping status retired/superseded | Do not use for new evaluation unless approved effective-date rules say otherwise. | `INACTIVE_MAPPING` |
| `EC-MAP-12` | Mapping exists but normalization rule is missing | Block evaluation for that evidence. | `MISSING_NORMALIZATION_RULE` |

---

# 5. Raw Score / Normalization Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-NORM-01` | Direct Skill value < `0` | Reject. | `OUT_OF_RANGE` |
| `EC-NORM-02` | Direct Skill value > `5` | Reject. | `OUT_OF_RANGE` |
| `EC-NORM-03` | Percentage < `0` | Reject before normalization. | `OUT_OF_RANGE` |
| `EC-NORM-04` | Percentage > `100` | Reject before normalization. | `OUT_OF_RANGE` |
| `EC-NORM-05` | Raw value is `null` | Treat as unavailable evidence; do not convert to `0`. | `MISSING_VALUE` |
| `EC-NORM-06` | Raw value is empty string | Reject or normalize to missing according to input validation; never convert to numeric zero silently. | `INVALID_VALUE` |
| `EC-NORM-07` | Raw numeric value = `0` | Accept when zero is valid for source scale. | normalized `0.00` |
| `EC-NORM-08` | Unknown raw score scale | Reject/flag; no heuristic conversion. | `UNSUPPORTED_SCORE_SCALE` |
| `EC-NORM-09` | Normalization version missing | Reject where reproducibility requires it. | `MISSING_NORMALIZATION_VERSION` |
| `EC-NORM-10` | Normalized result > `5` | Reject unless explicit approved clipping exists. | `OUT_OF_RANGE` |
| `EC-NORM-11` | Normalized result < `0` | Reject. | `OUT_OF_RANGE` |
| `EC-NORM-12` | Pass/Fail result without approved mapping | Do not infer proficiency. | `UNSUPPORTED_BINARY_MAPPING` |
| `EC-NORM-13` | Certificate present without proficiency mapping | Do not infer precise Skill Level. | evidence only / no level value |
| `EC-NORM-14` | Rubric version unavailable | Do not create mapped Skill Evidence. | `MISSING_RUBRIC_VERSION` |
| `EC-NORM-15` | Same evidence normalized under different versions | Preserve versioned results; do not silently overwrite history. | versioned history |

---

# 6. Evidence Availability / Validity Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-EVD-01` | No evidence exists | No demonstrated evidence; result remains unavailable/provisional according to approved evaluation contract. | `NO_EVIDENCE` |
| `EC-EVD-02` | Only self-assessment exists | Calculate provisional level from valid available evidence; Confidence remains low. | `PROVISIONAL_SELF_ASSESSMENT_ONLY` |
| `EC-EVD-03` | Optional evidence source missing | Re-normalize Skill Level across available valid sources. | valid calculation |
| `EC-EVD-04` | Evidence rejected | Do not positively contribute. | `REJECTED_EVIDENCE` |
| `EC-EVD-05` | Evidence voided | Stop contribution to current evaluation; preserve audit history. | `VOIDED_EVIDENCE` |
| `EC-EVD-06` | Evidence expired | Zero positive Confidence contribution under current SRS wording; Skill-level treatment follows approved current-evidence policy. | `EXPIRED_EVIDENCE` |
| `EC-EVD-07` | Evidence duplicate | Do not double-count. | `DUPLICATE_EVIDENCE` |
| `EC-EVD-08` | Evidence ownership mismatch | Reject. | `INVALID_EVIDENCE_OWNER` |
| `EC-EVD-09` | Evidence references wrong Skill | Reject/flag mapping/data issue. | `EVIDENCE_SKILL_MISMATCH` |
| `EC-EVD-10` | Evidence source unknown | Reject/flag. | `UNKNOWN_EVIDENCE_SOURCE` |
| `EC-EVD-11` | Multiple valid records from same source | Apply only approved same-source aggregation policy; currently TBD. | `SAME_SOURCE_POLICY_REQUIRED` |
| `EC-EVD-12` | All available source weights are zero | Reject configuration/evaluation. | `ZERO_TOTAL_WEIGHT` |

---

# 7. Evidence-Weight Configuration Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-WGT-01` | Negative evidence-source weight | Reject configuration. | `INVALID_WEIGHT` |
| `EC-WGT-02` | All configured weights = `0` | Reject configuration. | `ZERO_TOTAL_WEIGHT` |
| `EC-WGT-03` | Positive weights total != `1.00` | Normalize only according to approved configuration rule. | normalized weights |
| `EC-WGT-04` | Unknown source code in weight config | Reject/flag configuration. | `UNKNOWN_EVIDENCE_SOURCE` |
| `EC-WGT-05` | Weight config version missing | Reject for reproducible calculation. | `MISSING_WEIGHT_CONFIG_VERSION` |
| `EC-WGT-06` | Weight config changes | New evaluations use new version; old results remain reproducible. | versioned result |

---

# 8. Confidence Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-CONF-01` | No evidence | Confidence = `0.00`. | `low` |
| `EC-CONF-02` | Only self-assessment | Low/provisional Confidence. | `low` |
| `EC-CONF-03` | Verified evidence | Verification multiplier = `1.00`. | normal contribution |
| `EC-CONF-04` | Rejected/missing/expired evidence | Verification contribution = `0.00`. | zero contribution |
| `EC-CONF-05` | Pending evidence | Use approved partial multiplier only; exact value currently TBD. | `PENDING_FACTOR_REQUIRED` if not configured |
| `EC-CONF-06` | Evidence date missing | Apply only approved missing-date policy; do not assume freshest recency silently. | `MISSING_EVIDENCE_DATE` |
| `EC-CONF-07` | Evidence timestamp in future | Reject/flag. | `FUTURE_EVIDENCE_DATE` |
| `EC-CONF-08` | Unknown verification status | Reject/flag. | `UNKNOWN_VERIFICATION_STATUS` |
| `EC-CONF-09` | Recency config missing | Do not invent factor. | `MISSING_RECENCY_CONFIG` |
| `EC-CONF-10` | Configured confidence denominator = `0` | Reject configuration. | `ZERO_CONFIDENCE_DENOMINATOR` |
| `EC-CONF-11` | Confidence > `100` | Treat as implementation/configuration defect. | `CONFIDENCE_OUT_OF_RANGE` |
| `EC-CONF-12` | Confidence < `0` | Treat as defect. | `CONFIDENCE_OUT_OF_RANGE` |
| `EC-CONF-13` | Duplicate evidence | Must not increase Confidence twice. | `DUPLICATE_EVIDENCE` |
| `EC-CONF-14` | Many same-source records | Must not exceed intended source contribution without approved policy. | `SAME_SOURCE_POLICY_REQUIRED` |

---

# 9. Skill-Level Aggregation Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-EVAL-01` | No valid evidence remains after filtering | Do not fabricate weighted level. | `NO_VALID_EVIDENCE` |
| `EC-EVAL-02` | Available-evidence denominator = `0` | Do not divide; return validation/configuration failure. | `ZERO_EVALUATION_DENOMINATOR` |
| `EC-EVAL-03` | Final Skill Level > `5` | Reject/flag defect. | `OUT_OF_RANGE` |
| `EC-EVAL-04` | Final Skill Level < `0` | Reject/flag defect. | `OUT_OF_RANGE` |
| `EC-EVAL-05` | Missing optional source | Re-normalize over valid available source weights. | valid calculation |
| `EC-EVAL-06` | Source value exists but invalid mapping | Exclude invalid evidence and flag issue. | `FAILED_MAPPING` |
| `EC-EVAL-07` | Source value exists but normalization failed | Exclude/block according to severity; do not use raw value. | `NORMALIZATION_FAILURE` |
| `EC-EVAL-08` | Evaluation corrected after finalization | Create controlled revision/supersession. | versioned history |
| `EC-EVAL-09` | Algorithm/configuration changed | New evaluation version; preserve old result and versions. | versioned history |
| `EC-EVAL-10` | Same input + same versions recalculated | Must reproduce equivalent deterministic output. | reproducibility PASS/FAIL |

---

# 10. Distribution / Monitoring Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-DIST-01` | Skill Level outside `0–5` in stored analytical data | Hard validation failure. | `OUT_OF_RANGE` |
| `EC-DIST-02` | Confidence outside `0–100` | Hard validation failure. | `CONFIDENCE_OUT_OF_RANGE` |
| `EC-DIST-03` | Very small sample | Do not classify statistical anomaly; report insufficient sample. | `INSUFFICIENT_SAMPLE` |
| `EC-DIST-04` | Large concentration at `0` | Flag possible floor effect; investigate. | `POSSIBLE_FLOOR_EFFECT` |
| `EC-DIST-05` | Large concentration at `5` | Flag possible ceiling effect; investigate. | `POSSIBLE_CEILING_EFFECT` |
| `EC-DIST-06` | Sudden shift after config/version change | Compare versions and review. | `UNEXPECTED_VERSION_SHIFT` |
| `EC-DIST-07` | High failed mapping rate | Flag data-quality issue. | `HIGH_MAPPING_FAILURE_RATE` |
| `EC-DIST-08` | High self-assessment-only rate | Flag evidence maturity issue. | `HIGH_SELF_ASSESSMENT_ONLY_RATE` |
| `EC-DIST-09` | High low-confidence rate | Flag for evidence/mapping/recency review. | `HIGH_LOW_CONFIDENCE_RATE` |
| `EC-DIST-10` | Missing evaluation and true level `0` mixed together | Reject reporting logic; maintain separate states. | `MISSING_ZERO_COLLAPSE_ERROR` |

---

# 11. Service / Contract Failure Edge Cases

| ID | Condition | Required Behavior | Output / Flag |
|---|---|---|---|
| `EC-SVC-01` | Data Science request contains no Skills when Skills are required | Reject with validation error. | `VALIDATION_ERROR` |
| `EC-SVC-02` | Intelligence service timeout | Return safe unavailable/error state; do not fabricate result. | `SERVICE_UNAVAILABLE` |
| `EC-SVC-03` | Unsupported contract version | Reject with stable error. | `UNSUPPORTED_CONTRACT_VERSION` |
| `EC-SVC-04` | Required algorithm/config version missing | Reject or flag according to contract. | `MISSING_VERSION` |
| `EC-SVC-05` | Backend sends malformed evidence payload | Reject field-level validation. | `VALIDATION_ERROR` |
| `EC-SVC-06` | Duplicate request/retry creates duplicate evaluation | Use orchestration/idempotency strategy; do not create unintended duplicate analytical record. | Backend/orchestration control |

---

# 12. Versioning / Historical Edge Cases

| ID | Condition | Required Behavior |
|---|---|---|
| `EC-VER-01` | Taxonomy changes | New applicable taxonomy version; preserve historical reference. |
| `EC-VER-02` | Assessment mapping changes | New mapping version. |
| `EC-VER-03` | Normalization formula changes | New normalization version. |
| `EC-VER-04` | Evidence weights change | New evidence-weight config version. |
| `EC-VER-05` | Confidence formula changes | New confidence algorithm version. |
| `EC-VER-06` | Recency windows/factors change | New recency config version. |
| `EC-VER-07` | Rubric changes | Preserve rubric version used by finalized evaluation. |
| `EC-VER-08` | Defective configuration deactivated | Stop new decisions from using it; preserve historical decisions. |

---

# 13. Open Decisions Blocking Full Determinism

The following are intentionally **not invented** in this document:

```text
pending_verification_factor
same_source_evidence_aggregation_policy
missing_evidence_date_policy
minimum_distribution_sample_size
distribution_alert_thresholds
binary/pass-fail normalization policy
certificate proficiency normalization policy
```

These require Backend/Product/Domain/Data Science confirmation or real-data calibration.

---

# 14. Recommended Error / Flag Vocabulary

Recommended analytical codes:

```text
MISSING_SKILL_ID
INVALID_SKILL_ID
UNKNOWN_SKILL
UNMAPPED_SKILL
AMBIGUOUS_SKILL_ALIAS
FAILED_MAPPING
DUPLICATE_MAPPING
INVALID_MAPPING_WEIGHT
MISSING_NORMALIZATION_RULE
UNSUPPORTED_SCORE_SCALE
OUT_OF_RANGE
MISSING_VALUE
NORMALIZATION_FAILURE
DUPLICATE_EVIDENCE
UNKNOWN_EVIDENCE_SOURCE
UNKNOWN_VERIFICATION_STATUS
NO_EVIDENCE
NO_VALID_EVIDENCE
ZERO_TOTAL_WEIGHT
ZERO_EVALUATION_DENOMINATOR
MISSING_VERSION
PENDING_FACTOR_REQUIRED
MISSING_EVIDENCE_DATE
FUTURE_EVIDENCE_DATE
MISSING_RECENCY_CONFIG
CONFIDENCE_OUT_OF_RANGE
INSUFFICIENT_SAMPLE
SERVICE_UNAVAILABLE
```

Exact external API error codes require Backend contract approval.

---

# 15. Deterministic Edge-Case Test Candidates

These cases should later become executable test vectors:

### EDGE-TV-01 — Missing optional evidence

Input:

```text
assessment_test = 4.0
project_performance = 3.0
other optional sources missing
```

Expected:

```text
Skill Level uses only 0.30 + 0.35 denominator.
Missing sources are not zero.
```

### EDGE-TV-02 — Only self-assessment

Input:

```text
self_assessment = 4.0
```

Expected:

```text
provisional Skill Level = 4.00
Confidence = 10.00 using current default configuration
```

### EDGE-TV-03 — Invalid percentage

Input:

```text
assessment score = 120%
```

Expected:

```text
validation_error
No normalized evidence value.
```

### EDGE-TV-04 — Unknown Skill mapping

Input:

```text
assessment item -> skill_id unknown
```

Expected:

```text
FAILED_MAPPING / UNKNOWN_SKILL
No contribution to Skill Evaluation.
```

### EDGE-TV-05 — Duplicate evidence

Input:

```text
same learner + skill + source + reference + event duplicated
```

Expected:

```text
single analytical contribution only
duplicate flagged/rejected
```

### EDGE-TV-06 — No evidence

Expected:

```text
No fabricated Skill Level.
Confidence = 0.00.
```

### EDGE-TV-07 — Configuration change

Input:

```text
same evidence snapshot
algorithm/config version A
algorithm/config version B
```

Expected:

```text
results stored as separate versioned decisions;
historical result A remains reproducible.
```

---

# 16. Definition of Done

- [x] Canonical Skill edge cases documented.
- [x] Assessment mapping edge cases documented.
- [x] Normalization edge cases documented.
- [x] Evidence and weight edge cases documented.
- [x] Confidence edge cases documented.
- [x] Skill Evaluation aggregation edge cases documented.
- [x] Distribution/monitoring edge cases documented.
- [x] Service/contract failure cases documented.
- [x] Version/history cases documented.
- [x] Initial machine-readable flag vocabulary proposed.
- [x] Deterministic edge-case test candidates identified.
- [ ] Open configuration decisions approved.
- [ ] Backend error/status contract aligned.
- [ ] Executable test vectors implemented after approval.
