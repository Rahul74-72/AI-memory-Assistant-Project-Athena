"""Local-first configuration. Secrets never travel to the browser."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("ATHENA_DATA_DIR", ROOT / "data")).resolve()
OLLAMA_HOST = os.environ.get("ATHENA_OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
CHAT_MODEL = os.environ.get("ATHENA_MODEL", "athena-local")
VISION_MODEL = os.environ.get("ATHENA_VISION_MODEL", "moondream")
WHISPER_MODEL = os.environ.get("ATHENA_WHISPER_MODEL", "tiny")
MAX_UPLOAD = 8 * 1024 * 1024


def require_user_id(user_id):
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer.")
    return user_id
