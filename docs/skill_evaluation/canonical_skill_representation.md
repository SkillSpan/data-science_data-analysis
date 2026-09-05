# SkillSpan — Canonical Skill Representation Specification

**Area:** Data Science / Data Analysis
**Status:** Draft for Backend / Product / Domain Review
**Scope:** Skill Evaluation foundation
**Document purpose:** Define the canonical representation of a Skill used across assessment, evidence, evaluation, readiness, matching, and analytics.

---

## 1. Objective

SkillSpan requires one authoritative representation for each skill so that spelling variants do not create duplicate skills, assessments and evidence map to stable identifiers, historical evaluations remain reproducible, and readiness/matching consume consistent references.

This contract does **not** modify the current `skill-gap-v1` runtime contract.

## 2. Source-of-Truth Principle

- **Backend / authorized domain experts:** own canonical skill records, aliases, lifecycle, taxonomy publication, and version history.
- **Data Science / Intelligence:** consumes canonical identifiers and validated metadata.
- **Frontend:** displays labels supplied by Backend and must not create analytical skill identifiers from free text.

A Skill must be referenced analytically by its stable canonical identifier, not by display name alone.

## 3. Canonical Skill Entity

| Field | Type | Requirement | Purpose |
|---|---|---|---|
| `skill_id` | positive integer | Required | Stable canonical identifier used across mappings/evidence/evaluations/readiness. |
| `canonical_name` | string | Required | Official human-readable skill name. |
| `aliases` | array of strings | Required; may be empty | Alternate names/spelling variants resolving to this skill. |
| `taxonomy_version` | version identifier | Required | Taxonomy/configuration context used when the skill was resolved. |
| `category` | string / canonical reference | Recommended | Approved taxonomy grouping. |
| `description` | string or null | Optional | Domain description. |
| `lifecycle_status` | controlled value | Recommended | Exact allowed values require Backend/domain confirmation. |
| `superseded_by_skill_id` | positive integer or null | Conditional | Traceability when replaced by another canonical skill. |
| `updated_at` | ISO 8601 timestamp or null | Recommended | Audit/freshness metadata. |

## 4. Canonical Identity Rules

### CR-01 — Stable identifier
`skill_id` is the analytical identity. Renaming a skill must not create a new analytical skill if the underlying meaning is unchanged.

### CR-02 — Canonical name
`canonical_name` must be non-empty, trimmed, and represent one approved skill concept. It must not be used as the sole integration identity.

### CR-03 — Alias resolution
Every approved alias must resolve to exactly one canonical `skill_id` in the active taxonomy context.

Example:

```text
"PowerBI"     -> Power BI
"Power BI"    -> Power BI
"MS Power BI" -> Power BI
```

### CR-04 — Ambiguous aliases
If one alias can map to more than one canonical skill, automatic mapping must not guess. The value must be rejected as ambiguous or routed for authorized review.

### CR-05 — Unknown skills
Unmapped free-text skill names must not silently create new canonical skills.

### CR-06 — Historical integrity
Historical evidence/evaluations must retain the original canonical reference and version. Supersession must be explicit and auditable.

## 5. Lifecycle Semantics

The SRS requires skill lifecycle/versioning but does not define the exact lifecycle enum. Therefore exact values remain a Backend/domain decision.

Analytical behavior must still ensure:
- active skills may receive new mappings/evidence;
- retired/superseded skills remain resolvable historically;
- new decisions use the approved taxonomy;
- historical outputs retain the version used at calculation time.

## 6. Versioning Rules

A taxonomy version should change when analytical interpretation can change, for example:
- skill split;
- skill merge;
- alias remapping;
- supersession;
- material category/mapping changes.

## 7. Proposed Normalized Object

```json
{
  "skill_id": 7,
  "canonical_name": "SQL",
  "aliases": ["Structured Query Language"],
  "category": "Data",
  "description": "Querying and manipulating relational data using SQL.",
  "lifecycle_status": "active",
  "superseded_by_skill_id": null,
  "taxonomy_version": "skill-taxonomy-v1",
  "updated_at": "2026-09-02T00:00:00Z"
}
```

This is a proposed analytical representation, not a claim about current Laravel field names.

## 8. Validation Rules

1. `skill_id` must be positive.
2. `canonical_name` must be non-blank.
3. aliases must not contain blank entries.
4. duplicate aliases must be normalized or rejected.
5. one alias must not resolve to multiple active skills without explicit disambiguation.
6. `taxonomy_version` must be present.
7. `superseded_by_skill_id` must not equal `skill_id`.
8. supersession chains must not contain cycles.
9. lifecycle/category values must follow approved configuration.
10. timestamps, when exposed, must be ISO 8601 with timezone.

## 9. Data Science Usage Rules

Data Science should:
- use `skill_id` for joins/calculations;
- use canonical names for display/explanation only;
- never infer identity solely from spelling/capitalization;
- reject or flag unknown/unmapped skill references;
- retain taxonomy/mapping version information where it affects reproducibility.

## 10. Edge Cases

| Case | Required behavior |
|---|---|
| Same alias with different case | Resolve using approved normalization rules. |
| Whitespace-only alias | Reject. |
| Duplicate alias within one skill | Deduplicate or reject during taxonomy validation. |
| Alias maps to two active skills | Mark ambiguous; do not auto-select. |
| Unknown free-text skill | Do not auto-create a canonical skill. |
| Retired skill in historical evidence | Preserve and resolve historically. |
| Retired skill in new mapping | Reject or require approved supersession target. |
| Skill supersedes itself | Reject. |
| Supersession cycle | Reject taxonomy publication. |
| Missing taxonomy version | Reject where versioning is required for reproducibility. |

## 11. Backend Field Reconciliation — Confirmed Current Model

Current Backend `Skill` model fields confirmed by the Backend team:

```text
Skill.id              -> skill_id
Skill.name            -> canonical_name
Skill.slug            -> slug
Skill.category        -> category
Skill.description     -> description
Skill.status          -> lifecycle_status
Skill.version         -> taxonomy_version
Skill.parent_skill_id -> parent_skill_id
```

Data Science must use `Skill.id` as the canonical analytical identity. `Skill.name` and `Skill.slug` are descriptive/resolution fields and must not replace the stable ID in calculations or joins.

`parent_skill_id` may represent taxonomy hierarchy and must not be interpreted as supersession unless the Backend/domain contract explicitly defines that semantic.

### Remaining taxonomy integration gap

The SRS requires aliases to resolve spelling/name variants to one canonical Skill, but the confirmed current `Skill` fields do not include an alias field or alias table. Therefore alias persistence/resolution must be confirmed before implementing automatic alias mapping in FastAPI. Until then, Data Science should expect canonical `skill_id` values from Backend rather than infer identity from free text.

## 12. Backend / Domain Confirmations Required

Remaining confirmations before runtime integration:
- alias storage model;
- category allowed values and domain semantics;
- lifecycle/status allowed values;
- exact semantics and governance of `Skill.version`;
- superseded/retired skill representation, including whether `parent_skill_id` participates in that behavior;
- whether `updated_at` is exposed;
- whether Backend resolves aliases before sending Data Science payloads.

## 13. Definition of Done

- [x] Stable canonical identifier rule defined.
- [x] Canonical name and alias semantics defined.
- [x] Taxonomy version requirement defined.
- [x] Historical/supersession behavior defined.
- [x] Validation and edge cases documented.
- [x] Data Science consumption rules documented.
- [x] Current Backend `Skill` field mapping confirmed.
- [ ] Domain lifecycle/category values confirmed.
- [ ] Machine-readable schema approved.
- [ ] Runtime contract tests implemented after approval.
