from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_marks_implemented_capabilities_as_complete():
    source = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "- [x] Integrate embeddings into retrieval" in source
    assert "- [x] Add semantic similarity ranking" in source
    assert "- [x] Add LLM-based reasoning" in source
    assert "- [x] Add automated tests and evaluation" in source


def test_readme_links_detailed_roadmap_status():
    source = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/ROADMAP_STATUS.md" in source
