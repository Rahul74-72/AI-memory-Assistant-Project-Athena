"""Launch Athena locally. No model or dependency downloads during startup."""
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from dotenv import load_dotenv
    config = ROOT / ".env"
    if not config.exists():
        # Exclusive creation prevents concurrent launchers replacing the secret.
        with config.open("x", encoding="utf-8") as output:
            output.write("ATHENA_JWT_SECRET="+secrets.token_urlsafe(48)+"\n")
            output.write("ATHENA_MODEL=athena-local\nATHENA_ALLOW_REGISTRATION=1\n")
        try:
            config.chmod(0o600)
        except OSError:
            pass
    load_dotenv(config, override=False)
    print("Athena: http://127.0.0.1:8000 (Ctrl+C to stop)")
    import uvicorn
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, proxy_headers=False, workers=1)


if __name__ == "__main__":
    main()
