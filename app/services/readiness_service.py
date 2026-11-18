"""Versioned SRS 1.3 scoring; legacy endpoints retain their original behavior."""
from math import fsum

from app.schemas.readiness import COMPONENT_NAMES, ReadinessRequest


ALGORITHM_VERSION = "readiness-v2-srs13"


class ReadinessError(ValueError):
    pass


def calculate_readiness(request: ReadinessRequest) -> dict[str, object]:
    skills = request.skills
    if len({skill.skill_id for skill in skills}) != len(skills):
        raise ReadinessError("Duplicate skill identifiers are not allowed.")
    required = [skill for skill in skills if skill.required_level > 0]
    weight_total = fsum(skill.importance_weight for skill in required)
    if weight_total <= 0:
        raise ReadinessError("At least one positively weighted required skill is needed.")

    skill_match = 100 * fsum(
        min(skill.current_level / skill.required_level, 1) * skill.importance_weight
        for skill in required
    ) / weight_total
    scores = {"skill_match": skill_match, **{
        name: getattr(request, name) for name in COMPONENT_NAMES if name != "skill_match"
    }}
    policy = request.policy
    available = {name: value for name, value in scores.items() if value is not None}
    available_weight = fsum(getattr(policy, name) for name in available)
    if available_weight <= 0:
        raise ReadinessError("Available components have no positive weight.")
    effective_weights = {
        name: getattr(policy, name) / available_weight for name in available
    }
    uncapped = fsum(available[name] * effective_weights[name] for name in available)
    critical = [skill for skill in required if skill.is_critical
                and min(skill.current_level / skill.required_level, 1)
                < policy.critical_minimum_match]
    final = min(uncapped, policy.critical_cap) if critical else uncapped
    final = round(final, 2)
    band = ("foundation_needed" if final < 40 else "developing" if final < 60
            else "moderate_readiness" if final < 75 else "near_ready" if final < 90
            else "highly_ready")
    excluded = [name for name in COMPONENT_NAMES if scores[name] is None]
    results = []
    for skill in skills:
        gap = max(skill.required_level - skill.current_level, 0)
        ratio = min(skill.current_level / skill.required_level, 1) if skill.required_level else 1
        results.append({
            **skill.model_dump(), "gap": round(gap, 2),
            "status": "gap" if gap > 0 else "met",
            "match_score": round(100 * ratio, 2),
            "included_in_score": skill.required_level > 0,
            "normalized_importance_weight": (
                skill.importance_weight / weight_total if skill.required_level > 0 else 0
            ),
        })
    return {
        **{key: getattr(request, key) for key in (
            "student_profile_id", "career_role_id", "career_role_version", "user_id", "target_role"
        )},
        "algorithm_version": ALGORITHM_VERSION,
        "policy": policy.model_dump(),
        "base_readiness_score": round(skill_match, 2),
        "uncapped_readiness_score": round(uncapped, 2),
        "readiness_score": final,
        "practical_experience_component": request.practical_experience,
        "assessment_reliability_component": request.assessment_reliability,
        "profile_completeness_component": request.profile_completeness,
        "components": {name: {
            "score": None if scores[name] is None else round(scores[name], 2),
            "configured_weight": getattr(policy, name),
            "effective_weight": effective_weights.get(name, 0),
            "available": scores[name] is not None,
        } for name in COMPONENT_NAMES},
        "effective_weights": effective_weights,
        "excluded_components": excluded,
        "is_provisional": bool(excluded),
        "critical_skill_cap_applied": bool(critical) and uncapped > policy.critical_cap,
        "critical_skill_readiness_cap": policy.critical_cap if critical else None,
        "critical_skill_ids": [skill.skill_id for skill in critical],
        "critical_skill_names": [skill.skill_name for skill in critical],
        "critical_skill_gap_count": len(critical),
        "band": band,
        "total_skills": len(skills),
        "met_skills": sum(row["status"] == "met" for row in results),
        "skills_with_gap": sum(row["status"] == "gap" for row in results),
        "skill_results": results,
    }
