# Running Athena

## This Windows PC

Run `Start-Athena.cmd` or `.\.venv\Scripts\python.exe main.py`, then open
http://127.0.0.1:8000. Keep Ollama running. This is a local server, not an internet deployment.
Stop the launcher with Ctrl+C. Reloading the browser requires sign-in because tokens are held in memory only.

The first launch creates `.env` with a random secret and runs idempotent database migrations. Original
single-user records go to a disabled legacy account. Make backups before migration and before upgrades.
Never replace `.env` on routine restarts; doing so invalidates sessions and prevents decryption of existing MFA secrets.

Model setup: `python scripts/setup_models.py`. It downloads the chat, vision, embedding and speech models.
Speech input uses a CPU Whisper model. Speech output uses a locally installed browser/system voice; availability
depends on the browser and Windows voice packs. No remote speech-recognition API is used by the app.

## Container / future Linux server

`Dockerfile` and `compose.yaml` are provided. They have not necessarily been built on this Windows machine.
They run as a non-root user, use persistent data/cache volumes, drop capabilities, use a read-only root
filesystem, and expose the web port only on the host loopback interface.

1. Provision a server with enough RAM, disk, and optional GPU; install Docker and Ollama.
2. Copy source, install/download the selected models, and create `athena-local` from `models/Modelfile`.
3. Create a private `.env` with a strong random `ATHENA_JWT_SECRET`, the intended model names,
   and `ATHENA_ALLOWED_HOSTS=your-domain.example,localhost,127.0.0.1`.
4. Decide registration policy. Set `ATHENA_ALLOW_REGISTRATION=0` after creating intended accounts.
5. Run `docker compose up --build -d`. The API port remains `127.0.0.1:8000` on the host.
6. Put an HTTPS reverse proxy in front of it. Allow only your domain; cap requests at 8 MB plus multipart overhead;
   set an appropriate AI-request timeout. Add HSTS at the proxy. Keep request/body/token logging disabled.
7. Permit only HTTPS and a restricted administration path through the host firewall. Keep port 11434 private.
8. Verify registration policy, MFA, two-account isolation, backups/restoration, HTTPS microphone permissions,
   dependency audit and service restarts on that actual server before making it available to other users.

Compose uses `host.docker.internal:11434` for an existing host Ollama service. On Linux, Ollama must be reachable
from the Docker bridge; configure a private bridge binding/firewall or run Ollama on a private container network.
Do not expose an unauthenticated Ollama service publicly to solve connectivity.
One app worker is deliberate: current rate limits and model concurrency controls are process-local.
Multi-worker/multi-host deployment needs a shared limiter/queue and a suitable database architecture.

The image builds from version ranges. Record and audit the resolved dependency versions before deployment.
For native Windows service installation, use an OS-managed service account with restricted filesystem access;
the current launcher is a user-controlled local process, not a boot-time Windows Service.

## Backup and restore

`python scripts/backup.py --label manual` includes consistent SQLite snapshots and a SHA-256 file manifest.
Backups include private source/data and `.env`, but omit environment directories, Git metadata, previous backups
and model weights. Protect and encrypt off-machine copies. Store the original upgrade backups separately.
Restore to a new folder with the service stopped, verify manifest hashes, reinstall dependencies, then start
using the restored `.env`. Test restoration before depending on a backup in production.
