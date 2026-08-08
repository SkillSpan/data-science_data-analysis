# SkillBridge Skill Gap API Contract

## 1. Overview

The Skill Gap API is provided by the SkillBridge Intelligence Service.

It allows the main SkillBridge backend to send a user's current skill
levels and the levels required for a target career role.

The service returns:

- The user's readiness score.
- The gap for each skill.
- The number of satisfied skills.
- The number of skills that require improvement.
- A status for every analyzed skill.

## 2. Service Ownership

| Component | Responsibility |
|---|---|
| Laravel Backend | Stores users, career roles, skills, assessments, projects, and analysis results |
| FastAPI Intelligence Service | Validates the input, calculates skill gaps, calculates readiness, and returns the analysis |
| Frontend | Displays the analysis received through the Laravel backend |

The frontend should not call the FastAPI service directly.

The expected communication flow is:

```text
Frontend
   ↓
Laravel Backend
   ↓ HTTP/JSON
FastAPI Intelligence Service
   ↓ JSON
Laravel Backend
   ↓
Frontend
```

## 3. Local Service URL

```text
http://127.0.0.1:8001
```

The production URL will be configured through the deployment environment.

The Laravel application should store the FastAPI base URL in an environment
configuration value rather than hard-coding it.

Example:

```env
SKILLBRIDGE_INTELLIGENCE_URL=http://127.0.0.1:8001
```

## 4. Endpoint

| Property | Value |
|---|---|
| HTTP Method | `POST` |
| Path | `/api/v1/skill-gap` |
| Content Type | `application/json` |
| Authentication | Not implemented in the current MVP service |
| Success Status | `200 OK` |
| Validation Error | `422 Unprocessable Entity` |

Full local URL:

```text
http://127.0.0.1:8001/api/v1/skill-gap
```

## 5. Request Body

### Example

```json
{
  "user_id": 1,
  "target_role": "Data Analyst",
  "skills": [
    {
      "skill_name": "SQL",
      "current_level": 1,
      "required_level": 4,
      "importance_weight": 10,
      "is_critical": true
    },
    {
      "skill_name": "Python",
      "current_level": 5,
      "required_level": 5,
      "importance_weight": 45,
      "is_critical": false
    },
    {
      "skill_name": "Power BI",
      "current_level": 5,
      "required_level": 5,
      "importance_weight": 45,
      "is_critical": false
    }
  ]
}
```

### Request Fields

| Field | Type | Required | Validation | Description |
|---|---|---:|---|---|
| `user_id` | Integer | Yes | Must be greater than `0` | User identifier from the Laravel database |
| `target_role` | String | Yes | Length from `2` to `100` characters | Career role being analyzed |
| `skills` | Array | Yes | Must contain at least one skill | Skills included in the analysis |
| `skills[].skill_name` | String | Yes | Length from `2` to `100` characters | Skill name |
| `skills[].current_level` | Number | Yes | From `0` to `5` | User's current skill level |
| `skills[].required_level` | Number | Yes | From `0` to `5` | Level required by the target role |
| `skills[].importance_weight` | Number | No | Greater than `0` and no more than `100`; defaults to `1.0` | Relative importance of the skill for the target career role |
| `skills[].is_critical` | Boolean | No | Defaults to `false` | Indicates whether the skill is essential for the target career role |

## 6. Successful Response

### Status

```text
200 OK
```

### Example

```json
{
  "user_id": 1,
  "target_role": "Data Analyst",
  "base_readiness_score": 93.88,
  "readiness_score": 60.0,
  "critical_skill_cap_applied": true,
  "critical_skill_readiness_cap": 60.0,
  "critical_skill_gap_count": 1,
  "critical_skill_names": [
    "SQL"
  ],
  "total_skills": 3,
  "met_skills": 2,
  "skills_with_gap": 1,
  "skill_results": [
    {
      "skill_name": "SQL",
      "current_level": 1.0,
      "required_level": 4.0,
      "importance_weight": 10.0,
      "is_critical": true,
      "gap": 3.0,
      "status": "gap"
    },
    {
      "skill_name": "Python",
      "current_level": 5.0,
      "required_level": 5.0,
      "importance_weight": 45.0,
      "is_critical": false,
      "gap": 0.0,
      "status": "met"
    },
    {
      "skill_name": "Power BI",
      "current_level": 5.0,
      "required_level": 5.0,
      "importance_weight": 45.0,
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
| `user_id` | Integer | User identifier received in the request |
| `target_role` | String | Career role received in the request |
| `readiness_score` | Number | Overall readiness from `0` to `100` |
| `total_skills` | Integer | Total number of analyzed skills |
| `met_skills` | Integer | Number of skills meeting the required level |
| `skills_with_gap` | Integer | Number of skills below the required level |
| `skill_results` | Array | Detailed result for every skill |
| `skill_results[].skill_name` | String | Skill name |
| `skill_results[].current_level` | Number | Current user level |
| `skill_results[].required_level` | Number | Required career-role level |
| `skill_results[].gap` | Number | Missing skill level |
| `skill_results[].status` | String | Either `met` or `gap` |
| `skill_results[].importance_weight` | Number | Relative importance used in the readiness calculation |
| `base_readiness_score` | Number | Weighted readiness score before critical-skill rules are applied |
| `critical_skill_cap_applied` | Boolean | Indicates whether the final score was reduced by the critical-skill rule |
| `critical_skill_readiness_cap` | Number or Null | Maximum allowed score when a major critical-skill gap exists |
| `critical_skill_gap_count` | Integer | Number of critical skills with a major gap |
| `critical_skill_names` | Array of Strings | Names of critical skills that triggered the rule |
| `skill_results[].is_critical` | Boolean | Indicates whether the skill is essential for the target role |

## 7. Current Calculation Logic

For each skill:

```text
gap = max(required_level - current_level, 0)
```

The achieved level is capped at the required level:

```text
achieved_level = min(current_level, required_level)
```

The readiness score uses the importance assigned to each skill:

```text
weighted_achieved =
achieved_level × importance_weight
```

```text
weighted_required =
required_level × importance_weight
```

The final readiness score is:

```text
readiness_score =
(sum of weighted achieved levels / sum of weighted required levels) × 100
```

The result is rounded to two decimal places.

A skill receives:

```text
status = "met"
```

when its gap equals zero. Otherwise:

```text
status = "gap"
```

### Backward Compatibility

Both `importance_weight` and `is_critical` are optional request fields.

When omitted, the service uses:

```text
importance_weight = 1.0
is_critical = false
```

Therefore, integrations created before weighted scoring remain compatible.

The weights do not need to total `100`. The service normalizes their effect
through the weighted readiness formula.

### Critical Skills Rule

Some skills may be essential for a target career role.

A skill is marked as critical using:

```text
is_critical = true
```

The current major-gap threshold is:

```text
CRITICAL_SKILL_MAJOR_GAP_THRESHOLD = 2.0
```

When a critical skill has a gap greater than or equal to this threshold,
the final readiness score cannot exceed:

```text
CRITICAL_SKILL_READINESS_CAP = 60.0
```

The rule is applied as follows:

```text
final_readiness_score =
min(base_readiness_score, critical_skill_readiness_cap)
```

Example:

```text
Base readiness score: 93.88
Critical skill: SQL
SQL gap: 3.0
Final readiness score: 60.0
```

A critical skill with a gap below `2.0` does not trigger the readiness cap.

The response distinguishes between:

```text
base_readiness_score
```

and:

```text
readiness_score
```

so API consumers can explain why the final result was reduced.

The values `2.0` and `60.0` are current MVP business-rule constants and may
be moved to career-role configuration in a future version.

## 8. Validation Error

Invalid request data returns:

```text
422 Unprocessable Entity
```

Example invalid request:

```json
{
  "user_id": 1,
  "target_role": "Data Analyst",
  "skills": [
    {
      "skill_name": "Python",
      "current_level": 8,
      "required_level": 4
    }
  ]
}
```

The request is rejected because `current_level` must not exceed `5`.

Example response structure:

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "body",
        "skills",
        0,
        "current_level"
      ],
      "msg": "Input should be less than or equal to 5",
      "input": 8,
      "ctx": {
        "le": 5.0
      }
    }
  ]
}
```

The exact validation message may vary by the installed Pydantic version.
Laravel should primarily rely on the HTTP status and the `detail` field.

## 9. Additional Error Handling

The Laravel backend should handle the following situations:

| Situation | Expected Handling |
|---|---|
| `200 OK` | Save or return the analysis result |
| `422 Unprocessable Entity` | Log or display validation details |
| Connection refused | Treat the intelligence service as temporarily unavailable |
| Request timeout | Retry according to backend policy or return a temporary service error |
| `500 Internal Server Error` | Log the failure and avoid storing incomplete analysis |

The Laravel backend should configure a reasonable connection and response
timeout when calling the service.

## 10. Stateless Behavior

The endpoint is currently stateless.

It:

- Does not read from the Laravel database.
- Does not save analysis results.
- Does not update user information.
- Does not authenticate users.
- Calculates the result only from the submitted JSON.

Laravel remains the source of truth and is responsible for storing any result
that must be preserved.

## 11. Local Testing

Start the service:

```bat
cd /d H:\Projects\SkillBridge\data-science_data-analysis
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Interactive API documentation:

```text
http://127.0.0.1:8001/docs
```

Health endpoint:

```text
http://127.0.0.1:8001/health
```

## 12. Integration Readiness

The current API is ready for initial Laravel integration because it provides:

- A versioned endpoint.
- Validated request schemas.
- A documented response schema.
- Predictable validation errors.
- Automated API tests.
- Successful external HTTP testing.