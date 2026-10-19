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
CREATOR_NAME = "Voyanix"
CLEARANCE_LEVELS = ("D", "C", "B", "A", "S", "SS", "SSS", "EX")
SYSTEM_CLEARANCE = "EX"
PUBLIC_CLEARANCE_LEVELS = CLEARANCE_LEVELS[:-1]
OWNER_USERNAME = os.environ.get("ATHENA_OWNER_USERNAME", "voyanix").strip().lower()


def clearance_for_username(username):
    """Resolve clearance on the server; clients cannot request or alter it."""
    if isinstance(username, str) and username.lower() == OWNER_USERNAME:
        return SYSTEM_CLEARANCE
    return PUBLIC_CLEARANCE_LEVELS[-1]


def require_user_id(user_id):
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer.")
    return user_id
