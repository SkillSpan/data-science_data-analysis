# SkillSpan — Project Matching Data Framework v1

**Status:** Draft for Product / Backend / Data Science Review
**Scope:** MVP Launch Preparation — Project Data, Eligibility, and Matching
**Owner:** Data Analysis / Data Science
**Version:** `project-matching-data-framework-v1`

## 1. Purpose

Define the approved data logic connecting:

`Career Role → Skills → Skill Level → Project Requirements → Student Profile`

This document does not replace existing SkillSpan specifications. It references the approved canonical skill, career-role configuration, and skill-level normalization documents and adds the Project Matching MVP rules required for project creation, eligibility, ranking, and validation.

## 2. Existing Specifications Reused

The following existing specifications remain authoritative:

- `docs/career_roles/career_role_configuration_v1.md`
- `docs/skill_evaluation/canonical_skill_representation.md`
- `docs/skill_evaluation/skill_level_normalization.md`

Key rules reused here:

- Skills are joined analytically by stable `skill_id`, not display name.
- Career-role required levels use the canonical `0..5` scale.
- Decimal skill values between anchor levels are valid.
- Career-role prerequisite skills must exist inside the same career-role configuration.
- Core/Supporting classification is a career-role concept.
- Project Critical Entry is a separate project-eligibility concept.

## 3. MVP Supported Career Roles

Current MVP baseline:

1. Frontend Developer
2. Backend Developer
3. Data Analyst

Only approved Career Roles are eligible for Project Matching.

## 4. Current Career Role → Skill Mapping Baseline

| Career Role | Skill | Classification | Target Level | Importance Weight | Prerequisite |
|---|---|---|---:|---:|---|
| Frontend Developer | JavaScript | Core | 3.0 | 0.90 | — |
| Frontend Developer | React | Core | 3.0 | 0.90 | JavaScript |
| Frontend Developer | CSS / Tailwind | Supporting | 2.5 | 0.60 | — |
| Frontend Developer | TypeScript | Supporting | 2.0 | 0.50 | JavaScript |
| Backend Developer | Programming Fundamentals | TBD | TBD | TBD | — |
| Backend Developer | SQL & Databases | TBD | TBD | TBD | — |
| Backend Developer | REST APIs | TBD | TBD | TBD | — |
| Backend Developer | Authentication & Authorization | TBD | TBD | TBD | — |
| Backend Developer | Backend Architecture | TBD | TBD | TBD | — |
| Data Analyst | Python | Core | 3.0 | 0.90 | — |
| Data Analyst | Pandas | Core | 3.0 | 0.80 | Python |
| Data Analyst | SQL | Supporting | 2.5 | 0.70 | — |
| Data Analyst | NumPy | Supporting | 2.0 | 0.50 | Python |

## 5. Core vs Supporting Skills

### Core Skill

A skill that materially defines capability for the Career Role and carries higher role importance.

Core does **not** automatically mean that every project must treat the skill as a hard eligibility blocker.

### Supporting Skill

A skill that improves role effectiveness or broadens capability but is not necessarily a universal entry requirement for every project in that role.

### Project Critical Entry Skill

A separate project-level flag used by Eligibility.

A project may mark a Core or Supporting career skill as `is_critical_entry=true` when the learner must meet that project's minimum level before matching.

Therefore:

`Career Role Core/Supporting ≠ Project Critical/Non-Critical`

## 6. Skill-Level Policy for Project Matching

The canonical SkillSpan scale remains `0.00..5.00`.

Anchor labels:

| Anchor | Label |
|---:|---|
| 0 | Not Demonstrated |
| 1 | Awareness |
| 2 | Beginner |
| 3 | Intermediate |
| 4 | Advanced |
| 5 | Expert |

Decimal values between anchors are valid analytical values, for example `2.50`, `3.75`, and `4.20`.

For Project creation, `minimum_required_level` must use the same canonical scale so direct comparison is deterministic:

`student_skill_level >= project_minimum_required_level`

subject to the Eligibility rules defined later in this framework.

## 7. Backend Career-Role Mapping Alignment

Backend review of the current `feature/authentication` seed baseline confirmed that `Backend Developer` contains:

- Programming Fundamentals
- SQL & Databases
- REST APIs
- Authentication & Authorization
- Backend Architecture

`Node.js` is not currently mapped to `Backend Developer`; it belongs to the separate `Node.js Developer` role. No seeded `Node.js → JavaScript` prerequisite exists in the reviewed backend source.

Therefore this framework must not assume either `Node.js` membership in the Backend Developer role or a Node.js-to-JavaScript prerequisite.

The Backend Developer Core/Supporting classifications, target levels, and importance weights remain `TBD` until the approved Product/Backend mapping is confirmed. Project skills must remain mapped to the selected Career Role before Project Matching validation.

## 8. Skill Catalog Governance

Skills may exist in the canonical Skill Catalog without being mapped to an MVP Career Role.

Unmapped catalog skills must not influence Career Role or Project Matching unless they are explicitly added to an approved role/project mapping.

New free-text skills must not be created by Data Science or Frontend during matching.


## 10. Project Difficulty Classification

### 10.1 Objective

Classify every MVP Project consistently as:

- `Beginner`
- `Intermediate`
- `Advanced`

Difficulty must be based on multiple project characteristics and must not be inferred from the number of Required Skills alone.

The same framework applies across all supported Career Roles.

### 10.2 Difficulty Factors

The MVP classification uses six factors:

1. Required Skill Levels
2. Number of Required Skills
3. Project Complexity
4. Project Duration
5. Deliverables
6. Level of Independence Required

Each factor receives a deterministic factor score:

- `1` = Beginner characteristics
- `2` = Intermediate characteristics
- `3` = Advanced characteristics

### 10.3 Factor Criteria

| Factor | Score 1 — Beginner | Score 2 — Intermediate | Score 3 — Advanced |
|---|---|---|---|
| Required Skill Levels | Mean `minimum_required_level <= 2.5` and no Critical Entry skill requires `>= 4.0` | Mean `minimum_required_level > 2.5` and `< 3.5`, with no Critical Entry skill requiring `>= 4.0` | Mean `minimum_required_level >= 3.5`, or any Critical Entry skill requires `>= 4.0` |
| Number of Required Skills | `1–3` required skills | `4–6` required skills | `7+` required skills |
| Project Complexity | One bounded problem or standard workflow with few dependencies | Multiple connected tasks, components, or integrations | Multi-component/system-level work, significant ambiguity, or complex integration/architecture decisions |
| Project Duration | Up to `2` weeks | More than `2` and up to `6` weeks | More than `6` weeks |
| Deliverables | One primary, clearly bounded deliverable | `2–3` related deliverables or a multi-step delivery | `4+` deliverables, multiple major artifacts, or staged/versioned delivery |
| Independence Required | Guided execution; frequent instructions/checkpoints are expected | Limited support; learner makes standard implementation/analysis decisions | High autonomy; learner plans, makes complex decisions, and resolves unfamiliar issues independently |

### 10.3.1 Required Skill Level Aggregation

For difficulty classification, calculate:

`MeanRequiredSkillLevel = SUM(minimum_required_level) / number_of_required_skills`

All Required Skills participate in this mean. The value is calculated using full precision and is not rounded before factor classification.

The Critical Entry guardrail remains independent of the mean: any `is_critical_entry=true` skill with `minimum_required_level >= 4.0` forces the final Project Difficulty to `Advanced`.

### 10.4 Initial MVP Difficulty Weights

The initial configurable weights are:

| Factor | Weight |
|---|---:|
| Required Skill Levels | `0.30` |
| Project Complexity | `0.25` |
| Independence Required | `0.15` |
| Number of Required Skills | `0.10` |
| Project Duration | `0.10` |
| Deliverables | `0.10` |

Total weight:

`1.00`

### 10.5 Difficulty Index

For factor score `F_i` and factor weight `W_i`:

`DifficultyIndex = SUM(F_i * W_i)`

The index remains in the range `1.00..3.00`.

Initial MVP bands:

| Difficulty Index | Difficulty Band |
|---:|---|
| `1.00–1.66` | Beginner |
| `1.67–2.33` | Intermediate |
| `2.34–3.00` | Advanced |

The calculated index should be rounded to two decimals only after the full weighted calculation.

### 10.6 Classification Guardrails

The weighted index is the default classification mechanism, with the following guardrails:

1. If any `is_critical_entry=true` Project Skill has `minimum_required_level >= 4.0`, the Project is `Advanced`.
2. A Project must not be classified as `Beginner` when either Project Complexity or Independence Required has factor score `3`; such a case requires at least `Intermediate` classification and review.
3. Project Type (`simulation` or `company_sponsored`) does not determine difficulty by itself.
4. Career Role does not determine difficulty by itself; the same rubric is applied across roles.
5. Number of Required Skills must never be used as the sole difficulty rule.
6. Missing factor data must block final classification rather than be silently treated as Beginner.

### 10.7 Project-Creation Data Required for Difficulty

To classify difficulty deterministically, Project creation must expose enough structured data to derive all six factors, including:

- Required Skills and `minimum_required_level`
- Project Skill `is_critical_entry` flags
- structured Project Complexity selection or approved complexity rubric input
- duration or dates sufficient to derive duration
- Deliverables
- Independence Required

If a factor is stored as a manual Admin selection, the allowed values must be controlled and documented rather than free text.

### 10.8 Explainability

The system should be able to explain a Project Difficulty result using its strongest contributing factors.

Example:

`Intermediate because the project requires Intermediate skill levels, multiple connected tasks, and limited-support execution over four weeks.`

The explanation is descriptive only; the deterministic factor scores and configuration remain the calculation source of truth.

### 10.9 MVP Examples

#### Example A — Beginner Frontend Project

Typical characteristics:

- `2–3` required skills
- minimum levels around `2.0–2.5`
- one bounded interface/task
- up to two weeks
- one primary deliverable
- guided execution

Expected band: `Beginner`.

#### Example B — Intermediate Backend Project

Typical characteristics:

- `3–5` required skills
- minimum levels around `3.0`
- API/database integration
- three to six weeks
- multiple related deliverables
- limited support

Expected band: `Intermediate`.

#### Example C — Advanced Data Project

Typical characteristics:

- multiple required skills with one or more Critical Entry skills at `4.0+`
- complex end-to-end analysis or multi-component workflow
- more than six weeks or substantial scope
- multiple major deliverables
- high independence

Expected band: `Advanced`.

### 10.10 Difficulty Configuration Version

Initial analytical configuration identifier:

`project-difficulty-config-v1`

### 10.11 Runtime Difficulty Contract Alignment

The analytical framework may derive the human-readable bands `Beginner`, `Intermediate`, and `Advanced`, but the current Laravel and FastAPI Project Matching contract carries `difficulty` as a numeric value on the canonical `0..5` scale.

Therefore, the MVP implementation must not send categorical difficulty strings through the existing Project Matching payload. A deterministic mapping between the analytical difficulty band/index and the numeric `0..5` runtime value must be approved before automated difficulty classification is written back to Project data. Changing the payload to a categorical value requires a versioned Backend/FastAPI contract change.

Any material change to factor definitions, weights, thresholds, guardrails, or band boundaries requires a new configuration version so historical classifications remain reproducible.
## 11. Project Eligibility Rules

### 11.1 Objective

Eligibility is a hard-filter stage executed before Project Matching and Ranking.

Only Projects that pass all mandatory eligibility checks may enter the ranking process.

The eligibility result must be deterministic, explainable, and suitable for persistence/audit.

Initial configuration identifier:

`project-eligibility-config-v1`

### 11.2 Decision Principle

Eligibility answers one question:

`Can this learner validly enter this Project?`

It does **not** answer:

`How strongly should this Project be recommended?`

That second question belongs to Matching.

Therefore:

`Eligibility -> Matching -> Ranking`

An ineligible Project must never receive a qualified recommendation score.

### 11.3 Hard Eligibility Filters

The MVP eligibility stage evaluates the following hard filters when the relevant Project rule is configured:

1. Project status and visibility.
2. Application window.
3. Capacity / requested role availability.
4. Authorization and organization/access restrictions.
5. Mandatory Project constraints enforced by Laravel. In the current Backend runtime, `work_mode` and `schedule` are hard constraints when configured; `location` and `language` are not currently hard eligibility constraints.
6. Duplicate active application.
7. Conflicting active Project assignment where prohibited.
8. Project Critical Entry Skill requirements.
9. Any additional explicit blocking Project constraint.

Laravel remains authoritative for lifecycle, authorization, capacity, application state, and other persistence-backed business constraints.

FastAPI consumes the validated eligibility snapshot and must not override an authoritative Laravel rejection.

### 11.4 Skill Eligibility Rule

For every Project Required Skill with:

`is_critical_entry = true`

the learner must satisfy:

`student_skill_level >= project_minimum_required_level`

If the learner has no usable level for that Critical Entry Skill, the skill is treated as missing for eligibility and the learner is ineligible.

Examples:

| Student Level | Project Minimum | Critical Entry | Eligibility Effect |
|---:|---:|---|---|
| `3.0` | `3.0` | true | Pass |
| `3.5` | `3.0` | true | Pass |
| `2.5` | `3.0` | true | Fail |
| Missing | `3.0` | true | Fail |
| `2.0` | `3.0` | false | Does not hard-block; retained as a matching/growth gap |

### 11.5 Core / Supporting vs Critical Entry

Career Role classification and Project Eligibility remain separate concepts.

- `Core` / `Supporting` describes the importance of a Skill to a Career Role.
- `is_critical_entry` describes whether meeting a Project-specific minimum is mandatory before matching.

A Career Role Core Skill does not automatically block every Project.

For MVP Project creation, when a Core Skill must be mandatory for a specific Project, the Admin/configuration must explicitly mark that Project Skill as:

`is_critical_entry = true`

This preserves a single deterministic hard-blocking mechanism and avoids treating every Core Skill as universally mandatory across all Projects.

This rule requires Product/Backend approval because the MVP preparation story uses the wording "Core Skills" for minimum eligibility while the current runtime contract uses Project `is_critical_entry`.

### 11.6 Non-Critical Skill Gaps

For a Required Skill with:

`is_critical_entry = false`

a learner may remain eligible when the skill is missing or below the Project minimum.

The gap must be retained for Matching as a potential:

- Skill Compatibility limitation;
- Learning Value opportunity;
- explanation / limiting factor.

A non-critical gap must not be silently converted into a hard eligibility failure.

### 11.7 Career Role Eligibility

Every Project must be linked to an approved Career Role for MVP Project creation.

The Project Career Role is always used by Matching for Career Relevance.

A Career Role mismatch becomes a hard eligibility failure only when the Project explicitly defines the Career Role as an entry restriction.

Otherwise, Career Role alignment remains a Matching factor rather than an automatic eligibility blocker.

This avoids excluding potentially useful cross-role growth Projects unless Product explicitly configures them as role-restricted.

### 11.8 Constraint Representation

Eligibility constraints should be represented as structured data rather than free-text-only decisions.

Recommended decision snapshot fields remain aligned with the current matching contract:

- `eligibility_state`
- `validation_state`
- `constraints`
- `skill_gaps`
- `eligibility_reasons`
- `authorization`

Every blocking constraint should identify:

- constraint type;
- evaluated value or reference;
- blocking status;
- human-readable reason.

### 11.9 Eligibility and Validation State Contract

The current integration uses separate input-validation and recommendation-output states.

Laravel/FastAPI validation snapshot input:

| Field | Allowed State | Meaning |
|---|---|---|
| `eligibility_state` | `eligible` | Authoritative eligibility checks passed. |
| `eligibility_state` | `not_eligible` | One or more authoritative hard eligibility checks failed. |
| `validation_state` | `validated` | Eligibility validation completed. |
| `validation_state` | `not_validated` | Required validation could not be completed. |

FastAPI recommendation output:

| Field | Allowed State | Meaning |
|---|---|---|
| `eligibility_state` | `eligible` | Project is eligible for scored matching. |
| `eligibility_state` | `ineligible` | Input validation or matching eligibility prevents a qualified recommendation. |
| `matching_state` | `scored` | Recommendation was scored. |
| `matching_state` | `blocked` | Recommendation is blocked and must not enter qualified ranking. |

`not_validated` is a `validation_state`, not a recommendation `eligibility_state`. The framework must preserve this distinction in logs, persistence, tests, and documentation.

### 11.10 Missing Data Policy

Missing data must not be silently converted into a pass.

Rules:

1. Missing learner level for a Critical Entry Skill -> validation input `eligibility_state = not_eligible`; if evaluated by FastAPI directly, the recommendation output is `eligibility_state = ineligible` and `matching_state = blocked`.
2. Missing Project minimum for a Required Skill -> Project configuration invalid; do not publish/match.
3. Missing mandatory access/lifecycle data -> `validation_state = not_validated` or Backend rejection.
4. Missing non-critical learner skill -> learner may remain eligible; preserve the gap for Matching.
5. Missing optional Matching-only preference data must not become an eligibility failure.

### 11.11 Explainable Ineligibility Reasons

Every failed hard filter must produce a clear reason.

Examples:

- `Missing critical skill: Python.`
- `Python level 2.5 is below the Project minimum 3.0.`
- `Project application window is closed.`
- `Project capacity is full.`
- `Learner already has an active application for this Project.`
- `Learner is not authorized for this restricted Project.`

Multiple failures may be returned together so the decision is auditable and useful to the learner/admin.

### 11.12 Eligibility Evaluation Order

Recommended deterministic evaluation order:

1. Validate Project configuration completeness.
2. Validate Project lifecycle / visibility / application window.
3. Validate authorization and explicit access constraints.
4. Validate capacity / requested role availability where applicable.
5. Validate duplicate application / assignment conflicts.
6. Validate Project Critical Entry Skills.
7. Validate other configured blocking constraints.
8. Produce the final structured eligibility result.

Matching must execute only after the final eligibility state is `eligible`.

### 11.13 Eligibility Test Matrix

The minimum MVP validation set must include:

1. Eligible learner meeting all Critical Entry Skills.
2. Missing Critical Entry Skill.
3. Critical Entry Skill below minimum.
4. Missing non-critical Skill.
5. Multiple non-critical gaps.
6. Multiple Critical Entry failures.
7. Closed/expired Project.
8. Unauthorized/restricted Project.
9. Duplicate active application.
10. Conflicting active assignment where applicable.
11. Missing required Project configuration data.
12. Eligible learner with manageable growth gaps.

### 11.14 Eligibility Ownership Boundary

Laravel owns and validates persistence-backed business facts, including:

- Project lifecycle/status;
- visibility/access;
- application window;
- capacity;
- application state;
- authorization;
- active assignment conflicts.

Data Science / FastAPI owns deterministic analytical interpretation of the validated matching snapshot, including:

- Project skill compatibility;
- Critical Entry skill checks in the matching contract;
- structured analytical limiting factors;
- downstream Matching calculations for eligible candidates.

The same business fact must not be independently invented in both services.ouble-counting the same growth signal under both `Learning Value` and `Growth Potential`.

A future independent Growth Potential factor requires an approved algorithm/configuration version change.

## 12. Project Matching Criteria and Weights

### 12.1 Objective

Matching ranks only Projects whose final Eligibility state is `eligible`.

Each eligible Project receives an explainable score on a `0..100` scale using versioned, configurable factor weights.

Initial algorithm identifier:

`project-matching-v1`

Initial configuration identifier:

`project-matching-config-v1`

### 12.2 MVP Matching Factors and Weights

| Factor | Weight | Purpose |
|---|---:|---|
| Skill Compatibility | `0.35` | Measure how well the learner's current skill levels satisfy Project Required Skills. |
| Learning Value | `0.25` | Reward manageable non-critical gaps that create useful growth without making the Project ineligible. |
| Career Relevance | `0.20` | Measure alignment between the learner's target Career Role and Project role/domain context. |
| Interest Match | `0.10` | Measure alignment between learner interests and the Project domain. |
| Availability Fit | `0.10` | Measure compatibility between learner availability/preferences and Project schedule/work mode. |

Total weight:

`1.00`

Weights are configuration, not hidden constants. A material weight change requires a new configuration version.

### 12.3 Matching Formula

Each factor score is normalized to `0..100`.

`ProjectMatch = 0.35 * SkillCompatibility + 0.25 * LearningValue + 0.20 * CareerRelevance + 0.10 * InterestMatch + 0.10 * AvailabilityFit`

For each factor:

`WeightedContribution_i = FactorScore_i * Weight_i`

Final theoretical score:

`TheoreticalProjectMatch = SUM(WeightedContribution_i)`

The scored result is clamped to `0..100`.

If Eligibility is blocked, the Project must not enter qualified Ranking and its matching score is treated as `0`.

### 12.4 Growth Potential Alignment

The MVP Launch Preparation story lists `Growth Potential` as a Matching consideration.

For `project-matching-v1`, Growth Potential is **not** a separate sixth weighted factor.

It is represented primarily through `Learning Value`, which rewards manageable skill gaps, and through the recommendation explanation.

This avoids double-counting the same growth signal under both `Learning Value` and `Growth Potential`.

A future independent Growth Potential factor requires an approved algorithm/configuration version change.

### 12.5 Factor Semantics — Current v1 Baseline

#### Skill Compatibility

Skill Compatibility uses Project Required Skills and compares the learner's current level with each Project minimum.

Critical Entry failures are handled by Eligibility before qualified Ranking.

Non-critical missing/below-minimum Skills remain visible as compatibility limitations and growth opportunities.

#### Learning Value

Learning Value is growth-oriented.

Current v1 behavior evaluates non-critical Required Skills and rewards manageable gaps where:

`0 < skill_gap <= manageable_gap_max`

Current v1 configuration:

`manageable_gap_max = 1.0`

A missing or below-minimum non-critical Skill may therefore increase Learning Value when the gap is manageable, while a large gap does not receive the same growth reward.

Learning Value must never override a Critical Entry eligibility failure.

#### Career Relevance

Current v1 compares the learner's target Career Role title against Project role/domain metadata using deterministic normalized-term coverage.

Result states are:

- `strong`
- `partial`
- `weak`
- `unavailable`

When target-role or Project role/domain data is unavailable, v1 uses the configured neutral fallback score.

#### Interest Match

Current v1 compares learner interests with Project domain metadata using deterministic normalized-term coverage.

Result states are:

- `strong`
- `partial`
- `weak`
- `unavailable`

Missing optional interest/domain data uses the configured neutral fallback.

#### Availability Fit

Current v1 evaluates available comparisons between:

- learner availability and Project schedule;
- learner preferred work type and Project work mode.

Each available comparison contributes `100` for a normalized exact match or `0` for a mismatch, and available comparisons are averaged.

In the current integrated Backend flow, `work_mode` and `schedule` are also enforced as hard eligibility constraints when configured. A mismatch rejected by Laravel does not proceed to qualified FastAPI scoring. `location` and `language` are not currently enforced as hard eligibility constraints.

The current Backend comparison for `schedule` is strict text equality, so semantically equivalent values with different casing or formatting can fail eligibility. `weekly_availability_hours` is not currently part of the Project Matching payload. These are alignment items for a later contract/configuration revision rather than behavior to silently change in matching v1.

If no comparison can be made for an optional scoring factor, v1 uses the configured neutral fallback.

### 12.6 Optional-Factor Neutral Fallback

Current v1 configuration:

`optional_factor_fallback_score = 50.0`

The neutral fallback is used only when an optional factor cannot be evaluated from the supplied snapshot.

It must not be interpreted as evidence of a strong match or a mismatch.

Missing data required for Eligibility is handled by the Eligibility Missing Data Policy and must not use this optional-factor fallback.

### 12.7 Explainability Output

Every scored recommendation must expose enough information to explain the result, including:

- `factor_scores`
- `weighted_contributions`
- `explanation`
- `limiting_factors`
- `skill_results`
- `eligibility_state`
- `matching_state`
- `algorithm_version`
- `configuration_version`

The user-facing explanation should identify the strongest positive factors, meaningful skill gaps, and relevant limitations without hiding the deterministic score components.

### 12.8 Configuration Validation

The five Matching weights must:

- each remain within `0..1`;
- sum to exactly `1.0`;
- be versioned with the Matching configuration.

Unsupported algorithm or configuration versions must be rejected rather than silently interpreted using current rules.

### 12.9 Current v1 Scope vs MVP Enrichment

The current v1 runtime already supports the five-factor formula above.

The MVP preparation work should treat the following as enrichment items requiring explicit contract/data alignment before changing the algorithm:

- Career Relevance enrichment using structured Project learning outcomes;
- Availability Fit enrichment using duration/workload and learner weekly availability;
- location/language preference scoring where the Product defines them as Matching factors rather than hard constraints;
- Top-N Project ranking orchestration across multiple eligible Projects.

These items must not be described as implemented until their required Backend fields and versioned runtime behavior are confirmed.

## 13. Project Ranking Logic

### 13.1 Ranking Input

Only Projects with final `eligibility_state = eligible` and `matching_state = scored` may enter the qualified recommendation ranking.

Ineligible, blocked, or not-validated Projects must not appear as qualified recommendations.

### 13.2 Deterministic Sort Order

Eligible scored Projects are ordered by:

1. `score DESC`
2. `project_id ASC` as the deterministic tie-breaker when scores are equal.

Identical input snapshots and configuration versions must always produce the same ranking order.

### 13.3 Top-N Recommendations

The MVP recommendation flow should support a configurable `top_n` result count after Eligibility and scoring.

If fewer than `top_n` eligible Projects exist, return all available eligible scored Projects rather than filling the list with ineligible Projects.

### 13.4 Ranked Recommendation Output

Each ranked Project should expose enough data to explain and reproduce its position, including:

- `rank`
- `project_id` and `project_version`
- final `score`
- `factor_scores`
- `weighted_contributions`
- `explanation`
- `limiting_factors`
- `skill_results`
- `algorithm_version`
- `configuration_version`

### 13.5 Ineligible Project Handling

Diagnostic calculations may retain blocked Projects for audit or debugging, but blocked Projects must never be presented to the learner as qualified recommendations.

A blocked Project is treated as score `0` for matching output and excluded from qualified Top-N ranking.

### 13.6 Current v1 Runtime Alignment

The current integrated API flow matches one Project per request. Laravel exposes Project-level matching rather than a Top-N recommendation endpoint, and its recommendation listing uses pagination rather than ranking orchestration.

FastAPI contains deterministic multi-project sorting logic with scored Projects first, score descending, and `project_id` ascending as the tie-breaker, but there is no current end-to-end HTTP flow that evaluates a candidate set and returns the best N Projects.

Therefore Top-N remains an integration/design item. Pilot validation can still evaluate Projects independently and apply deterministic ranking to the resulting eligible scored recommendations without claiming that a Product Top-N endpoint is already implemented.

### 13.7 Ranking Validation Cases

Minimum validation cases:

1. Higher score ranks before lower score.
2. Equal scores use `project_id ASC` tie-breaking.
3. Ineligible Projects are excluded from qualified ranking.
4. Fewer than Top-N eligible Projects returns only the available eligible set.
5. Repeated identical input produces identical ranking.
6. Configuration-version changes are traceable and do not silently rewrite historical ranking results.


## 14. Representative Student Profiles

### 14.1 Purpose

These profiles are deterministic MVP validation fixtures.
They are not real learner records.
All skill values use the canonical `0..5` scale.

### 14.2 SP-01 - Beginner Frontend Learner

Target Career Role: `Frontend Developer`

Skills:
- JavaScript: `2.0`
- React: `1.5`
- CSS / Tailwind: `2.0`
- TypeScript: `1.0`

Interests: `frontend`, `UI`
Availability: `part_time`
Preferred work type: `remote`

Validation intent:
- eligible for suitable Beginner Frontend Projects when Critical Entry minimums are met;
- lower Skill Compatibility than stronger Frontend profiles on the same Project;
- manageable non-critical gaps may contribute to Learning Value.

### 14.3 SP-02 - Intermediate Backend Learner

Target Career Role: `Backend Developer`

Skills:
- Programming Fundamentals: `3.0`
- SQL & Databases: `3.0`
- REST APIs: `3.0`
- Authentication & Authorization: `2.5`
- Backend Architecture: `2.5`

Interests: `backend`, `APIs`
Availability: `full_time`
Preferred work type: `remote`

Validation intent:
- strong Career Relevance for Backend Projects;
- eligible when configured Critical Entry minimums are met;
- suitable baseline for Intermediate Backend Project ranking tests.

### 14.4 SP-03 - Advanced Data Analyst Learner

Target Career Role: `Data Analyst`

Skills:
- Python: `4.0`
- Pandas: `4.0`
- SQL: `3.5`
- NumPy: `3.5`

Interests: `data analysis`, `analytics`
Availability: `full_time`
Preferred work type: `hybrid`

Validation intent:
- high Skill Compatibility for aligned Data Analyst Projects;
- Advanced Projects remain eligible only when every Critical Entry minimum is met;
- unrelated Career Roles must not rank first based only on high skill levels.

### 14.5 SP-04 - Learner with Skill Gaps

Target Career Role: `Backend Developer`

Skills:
- Programming Fundamentals: `3.0`
- SQL & Databases: `2.0`
- REST APIs: `2.5`
- Authentication & Authorization: `2.0`
- Backend Architecture: `2.0`

Interests: `backend`
Availability: `part_time`
Preferred work type: `remote`

Validation intent:
- non-critical gaps may remain eligible;
- a gap of `1.0` may be treated as manageable by current v1 Learning Value logic;
- the same gap must block Eligibility when that skill is Critical Entry.

### 14.6 SP-05 - Multi-Interest Learner

Target Career Role: `Data Analyst`

Skills:
- Python: `3.0`
- Pandas: `3.0`
- SQL: `3.0`
- NumPy: `2.5`

Interests: `data analysis`, `backend`, `APIs`
Availability: `full_time`
Preferred work type: `remote`

Validation intent:
- Career Relevance remains centered on the target Data Analyst role;
- multiple interests may affect Interest Match;
- interests must not override Critical Entry Eligibility.

### 14.7 SP-06 - Availability-Constrained Learner

Target Career Role: `Frontend Developer`

Skills:
- JavaScript: `3.0`
- React: `3.0`
- CSS / Tailwind: `2.5`
- TypeScript: `2.0`

Interests: `frontend`
Availability: `part_time`
Preferred work type: `remote`

Validation intent:
- strong skills may coexist with reduced Availability Fit;
- optional schedule or work-mode mismatch reduces Matching only;
- mandatory schedule or work-mode mismatch must be rejected by Eligibility first.

### 14.8 Profile Validation Rules

Executable fixtures must use canonical `skill_id` values.
Preserve Career Role, Project, algorithm, and configuration versions.
Run Eligibility before Matching.
Record factor scores, weighted contributions, limiting factors, and explanation.
Repeated identical snapshots must return identical results.


## 15. Deterministic Validation Scenarios

### 15.1 Validation Principle

Validation must use controlled Student and Project snapshots.
Each snapshot must preserve algorithm and configuration versions.
Eligibility must execute before qualified Matching and Ranking.
Repeated identical input must produce identical output.

Final Pilot ranking assertions require an approved Pilot Project fixture set.
Do not invent final Pilot rankings before those Project fixtures exist.

### 15.2 Difficulty Validation Scenarios

`DIF-01` - Low required levels, bounded scope, short duration, one deliverable, guided execution.
Expected: `Beginner`.

`DIF-02` - Intermediate levels, connected tasks, medium duration, multiple deliverables, limited support.
Expected: `Intermediate`.

`DIF-03` - Complex scope, high independence, major deliverables, and advanced skill demand.
Expected: `Advanced`.

`DIF-04` - Critical Entry Skill has minimum level `4.0`.
Expected: Advanced guardrail applies.

`DIF-05` - Complexity is Advanced while the weighted index would otherwise fall in Beginner.
Expected: minimum `Intermediate` classification and review.

`DIF-06` - One required difficulty factor is missing.
Expected: final Difficulty classification is blocked.

### 15.3 Eligibility and Matching Validation Scenarios

`VAL-01` - SP-01 meets all Critical Entry minimums on a Beginner Frontend Project.
Expected: eligible and scored.

`VAL-02` - SP-01 is below a Critical Entry JavaScript or React minimum.
Expected: not eligible and excluded from qualified Ranking.

`VAL-03` - SP-02 meets Intermediate Backend Critical Entry requirements.
Expected: eligible with strong Backend Career Relevance.

`VAL-04` - SP-04 has a `1.0` gap on a non-critical SQL requirement.
Expected: eligible and the manageable gap contributes to Learning Value.

`VAL-05` - The same SQL requirement in VAL-04 is marked Critical Entry.
Expected: not eligible because the minimum is not met.

`VAL-06` - SP-03 is evaluated against an aligned Advanced Data Analyst Project.
Expected: eligible only when every Critical Entry minimum is met.

`VAL-07` - An Advanced Data Project requires a Critical Entry level above SP-03 current level.
Expected: not eligible regardless of other strong factors.

`VAL-08` - SP-05 matches several interests but the Project has weak Career Relevance.
Expected: Interest Match may improve the score but must not override the configured factor weights.

`VAL-09` - SP-06 has strong Frontend skills but a non-hard availability preference mismatch, such as a future configured location/language preference.
Expected: learner remains eligible; the preference may affect Matching only when that factor is implemented and configured.

`VAL-10` - SP-06 violates a configured `schedule` or `work_mode` constraint in the current Backend flow.
Expected: Laravel Eligibility rejects the Project before qualified Matching or Ranking.

`VAL-11` - Two eligible Projects have different Project Match scores.
Expected: higher score ranks first.

`VAL-12` - Two eligible Projects have equal scores.
Expected: lower `project_id` ranks first as the deterministic tie-breaker.

`VAL-13` - Eligible and ineligible Projects are evaluated together.
Expected: only eligible scored Projects enter qualified Top-N Ranking.

`VAL-14` - Optional Interest or Availability data cannot be evaluated.
Expected: use the configured neutral fallback score `50.0`.

`VAL-15` - The same validated snapshot is evaluated twice.
Expected: factor scores, final score, explanation inputs, and ordering are identical.

### 15.4 Validation Result Record

Each executed validation case should record:
- scenario ID;
- Student Profile ID;
- Project ID and version;
- Eligibility result;
- ineligibility reasons when blocked;
- factor scores;
- weighted contributions;
- final Project Match score;
- ranking position;
- recommendation explanation;
- expected result;
- actual result;
- pass or fail;
- issue reference when unexpected.

## 16. MVP Approval Baseline

### 16.1 Data Framework Deliverables

This framework now defines the requested MVP analytical artifacts:
- Career Role to Skill mapping baseline;
- Core and Supporting Skill semantics;
- canonical Skill Level usage for Project requirements;
- Project Difficulty criteria and configuration;
- Project Eligibility rules;
- Matching factors, weights, and formula;
- deterministic Ranking logic;
- representative Student Profiles;
- deterministic validation scenarios.

### 16.2 Decisions Requiring Approval

The following decisions remain subject to Product, Backend, or Domain approval:
- confirm the final Backend Developer Core/Supporting classifications, target levels, and importance weights against the approved backend catalog;
- confirm Career Role Core semantics versus Project Critical Entry semantics;
- approve Difficulty factor weights, thresholds, bands, and guardrails;
- approve Growth Potential as part of Learning Value for matching v1;
- decide whether the current hard `schedule` constraint should remain for the Pilot or move to preference scoring after schedule values are standardized; `work_mode` is currently hard while `location` and `language` are not;
- define Top-N ownership/orchestration and the Product recommendation count; the current integrated API matches one Project per request;
- approve the Pilot Project Catalog used for final validation.

### 16.3 Pilot Readiness Status

Data Framework status: `Ready for cross-team review and implementation alignment`.

Backend ↔ FastAPI isolated Project Matching E2E status: `PASS` — successful eligible/scored flow, persistence/readback, and critical-skill rejection before FastAPI invocation were verified by the Backend team.

Deployed Render Project Matching verification status: `Pending` — the deployed version and `DATA_SCIENCE_PROJECT_MATCHING_ENABLED` setting have not yet been confirmed.

Pilot Recommendation Validation status: `Pending approved Pilot Project fixtures and execution`.

Student MVP Pilot Launch status: `Not approved by this analytical document alone`.

Final approval requires execution of the validation matrix, review of unexpected Recommendations, resolution of critical issues, and approval of the final Matching configuration.
