from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
TEST_TOKEN = "test-service-token"


def test_health_is_public_without_service_token(monkeypatch) -> None:
    monkeypatch.delenv("DATA_SCIENCE_SERVICE_TOKEN", raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_fails_closed_when_service_token_is_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("DATA_SCIENCE_SERVICE_TOKEN", raising=False)

    response = client.post("/api/v1/skill-match", json={})

    assert response.status_code == 503
    assert response.json() == {"detail": "Data Science service authentication is not configured."}


def test_api_rejects_missing_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("DATA_SCIENCE_SERVICE_TOKEN", TEST_TOKEN)

    response = client.post("/api/v1/skill-match", json={})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_api_rejects_invalid_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("DATA_SCIENCE_SERVICE_TOKEN", TEST_TOKEN)

    response = client.post(
        "/api/v1/skill-match",
        json={},
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_api_accepts_valid_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("DATA_SCIENCE_SERVICE_TOKEN", TEST_TOKEN)

    response = client.post(
        "/api/v1/skill-match",
        json={},
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    assert response.status_code == 422
