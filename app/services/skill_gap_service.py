from app.schemas.skill_gap import SkillGapRequest


ALGORITHM_VERSION = "skill-gap-v1"
CRITICAL_SKILL_MAJOR_GAP_THRESHOLD = 2.0
CRITICAL_SKILL_READINESS_CAP = 60.0


def calculate_skill_gap(request: SkillGapRequest) -> dict[str, object]:
    """Calculate weighted skill gaps and the final readiness score."""

    skill_results: list[dict[str, object]] = []
    critical_skill_ids: list[int] = []
    critical_skill_names: list[str] = []

    total_weighted_required_level = 0.0
    total_weighted_achieved_level = 0.0
    met_skills = 0

    for skill in request.skills:
        gap = max(skill.required_level - skill.current_level, 0.0)
        achieved_level = min(skill.current_level, skill.required_level)

        total_weighted_required_level += (
            skill.required_level * skill.importance_weight
        )

        total_weighted_achieved_level += (
            achieved_level * skill.importance_weight
        )

        status = "met" if gap == 0 else "gap"

        if status == "met":
            met_skills += 1

        if (
            skill.is_critical
            and gap >= CRITICAL_SKILL_MAJOR_GAP_THRESHOLD
        ):
            critical_skill_ids.append(skill.skill_id)
            critical_skill_names.append(skill.skill_name)

        skill_results.append(
            {
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "current_level": skill.current_level,
                "required_level": skill.required_level,
                "importance_weight": skill.importance_weight,
                "is_critical": skill.is_critical,
                "gap": round(gap, 2),
                "status": status,
            }
        )

    if total_weighted_required_level == 0:
        base_readiness_score = 100.0
    else:
        base_readiness_score = round(
            (
                total_weighted_achieved_level
                / total_weighted_required_level
            )
            * 100,
            2,
        )

    has_major_critical_gap = bool(critical_skill_ids)

    critical_skill_cap_applied = (
        has_major_critical_gap
        and base_readiness_score > CRITICAL_SKILL_READINESS_CAP
    )

    if has_major_critical_gap:
        readiness_score = min(
            base_readiness_score,
            CRITICAL_SKILL_READINESS_CAP,
        )
        critical_skill_readiness_cap: float | None = (
            CRITICAL_SKILL_READINESS_CAP
        )
    else:
        readiness_score = base_readiness_score
        critical_skill_readiness_cap = None

    return {
        "student_profile_id": request.student_profile_id,
        "career_role_id": request.career_role_id,
        "career_role_version": request.career_role_version,
        "user_id": request.user_id,
        "target_role": request.target_role,
        "algorithm_version": ALGORITHM_VERSION,
        "base_readiness_score": base_readiness_score,
        "readiness_score": readiness_score,
        "critical_skill_cap_applied": critical_skill_cap_applied,
        "critical_skill_readiness_cap": critical_skill_readiness_cap,
        "critical_skill_gap_count": len(critical_skill_ids),
        "critical_skill_ids": critical_skill_ids,
        "critical_skill_names": critical_skill_names,
        "total_skills": len(request.skills),
        "met_skills": met_skills,
        "skills_with_gap": len(request.skills) - met_skills,
        "skill_results": skill_results,
    }
