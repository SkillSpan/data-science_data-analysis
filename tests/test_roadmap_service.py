import pytest

from app.schemas.roadmap import RoadmapRequest
from app.services.roadmap_service import RoadmapError, generate_roadmap


def build_request(*, weekly_hours=10.0, skills=None):
    return RoadmapRequest.model_validate(
        {
            "learner": {
                "student_profile_id": 15,
                "user_id": 20,
                "availability": "part_time",
                "weekly_availability_hours": weekly_hours,
            },
            "role": {
                "id": 3,
                "title": "Backend Developer",
                "version": 2,
            },
            "skills": skills
            or [
                {
                    "skill_id": 1,
                    "skill_name": "Python",
                    "current_level": 2.0,
                    "required_level": 4.0,
                    "importance_weight": 0.5,
                    "is_critical": True,
                    "confidence": 0.9,
                    "prerequisite_skill_ids": [],
                },
                {
                    "skill_id": 2,
                    "skill_name": "FastAPI",
                    "current_level": 2.5,
                    "required_level": 4.0,
                    "importance_weight": 0.3,
                    "is_critical": True,
                    "confidence": 0.8,
                    "prerequisite_skill_ids": [1],
                },
                {
                    "skill_id": 3,
                    "skill_name": "Git",
                    "current_level": 4.0,
                    "required_level": 4.0,
                    "importance_weight": 0.2,
                    "is_critical": False,
                    "confidence": 0.8,
                    "prerequisite_skill_ids": [],
                },
            ],
        }
    )


def all_actions(result):
    return [
        action
        for phase in result["phases"]
        for action in phase["actions"]
    ]


def test_roadmap_orders_prerequisite_before_dependent_and_preserves_all_ids():
    result = generate_roadmap(build_request())
    actions = all_actions(result)

    assert [action["target_skill_id"] for action in actions] == [1, 2]
    assert actions[1]["prerequisite_skill_ids"] == [1]
    assert actions[1]["blocking_prerequisite_skill_ids"] == [1]
    assert result["next_best_action_id"] == actions[0]["action_id"]


def test_met_skills_are_not_repeated_in_roadmap():
    result = generate_roadmap(build_request())

    assert 3 not in [action["target_skill_id"] for action in all_actions(result)]


def test_missing_market_demand_uses_neutral_factor_and_reports_limitation():
    result = generate_roadmap(build_request())

    assert "market_demand_factor_unavailable_neutral_1_0" in result["limitations"]
    python_action = all_actions(result)[0]
    assert any("neutral factor 1.0" in reason for reason in python_action["explanation"])


def test_missing_weekly_availability_returns_effort_without_fabricating_duration():
    result = generate_roadmap(build_request(weekly_hours=None))

    assert result["estimated_total_hours"] > 0
    assert result["estimated_duration_weeks"] is None
    assert "weekly_availability_hours_unavailable" in result["limitations"]
    assert all(
        action["estimated_duration_weeks"] is None
        for action in all_actions(result)
    )


def test_weekly_availability_produces_deterministic_duration():
    result = generate_roadmap(build_request(weekly_hours=10.0))

    assert result["estimated_duration_weeks"] >= 1
    assert all(
        action["estimated_duration_weeks"] >= 1
        for action in all_actions(result)
    )


def test_low_confidence_prefers_assessment_action():
    request = build_request(
        skills=[
            {
                "skill_id": 1,
                "skill_name": "Python",
                "current_level": 3.0,
                "required_level": 4.0,
                "importance_weight": 1.0,
                "is_critical": False,
                "confidence": 0.4,
                "prerequisite_skill_ids": [],
            }
        ]
    )

    action = all_actions(generate_roadmap(request))[0]
    assert action["action_type"] == "assessment"


def test_small_high_confidence_gap_can_produce_real_project_action():
    request = build_request(
        skills=[
            {
                "skill_id": 1,
                "skill_name": "Python",
                "current_level": 3.8,
                "required_level": 4.0,
                "importance_weight": 1.0,
                "is_critical": False,
                "confidence": 0.9,
                "prerequisite_skill_ids": [],
                "market_demand_factor": 1.0,
            }
        ]
    )

    action = all_actions(generate_roadmap(request))[0]
    assert action["action_type"] == "real_project"


def test_multiple_prerequisites_are_preserved_without_loss():
    request = build_request(
        skills=[
            {
                "skill_id": 1,
                "skill_name": "Python",
                "current_level": 4.0,
                "required_level": 4.0,
                "importance_weight": 0.3,
                "is_critical": False,
                "confidence": 0.9,
                "prerequisite_skill_ids": [],
            },
            {
                "skill_id": 2,
                "skill_name": "SQL",
                "current_level": 4.0,
                "required_level": 4.0,
                "importance_weight": 0.3,
                "is_critical": False,
                "confidence": 0.9,
                "prerequisite_skill_ids": [],
            },
            {
                "skill_id": 3,
                "skill_name": "APIs",
                "current_level": 2.0,
                "required_level": 4.0,
                "importance_weight": 0.4,
                "is_critical": True,
                "confidence": 0.9,
                "prerequisite_skill_ids": [1, 2],
            },
        ]
    )

    action = all_actions(generate_roadmap(request))[0]
    assert action["prerequisite_skill_ids"] == [1, 2]
    assert action["blocking_prerequisite_skill_ids"] == []


def test_cycle_is_rejected():
    request = build_request(
        skills=[
            {
                "skill_id": 1,
                "skill_name": "Python",
                "current_level": 2.0,
                "required_level": 4.0,
                "importance_weight": 0.5,
                "is_critical": True,
                "confidence": 0.9,
                "prerequisite_skill_ids": [2],
            },
            {
                "skill_id": 2,
                "skill_name": "FastAPI",
                "current_level": 2.0,
                "required_level": 4.0,
                "importance_weight": 0.5,
                "is_critical": True,
                "confidence": 0.9,
                "prerequisite_skill_ids": [1],
            },
        ]
    )

    with pytest.raises(RoadmapError) as exc:
        generate_roadmap(request)

    assert exc.value.code == "PREREQUISITE_CYCLE"


def test_identical_input_is_deterministic():
    request = build_request()

    assert generate_roadmap(request) == generate_roadmap(request)
