# SkillSpan Profile Completeness API Contract v1

## Endpoint

`POST /api/v1/profile-completeness`

## Versions

- Algorithm: `profile-completeness-v1`
- Configuration: `profile-completeness-config-v1`

## Request

```json
{
  "student_profile_id": 123,
  "fields": {
    "university_name": "Test University",
    "student_university_number": "12345",
    "specialization": "Computer Science",
    "academic_level": "Senior",
    "career_status": "student",
    "interests": ["data-analysis"],
    "availability": "full_time"
  }
}
```

Individual profile fields may be omitted or supplied as `null`; they then count as incomplete.

Unknown profile fields are rejected.

The six text fields accept at most 100 characters.

## Formula

```text
score = round((completed_fields_count / 7) * 100, 2)
```

All seven fields have equal weight and are always applicable.

## Response

```json
{
  "student_profile_id": 123,
  "algorithm_version": "profile-completeness-v1",
  "configuration_version": "profile-completeness-config-v1",
  "component_status": "available",
  "total_fields_count": 7,
  "completed_fields_count": 7,
  "incomplete_fields_count": 0,
  "profile_completeness_score": 100.0
}
```

## Important Semantics

- blank or whitespace-only free strings are incomplete;
- `null` is incomplete;
- empty `interests` is incomplete;
- non-empty `interests` is complete;
- missing fields are incomplete;
- an incomplete profile remains `available`;
- zero completeness is a valid score and is not missing data;
- FastAPI remains stateless;
- Laravel owns `StudentProfile` persistence and supplies the snapshot.
