# SkillSpan Data Science & Intelligence Service

FastAPI-based intelligence service for the SkillSpan platform.

The service currently provides the Skill Gap / Skill Match MVP used by the Laravel Backend to analyze a learner against a target career role.

> The current score is a Skill Match / Skill Gap result.
> It is not yet the complete multi-component SkillSpan Readiness Score.

---

## Architecture

```text
React Frontend
      â†“
Laravel Backend
      â†“
FastAPI Intelligence Service
      â†“
Laravel Backend
      â†“
Database / Frontend
```

### Responsibility Boundary

**Laravel Backend**
- Source of truth for users and learner profiles.
- Owns authentication and authorization.
- Owns career roles and role versions.
- Owns skill evaluations.
- Builds trusted intelligence-service requests.
- Persists readiness results.

**FastAPI Intelligence Service**
- Validates the supplied integration payload.
- Calculates skill gaps.
- Calculates the weighted Skill Match score.
- Applies the current critical-skill rule.
- Returns deterministic, versioned calculation results.
- Does not connect directly to the Laravel database.

**Frontend**
- Communicates with Laravel.
- Must not call the FastAPI service directly.

---

## Current Features

- FastAPI application.
- Health-check endpoint.
- Automatic OpenAPI / Swagger documentation.
- Skill-gap analysis.
- Weighted Skill Match calculation.
- Critical-skill detection.
- Critical-skill readiness cap.
- Stable Backend identifiers in request and response.
- Algorithm versioning.
- `X-Request-ID` correlation support.
- Pydantic request/response validation.
- Automated API, contract, and edge-case tests.
- GitHub Actions continuous integration.

---

## Skill Gap API

### Endpoint

```http
POST /api/v1/skill-gap
```

Local URL:

```text
http://127.0.0.1:8001/api/v1/skill-gap
```

### Request Example

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

### Important Contract Rules

- Skill levels use the `0..5` scale.
- `skill_id` must be a positive Backend identifier.
- `importance_weight` is required.
- `importance_weight` must satisfy:

```text
0 < importance_weight <= 1
```

- `is_critical` is required.
- At least one skill must be supplied.
- Laravel is responsible for supplying trusted learner, role, and evaluation data.

---

## Current Algorithm

Algorithm version:

```text
skill-gap-v1
```

For every skill:

```text
gap = max(required_level - current_level, 0)
```

Achieved level is capped at the role requirement:

```text
achieved_level = min(current_level, required_level)
```

Weighted base score:

```text
base_readiness_score =
    sum(achieved_level Ã— importance_weight)
    /
    sum(required_level Ã— importance_weight)
    Ã— 100
```

### Current Critical-Skill Rule

Current implementation:

```text
Major critical gap threshold = 2.0
Readiness cap              = 60.0
```

If a critical skill has:

```text
gap >= 2.0
```

the final current Skill Match score cannot exceed:

```text
60.0
```

These values belong to the current `skill-gap-v1` implementation.

They must not be silently changed without an approved product/domain decision and an appropriate algorithm-version change.

---

## Current Scope vs Future Readiness

The current implementation covers:

```text
Skill Gap
+
Weighted Skill Match
+
Critical Skill Rule
```

The complete SkillSpan Readiness model is expected to include additional components such as:

```text
Skill Match
Practical Experience
Assessment Reliability
Profile Completeness
```

Those future components are not yet calculated by this service.

---

## Request Correlation

Laravel may send:

```http
X-Request-ID: <request-id>
```

The FastAPI service preserves the supplied request ID and returns it in the response header.

If no request ID is supplied, the service generates a UUID automatically.

This supports request correlation between Laravel and FastAPI logs.

---

## Service Authentication

Service-to-service authentication is not implemented in the current FastAPI MVP.

Production authentication between Laravel and FastAPI must be agreed and implemented by both services before production deployment.

---

## Local Setup

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate on Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install Runtime Dependencies

```bash
python -m pip install -r requirements.txt
```

### Install Development / Test Dependencies

```bash
python -m pip install -r requirements-dev.txt
```

### Run the Service

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

---

## Local URLs

Health:

```text
http://127.0.0.1:8001/health
```

Swagger UI:

```text
http://127.0.0.1:8001/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8001/openapi.json
```

Skill Gap API:

```text
http://127.0.0.1:8001/api/v1/skill-gap
```

---

## Testing

Run the complete test suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Current verified state:

```text
18 passed
```

The test suite covers:

- Successful Backend-shaped requests.
- Request and response identifiers.
- Skill-level validation.
- Normalized importance-weight validation.
- Required integration fields.
- Weighted scoring behavior.
- Non-negative skill gaps.
- Zero required-level behavior.
- Major and minor critical gaps.
- Multiple critical gaps.
- Critical-cap behavior.
- Deterministic repeated calculations.
- `X-Request-ID` preservation.
- Automatic request-ID generation.

---

## Continuous Integration

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

CI runs automatically for:

- Pull requests targeting `main`.
- Pushes to `main`.

The workflow:

1. Checks out the repository.
2. Configures Python 3.13.
3. Installs development dependencies.
4. Runs the complete pytest suite.

---

## API Documentation

Detailed integration documentation is available at:

```text
docs/api/skill_gap_api.md
```

This document is the detailed contract reference for Laravel â†” FastAPI integration.

---

## Known Development Warning

The current test environment may emit a Starlette/TestClient deprecation warning related to `httpx`.

The warning does not currently fail the automated test suite and should be handled through a deliberate dependency upgrade rather than an unreviewed package replacement.

---

## Repository

```text
https://github.com/SkillSpan/data-science_data-analysis
```

The active integration work should be developed through feature branches and merged into `main` only after tests and review pass.
