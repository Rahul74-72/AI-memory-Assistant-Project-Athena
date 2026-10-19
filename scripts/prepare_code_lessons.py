"""Prepare a reviewable curriculum from selected existing Athena source files.

No secrets, databases, chats, uploaded images, or arbitrary directories are scanned.
The result is a draft for human review, not automatically approved training data.
"""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "beginner": ["app/embeddings/memory_text.py", "app/memory/importance_calibrator.py"],
    "intermediate": ["app/retrieval/retriever.py", "app/extractor/extractor.py"],
    "advanced": ["app/memory/memory_store.py", "app/context/evidence_confidence.py"],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for level, paths in SOURCES.items():
        for name in paths:
            source = (ROOT/name).read_text(encoding="utf-8-sig")
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.FunctionDef):
                    code = ast.get_source_segment(source, node)
                    if code and len(code) <= 10000:
                        rows.append({"level":level,"approved":False,"source":name,
                            "prompt":f"Explain {node.name} from {name} at {level} level and suggest a test.",
                            "reference_code":code,"answer":""})
    with args.output.open("x", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False)+"\n")
    print(f"Prepared {len(rows)} draft exercises. Write and review answers in Athena's Learning panel.")


if __name__ == "__main__":
    main()
