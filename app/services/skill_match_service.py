from app.schemas.skill_match import SkillMatchRequest


ALGORITHM_VERSION = "skill-match-v1"
WEIGHT_CONFIGURATION_VERSION = "career-role-config-v1"


class SkillMatchError(ValueError):
    """Represent a deterministic Skill Match validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def calculate_skill_match(request: SkillMatchRequest) -> dict[str, object]:
    """Calculate deterministic weighted Skill Match v1."""

    skill_ids = [skill.skill_id for skill in request.skills]
    if len(skill_ids) != len(set(skill_ids)):
        raise SkillMatchError(
            "DUPLICATE_SKILL_ID",
            "Skill Match input must not contain duplicate skill_id values.",
        )

    original_weight_total = sum(
        skill.importance_weight for skill in request.skills
    )
    if original_weight_total <= 0:
        raise SkillMatchError(
            "INVALID_WEIGHT_TOTAL",
            "Skill Match importance weights must have a positive total.",
        )

    weighted_achieved_total = 0.0
    weighted_required_total = 0.0
    skill_results: list[dict[str, object]] = []
    met_skills = 0
    partial_skills = 0
    not_required_skills = 0

    for skill in request.skills:
        normalized_weight = skill.importance_weight / original_weight_total
        achieved_level = min(skill.current_level, skill.required_level)

        if skill.required_level == 0:
            match_ratio = 1.0
            status = "not_required"
            not_required_skills += 1
        else:
            match_ratio = min(achieved_level / skill.required_level, 1.0)
            if match_ratio == 1.0:
                status = "met"
                met_skills += 1
            else:
                status = "partial"
                partial_skills += 1

        weighted_achieved_total += achieved_level * normalized_weight
        weighted_required_total += skill.required_level * normalized_weight

        skill_results.append(
            {
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "current_level": skill.current_level,
                "required_level": skill.required_level,
                "importance_weight": skill.importance_weight,
                "is_critical": skill.is_critical,
                "normalized_importance_weight": round(normalized_weight, 6),
                "achieved_level": round(achieved_level, 2),
                "match_ratio": round(match_ratio, 6),
                "status": status,
            }
        )

    if weighted_required_total == 0:
        skill_match_score = 100.0
    else:
        skill_match_score = min(
            round(
                100 * weighted_achieved_total / weighted_required_total,
                2,
            ),
            100.0,
        )

    return {
        "student_profile_id": request.student_profile_id,
        "career_role_id": request.career_role_id,
        "career_role_version": request.career_role_version,
        "user_id": request.user_id,
        "target_role": request.target_role,
        "algorithm_version": ALGORITHM_VERSION,
        "weight_configuration_version": WEIGHT_CONFIGURATION_VERSION,
        "original_weight_total": round(original_weight_total, 6),
        "normalized_weight_total": 1.0,
        "weighted_achieved_total": round(weighted_achieved_total, 6),
        "weighted_required_total": round(weighted_required_total, 6),
        "skill_match_score": skill_match_score,
        "total_skills": len(request.skills),
        "met_skills": met_skills,
        "partial_skills": partial_skills,
        "not_required_skills": not_required_skills,
        "skill_results": skill_results,
    }
