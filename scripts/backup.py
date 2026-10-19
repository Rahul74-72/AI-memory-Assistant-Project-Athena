"""Snapshot project files and SQLite consistently. Backups contain private data."""
import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", ".training-venv", "venv", "backups", "__pycache__", ".pytest_cache", ".cache", "node_modules"}


def backup(label):
    folder = ROOT / "backups"
    folder.mkdir(exist_ok=True)
    destination = folder / f"athena-{label}-{datetime.now():%Y%m%d-%H%M%S-%f}.zip"
    entries = []
    with tempfile.TemporaryDirectory() as temporary, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED for part in relative.parts) or path.is_symlink() or not path.is_file():
                continue
            if path.name.endswith(("-wal", "-shm")):
                continue
            # Model weights are reproducible and can be many gigabytes.
            if path.suffix in {".safetensors", ".gguf", ".bin"}:
                continue
            content_path = path
            if path.suffix in {".db", ".sqlite", ".sqlite3"}:
                snapshot = Path(temporary) / f"{len(entries)}.db"
                source = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)
                target = sqlite3.connect(snapshot)
                try:
                    source.backup(target)
                finally:
                    source.close()
                    target.close()
                content_path = snapshot
            data = content_path.read_bytes()
            archive.writestr(relative.as_posix(), data)
            entries.append({"path": relative.as_posix(), "sha256": hashlib.sha256(data).hexdigest()})
        archive.writestr("BACKUP-MANIFEST.json", json.dumps(entries, indent=2))
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Backup verification failed")
    print(destination)
    print("SHA256", hashlib.sha256(destination.read_bytes()).hexdigest())
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="manual", choices=["before", "after", "manual"])
    backup(parser.parse_args().label)
