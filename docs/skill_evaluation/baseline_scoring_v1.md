# SkillSpan - Baseline Scoring v1.0

**Area:** Data Science / Data Analysis
**Status:** Implemented v1 behavior
**Algorithm Version:** `baseline-v1.0`

## 1. Purpose

Defines deterministic Baseline assessment scoring in FastAPI. Laravel owns assessment items, correct answers, scale rules, skill mappings, and item weights. FastAPI owns calculation only and does not query or mutate the Laravel database directly.

This algorithm does not modify `skill-gap-v1` or the generic Skill Evaluation confidence rules.

## 2. Mapping Contract

FastAPI fetches the Backend-owned mapping from:

`GET /api/v1/internal/baseline-items?version=<assessment_version>`

using `X-Internal-Secret`. The incoming `X-Request-ID` is propagated to this request.

Authoritative fields include `item_id`, `item_type`, `options`, `correct_answer`, `scoring_rule`, `skill_id`, `skill_slug`, and `weight`. `skill_id` is authoritative; `skill_slug` is supporting metadata. `weight_scale` is `0..1`.

## 3. Item Scoring

For `single_choice`:

`item_score = 1.0` when `answer == correct_answer`, otherwise `0.0`.

For `scale`:

`item_score = scoring_rule[answer]`.

All normalized item scores are in `0..1`.

## 4. Skill Level

For each skill:

`normalized_skill_score = SUM(item_score * weight) / SUM(answered positive weights)`

`skill_level = normalized_skill_score * 5.0`

Skill Level is returned on `0..5` and rounded to two decimals.

## 5. Overall Score

`overall_score = 100 * SUM(item_score * weight) / SUM(answered positive weights)`

The result is rounded to two decimals.

## 6. Partial Responses

Partial responses are supported in `baseline-v1.0`. Missing items are not treated as incorrect answers and are excluded from Skill Level and overall-score denominators.

This prevents missing assessment data from being interpreted as demonstrated incompetence.

## 7. Baseline Confidence

Baseline response `confidence` is an assessment-coverage signal on `0..1`:

`confidence = answered positive weight for skill / total configured weight for skill`

A wrong answer still counts as answered coverage. Confidence measures coverage, not correctness.

Example: configured SQL weights `1.0 + 0.8 = 1.8`; if only the `1.0` item is answered, confidence is `1.0 / 1.8 = 0.5556`.

This Baseline confidence is separate from the generic Skill Evaluation confidence defined in `confidence_rules.md`, which uses evidence weights, verification, and recency and operates on `0..100`.

## 8. Zero-Weight Items

Backend mapping allows `weight` in `0..1`. A zero-weight item is valid configuration but contributes nothing to Skill Level, overall score, or coverage confidence. If a request contains no positively weighted scorable item, evaluation fails instead of fabricating a score.

## 9. Failure Semantics

- Unknown `item_id`: reject as invalid submitted input.
- Answer outside configured options: reject as invalid submitted input.
- Mapping version mismatch: reject as upstream configuration error.
- Invalid mapping contract: reject as upstream contract error.
- Missing Backend integration config or unavailable mapping dependency: do not fabricate a score.
- Inconsistent `skill_slug` for the same `skill_id`: reject configuration.

Current HTTP mapping: semantic input errors `422`; invalid/inconsistent upstream mapping `502`; missing configuration or unavailable Backend dependency `503`.

## 10. Determinism

Identical submitted responses, assessment version, Backend mapping content, and algorithm version must produce identical output.

## 11. Versioning

Any material change to item scoring, weighted aggregation, partial-response semantics, Baseline confidence, zero-weight handling, rounding, or outcome-affecting failure semantics requires a new algorithm/configuration version.

## 12. Current Validation

Runtime tests cover weighted scoring, `single_choice`, `scale`, partial coverage confidence, invalid answers, unknown items, version mismatch, Backend mapping validation, failure handling, and `X-Request-ID` propagation.
