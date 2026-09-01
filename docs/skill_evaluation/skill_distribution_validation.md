# SkillSpan — Skill-Level Distribution Validation Plan

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation validation and monitoring
**Purpose:** Define how SkillSpan validates the statistical quality of calculated Skill Levels and Confidence Scores without inventing unsupported thresholds or changing the Skill Evaluation formula.

---

## 1. Objective

SkillSpan must monitor Skill Evaluation outputs for data-quality and algorithm-quality problems such as:

- impossible values;
- failed mappings;
- excessive missingness;
- suspicious concentration at specific levels;
- sudden distribution shifts after configuration changes;
- skills with too little evaluation coverage;
- sources that produce systematically unusual values.

This validation layer is analytical monitoring.

It does **not**:

- change the learner's Skill Level;
- change `skill-gap-v1`;
- automatically reject a learner because a distribution looks unusual;
- define fairness conclusions without approved analysis.

---

## 2. SRS Baseline

The current SkillSpan requirements establish that the data team should monitor:

- missing fields;
- duplicate rates;
- stale evidence;
- failed mappings;
- anomalous distributions;
- score distributions and error rates;
- quality changes after algorithm/configuration updates.

The SRS does not define fixed numeric alert thresholds for these checks.

Therefore this plan defines the metrics and review process first. Production thresholds remain configurable and require approval after real data is available.

---

## 3. Validation Levels

Distribution validation should operate at several levels.

### 3.1 Global

Across all evaluated Skills:

```text
all current SkillEvaluation records
```

Use for:

- overall scale sanity;
- general missingness;
- confidence distribution;
- global changes between versions.

### 3.2 Per Skill

Example:

```text
SQL
Python
Power BI
```

Use for:

- skill-specific central tendency;
- floor/ceiling effects;
- insufficient sample size;
- mapping or assessment design issues.

### 3.3 Per Evidence Source

Example:

```text
self_assessment
assessment_test
project_performance
expert_evaluation
verified_certificate
```

Use for:

- source bias patterns;
- normalization differences;
- stale/verification problems.

### 3.4 Per Algorithm / Configuration Version

Compare distributions for:

```text
skill-evaluation-v1
evidence-weights-v1
skill-normalization-v1
assessment-skill-map-v1
```

A material version change should be reviewed for expected vs unexpected output shifts.

### 3.5 Approved Non-Identifying Segments

Where Product/Privacy approves, analysis may compare non-identifying operational segments.

Protected or unrelated attributes must not be used to reduce Skill Levels, Readiness, eligibility, or ranking.

---

## 4. Core Metrics

For every sufficiently populated analytical group, calculate:

| Metric | Purpose |
|---|---|
| `count` | Number of evaluated observations. |
| `missing_count` | Missing or unavailable evaluations. |
| `missing_rate` | Coverage/data-quality signal. |
| `mean` | Average Skill Level. |
| `median` | Robust central tendency. |
| `std_dev` | Spread of results. |
| `min` | Lower-bound validation. |
| `max` | Upper-bound validation. |
| `q25` | First quartile. |
| `q75` | Third quartile. |
| `iqr` | Distribution spread. |
| `p05` | Lower-tail indicator. |
| `p95` | Upper-tail indicator. |
| `zero_rate` | Percentage exactly at `0.00`. |
| `five_rate` | Percentage exactly at `5.00`. |
| `integer_level_rate` | Detects unexpected discretization/rounding. |
| `low_confidence_rate` | Percentage of evaluations in Low confidence band. |
| `mapping_failure_rate` | Failed canonical/mapping resolution. |
| `normalization_failure_rate` | Unsupported or invalid source-value conversion. |

These metrics describe behavior; they do not by themselves prove a defect.

---

## 5. Hard Validation Checks

These checks do not require statistical thresholds.

### DIST-HARD-01 — Skill Range

Every calculated Skill Level must satisfy:

```text
0.00 <= skill_level <= 5.00
```

Anything outside the range is an implementation/configuration defect.

### DIST-HARD-02 — Confidence Range

Every Confidence Score must satisfy:

```text
0.00 <= confidence_score <= 100.00
```

### DIST-HARD-03 — Required Versions

Each material Skill Evaluation should retain the required algorithm/configuration version references needed for reproduction.

### DIST-HARD-04 — Canonical Skill

Every evaluation must reference a valid canonical `skill_id`.

### DIST-HARD-05 — Invalid Mapping

Unknown, retired-without-approved-supersession, or ambiguous mappings must not silently contribute.

### DIST-HARD-06 — Duplicate Contribution

Duplicate underlying evidence must not be counted more than once unintentionally.

---

## 6. Distribution Shape Checks

These checks identify candidates for investigation.

### DIST-SHAPE-01 — Floor Effect

Flag for review when a Skill has an unexpectedly high concentration near:

```text
0.00
```

Possible causes:

- assessment too difficult;
- mapping error;
- missing evidence treated incorrectly;
- normalization problem;
- genuine population weakness.

No numeric threshold is fixed yet.

### DIST-SHAPE-02 — Ceiling Effect

Flag for review when a Skill has excessive concentration near:

```text
5.00
```

Possible causes:

- assessment too easy;
- over-generous normalization;
- evidence duplication;
- rubric inflation;
- genuine expert-heavy sample.

### DIST-SHAPE-03 — Single-Value Spike

Unexpected concentration at one exact value may indicate:

- default/fallback value misuse;
- rounding bug;
- source import issue;
- overly coarse score mapping.

### DIST-SHAPE-04 — Integer-Level Spike

If nearly all outputs are exact integers despite decimal-capable evidence, review normalization and rounding.

This is a diagnostic signal, not automatically a defect.

### DIST-SHAPE-05 — Bimodality / Multi-Peak Pattern

Strongly separated peaks may reflect:

- mixed learner populations;
- assessment versions;
- mapping changes;
- source-specific effects.

Investigate by version/source before concluding there is an algorithm issue.

---

## 7. Coverage Checks

### DIST-COV-01 — Evaluation Coverage

For each Skill:

```text
evaluation_coverage =
learners_with_valid_skill_evaluation
/
eligible_learners_or_observed_population
```

Exact denominator depends on approved reporting context.

### DIST-COV-02 — Evidence Diversity

Track how many source categories support each evaluation.

Example:

```text
1 source
2 sources
3+ sources
```

This helps interpret Confidence distributions.

### DIST-COV-03 — Self-Assessment-Only Rate

Measure:

```text
evaluations supported only by self_assessment
```

High rates indicate weak evidence maturity even if Skill Levels exist.

### DIST-COV-04 — Mapping Coverage

For assessments:

```text
mapped assessment items
/
assessment items intended for scoring
```

Unmapped content should be reported.

---

## 8. Source Comparison Checks

For the same Skill, compare source-normalized values.

Example:

```text
SQL self-assessment distribution
vs
SQL assessment-test distribution
vs
SQL project-performance distribution
```

Useful metrics:

- mean difference;
- median difference;
- correlation where paired observations exist;
- absolute disagreement;
- sample size by source.

Large differences are not automatically wrong.

They may reflect:

- self-report bias;
- different measurement goals;
- assessment difficulty;
- project selection effects;
- mapping problems.

---

## 9. Confidence Distribution Checks

Monitor:

- `low` band rate;
- `moderate` band rate;
- `good` band rate;
- `high` band rate;
- mean and median Confidence;
- confidence by Skill;
- confidence by evidence-source mix;
- confidence by recency bucket.

Example question:

> Are many Skill Levels high while Confidence remains very low?

That may be valid for cold-start learners, but it should be visible.

---

## 10. Version-to-Version Drift

A new algorithm/configuration version must be compared with the prior approved version when comparable data exists.

Recommended comparisons:

```text
mean_delta
median_delta
std_delta
zero_rate_delta
five_rate_delta
low_confidence_rate_delta
mapping_failure_rate_delta
```

Optional statistical techniques may later include:

- Kolmogorov-Smirnov test;
- Wasserstein distance;
- Population Stability Index;
- Jensen-Shannon divergence.

These techniques are **monitoring options**, not mandatory SRS formulas.

No alert threshold is fixed until sample size and real-data behavior are understood.

---

## 11. Small Sample Handling

Distribution conclusions must not be drawn from extremely small groups.

Recommended rule:

```text
if sample size is below an approved minimum:
    report metrics as insufficient_sample
    do not classify distribution as anomalous
```

Exact:

```text
minimum_sample_size = TBD
```

Product/Data Science must approve this after observing dataset size.

---

## 12. Missing Data Validation

Track separately:

```text
no evidence
invalid evidence
unmapped evidence
normalization failure
evaluation unavailable
```

Do not collapse all conditions into:

```text
skill_level = 0
```

A true demonstrated zero and a missing evaluation are analytically different states.

---

## 13. Proposed Validation Output

Example:

```json
{
  "skill_id": 7,
  "skill_name": "SQL",
  "algorithm_version": "skill-evaluation-v1",
  "configuration_version": "skill-evaluation-config-v1",
  "sample_size": 420,
  "metrics": {
    "mean": 3.12,
    "median": 3.20,
    "std_dev": 0.84,
    "min": 0.50,
    "max": 5.00,
    "q25": 2.60,
    "q75": 3.80,
    "zero_rate": 0.01,
    "five_rate": 0.04,
    "low_confidence_rate": 0.22
  },
  "quality_flags": [],
  "validation_status": "reviewed"
}
```

This is a proposed analytical reporting structure, not a current Backend API contract.

---

## 14. Quality Flags

Recommended machine-readable flag vocabulary:

```text
OUT_OF_RANGE
MISSING_VERSION
UNKNOWN_SKILL
FAILED_MAPPING
NORMALIZATION_FAILURE
DUPLICATE_EVIDENCE
INSUFFICIENT_SAMPLE
POSSIBLE_FLOOR_EFFECT
POSSIBLE_CEILING_EFFECT
POSSIBLE_ROUNDING_SPIKE
UNEXPECTED_VERSION_SHIFT
HIGH_SELF_ASSESSMENT_ONLY_RATE
HIGH_LOW_CONFIDENCE_RATE
```

A flag indicates review is needed.

It must not automatically modify the learner's result unless a separate approved business rule says so.

---

## 15. Deterministic Validation Cases

### DIST-TV-01 — Valid Range

Input:

```text
skill levels:
[1.0, 2.5, 3.0, 4.25, 5.0]
```

Expected:

```text
range validation = PASS
```

### DIST-TV-02 — Out-of-Range Value

Input:

```text
[2.5, 3.2, 5.4]
```

Expected:

```text
OUT_OF_RANGE
validation failure
```

### DIST-TV-03 — Missing Version

Input:

```text
skill_level = 3.5
algorithm_version = null
```

Expected:

```text
MISSING_VERSION
```

### DIST-TV-04 — Missing vs Zero

Input:

```text
learner A -> skill_level = 0.0
learner B -> no evaluation
```

Expected:

```text
A counts as demonstrated zero.
B counts as missing/unavailable.
They must not be merged.
```

### DIST-TV-05 — Small Sample

Input:

```text
sample_size < configured minimum_sample_size
```

Expected:

```text
INSUFFICIENT_SAMPLE
No anomaly classification.
```

---

## 16. Review Workflow

Recommended process:

```text
Generate metrics
      ↓
Run hard validation checks
      ↓
Generate distribution-quality flags
      ↓
Slice by Skill / Source / Version
      ↓
Data Science review
      ↓
If needed: Backend / Domain / Product investigation
      ↓
Correct mapping/config/data through controlled versioning
```

Historical outputs should remain auditable.

---

## 17. What Must Not Happen

Distribution monitoring must not:

- silently rewrite learner Skill Levels;
- remove historical results without audit;
- treat missing evidence as demonstrated zero;
- use protected attributes to penalize a learner;
- declare bias solely from an unreviewed group difference;
- change thresholds or mappings without versioning;
- automatically retrain or enable learned models.

---

## 18. Configuration Items Still Required

The following remain intentionally open:

```text
minimum_sample_size = TBD
floor_effect_threshold = TBD
ceiling_effect_threshold = TBD
version_shift_thresholds = TBD
source_disagreement_threshold = TBD
mapping_failure_alert_threshold = TBD
```

These should be calibrated using real SkillSpan data and approved as versioned monitoring configuration.

---

## 19. Suggested Monitoring Version

```text
skill-distribution-validation-v1
```

Create a new version when:

- metrics materially change;
- anomaly rules change;
- thresholds change;
- segmentation policy changes;
- statistical tests or alert semantics change.

---

## 20. Backend / Product / Data Confirmations Required

Before operational implementation, confirm:

- where SkillEvaluation records are stored and queried;
- available algorithm/configuration version fields;
- canonical evidence-source/status values;
- assessment mapping failure logging;
- population denominator for evaluation coverage;
- approved reporting segments;
- minimum sample size;
- initial alert thresholds;
- whether validation reports are stored, exported, or dashboard-only.

---

## 21. Definition of Done

- [x] Validation levels defined.
- [x] Core descriptive metrics defined.
- [x] Hard correctness checks defined.
- [x] Distribution shape checks defined.
- [x] Coverage/evidence-diversity checks defined.
- [x] Confidence distribution checks defined.
- [x] Version drift review defined.
- [x] Missing-vs-zero semantics preserved.
- [x] Initial deterministic validation cases defined.
- [x] Proposed quality flags defined.
- [ ] Real dataset/profile population confirmed.
- [ ] Minimum sample size approved.
- [ ] Alert thresholds calibrated.
- [ ] Automated reporting/tests implemented after approval.
