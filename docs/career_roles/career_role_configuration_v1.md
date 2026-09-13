# SkillSpan — Career Role Configuration v1

## Purpose

Define and validate the versioned career-role configuration consumed by the SkillSpan Intelligence Service while Laravel remains the source of truth for persistence and lifecycle management.

## Version

`career-role-config-v1`

## Ownership

- Laravel owns career roles, versions, skills, approval status, effective dates, and persistence.
- FastAPI validates the configuration deterministically and remains stateless.
- This contract does not modify `skill-gap-v1` or `baseline-v1.0`.

## Career Role Metadata

A role configuration includes:

- `career_role_id`
- `title`
- `slug`
- `version`
- `status`: `draft`, `approved`, or `retired`
- optional `effective_date`
- optional `description`
- one or more required skills

Only an `approved` configuration is marked `production_eligible=true` by this validator.

## Required Skill Configuration

Each role skill contains:

- `skill_id`
- `skill_name`
- `required_level` on the approved `0..5` scale
- `importance_weight` with `0 < weight <= 1`
- `is_critical`
- `prerequisites`: zero or more prerequisite skill references, each containing `skill_id` and optional `slug` / `name` metadata
- optional legacy `prerequisite_skill_id`, retained for backward compatibility

Duplicate `skill_id` values are rejected.

## Weight Normalization

Configured weights are preserved as input values. FastAPI calculates normalized weights deterministically as:

`normalized_weight = importance_weight / SUM(importance_weight)`

The configured total must be positive. A positive total different from `1.00` is normalized rather than silently treated as an error.

## Prerequisite Validation

Prerequisite relationships may contain multiple prerequisites per skill. The Backend decision-snapshot shape is:

```json
"prerequisites": [
  {
    "skill_id": 2,
    "slug": "javascript",
    "name": "JavaScript"
  }
]
```

The validator also accepts the legacy single `prerequisite_skill_id` field for backward compatibility. When both forms are present, their skill IDs are merged for graph validation.

Prerequisite relationships must satisfy all of the following:

1. A skill cannot depend on itself.
2. Every prerequisite must exist inside the same career-role configuration.
3. Duplicate references inside `prerequisites` are rejected.
4. The prerequisite graph must be acyclic, including cycles involving multiple prerequisites.
5. A deterministic topological prerequisite order is returned for valid configurations.

Configurations containing cycles are rejected.

## API

`POST /api/v1/career-role-configuration/validate`

The endpoint returns HTTP `200` for a valid configuration and HTTP `422` for semantic configuration errors such as duplicate skills, invalid prerequisite references, self-dependencies, or cycles.

## Output

The validation response contains:

- configuration version
- career role ID and role version
- lifecycle status
- original weight total
- normalized weight total
- production eligibility
- prerequisite order
- normalized skill weights

## Test Coverage

Runtime tests cover:

- valid approved configuration
- deterministic prerequisite ordering
- multiple prerequisites per skill
- mixed legacy/new prerequisite compatibility
- normalization when weights already sum to `1.00`
- normalization when positive weights do not sum to `1.00`
- draft production eligibility
- duplicate skills
- self-prerequisites
- missing prerequisite references
- duplicate multiple-prerequisite references
- prerequisite cycles, including multiple-prerequisite graphs
- API success and API rejection behavior

## Compatibility

This validator is an independent configuration-validation boundary. Multiple-prerequisite support is an additive backward-compatible extension of `career-role-config-v1`; the legacy single prerequisite field remains accepted during migration. This change does not modify Skill Match scoring, the existing Skill Gap readiness formula, critical-skill cap behavior, Baseline scoring, or their algorithm versions.
