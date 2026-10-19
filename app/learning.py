"""Private, reviewed examples. Retrieval is immediate; weight training is separate."""
import hashlib
import json
import re
from sqlalchemy import select
from app.database.models import TrainingExample
from app.settings import require_user_id


def contains_secret(text):
    return bool(re.search(
        r"(?i)(-----BEGIN .*PRIVATE KEY|\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{16,}|"
        r"\b(?:password|api[_-]?key|secret|token)\s*[:=]\s*['\"]?[^\s'\"]{8,})", text))


def export_examples(db, user_id):
    require_user_id(user_id)
    examples = db.scalars(select(TrainingExample).where(
        TrainingExample.user_id == user_id, TrainingExample.approved.is_(True)
    ).order_by(TrainingExample.id)).all()
    rows, seen = [], set()
    for example in examples:
        if contains_secret(example.prompt + "\n" + example.answer):
            continue
        fingerprint = hashlib.sha256((example.prompt+"\n"+example.answer).encode()).hexdigest()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        rows.append({"messages": [
            {"role": "user", "content": example.prompt},
            {"role": "assistant", "content": example.answer},
        ], "level": example.level, "fingerprint": fingerprint})
    order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    rows.sort(key=lambda row: (order[row["level"]], row["fingerprint"]))
    return "".join(json.dumps(row, ensure_ascii=False)+"\n" for row in rows)
