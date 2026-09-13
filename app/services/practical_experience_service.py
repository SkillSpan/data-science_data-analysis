from app.schemas.practical_experience import PracticalExperienceRequest


ALGORITHM_VERSION = "practical-experience-v1"
CONFIGURATION_VERSION = "practical-experience-config-v1"
FULL_CREDIT_PROJECT_COUNT = 2


def _project_is_eligible(project, user_id: int) -> bool:
    if project.project_status != "completed":
        return False

    has_completed_membership = any(
        member.user_id == user_id and member.assignment_state == "completed"
        for member in project.team_members
    )
    if not has_completed_membership:
        return False

    accepted_submission_ids = {
        submission.submission_id
        for submission in project.submissions
        if submission.contributor_id == user_id and submission.status == "accepted"
    }
    if not accepted_submission_ids:
        return False

    return any(
        evaluation.submission_id in accepted_submission_ids
        and evaluation.status in {"finalized", "moderated"}
        for evaluation in project.evaluations
    )


def calculate_practical_experience(
    request: PracticalExperienceRequest,
) -> dict[str, object]:
    """Calculate deterministic Practical Experience v1 from SkillSpan projects."""

    eligible_project_ids = sorted({
        project.project_id
        for project in request.projects
        if _project_is_eligible(project, request.user_id)
    })
    eligible_projects_count = len(eligible_project_ids)

    if eligible_projects_count == 0:
        component_status = "unavailable"
        practical_experience_score = None
    else:
        component_status = "available"
        practical_experience_score = min(
            eligible_projects_count / FULL_CREDIT_PROJECT_COUNT,
            1.0,
        ) * 100
        practical_experience_score = round(practical_experience_score, 2)

    return {
        "student_profile_id": request.student_profile_id,
        "user_id": request.user_id,
        "algorithm_version": ALGORITHM_VERSION,
        "configuration_version": CONFIGURATION_VERSION,
        "component_status": component_status,
        "eligible_projects_count": eligible_projects_count,
        "full_credit_project_count": FULL_CREDIT_PROJECT_COUNT,
        "practical_experience_score": practical_experience_score,
        "eligible_project_ids": eligible_project_ids,
    }
