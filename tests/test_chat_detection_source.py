import ast
from pathlib import Path


CHAT_SOURCE = Path(__file__).resolve().parents[1] / "app" / "chat" / "chat.py"


def test_memory_question_detection_uses_token_boundaries():
    tree = ast.parse(CHAT_SOURCE.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ChatEngine"
        for node in node.body
        if isinstance(node, ast.FunctionDef) and node.name == "is_memory_question"
    )

    source = ast.unparse(function)

    assert "re.findall" in source
    assert r"\\b\\w+\\b" in source
    assert "words & keywords" in source


def test_memory_question_keywords_remain_explicit():
    source = CHAT_SOURCE.read_text(encoding="utf-8")

    for keyword in ("what", "where", "who", "remember", "favorite", "goal", "skill"):
        assert f'"{keyword}"' in source
