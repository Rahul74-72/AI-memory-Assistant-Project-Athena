from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import api as api_module
from app.auth_routes import get_current_user


client = TestClient(api_module.app)


@pytest.fixture
def authenticated():
    api_module.app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=42, username="testuser")
    )
    try:
        yield
    finally:
        api_module.app.dependency_overrides.pop(
            get_current_user, None
        )


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Project Athena API",
    }


def test_chat_requires_authentication():
    response = client.post(
        "/chat",
        json={"message": "Hello Athena"},
    )
    assert response.status_code == 401


def test_chat_endpoint_returns_response(monkeypatch, authenticated):
    closed = []

    class FakeEngine:
        def __init__(self, user_id):
            assert user_id == 42

        def process_message(self, message):
            assert message == "Hello Athena"
            return {
                "response": "Hello! How can I help?",
                "memory_action": None,
            }

        def close(self):
            closed.append(True)

    monkeypatch.setattr(api_module, "ChatEngine", FakeEngine)

    response = client.post(
        "/chat",
        json={"message": "Hello Athena"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Hello! How can I help?",
        "memory_action": None,
    }
    assert closed == [True]


def test_chat_rejects_empty_message(authenticated):
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_rejects_whitespace_message(authenticated):
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_rejects_missing_message(authenticated):
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_hides_internal_error(monkeypatch, authenticated):
    class FailingEngine:
        def __init__(self, user_id):
            assert user_id == 42

        def process_message(self, message):
            raise RuntimeError("Sensitive internal details")

        def close(self):
            pass

    monkeypatch.setattr(api_module, "ChatEngine", FailingEngine)

    response = client.post(
        "/chat",
        json={"message": "Trigger test error"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Athena could not process the message."
    )
    assert "Sensitive internal details" not in response.text


def test_chat_closes_engine_on_failure(monkeypatch, authenticated):
    closed = []

    class FailingEngine:
        def __init__(self, user_id):
            assert user_id == 42

        def process_message(self, message):
            raise RuntimeError("Simulated error")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(api_module, "ChatEngine", FailingEngine)

    response = client.post(
        "/chat",
        json={"message": "Test cleanup"},
    )

    assert response.status_code == 500
    assert closed == [True]