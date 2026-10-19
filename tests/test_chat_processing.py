
import pytest

from app.chat.chat import ChatEngine


class FakeMemory:
    def __init__(self):
        self.messages = []

    def save_message(self, speaker, message):
        self.messages.append((speaker, message))


class FakeExtractor:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def extract(self, message):
        self.calls.append(message)
        return self.result


class FakeMemoryStore:
    def __init__(self, result=None):
        self.result = result or {"action": "created"}
        self.saved = []

    def save_memory(self, **kwargs):
        self.saved.append(kwargs)
        return self.result


def make_engine(extraction_result):
    engine = ChatEngine.__new__(ChatEngine)
    engine.memory = FakeMemory()
    engine.extractor = FakeExtractor(extraction_result)
    engine.memory_store = FakeMemoryStore()

    engine.handle_forget_request = lambda message: None
    engine.generate_response = lambda message: "Athena test response"

    return engine


def test_process_message_saves_conversation_and_memory():
    extraction = {
        "save": True,
        "subject": "User",
        "relation": "likes",
        "value": "Python",
        "category": "PREFERENCE",
        "importance": 7,
    }
    engine = make_engine(extraction)

    result = engine.process_message("I like Python")

    assert result == {
        "response": "Athena test response",
        "memory_action": "created",
    }
    assert engine.memory.messages == [
        ("User", "I like Python"),
        ("AI", "Athena test response"),
    ]
    assert engine.extractor.calls == ["I like Python"]
    assert engine.memory_store.saved == [{
        "subject": "User",
        "relation": "likes",
        "value": "Python",
        "category": "PREFERENCE",
        "importance": 7,
    }]


def test_process_message_does_not_save_when_extraction_declines():
    engine = make_engine({"save": False})

    result = engine.process_message("Hello Athena")

    assert result == {
        "response": "Athena test response",
        "memory_action": None,
    }
    assert engine.memory.messages == [
        ("User", "Hello Athena"),
        ("AI", "Athena test response"),
    ]
    assert engine.memory_store.saved == []


def test_process_message_handles_forgetting_without_extraction():
    engine = make_engine({"save": True})
    engine.handle_forget_request = (
        lambda message: "I've forgotten where you live."
    )

    result = engine.process_message("Forget where I live")

    assert result == {
        "response": "I've forgotten where you live.",
        "memory_action": None,
    }
    assert engine.memory.messages == [
        ("User", "Forget where I live"),
        ("AI", "I've forgotten where you live."),
    ]
    assert engine.extractor.calls == []
    assert engine.memory_store.saved == []


def test_process_message_rejects_blank_input():
    engine = make_engine({"save": False})

    with pytest.raises(ValueError, match="Message cannot be empty"):
        engine.process_message("   ")

    assert engine.memory.messages == []
    assert engine.extractor.calls == []
def test_cli_closes_resources_when_user_exits(monkeypatch, capsys):
    engine = ChatEngine.__new__(ChatEngine)

    class FakeResource:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    engine.memory = FakeResource()
    engine.memory_store = FakeResource()

    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")

    engine.chat()

    assert engine.memory.closed is True
    assert engine.memory_store.closed is True
    assert "Goodbye!" in capsys.readouterr().out