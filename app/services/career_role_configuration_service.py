from collections import deque

from app.schemas.career_role_configuration import (
    CareerRoleConfigurationRequest,
)


CONFIGURATION_VERSION = "career-role-config-v1"


class CareerRoleConfigurationError(ValueError):
    """Represent an invalid career-role configuration."""


def _prerequisite_ids(skill) -> list[int]:
    """Return merged legacy and multiple-prerequisite references deterministically."""

    new_ids = [item.skill_id for item in skill.prerequisites]
    if len(new_ids) != len(set(new_ids)):
        raise CareerRoleConfigurationError(
            f"Skill {skill.skill_id} contains duplicate prerequisite references."
        )

    prerequisite_ids = set(new_ids)
    if skill.prerequisite_skill_id is not None:
        prerequisite_ids.add(skill.prerequisite_skill_id)

    return sorted(prerequisite_ids)



def _build_prerequisite_order(
    request: CareerRoleConfigurationRequest,
) -> list[int]:
    """Validate prerequisite references and return a topological order."""

    skill_ids = {skill.skill_id for skill in request.skills}
    indegree = {skill_id: 0 for skill_id in skill_ids}
    dependents: dict[int, list[int]] = {
        skill_id: [] for skill_id in skill_ids
    }

    for skill in request.skills:
        for prerequisite_id in _prerequisite_ids(skill):
            if prerequisite_id == skill.skill_id:
                raise CareerRoleConfigurationError(
                    f"Skill {skill.skill_id} cannot depend on itself."
                )

            if prerequisite_id not in skill_ids:
                raise CareerRoleConfigurationError(
                    f"Prerequisite skill {prerequisite_id} for skill "
                    f"{skill.skill_id} is not present in the same career role."
                )

            indegree[skill.skill_id] += 1
            dependents[prerequisite_id].append(skill.skill_id)

    queue = deque(sorted(skill_id for skill_id, degree in indegree.items() if degree == 0))
    order: list[int] = []

    while queue:
        skill_id = queue.popleft()
        order.append(skill_id)

        for dependent_id in sorted(dependents[skill_id]):
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                queue.append(dependent_id)

    if len(order) != len(skill_ids):
        raise CareerRoleConfigurationError(
            "Career-role prerequisite relationships contain a cycle."
        )

    return order


def validate_career_role_configuration(
    request: CareerRoleConfigurationRequest,
) -> dict[str, object]:
    """Validate and normalize a versioned career-role configuration."""

    skill_ids = [skill.skill_id for skill in request.skills]

    if len(skill_ids) != len(set(skill_ids)):
        raise CareerRoleConfigurationError(
            "Career-role configuration must not contain duplicate skill_id values."
        )

    weight_total = sum(skill.importance_weight for skill in request.skills)

    if weight_total <= 0:
        raise CareerRoleConfigurationError(
            "Career-role importance weights must have a positive total."
        )

    prerequisite_order = _build_prerequisite_order(request)

    normalized_skills = [
        {
            "skill_id": skill.skill_id,
            "normalized_importance_weight": skill.importance_weight / weight_total,
            "prerequisite_skill_id": skill.prerequisite_skill_id,
            "prerequisites": [item.model_dump() for item in skill.prerequisites],
        }
        for skill in request.skills
    ]

    return {
        "configuration_version": CONFIGURATION_VERSION,
        "career_role_id": request.career_role_id,
        "career_role_version": request.version,
        "status": request.status,
        "original_weight_total": round(weight_total, 6),
        "normalized_weight_total": 1.0,
        "production_eligible": request.status == "approved",
        "prerequisite_order": prerequisite_order,
        "skills": normalized_skills,
    }
