# SkillSpan Skill Gap API Contract

## 1. Overview

The Skill Gap API is provided by the SkillSpan Intelligence Service.

It allows the Laravel backend to submit the trusted learner profile, target
career role, evaluated skill levels, career-role requirements, normalized
importance weights, and critical-skill flags.

The service returns:

- The weighted base readiness score.
- The final readiness score after the current critical-skill rule.
- The gap for every analyzed skill.
- Stable backend identifiers for every analyzed skill.
- Critical skills that triggered the readiness cap.
- The algorithm version used for the calculation.

This endpoint represents the current Skill Gap / Skill Match MVP calculation.
It must not be interpreted as the complete multi-component SkillSpan readiness
model.

---

## 2. Service Ownership

| Component | Responsibility |
|---|---|
| Laravel Backend | Source of truth for users, student profiles, career roles, skills, evaluations, and persisted readiness results |
| FastAPI Intelligence Service | Validates the supplied payload, calculates skill gaps and the current weighted readiness result, and returns a versioned result |
| Frontend | Calls Laravel and displays results returned by Laravel |

The frontend must not call FastAPI directly.

Expected communication flow:

```text
Frontend
   ->
Laravel Backend
   ->
FastAPI Intelligence Service
   ->
Laravel Backend
   ->
Database / Frontend
```

FastAPI does not connect directly to the Laravel database.

---

## 3. Local Service URL

```text
http://127.0.0.1:8001
```

The production URL should be configured through the deployment environment
rather than hard-coded.

---

## 4. Endpoint

| Property | Value |
|---|---|
| HTTP Method | `POST` |
| Path | `/api/v1/skill-gap` |
| Content Type | `application/json` |
| Authentication | Not implemented in the current FastAPI MVP service |
| Success Status | `200 OK` |
| Validation Error | `422 Unprocessable Entity` |

Full local URL:

```text
http://127.0.0.1:8001/api/v1/skill-gap
```

Laravel may include an `X-Request-ID` header for correlation and logging.

---

## 5. Request Body

### Example

```json
{
  "student_profile_id": 15,
  "career_role_id": 3,
  "career_role_version": 1,
  "user_id": 20,
  "target_role": "Data Analyst",
  "skills": [
    {
      "skill_id": 7,
      "skill_name": "SQL",
      "current_level": 1.0,
      "required_level": 4.0,
      "importance_weight": 0.45,
      "is_critical": true
    },
    {
      "skill_id": 11,
      "skill_name": "Python",
      "current_level": 4.0,
      "required_level": 4.0,
      "importance_weight": 0.30,
      "is_critical": true
    },
    {
      "skill_id": 19,
      "skill_name": "Power BI",
      "current_level": 4.0,
      "required_level": 4.0,
      "importance_weight": 0.25,
      "is_critical": false
    }
  ]
}
```

### Request Fields

| Field | Type | Required | Validation | Description |
|---|---|---:|---|---|
| `student_profile_id` | Integer | Yes | `> 0` | Student profile identifier from Laravel |
| `career_role_id` | Integer | Yes | `> 0` | Target career role identifier |
| `career_role_version` | Integer | Yes | `> 0` | Career role version used for the calculation |
| `user_id` | Integer | Yes | `> 0` | Authenticated platform user identifier |
| `target_role` | String | Yes | Length `2..100` | Human-readable career role title |
| `skills` | Array | Yes | At least one item | Skills included in the calculation |
| `skills[].skill_id` | Integer | Yes | `> 0` | Stable backend skill identifier |
| `skills[].skill_name` | String | Yes | Length `2..100` | Human-readable skill name |
| `skills[].current_level` | Number | Yes | `0..5` | Latest evaluated learner skill level |
| `skills[].required_level` | Number | Yes | `0..5` | Level required by the career role |
| `skills[].importance_weight` | Number | Yes | `0 < weight <= 1` | Normalized relative importance |
| `skills[].is_critical` | Boolean | Yes | `true` or `false` | Whether the skill is critical for the role |

### Importance Weight Contract

The integration contract uses normalized weights:

```text
0 < importance_weight <= 1
```

Example:

```text
SQL       = 0.45
Python    = 0.30
Power BI  = 0.25
```

Career-role configuration should normally normalize the set of weights to
approximately:

```text
1.00
```

FastAPI currently validates each individual weight but does not enforce that
the entire skills array totals exactly `1.00`.

Values such as:

```text
45
30
25
```

are invalid under the current API contract.

---

## 6. Successful Response

### Status

```text
200 OK
```

### Example

```json
{
  "student_profile_id": 15,
  "career_role_id": 3,
  "career_role_version": 1,
  "user_id": 20,
  "target_role": "Data Analyst",
  "algorithm_version": "skill-gap-v1",
  "base_readiness_score": 66.25,
  "readiness_score": 60.0,
  "critical_skill_cap_applied": true,
  "critical_skill_readiness_cap": 60.0,
  "critical_skill_gap_count": 1,
  "critical_skill_ids": [
    7
  ],
  "critical_skill_names": [
    "SQL"
  ],
  "total_skills": 3,
  "met_skills": 2,
  "skills_with_gap": 1,
  "skill_results": [
    {
      "skill_id": 7,
      "skill_name": "SQL",
      "current_level": 1.0,
      "required_level": 4.0,
      "importance_weight": 0.45,
      "is_critical": true,
      "gap": 3.0,
      "status": "gap"
    },
    {
      "skill_id": 11,
      "skill_name": "Python",
      "current_level": 4.0,
      "required_level": 4.0,
      "importance_weight": 0.30,
      "is_critical": true,
      "gap": 0.0,
      "status": "met"
    },
    {
      "skill_id": 19,
      "skill_name": "Power BI",
      "current_level": 4.0,
      "required_level": 4.0,
      "importance_weight": 0.25,
      "is_critical": false,
      "gap": 0.0,
      "status": "met"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `student_profile_id` | Integer | Student profile identifier received from Laravel |
| `career_role_id` | Integer | Career role used for the calculation |
| `career_role_version` | Integer | Career role version used |
| `user_id` | Integer | Platform user identifier received from Laravel |
| `target_role` | String | Career role title |
| `algorithm_version` | String | Algorithm version used by FastAPI |
| `base_readiness_score` | Number | Weighted score before critical-skill rules |
| `readiness_score` | Number | Final score after the current critical-skill rule |
| `critical_skill_cap_applied` | Boolean | Whether the final score was reduced by the cap |
| `critical_skill_readiness_cap` | Number or Null | Active cap value when a major critical gap exists |
| `critical_skill_gap_count` | Integer | Number of critical skills meeting the major-gap rule |
| `critical_skill_ids` | Array of Integers | Backend IDs of critical skills triggering the rule |
| `critical_skill_names` | Array of Strings | Names of critical skills triggering the rule |
| `total_skills` | Integer | Number of analyzed skills |
| `met_skills` | Integer | Skills meeting or exceeding the requirement |
| `skills_with_gap` | Integer | Skills below the required level |
| `skill_results` | Array | Detailed per-skill results |
| `skill_results[].skill_id` | Integer | Backend skill identifier |
| `skill_results[].skill_name` | String | Skill name |
| `skill_results[].current_level` | Number | Evaluated learner level |
| `skill_results[].required_level` | Number | Required career-role level |
| `skill_results[].importance_weight` | Number | Weight used in the calculation |
| `skill_results[].is_critical` | Boolean | Critical-skill flag |
| `skill_results[].gap` | Number | Missing skill level |
| `skill_results[].status` | String | `met` or `gap` |

---

## 7. Current Calculation Logic

For each skill:

```text
gap = max(required_level - current_level, 0)
```

The achieved level is capped at the required level:

```text
achieved_level = min(current_level, required_level)
```

Weighted achieved level:

```text
weighted_achieved =
achieved_level * importance_weight
```

Weighted required level:

```text
weighted_required =
required_level * importance_weight
```

Base readiness:

```text
base_readiness_score =
(
  sum(weighted_achieved)
  /
  sum(weighted_required)
) * 100
```

The result is rounded to two decimal places.

A skill has:

```text
status = "met"
```

when its gap equals zero.

Otherwise:

```text
status = "gap"
```

---

## 8. Current Critical Skill Rule

The current Skill Gap MVP service uses:

```text
CRITICAL_SKILL_MAJOR_GAP_THRESHOLD = 2.0
CRITICAL_SKILL_READINESS_CAP = 60.0
```

A critical skill triggers the rule when:

```text
is_critical = true
AND
gap >= 2.0
```

When a major critical gap exists:

```text
readiness_score =
min(base_readiness_score, 60.0)
```

Example:

```text
SQL current level  = 1
SQL required level = 4
SQL gap            = 3
SQL critical       = true

base_readiness_score = 66.25
readiness_score      = 60.0
```

The response retains both the base and final scores so the backend can persist
and explain the result.

These constants describe the current `skill-gap-v1` implementation and may
later move to approved algorithm or career-role configuration.

---

## 9. Algorithm Version

Current version:

```text
skill-gap-v1
```

FastAPI returns the algorithm version used for every successful calculation.

Example:

```json
{
  "algorithm_version": "skill-gap-v1"
}
```

Laravel should persist this returned version with the readiness result and
snapshot.

---

## 10. Validation Errors

Invalid request data returns:

```text
422 Unprocessable Entity
```

Examples include:

- Missing required identity fields.
- Missing `skill_id`.
- Missing `importance_weight`.
- Missing `is_critical`.
- `current_level` outside `0..5`.
- `required_level` outside `0..5`.
- `importance_weight <= 0`.
- `importance_weight > 1`.
- Empty `skills` array.

Example invalid weight:

```json
{
  "student_profile_id": 15,
  "career_role_id": 3,
  "career_role_version": 1,
  "user_id": 20,
  "target_role": "Data Analyst",
  "skills": [
    {
      "skill_id": 11,
      "skill_name": "Python",
      "current_level": 3.0,
      "required_level": 4.0,
      "importance_weight": 25,
      "is_critical": false
    }
  ]
}
```

The exact Pydantic validation message may vary by installed version.

Laravel should primarily rely on the HTTP status and structured `detail`
response.

---

## 11. Laravel Integration Responsibilities

Laravel is responsible for:

1. Authenticating and authorizing the learner.
2. Resolving the learner's `student_profile_id`.
3. Resolving the requested or primary career role.
4. Ensuring the career role is approved.
5. Loading the required career-role skills.
6. Selecting the latest trusted skill evaluation for every required skill.
7. Rejecting incomplete assessment data instead of silently using zero.
8. Sending normalized `importance_weight` values using the `0..1` contract.
9. Calling FastAPI.
10. Validating the FastAPI response.
11. Persisting successful readiness results.
12. Storing enough snapshot data for reproducibility.
13. Avoiding persistence when FastAPI fails or returns an invalid response.

---

## 12. Additional Error Handling

| Situation | Expected Handling |
|---|---|
| `200 OK` | Validate and persist or return the result |
| `422 Unprocessable Entity` | Treat the FastAPI payload as invalid |
| Connection failure | Treat the intelligence service as unavailable |
| Timeout | Return a temporary service error according to backend policy |
| FastAPI `5xx` | Log the failure and do not persist incomplete results |
| Invalid JSON or contract | Reject the response and do not persist it |

---

## 13. Stateless FastAPI Behavior

The endpoint is stateless.

It:

- Does not read from Clever Cloud or the Laravel database.
- Does not save readiness results.
- Does not update learner information.
- Does not determine authoritative application records.
- Calculates only from the validated JSON supplied by Laravel.

Laravel remains the source of truth for application data and persistence.

---

## 14. Local Testing

Activate the project environment:

```powershell
cd H:\Projects\SkillSpan\data-science_data-analysis
.\.venv\Scripts\Activate.ps1
```

Run tests:

```powershell
python -m pytest -q
```

Current expected result:

```text
6 passed
```

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

Health endpoint:

```text
http://127.0.0.1:8001/health
```

---

## 15. Current Integration Status

The FastAPI side currently provides:

- Versioned `/api/v1/skill-gap` endpoint.
- Laravel-aligned identity fields.
- Stable backend skill identifiers.
- Required normalized importance weights.
- Required critical-skill flags.
- Weighted skill-gap calculation.
- Current critical-skill rule.
- Versioned algorithm response.
- Validated request and response schemas.
- Automated API tests.
- Successful Laravel-shaped request simulation.

Current communication contract:

```text
Laravel
   ->
FastAPI /api/v1/skill-gap
   ->
Validated skill-gap-v1 response
   ->
Laravel readiness persistence
```
