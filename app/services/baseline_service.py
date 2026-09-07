from app.schemas.baseline import BaselineRequest


class BaselineEvaluationUnavailableError(RuntimeError):
    """Raised when baseline scoring dependencies are not available."""


def evaluate_baseline(request: BaselineRequest) -> dict[str, object]:
    """Evaluate a baseline assessment once Backend mapping is available."""

    raise BaselineEvaluationUnavailableError(
        "Baseline evaluation requires Backend-owned assessment item "
        "definitions and item-to-skill mapping."
    )
