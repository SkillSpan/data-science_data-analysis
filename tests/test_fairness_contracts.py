from app.schemas.assessment_reliability import AssessmentReliabilityRequest
from app.schemas.baseline import BaselineRequest
from app.schemas.career_role_configuration import CareerRoleConfigurationRequest
from app.schemas.practical_experience import PracticalExperienceRequest
from app.schemas.profile_completeness import ProfileCompletenessRequest
from app.schemas.skill_confidence import SkillConfidenceRequest
from app.schemas.skill_gap import SkillGapRequest
from app.schemas.skill_match import SkillMatchRequest


FAIRNESS_SENTINEL_ATTRIBUTE_NAMES = {
    "age",
    "disability",
    "ethnicity",
    "gender",
    "nationality",
    "race",
    "religion",
    "sex",
}

# Non-exhaustive regression sentinels only. The project policy remains generic:
# protected or unrelated learner attributes must not become analytical decision inputs.

ANALYTICAL_REQUEST_MODELS = (
    AssessmentReliabilityRequest,
    BaselineRequest,
    CareerRoleConfigurationRequest,
    PracticalExperienceRequest,
    ProfileCompletenessRequest,
    SkillConfidenceRequest,
    SkillGapRequest,
    SkillMatchRequest,
)


def _property_names(node: object) -> set[str]:
    if isinstance(node, dict):
        names = set(node.get("properties", {}).keys())
        for value in node.values():
            names.update(_property_names(value))
        return names
    if isinstance(node, list):
        names: set[str] = set()
        for value in node:
            names.update(_property_names(value))
        return names
    return set()


def test_analytical_request_contracts_do_not_expose_protected_attributes() -> None:
    """Protected learner attributes must not become scoring or ranking inputs."""

    for model in ANALYTICAL_REQUEST_MODELS:
        property_names = {name.lower() for name in _property_names(model.model_json_schema())}
        exposed = sorted(FAIRNESS_SENTINEL_ATTRIBUTE_NAMES & property_names)

        assert exposed == [], (
            f"{model.__name__} exposes protected analytical input fields: {exposed}"
        )
