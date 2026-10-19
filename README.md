# Project Athena — AI Memory Assistant

Project Athena is an AI memory system that stores conversation history and structured long-term memories, then retrieves relevant memories from user queries.

## Current status

**Windows-first local workspace.** Chat, NLP memory, voice transcription, picture memory,
coding assistance, reviewed learning data, and authentication are integrated. A separate
`athena-local` Ollama model configuration uses Llama 3.2 3B. This is not a model trained
from scratch, and private fine-tuning is a separate reviewed workflow.

## Start on Windows

Open this folder in VS Code. After the one-time setup below, double-click
`Start-Athena.cmd`, or run `.\.venv\Scripts\python.exe main.py`.
Open **http://127.0.0.1:8000** and create your own account. There is no default password.
The launcher creates a random signing secret in the local `.env` on first use.

One-time setup (Python 3.10+ and Ollama must be installed):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/setup_models.py
.\.venv\Scripts\python.exe main.py
```

Models are downloaded during setup. Afterwards chat, embeddings, vision and transcription
run locally. Keep Ollama running. Initial model loading can take time on a laptop.
See [server deployment](docs/DEPLOYMENT.md), [training](docs/TRAINING.md), and
[security requirements from the reference video](docs/SECURITY.md).

### Current capabilities

- Persistent conversation storage with SQLite + SQLAlchemy
- Structured long-term memory using subject / relation / value
- Single-value relationship updates (for example, `lives_in`)
- Multi-value relationships (for example, `likes`)
- Duplicate-memory detection
- Rule-based plus local LLM structured NLP extraction, with evidence validation
- Embedding-based semantic retrieval
- Semantic similarity ranking of retrieved memories
- LLM-based reasoning over retrieved memory context
- Automated regression tests for core retrieval, context, and chat behavior
- Private image upload, local image descriptions, picture recall and deletion
- Local Whisper voice transcription; optional local browser/Windows speech output
- Coding workspace with saved reference files and beginner/intermediate/advanced tutoring
- Opt-in collection of training examples, history import, approval, and private JSONL export
- Password hashing, session revocation, optional authenticator MFA, request limits and scoped downloads

## Everyday use

- **Chat:** share facts such as “I live in Jaipur” or ask “Where do I live?”.
- **Voice:** press Record voice, stop, review the transcript, and send it. Enable Read replies aloud
  for a local system voice. Recording needs localhost or HTTPS and browser microphone permission.
- **Pictures:** upload JPEG/PNG/WebP. Use your own caption or automatic local description, then ask
  about pictures in this panel. Model descriptions are imperfect and can be edited by replacing the picture.
- **Coding studio:** write or load a text source file, save it, select the reference and learning level,
  and ask for an explanation or code. Generated code is displayed as text and is not executed.
- **Learning:** optionally collect future answers, import your previous chats for review, correct answers,
  approve lessons and export them. Unapproved answers never enter training exports.
- **Account & security:** enable MFA. Signing out revokes all sessions for your account.

Old single-user data is retained in a disabled legacy account. It is never silently given to a new user.
If all of it is yours, make a backup and use `scripts/claim_legacy.py --username YOUR_NAME --i-own-all-legacy-data`.
The command asks for that account's password. Do not use it on a database containing multiple people's legacy data.

## Backups and tests

```powershell
.\.venv\Scripts\python.exe scripts/backup.py --label manual
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Backups live in `backups/`, contain private data and the signing secret when present,
and must be kept private. The backup tool uses SQLite's snapshot API and verifies ZIP integrity.
Virtual environments, Git metadata, previous backups, and large model weights are excluded.
Restore into a new directory with the server stopped, verify `BACKUP-MANIFEST.json`, reinstall dependencies,
and restore/download model weights separately. Never upload these backups to a public repository.

## Project Structure

```text
app/
├── chat/
├── context/
├── database/
├── extractor/
├── llm/
├── memory/
├── retrieval/
└── utils/

tests/
docs/
main.py
requirements.txt
```

Local runtime data such as `data/` is ignored by Git.

## Run

```bash
python -m venv .venv
```

Activate the environment, then:

```bash
pip install -r requirements.txt
python main.py
```

## Example memories

```text
I live in Neemrana
I like Python
I love cricket
I want to become an AI Engineer
I am building an AI Memory Assistant
```

## Roadmap

- [x] Add local structured NLP extraction (accuracy evaluation remains ongoing)
- [x] Integrate embeddings into retrieval
- [x] Add semantic similarity ranking
- [x] Scope single-value replacements and contradiction tools to the current user
- [x] Add memory deletion / forgetting
- [x] Add LLM-based reasoning
- [x] Add automated tests and evaluation
- [x] Add API / web interface
- [x] Add local voice and picture memory
- [x] Prepare private fine-tuning and reviewed training data
- [ ] Train and evaluate a private adapter on a sufficiently large reviewed dataset
- [ ] Deploy and verify on a selected internet server with TLS

See [`docs/ROADMAP_STATUS.md`](docs/ROADMAP_STATUS.md) for the implementation details and remaining work.

## Note

The local implementation does not constitute a security certification. Public deployment,
real model quality evaluation, and private adapter acceptance require the checks documented above.
