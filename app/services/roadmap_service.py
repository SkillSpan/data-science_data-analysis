from __future__ import annotations

from collections import defaultdict, deque
from math import ceil

from app.schemas.roadmap import (
    RoadmapAction,
    RoadmapPhase,
    RoadmapRequest,
    RoadmapResponse,
    RoadmapSkillSnapshot,
)


ALGORITHM_VERSION = "roadmap-v1"
CONFIGURATION_VERSION = "roadmap-config-v1"

PHASE_ORDER = {
    "foundations": 1,
    "core_skills": 2,
    "applied_practice": 3,
    "career_readiness": 4,
}

ACTION_HOURS_PER_GAP = {
    "assessment": 2.0,
    "resource": 8.0,
    "practice": 6.0,
    "simulated_project": 10.0,
    "real_project": 12.0,
}

ACTION_MIN_HOURS = {
    "assessment": 2.0,
    "resource": 4.0,
    "practice": 4.0,
    "simulated_project": 8.0,
    "real_project": 12.0,
}


class RoadmapError(ValueError):
    """Represent a deterministic Roadmap v1 contract/business-rule error."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def generate_roadmap(request: RoadmapRequest) -> dict:
    """Generate one deterministic, stateless Career Roadmap v1."""

    skills_by_id = {skill.skill_id: skill for skill in request.skills}
    _validate_prerequisite_references(skills_by_id)
    _validate_acyclic_graph(skills_by_id)

    unmet_skills = {
        skill_id: skill
        for skill_id, skill in skills_by_id.items()
        if _gap(skill) > 0
    }

    limitations: list[str] = []
    if any(skill.market_demand_factor is None for skill in request.skills):
        limitations.append("market_demand_factor_unavailable_neutral_1_0")

    weekly_hours = request.learner.weekly_availability_hours
    if weekly_hours is None:
        limitations.append("weekly_availability_hours_unavailable")
    elif weekly_hours == 0:
        limitations.append("weekly_availability_hours_zero_no_calendar_duration")
    elif weekly_hours == 0:
        limitations.append("weekly_availability_hours_zero_no_calendar_duration")

    priorities = {
        skill_id: _priority_score(skill, skills_by_id)
        for skill_id, skill in unmet_skills.items()
    }

    ordered_skill_ids = _topological_unmet_order(
        unmet_skills=unmet_skills,
        all_skills=skills_by_id,
        priorities=priorities,
    )

    actions: list[tuple[str, RoadmapAction]] = []
    phase_by_skill: dict[int, str] = {}
    for index, skill_id in enumerate(ordered_skill_ids, start=1):
        skill = unmet_skills[skill_id]
        gap = _gap(skill)
        action_type = _select_action_type(skill, gap)
        base_phase = _select_phase(skill, action_type, unmet_skills)
        phase = _respect_prerequisite_phase_order(
            skill=skill,
            base_phase=base_phase,
            phase_by_skill=phase_by_skill,
            unmet_skills=unmet_skills,
        )
        phase_by_skill[skill_id] = phase
        blocking = [
            prerequisite_id
            for prerequisite_id in skill.prerequisite_skill_ids
            if prerequisite_id in unmet_skills
        ]

        estimated_hours = _estimate_hours(action_type, gap)
        duration_weeks = (
            max(1, ceil(estimated_hours / weekly_hours))
            if weekly_hours is not None and weekly_hours > 0 and weekly_hours > 0
            else None
        )

        action = RoadmapAction(
            action_id=f"R1-{skill.skill_id}-{index}",
            action_type=action_type,
            title=_title_for(action_type, skill.skill_name),
            objective=_objective_for(skill),
            target_skill_id=skill.skill_id,
            target_skill_name=skill.skill_name,
            prerequisite_skill_ids=list(skill.prerequisite_skill_ids),
            blocking_prerequisite_skill_ids=blocking,
            priority_score=priorities[skill_id],
            estimated_hours=estimated_hours,
            estimated_duration_weeks=duration_weeks,
            completion_criteria=_completion_criteria(action_type, skill),
            explanation=_explanation(skill, gap, priorities[skill_id], blocking),
        )
        actions.append((phase, action))

    phases = _build_phases(actions)
    total_hours = round(sum(action.estimated_hours for _, action in actions), 2)
    total_weeks = (
        ceil(total_hours / weekly_hours)
        if weekly_hours is not None and weekly_hours > 0 and weekly_hours > 0 and total_hours > 0
        else (0 if weekly_hours is not None and weekly_hours > 0 and weekly_hours > 0 else None)
    )

    next_best_action_id = _next_best_action(actions)

    result = RoadmapResponse(
        student_profile_id=request.learner.student_profile_id,
        career_role_id=request.role.id,
        career_role_version=request.role.version,
        algorithm_version=ALGORITHM_VERSION,
        configuration_version=CONFIGURATION_VERSION,
        estimated_total_hours=total_hours,
        estimated_duration_weeks=total_weeks,
        phases=phases,
        next_best_action_id=next_best_action_id,
        limitations=limitations,
    )
    return result.model_dump()


def _gap(skill: RoadmapSkillSnapshot) -> float:
    return round(max(skill.required_level - skill.current_level, 0.0), 4)


def _priority_score(
    skill: RoadmapSkillSnapshot,
    skills_by_id: dict[int, RoadmapSkillSnapshot],
) -> float:
    gap_factor = _gap(skill) / 5.0
    market_demand = skill.market_demand_factor or 1.0
    criticality_factor = 1.25 if skill.is_critical else 1.0

    unmet_prerequisites = [
        prerequisite_id
        for prerequisite_id in skill.prerequisite_skill_ids
        if _gap(skills_by_id[prerequisite_id]) > 0
    ]
    dependency_readiness = 0.5 if unmet_prerequisites else 1.0

    score = (
        gap_factor
        * skill.importance_weight
        * market_demand
        * criticality_factor
        * dependency_readiness
    )
    return round(min(max(score, 0.0), 1.0), 6)


def _validate_prerequisite_references(
    skills_by_id: dict[int, RoadmapSkillSnapshot],
) -> None:
    known = set(skills_by_id)
    for skill in skills_by_id.values():
        unknown = sorted(set(skill.prerequisite_skill_ids) - known)
        if unknown:
            raise RoadmapError(
                f"Unknown prerequisite skill ids for skill_id {skill.skill_id}: {unknown}.",
                "UNKNOWN_PREREQUISITE_SKILL",
            )


def _validate_acyclic_graph(
    skills_by_id: dict[int, RoadmapSkillSnapshot],
) -> None:
    indegree = {skill_id: 0 for skill_id in skills_by_id}
    dependents: dict[int, list[int]] = defaultdict(list)

    for skill in skills_by_id.values():
        for prerequisite_id in skill.prerequisite_skill_ids:
            dependents[prerequisite_id].append(skill.skill_id)
            indegree[skill.skill_id] += 1

    queue = deque(sorted(skill_id for skill_id, degree in indegree.items() if degree == 0))
    visited = 0

    while queue:
        skill_id = queue.popleft()
        visited += 1
        for dependent_id in sorted(dependents[skill_id]):
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                queue.append(dependent_id)

    if visited != len(skills_by_id):
        raise RoadmapError(
            "Career-role prerequisites contain a cycle.",
            "PREREQUISITE_CYCLE",
        )


def _topological_unmet_order(
    *,
    unmet_skills: dict[int, RoadmapSkillSnapshot],
    all_skills: dict[int, RoadmapSkillSnapshot],
    priorities: dict[int, float],
) -> list[int]:
    if not unmet_skills:
        return []

    indegree = {skill_id: 0 for skill_id in unmet_skills}
    dependents: dict[int, list[int]] = defaultdict(list)

    for skill_id, skill in unmet_skills.items():
        for prerequisite_id in skill.prerequisite_skill_ids:
            if prerequisite_id in unmet_skills:
                dependents[prerequisite_id].append(skill_id)
                indegree[skill_id] += 1

    ready = [skill_id for skill_id, degree in indegree.items() if degree == 0]
    ordered: list[int] = []

    while ready:
        ready.sort(key=lambda skill_id: (-priorities[skill_id], skill_id))
        skill_id = ready.pop(0)
        ordered.append(skill_id)

        for dependent_id in dependents[skill_id]:
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                ready.append(dependent_id)

    if len(ordered) != len(unmet_skills):
        raise RoadmapError(
            "Unable to order unmet skills because of prerequisite constraints.",
            "ROADMAP_ORDERING_FAILED",
        )

    return ordered


def _select_action_type(skill: RoadmapSkillSnapshot, gap: float) -> str:
    if skill.confidence < 60.0:
        return "assessment"
    if skill.current_level < 2.0 or gap >= 2.0:
        return "resource"
    if gap > 1.0:
        return "practice"
    if gap > 0.5:
        return "simulated_project"
    return "real_project"


def _select_phase(
    skill: RoadmapSkillSnapshot,
    action_type: str,
    unmet_skills: dict[int, RoadmapSkillSnapshot],
) -> str:
    is_unmet_prerequisite = any(
        skill.skill_id in candidate.prerequisite_skill_ids
        for candidate in unmet_skills.values()
    )

    if is_unmet_prerequisite or skill.current_level < 2.0:
        return "foundations"
    if action_type in {"simulated_project", "real_project"}:
        return "applied_practice"
    return "core_skills"


def _respect_prerequisite_phase_order(
    *,
    skill: RoadmapSkillSnapshot,
    base_phase: str,
    phase_by_skill: dict[int, str],
    unmet_skills: dict[int, RoadmapSkillSnapshot],
) -> str:
    phase_order = PHASE_ORDER[base_phase]
    for prerequisite_id in skill.prerequisite_skill_ids:
        if prerequisite_id in unmet_skills:
            prerequisite_phase = phase_by_skill[prerequisite_id]
            phase_order = max(phase_order, PHASE_ORDER[prerequisite_phase])

    return next(
        phase
        for phase, order in PHASE_ORDER.items()
        if order == phase_order
    )


def _estimate_hours(action_type: str, gap: float) -> float:
    estimate = gap * ACTION_HOURS_PER_GAP[action_type]
    return round(max(ACTION_MIN_HOURS[action_type], estimate), 1)


def _title_for(action_type: str, skill_name: str) -> str:
    labels = {
        "assessment": "Validate",
        "resource": "Learn",
        "practice": "Practice",
        "simulated_project": "Apply in a simulated project",
        "real_project": "Apply in a real project",
    }
    return f"{labels[action_type]} {skill_name}"


def _objective_for(skill: RoadmapSkillSnapshot) -> str:
    return (
        f"Progress {skill.skill_name} from level {skill.current_level:g} "
        f"toward the required level {skill.required_level:g}."
    )


def _completion_criteria(
    action_type: str,
    skill: RoadmapSkillSnapshot,
) -> list[str]:
    criteria = {
        "assessment": [
            f"Complete an approved assessment for {skill.skill_name}.",
            "Produce a newer validated skill result or approved evidence.",
        ],
        "resource": [
            f"Complete an approved learning activity targeting {skill.skill_name}.",
            "Provide completion evidence accepted by SkillSpan.",
        ],
        "practice": [
            f"Complete a focused practice task using {skill.skill_name}.",
            "Submit evidence that can be reviewed or assessed.",
        ],
        "simulated_project": [
            f"Complete a simulated project that applies {skill.skill_name}.",
            "Submit the required deliverable for evaluation.",
        ],
        "real_project": [
            f"Complete an eligible real-project activity applying {skill.skill_name}.",
            "Receive accepted project evidence or evaluation.",
        ],
    }
    return criteria[action_type]


def _explanation(
    skill: RoadmapSkillSnapshot,
    gap: float,
    priority_score: float,
    blocking: list[int],
) -> list[str]:
    reasons = [
        (
            f"{skill.skill_name} has a gap of {gap:g} levels for the selected role "
            f"with importance weight {skill.importance_weight:g}."
        ),
        f"Calculated roadmap priority is {priority_score:.6f}.",
    ]

    if skill.is_critical:
        reasons.append("The target role marks this skill as critical.")
    if skill.market_demand_factor is None:
        reasons.append("Market demand is unavailable, so the neutral factor 1.0 was used.")
    if blocking:
        reasons.append(
            "This action remains dependent on unmet prerequisite skill ids: "
            + ", ".join(str(skill_id) for skill_id in blocking)
            + "."
        )
    else:
        reasons.append("No unmet prerequisite blocks this action.")

    return reasons


def _build_phases(
    actions: list[tuple[str, RoadmapAction]],
) -> list[RoadmapPhase]:
    grouped: dict[str, list[RoadmapAction]] = defaultdict(list)
    for phase, action in actions:
        grouped[phase].append(action)

    phases: list[RoadmapPhase] = []
    for phase, order in PHASE_ORDER.items():
        phases.append(
            RoadmapPhase(
                phase=phase,
                order=order,
                actions=grouped.get(phase, []),
            )
        )
    return phases


def _next_best_action(
    actions: list[tuple[str, RoadmapAction]],
) -> str | None:
    candidates = [
        (phase, action)
        for phase, action in actions
        if not action.blocking_prerequisite_skill_ids
    ]
    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            PHASE_ORDER[item[0]],
            -item[1].priority_score,
            item[1].target_skill_id,
        )
    )
    return candidates[0][1].action_id
