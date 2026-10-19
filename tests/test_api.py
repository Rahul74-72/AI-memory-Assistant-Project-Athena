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


def test_system_identity_and_clearance_ladder():
    response = client.get("/about")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Project Athena",
        "creator": "Voyanix",
        "maximum_clearance": "SSS",
        "clearance_levels": ["D", "C", "B", "A", "S", "SS", "SSS"],
    }
    assert "EX" not in response.text


def test_ex_clearance_is_owner_only(monkeypatch):
    from app import settings

    monkeypatch.setattr(settings, "OWNER_USERNAME", "private_owner")
    assert settings.clearance_for_username("private_owner") == "EX"
    assert settings.clearance_for_username("PRIVATE_OWNER") == "EX"
    assert settings.clearance_for_username("another_user") == "SSS"


def test_installable_app_assets_are_available():
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    assert manifest.json()["display"] == "standalone"
    assert manifest.json()["start_url"] == "/"

    worker = client.get("/service-worker.js")
    assert worker.status_code == 200
    assert worker.headers["service-worker-allowed"] == "/"
    assert "/chat" not in worker.text


def test_app_shell_links_manifest_and_avoids_token_persistence():
    home = client.get("/")
    script = client.get("/static/app.js")
    assert home.status_code == 200
    assert 'rel="manifest" href="/manifest.webmanifest"' in home.text
    assert "serviceWorker.register('/service-worker.js')" in script.text
    assert "localStorage" not in script.text


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
