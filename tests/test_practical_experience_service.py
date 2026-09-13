from app.schemas.practical_experience import PracticalExperienceRequest
from app.services.practical_experience_service import calculate_practical_experience


def test_one_eligible_project_scores_fifty_percent() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "completed",
                "team_members": [
                    {"user_id": 20, "assignment_state": "completed"}
                ],
                "submissions": [
                    {
                        "submission_id": 501,
                        "contributor_id": 20,
                        "status": "accepted"
                    }
                ],
                "evaluations": [
                    {
                        "submission_id": 501,
                        "status": "finalized"
                    }
                ]
            }
        ]
    })

    result = calculate_practical_experience(request)

    assert result["algorithm_version"] == "practical-experience-v1"
    assert result["configuration_version"] == "practical-experience-config-v1"
    assert result["component_status"] == "available"
    assert result["eligible_projects_count"] == 1
    assert result["full_credit_project_count"] == 2
    assert result["practical_experience_score"] == 50.0
    assert result["eligible_project_ids"] == [101]


def test_zero_eligible_projects_is_unavailable_not_zero() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "in_progress",
                "team_members": [{"user_id": 20, "assignment_state": "completed"}],
                "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "accepted"}],
                "evaluations": [{"submission_id": 501, "status": "finalized"}],
            }
        ],
    })

    result = calculate_practical_experience(request)

    assert result["component_status"] == "unavailable"
    assert result["eligible_projects_count"] == 0
    assert result["practical_experience_score"] is None
    assert result["eligible_project_ids"] == []


def test_evaluation_for_another_submission_does_not_make_project_eligible() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "completed",
                "team_members": [{"user_id": 20, "assignment_state": "completed"}],
                "submissions": [
                    {"submission_id": 501, "contributor_id": 20, "status": "accepted"},
                    {"submission_id": 999, "contributor_id": 30, "status": "accepted"},
                ],
                "evaluations": [{"submission_id": 999, "status": "finalized"}],
            }
        ],
    })

    result = calculate_practical_experience(request)

    assert result["component_status"] == "unavailable"
    assert result["eligible_projects_count"] == 0
    assert result["practical_experience_score"] is None


def test_duplicate_project_id_is_counted_once() -> None:
    project = {
        "project_id": 101,
        "project_status": "completed",
        "team_members": [{"user_id": 20, "assignment_state": "completed"}],
        "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "accepted"}],
        "evaluations": [{"submission_id": 501, "status": "moderated"}],
    }
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [project, project],
    })

    result = calculate_practical_experience(request)

    assert result["eligible_projects_count"] == 1
    assert result["eligible_project_ids"] == [101]
    assert result["practical_experience_score"] == 50.0


def test_two_eligible_projects_receive_full_credit() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "completed",
                "team_members": [{"user_id": 20, "assignment_state": "completed"}],
                "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "accepted"}],
                "evaluations": [{"submission_id": 501, "status": "finalized"}],
            },
            {
                "project_id": 102,
                "project_status": "completed",
                "team_members": [{"user_id": 20, "assignment_state": "completed"}],
                "submissions": [{"submission_id": 502, "contributor_id": 20, "status": "accepted"}],
                "evaluations": [{"submission_id": 502, "status": "moderated"}],
            },
        ],
    })

    result = calculate_practical_experience(request)

    assert result["component_status"] == "available"
    assert result["eligible_projects_count"] == 2
    assert result["practical_experience_score"] == 100.0


def test_practical_experience_score_is_capped_at_one_hundred() -> None:
    projects = []
    for index in range(3):
        project_id = 101 + index
        submission_id = 501 + index
        projects.append({
            "project_id": project_id,
            "project_status": "completed",
            "team_members": [{"user_id": 20, "assignment_state": "completed"}],
            "submissions": [{"submission_id": submission_id, "contributor_id": 20, "status": "accepted"}],
            "evaluations": [{"submission_id": submission_id, "status": "finalized"}],
        })

    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": projects,
    })

    result = calculate_practical_experience(request)

    assert result["eligible_projects_count"] == 3
    assert result["practical_experience_score"] == 100.0


def test_other_users_completed_membership_does_not_make_project_eligible() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "completed",
                "team_members": [{"user_id": 30, "assignment_state": "completed"}],
                "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "accepted"}],
                "evaluations": [{"submission_id": 501, "status": "finalized"}],
            }
        ],
    })

    result = calculate_practical_experience(request)

    assert result["component_status"] == "unavailable"
    assert result["eligible_projects_count"] == 0
    assert result["practical_experience_score"] is None


def test_practical_experience_is_deterministic_for_identical_input() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [
            {
                "project_id": 101,
                "project_status": "completed",
                "team_members": [{"user_id": 20, "assignment_state": "completed"}],
                "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "accepted"}],
                "evaluations": [{"submission_id": 501, "status": "moderated"}],
            }
        ],
    })

    first = calculate_practical_experience(request)
    second = calculate_practical_experience(request)

    assert first == second


def test_non_accepted_submission_does_not_make_project_eligible() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [{
            "project_id": 101,
            "project_status": "completed",
            "team_members": [{"user_id": 20, "assignment_state": "completed"}],
            "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "under_review"}],
            "evaluations": [{"submission_id": 501, "status": "finalized"}],
        }],
    })

    result = calculate_practical_experience(request)

    assert result["component_status"] == "unavailable"
    assert result["eligible_projects_count"] == 0
    assert result["practical_experience_score"] is None


def test_non_final_evaluation_does_not_make_project_eligible() -> None:
    request = PracticalExperienceRequest.model_validate({
        "student_profile_id": 10,
        "user_id": 20,
        "projects": [{
            "project_id": 101,
            "project_status": "completed",
            "team_members": [{"user_id": 20, "assignment_state": "completed"}],
            "submissions": [{"submission_id": 501, "contributor_id": 20, "status": "accepted"}],
            "evaluations": [{"submission_id": 501, "status": "draft"}],
        }],
    })

    result = calculate_practical_experience(request)

    assert result["component_status"] == "unavailable"
    assert result["eligible_projects_count"] == 0
    assert result["practical_experience_score"] is None
