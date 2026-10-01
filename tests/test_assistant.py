from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import assistant as assistant_route
from app.assistant.rag.index import _cosine

TOKEN = "assistant-test-token"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATA_SCIENCE_SERVICE_TOKEN", TOKEN)
    with TestClient(app) as test_client:
        test_client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        yield test_client


def _hit(source: str, text: str, score: float = 0.8):
    return SimpleNamespace(chunk=SimpleNamespace(source=source, text=text), score=score)


class StubRetriever:
    def __init__(self, hits=None, available=True):
        self.hits = hits or []
        self.available = available

    def retrieve(self, question: str):
        return self.hits


def test_assistant_returns_grounded_answer_and_sources(client, monkeypatch):
    retriever = StubRetriever([_hit("02-readiness-score.md", "Readiness uses weighted components.")])
    monkeypatch.setattr(assistant_route, "_retriever_for_request", lambda: retriever)
    async def fake_reply(system_prompt, user_prompt):
        assert "APPROVED SKILLSPAN KNOWLEDGE" in user_prompt
        return "Grounded answer", "groq"
    monkeypatch.setattr(assistant_route, "generate_reply", fake_reply)
    response = client.post("/api/v1/assistant/chat", json={"message": "How is readiness calculated?"}, headers={"X-Request-ID": "req-assistant-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["grounded"] is True
    assert body["sources"] == ["02-readiness-score.md"]
    assert body["provider_used"] == "groq"
    assert body["request_id"] == "req-assistant-1"


def test_assistant_returns_insufficient_context_without_provider(client, monkeypatch):
    monkeypatch.setattr(assistant_route, "_retriever_for_request", lambda: StubRetriever([]))
    async def should_not_run(*args, **kwargs):
        raise AssertionError("provider must not run without grounded context")
    monkeypatch.setattr(assistant_route, "generate_reply", should_not_run)
    response = client.post("/api/v1/assistant/chat", json={"message": "Unrelated question"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_context"
    assert body["grounded"] is False
    assert body["sources"] == []


def test_assistant_localizes_insufficient_context_to_arabic(client, monkeypatch):
    monkeypatch.setattr(assistant_route, "_retriever_for_request", lambda: StubRetriever([]))
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Unrelated question", "locale": "ar"},
    )
    assert response.status_code == 200
    assert response.json()["reply"].encode("unicode_escape").startswith(b"\\u0644\\u0627 \\u062a\\u0648\\u062c\\u062f")
def test_assistant_returns_503_when_retrieval_is_unavailable(client, monkeypatch):
    monkeypatch.setattr(assistant_route, "_retriever_for_request", lambda: StubRetriever(available=False))
    response = client.post("/api/v1/assistant/chat", json={"message": "Hello"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "assistant_retrieval_unavailable"


def test_assistant_returns_503_when_all_providers_fail(client, monkeypatch):
    monkeypatch.setattr(assistant_route, "_retriever_for_request", lambda: StubRetriever([_hit("01-overview.md", "SkillSpan overview")]))
    async def unavailable(*args, **kwargs):
        return None, None
    monkeypatch.setattr(assistant_route, "generate_reply", unavailable)
    response = client.post("/api/v1/assistant/chat", json={"message": "What is SkillSpan?"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "assistant_provider_unavailable"


def test_assistant_accepts_laravel_context_and_bypasses_retrieval(client, monkeypatch):
    def should_not_load_retriever():
        raise AssertionError("RAG must not run when Laravel supplies approved context")

    monkeypatch.setattr(assistant_route, "_retriever_for_request", should_not_load_retriever)

    async def fake_reply(system_prompt, user_prompt):
        assert "Approved assistant intent: explain_readiness" in user_prompt
        assert "SkillSpan learner context (authoritative stored values)" in user_prompt
        assert '"readiness_score": 67' in user_prompt
        return "Your readiness is 67 because of the supplied components.", "groq"

    monkeypatch.setattr(assistant_route, "generate_reply", fake_reply)
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "user_id": "42",
            "message": "Why is my readiness 67?",
            "intent": "explain_readiness",
            "context": 'SkillSpan learner context (authoritative stored values):\\n{"readiness_score": 67}',
        },
        headers={"X-Request-ID": "req-laravel-assistant-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["grounded"] is True
    assert body["sources"] == ["laravel_context"]
    assert body["provider_used"] == "groq"
    assert body["request_id"] == "req-laravel-assistant-1"


def test_assistant_rejects_unknown_intent(client):
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "user_id": "42",
            "message": "Do something outside scope",
            "intent": "complete_assignment",
            "context": "Approved context",
        },
    )
    assert response.status_code == 422
def test_cosine_rejects_dimension_mismatch():
    with pytest.raises(ValueError, match="same dimensions"):
        _cosine([1.0, 0.0], [1.0])
