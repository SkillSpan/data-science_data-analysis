import re
from app.schemas.project_matching import (
    ProjectMatchingConfiguration,
    ProjectMatchingRequest,
)


ALGORITHM_VERSION = "project-matching-v1"
CONFIGURATION_VERSION = "project-matching-config-v1"


class ProjectMatchingError(ValueError):
    """Represent a deterministic Project Matching validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _skill_label(skill_id: int, skill_name: str | None) -> str:
    """Return a deterministic human-readable skill label."""

    if skill_name:
        return skill_name

    return f"skill {skill_id}"


def _validate_matching_input(request: ProjectMatchingRequest) -> None:
    """Validate cross-field Project Matching input integrity."""

    if request.project_version != request.project.version:
        raise ProjectMatchingError(
            "PROJECT_VERSION_MISMATCH",
            "project_version must match project.version.",
        )

    required_skill_ids = [
        skill.skill_id
        for skill in request.required_skills
    ]

    if len(required_skill_ids) != len(set(required_skill_ids)):
        raise ProjectMatchingError(
            "DUPLICATE_PROJECT_SKILL_ID",
            "Project Matching required_skills must not contain duplicate skill_id values.",
        )

    learner_skill_ids = [
        skill.skill_id
        for skill in request.learner.current_skills
    ]

    if len(learner_skill_ids) != len(set(learner_skill_ids)):
        raise ProjectMatchingError(
            "DUPLICATE_LEARNER_SKILL_ID",
            "Project Matching learner current_skills must not contain duplicate skill_id values.",
        )


def evaluate_skill_compatibility(
    request: ProjectMatchingRequest,
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Evaluate deterministic learner capability against project requirements."""

    config = configuration or ProjectMatchingConfiguration()

    _validate_matching_input(request)

    learner_skills = {
        skill.skill_id: skill
        for skill in request.learner.current_skills
    }

    skill_results: list[dict[str, object]] = []
    active_match_ratios: list[float] = []

    strengths: list[str] = []
    growth_opportunities: list[str] = []
    limiting_factors: list[str] = []
    critical_blockers: list[str] = []

    for required_skill in sorted(
        request.required_skills,
        key=lambda item: item.skill_id,
    ):
        learner_skill = learner_skills.get(
            required_skill.skill_id
        )

        current_level = (
            learner_skill.level
            if learner_skill is not None
            else 0.0
        )

        minimum_level = required_skill.minimum_level

        skill_label = _skill_label(
            required_skill.skill_id,
            required_skill.skill_name,
        )

        if minimum_level == 0:
            gap = 0.0
            match_ratio = 1.0
            status = "not_required"

        else:
            gap = max(
                minimum_level - current_level,
                0.0,
            )

            match_ratio = min(
                current_level / minimum_level,
                1.0,
            )

            active_match_ratios.append(match_ratio)

            if learner_skill is None:
                if required_skill.is_critical_entry:
                    status = "missing_critical"

                    message = (
                        f"Missing critical skill: {skill_label}."
                    )

                    critical_blockers.append(message)
                    limiting_factors.append(message)

                else:
                    status = "missing_non_critical"

                    limiting_factors.append(
                        f"Missing non-critical skill: {skill_label}."
                    )

                    if gap <= config.manageable_gap_max:
                        growth_opportunities.append(
                            f"{skill_label} is a manageable learning opportunity."
                        )

            elif gap == 0:
                status = "met"

                strengths.append(
                    f"{skill_label} meets the project requirement."
                )

            elif required_skill.is_critical_entry:
                status = "critical_below_minimum"

                message = (
                    f"Critical skill {skill_label} is "
                    f"{round(gap, 2)} level(s) below the minimum."
                )

                critical_blockers.append(message)
                limiting_factors.append(message)

            elif gap <= config.manageable_gap_max:
                status = "manageable_gap"

                growth_opportunities.append(
                    f"{skill_label} has a manageable gap of "
                    f"{round(gap, 2)} level(s)."
                )

            else:
                status = "large_gap"

                limiting_factors.append(
                    f"{skill_label} is {round(gap, 2)} "
                    f"level(s) below the project minimum."
                )

        skill_results.append(
            {
                "skill_id": required_skill.skill_id,
                "skill_name": required_skill.skill_name,
                "current_level": round(
                    current_level,
                    2,
                ),
                "minimum_level": round(
                    minimum_level,
                    2,
                ),
                "gap": round(
                    gap,
                    2,
                ),
                "match_ratio": round(
                    match_ratio,
                    6,
                ),
                "is_critical_entry": (
                    required_skill.is_critical_entry
                ),
                "status": status,
            }
        )

    if not active_match_ratios:
        skill_compatibility_score = 100.0
    else:
        skill_compatibility_score = round(
            100
            * sum(active_match_ratios)
            / len(active_match_ratios),
            2,
        )

    return {
        "skill_compatibility_score": (
            skill_compatibility_score
        ),
        "skill_results": skill_results,
        "strengths": strengths,
        "growth_opportunities": growth_opportunities,
        "limiting_factors": limiting_factors,
        "critical_blockers": critical_blockers,
        "has_critical_blocker": bool(
            critical_blockers
        ),
    }

def evaluate_learning_value(
    skill_evaluation: dict[str, object],
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Calculate deterministic growth-oriented learning value."""

    config = configuration or ProjectMatchingConfiguration()

    skill_results = skill_evaluation["skill_results"]

    active_non_critical_skills = [
        skill
        for skill in skill_results
        if not skill["is_critical_entry"]
        and skill["minimum_level"] > 0
    ]

    if not active_non_critical_skills:
        return {
            "learning_value_score": 0.0,
            "opportunity_count": 0,
            "evaluated_skill_count": 0,
        }

    opportunity_scores: list[float] = []
    opportunity_count = 0

    for skill in active_non_critical_skills:
        status = skill["status"]
        gap = skill["gap"]

        if (
            status in {
                "manageable_gap",
                "missing_non_critical",
            }
            and gap > 0
            and gap <= config.manageable_gap_max
        ):
            opportunity_count += 1

            if config.manageable_gap_max == 0:
                opportunity_score = 0.0
            else:
                opportunity_score = min(
                    gap / config.manageable_gap_max,
                    1.0,
                )

        else:
            opportunity_score = 0.0

        opportunity_scores.append(
            opportunity_score
        )

    learning_value_score = round(
        100
        * sum(opportunity_scores)
        / len(active_non_critical_skills),
        2,
    )

    return {
        "learning_value_score": learning_value_score,
        "opportunity_count": opportunity_count,
        "evaluated_skill_count": len(
            active_non_critical_skills
        ),
    }

def _normalized_terms(value: str | None) -> set[str]:
    """Normalize text into deterministic Unicode alphanumeric terms."""

    if value is None:
        return set()

    return set(
        re.findall(
            r"[^\W_]+",
            value.casefold(),
            flags=re.UNICODE,
        )
    )

def _target_term_coverage(
    target: str,
    candidate: str | None,
) -> float:
    """Return deterministic target-term coverage in the 0-1 range."""

    target_terms = _normalized_terms(target)
    candidate_terms = _normalized_terms(candidate)

    if not target_terms or not candidate_terms:
        return 0.0

    return len(
        target_terms & candidate_terms
    ) / len(target_terms)


def evaluate_career_relevance(
    request: ProjectMatchingRequest,
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Calculate deterministic career-role relevance from supplied metadata."""

    config = configuration or ProjectMatchingConfiguration()

    target_role = request.learner.target_career_role

    if target_role is None:
        return {
            "career_relevance_score": (
                config.optional_factor_fallback_score
            ),
            "career_relevance_state": "unavailable",
            "matched_source": None,
        }

    project_role = request.project.role
    project_domain = request.project.domain

    if project_role is None and project_domain is None:
        return {
            "career_relevance_score": (
                config.optional_factor_fallback_score
            ),
            "career_relevance_state": "unavailable",
            "matched_source": None,
        }

    role_coverage = _target_term_coverage(
        target_role.title,
        project_role,
    )

    domain_coverage = _target_term_coverage(
        target_role.title,
        project_domain,
    )

    best_coverage = max(
        role_coverage,
        domain_coverage,
    )

    if role_coverage >= domain_coverage:
        matched_source = (
            "project_role"
            if project_role is not None
            else "project_domain"
        )
    else:
        matched_source = "project_domain"

    career_relevance_score = round(
        best_coverage * 100,
        2,
    )

    if career_relevance_score == 100:
        state = "strong"
    elif career_relevance_score > 0:
        state = "partial"
    else:
        state = "weak"

    return {
        "career_relevance_score": career_relevance_score,
        "career_relevance_state": state,
        "matched_source": matched_source,
    }

def evaluate_interest_match(
    request: ProjectMatchingRequest,
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Calculate deterministic learner-interest alignment with project domain."""

    config = configuration or ProjectMatchingConfiguration()

    interests = request.learner.interests
    project_domain = request.project.domain

    if not interests or project_domain is None:
        return {
            "interest_match_score": (
                config.optional_factor_fallback_score
            ),
            "interest_match_state": "unavailable",
            "matched_interest": None,
        }

    scored_interests = sorted(
        (
            (
                interest,
                _target_term_coverage(
                    interest,
                    project_domain,
                ),
            )
            for interest in interests
        ),
        key=lambda item: (
            -item[1],
            item[0].casefold(),
            item[0],
        ),
    )

    matched_interest, best_coverage = scored_interests[0]

    interest_match_score = round(
        best_coverage * 100,
        2,
    )

    if interest_match_score == 100:
        state = "strong"
    elif interest_match_score > 0:
        state = "partial"
    else:
        state = "weak"

    return {
        "interest_match_score": interest_match_score,
        "interest_match_state": state,
        "matched_interest": matched_interest,
    }

def _normalized_category(value: str | None) -> str | None:
    """Normalize categorical text for deterministic equality comparison."""

    if value is None:
        return None

    terms = re.findall(
        r"[^\W_]+",
        value.casefold(),
        flags=re.UNICODE,
    )

    if not terms:
        return None

    return " ".join(terms)


def evaluate_availability_fit(
    request: ProjectMatchingRequest,
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Calculate deterministic availability/work-mode compatibility."""

    config = configuration or ProjectMatchingConfiguration()

    comparisons: list[dict[str, object]] = []

    learner_availability = _normalized_category(
        request.learner.availability
    )
    project_schedule = _normalized_category(
        request.project.schedule
    )

    if (
        learner_availability is not None
        and project_schedule is not None
    ):
        schedule_score = (
            100.0
            if learner_availability == project_schedule
            else 0.0
        )

        comparisons.append(
            {
                "factor": "schedule",
                "score": schedule_score,
            }
        )

    preferred_work_type = _normalized_category(
        request.learner.preferred_work_type
    )
    project_work_mode = _normalized_category(
        request.project.work_mode
    )

    if (
        preferred_work_type is not None
        and project_work_mode is not None
    ):
        work_mode_score = (
            100.0
            if preferred_work_type == project_work_mode
            else 0.0
        )

        comparisons.append(
            {
                "factor": "work_mode",
                "score": work_mode_score,
            }
        )

    if not comparisons:
        return {
            "availability_fit_score": (
                config.optional_factor_fallback_score
            ),
            "availability_fit_state": "unavailable",
            "comparisons": [],
        }

    availability_fit_score = round(
        sum(
            item["score"]
            for item in comparisons
        )
        / len(comparisons),
        2,
    )

    if availability_fit_score == 100:
        state = "strong"
    elif availability_fit_score > 0:
        state = "partial"
    else:
        state = "mismatch"

    return {
        "availability_fit_score": availability_fit_score,
        "availability_fit_state": state,
        "comparisons": comparisons,
    }

def evaluate_project_eligibility(
    request: ProjectMatchingRequest,
    skill_evaluation: dict[str, object],
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Combine Laravel validation with intelligence-layer hard constraints."""

    config = configuration or ProjectMatchingConfiguration()

    blocking_reasons: list[str] = []

    if request.validation.validation_state != "validated":
        blocking_reasons.append(
            "Laravel validation state is not validated."
        )

    if request.validation.eligibility_state != "eligible":
        blocking_reasons.append(
            "Laravel marked the learner as not eligible for this project."
        )

    if (
        request.validation.authorization is not None
        and request.validation.authorization
        != "authorized"
    ):
        blocking_reasons.append(
            "Laravel authorization state does not permit project matching."
        )

    blocking_constraints = sorted(
        (
            constraint
            for constraint in request.validation.constraints
            if hasattr(constraint, "blocking")
            and constraint.blocking
        ),
        key=lambda item: (
            item.type,
            str(item.value),
        ),
    )

    for constraint in blocking_constraints:
        blocking_reasons.append(
            f"Blocking project constraint: "
            f"{constraint.type}={constraint.value}."
        )

    if config.critical_entry_is_hard_constraint:
        blocking_reasons.extend(
            skill_evaluation["critical_blockers"]
        )

    eligibility_state = (
        "eligible"
        if not blocking_reasons
        else "ineligible"
    )

    return {
        "eligibility_state": eligibility_state,
        "matching_state": (
            "scored"
            if eligibility_state == "eligible"
            else "blocked"
        ),
        "blocking_reasons": blocking_reasons,
    }

def _validate_configuration(
    configuration: ProjectMatchingConfiguration,
) -> None:
    """Reject unsupported Project Matching algorithm/configuration versions."""

    if configuration.algorithm_version != ALGORITHM_VERSION:
        raise ProjectMatchingError(
            "UNSUPPORTED_ALGORITHM_VERSION",
            (
                "Unsupported Project Matching algorithm version: "
                f"{configuration.algorithm_version}."
            ),
        )

    if configuration.configuration_version != CONFIGURATION_VERSION:
        raise ProjectMatchingError(
            "UNSUPPORTED_CONFIGURATION_VERSION",
            (
                "Unsupported Project Matching configuration version: "
                f"{configuration.configuration_version}."
            ),
        )


def _append_unique(
    items: list[str],
    value: str,
) -> None:
    """Append a string once while preserving deterministic order."""

    if value not in items:
        items.append(value)


def _build_explanation(
    skill_evaluation: dict[str, object],
    learning_evaluation: dict[str, object],
    career_evaluation: dict[str, object],
    interest_evaluation: dict[str, object],
    availability_evaluation: dict[str, object],
) -> list[str]:
    """Build deterministic recommendation explanations from calculated factors."""

    explanation: list[str] = []

    skill_score = float(
        skill_evaluation["skill_compatibility_score"]
    )

    if skill_score >= 80:
        explanation.append(
            f"Strong skill compatibility at {skill_score:.2f}%."
        )
    elif skill_score >= 50:
        explanation.append(
            f"Moderate skill compatibility at {skill_score:.2f}%."
        )
    else:
        explanation.append(
            f"Limited skill compatibility at {skill_score:.2f}%."
        )

    opportunity_count = int(
        learning_evaluation["opportunity_count"]
    )

    learning_score = float(
        learning_evaluation["learning_value_score"]
    )

    if opportunity_count > 0:
        noun = (
            "opportunity"
            if opportunity_count == 1
            else "opportunities"
        )

        explanation.append(
            (
                f"The project provides {opportunity_count} manageable "
                f"learning {noun}, with learning value "
                f"{learning_score:.2f}%."
            )
        )
    else:
        explanation.append(
            "No manageable non-critical learning opportunity was identified."
        )

    career_state = career_evaluation[
        "career_relevance_state"
    ]

    if career_state == "strong":
        explanation.append(
            "The project strongly aligns with the learner's target career role."
        )
    elif career_state == "partial":
        explanation.append(
            "The project partially aligns with the learner's target career role."
        )
    elif career_state == "weak":
        explanation.append(
            "The project has weak alignment with the learner's target career role."
        )
    else:
        explanation.append(
            "Career-role information was unavailable; the neutral fallback was applied."
        )

    interest_state = interest_evaluation[
        "interest_match_state"
    ]

    if interest_state == "strong":
        explanation.append(
            "The project domain strongly aligns with the learner's interests."
        )
    elif interest_state == "partial":
        explanation.append(
            "The project domain partially aligns with the learner's interests."
        )
    elif interest_state == "weak":
        explanation.append(
            "The project domain has weak alignment with the learner's interests."
        )
    else:
        explanation.append(
            "Interest information was unavailable; the neutral fallback was applied."
        )

    availability_state = availability_evaluation[
        "availability_fit_state"
    ]

    if availability_state == "strong":
        explanation.append(
            "Learner availability and work-mode preferences match the project."
        )
    elif availability_state == "partial":
        explanation.append(
            "Learner availability or work-mode preferences partially match the project."
        )
    elif availability_state == "mismatch":
        explanation.append(
            "Learner availability and project requirements do not align."
        )
    else:
        explanation.append(
            "Availability information was unavailable; the neutral fallback was applied."
        )

    return explanation


def _build_limiting_factors(
    skill_evaluation: dict[str, object],
    eligibility_evaluation: dict[str, object],
    career_evaluation: dict[str, object],
    interest_evaluation: dict[str, object],
    availability_evaluation: dict[str, object],
) -> list[str]:
    """Build deterministic limiting factors supported by actual calculations."""

    limiting_factors: list[str] = []

    for reason in eligibility_evaluation[
        "blocking_reasons"
    ]:
        _append_unique(
            limiting_factors,
            str(reason),
        )

    for reason in skill_evaluation[
        "limiting_factors"
    ]:
        _append_unique(
            limiting_factors,
            str(reason),
        )

    for skill in skill_evaluation[
        "skill_results"
    ]:
        if skill["status"] == "manageable_gap":
            skill_label = _skill_label(
                skill["skill_id"],
                skill["skill_name"],
            )

            _append_unique(
                limiting_factors,
                (
                    f"Manageable skill gap: {skill_label} is "
                    f"{skill['gap']} level(s) below the project minimum."
                ),
            )

    if (
        career_evaluation["career_relevance_state"]
        == "weak"
    ):
        _append_unique(
            limiting_factors,
            "Weak career relevance.",
        )

    if (
        interest_evaluation["interest_match_state"]
        == "weak"
    ):
        _append_unique(
            limiting_factors,
            "Limited interest alignment.",
        )

    if (
        availability_evaluation["availability_fit_state"]
        == "mismatch"
    ):
        _append_unique(
            limiting_factors,
            "Availability mismatch.",
        )

    return limiting_factors


def calculate_project_match(
    request: ProjectMatchingRequest,
    configuration: ProjectMatchingConfiguration | None = None,
) -> dict[str, object]:
    """Calculate deterministic Project Matching v1 recommendation output."""

    config = (
        configuration
        or ProjectMatchingConfiguration()
    )

    _validate_configuration(config)
    _validate_matching_input(request)

    skill_evaluation = evaluate_skill_compatibility(
        request,
        config,
    )

    learning_evaluation = evaluate_learning_value(
        skill_evaluation,
        config,
    )

    career_evaluation = evaluate_career_relevance(
        request,
        config,
    )

    interest_evaluation = evaluate_interest_match(
        request,
        config,
    )

    availability_evaluation = evaluate_availability_fit(
        request,
        config,
    )

    eligibility_evaluation = evaluate_project_eligibility(
        request,
        skill_evaluation,
        config,
    )

    factor_scores = {
        "skill_compatibility": float(
            skill_evaluation[
                "skill_compatibility_score"
            ]
        ),
        "learning_value": float(
            learning_evaluation[
                "learning_value_score"
            ]
        ),
        "career_relevance": float(
            career_evaluation[
                "career_relevance_score"
            ]
        ),
        "interest_match": float(
            interest_evaluation[
                "interest_match_score"
            ]
        ),
        "availability_fit": float(
            availability_evaluation[
                "availability_fit_score"
            ]
        ),
    }

    weights = config.weights

    weighted_contributions = {
        "skill_compatibility": round(
            factor_scores["skill_compatibility"]
            * weights.skill_compatibility,
            2,
        ),
        "learning_value": round(
            factor_scores["learning_value"]
            * weights.learning_value,
            2,
        ),
        "career_relevance": round(
            factor_scores["career_relevance"]
            * weights.career_relevance,
            2,
        ),
        "interest_match": round(
            factor_scores["interest_match"]
            * weights.interest_match,
            2,
        ),
        "availability_fit": round(
            factor_scores["availability_fit"]
            * weights.availability_fit,
            2,
        ),
    }

    theoretical_score = round(
        sum(
            weighted_contributions.values()
        ),
        2,
    )

    theoretical_score = min(
        max(theoretical_score, 0.0),
        100.0,
    )

    if (
        eligibility_evaluation[
            "matching_state"
        ]
        == "blocked"
    ):
        final_score = 0.0
    else:
        final_score = theoretical_score

    explanation = _build_explanation(
        skill_evaluation,
        learning_evaluation,
        career_evaluation,
        interest_evaluation,
        availability_evaluation,
    )

    limiting_factors = _build_limiting_factors(
        skill_evaluation,
        eligibility_evaluation,
        career_evaluation,
        interest_evaluation,
        availability_evaluation,
    )

    return {
        "request_id": request.request_id,
        "algorithm_version": (
            config.algorithm_version
        ),
        "configuration_version": (
            config.configuration_version
        ),
        "recommendation": {
            "project_id": request.project.id,
            "project_version": request.project.version,
            "eligibility_state": (
                eligibility_evaluation[
                    "eligibility_state"
                ]
            ),
            "matching_state": (
                eligibility_evaluation[
                    "matching_state"
                ]
            ),
            "score": final_score,
            "factor_scores": factor_scores,
            "weighted_contributions": (
                weighted_contributions
            ),
            "explanation": explanation,
            "limiting_factors": (
                limiting_factors
            ),
            "skill_results": (
                skill_evaluation[
                    "skill_results"
                ]
            ),
        },
    }

def rank_project_matches(
    requests: list[ProjectMatchingRequest],
    configuration: ProjectMatchingConfiguration | None = None,
) -> list[dict[str, object]]:
    """Rank multiple project matches deterministically."""

    config = configuration or ProjectMatchingConfiguration()
    _validate_configuration(config)

    project_ids = [request.project.id for request in requests]
    if len(project_ids) != len(set(project_ids)):
        raise ProjectMatchingError(
            "DUPLICATE_PROJECT_ID",
            "Project ranking input must not contain duplicate project IDs.",
        )

    recommendations = [
        calculate_project_match(request, config)["recommendation"]
        for request in requests
    ]

    return sorted(
        recommendations,
        key=lambda recommendation: (
            0 if recommendation["matching_state"] == "scored" else 1,
            -float(recommendation["score"]),
            int(recommendation["project_id"]),
        ),
    )
