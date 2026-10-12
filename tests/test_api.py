
from fastapi.testclient import TestClient

from app import api as api_module


client = TestClient(api_module.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Project Athena API",
    }


def test_chat_endpoint_returns_response(monkeypatch):
    def fake_process_message(message):
        assert message == "Hello Athena"
        return {
            "response": "Hello! How can I help?",
            "memory_action": None,
        }

    monkeypatch.setattr(
        api_module.assistant,
        "process_message",
        fake_process_message,
    )

    response = client.post(
        "/chat",
        json={"message": "Hello Athena"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Hello! How can I help?",
        "memory_action": None,
    }


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_rejects_whitespace_message():
    response = client.post("/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_rejects_missing_message():
    response = client.post("/chat", json={})

    assert response.status_code == 422


def test_chat_hides_internal_error(monkeypatch):
    def fail_processing(message):
        raise RuntimeError("Sensitive internal details")

    monkeypatch.setattr(
        api_module.assistant,
        "process_message",
        fail_processing,
    )

    response = client.post(
        "/chat",
        json={"message": "Trigger test error"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Athena could not process the message."
    )
    assert "Sensitive internal details" not in response.text
