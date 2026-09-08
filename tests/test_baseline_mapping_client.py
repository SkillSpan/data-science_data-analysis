import httpx
import pytest

from app.services.baseline_mapping_client import (
    BaselineMappingConfigurationError,
    BaselineMappingInvalidResponseError,
    BaselineMappingUnavailableError,
    fetch_baseline_mapping,
)


def _valid_mapping_payload() -> dict[str, object]:
    return {
        "success": True,
        "assessment_version": "v1.0",
        "weight_scale": "0..1",
        "items": [
            {
                "item_id": "sql-001",
                "item_type": "single_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "B",
                "scoring_rule": None,
                "skill_id": 5,
                "skill_slug": "sql",
                "weight": 1.0,
            },
            {
                "item_id": "python-002",
                "item_type": "scale",
                "options": ["1", "2", "3", "4", "5"],
                "correct_answer": None,
                "scoring_rule": {
                    "1": 0.0,
                    "2": 0.25,
                    "3": 0.5,
                    "4": 0.75,
                    "5": 1.0,
                },
                "skill_id": 1,
                "skill_slug": "python",
                "weight": 0.5,
            },
        ],
    }


def _configure_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_BASE_URL", "https://backend.example.test/")
    monkeypatch.setenv("BASELINE_INTERNAL_SECRET", "test-secret")


def test_fetch_baseline_mapping_requires_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BACKEND_BASE_URL", raising=False)
    monkeypatch.delenv("BASELINE_INTERNAL_SECRET", raising=False)

    with pytest.raises(BaselineMappingConfigurationError):
        fetch_baseline_mapping("v1.0", "req-123")


def test_fetch_baseline_mapping_sends_contract_headers_and_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_backend(monkeypatch)
    captured: dict[str, object] = {}

    def fake_get(url: str, **fkwargs: object) -> httpx.Response:
        captured["url"] = url
        captured.update(fkwargs)
        return httpx.Response(
            200,
            json=_valid_mapping_payload(),
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    mapping = fetch_baseline_mapping("v1.0", "req-123")

    assert mapping.assessment_version == "v1.0"
    assert captured["url"] == (
        "https://backend.example.test/api/v1/internal/baseline-items"
    )
    assert captured["params"] == {"version": "v1.0"}
    assert captured["headers"] == {
        "Accept": "application/json",
        "X-Internal-Secret": "test-secret",
        "X-Request-ID": "req-123",
    }
    assert captured["timeout"] == 8.0


def test_fetch_baseline_mapping_maps_request_errors_to_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_backend(monkeypatch)

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        request = httpx.Request("GET", url)
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(BaselineMappingUnavailableError):
        fetch_baseline_mapping("v1.0")


def test_fetch_baseline_mapping_rejects_non_200_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_backend(monkeypatch)

    def fake_get(url: str, **fkwargs: object) -> httpx.Response:
        return httpx.Response(
            500,
            json={"success": False},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(BaselineMappingUnavailableError):
        fetch_baseline_mapping("v1.0")


def test_fetch_baseline_mapping_rejects_invalid_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_backend(monkeypatch)
    payload = _valid_mapping_payload()
    payload["weight_scale"] = "0..100"

    def fake_get(url: str, **fwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(BaselineMappingInvalidResponseError):
        fetch_baseline_mapping("v1.0")

def test_fetch_baseline_mapping_rejects_version_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_backend(monkeypatch)
    payload = _valid_mapping_payload()
    payload["assessment_version"] = "v2.0"

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
         )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(BaselineMappingInvalidResponseError):
        fetch_baseline_mapping("v1.0")


def test_fetch_baseline_mapping_uses_configured_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_backend(monkeypatch)
    monkeypatch.setenv("BASELINE_MAPPING_TIMEOUT_SECONDS", "12.5")
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        captured.update(kwargs)
        return httpx.Response(
            200,
            json=_valid_mapping_payload(),
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    fetch_baseline_mapping("v1.0")

    assert captured["timeout"] == 12.5


@pytest.mark.parametrize("value", ["invalid", "0", "-1", "nan", "inf"])
def test_fetch_baseline_mapping_rejects_invalid_timeout_configuration(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    _configure_backend(monkeypatch)
    monkeypatch.setenv("BASELINE_MAPPING_TIMEOUT_SECONDS", value)

    with pytest.raises(
        BaselineMappingConfigurationError,
        match="BASELINE_MAPPING_TIMEOUT_SECONDS",
    ):
        fetch_baseline_mapping("v1.0")
