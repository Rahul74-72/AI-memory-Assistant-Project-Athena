# Project Athena — AI Memory Assistant

Project Athena is a prototype AI memory system that stores conversation history and structured long-term memories, then retrieves relevant memories from user queries.

## Current Version

**v0.1 — Prototype**

### Current capabilities

- Persistent conversation storage with SQLite + SQLAlchemy
- Structured long-term memory using subject / relation / value
- Single-value relationship updates (for example, `lives_in`)
- Multi-value relationships (for example, `likes`)
- Duplicate-memory detection
- Rule-based memory extraction
- Basic keyword-based memory retrieval
- Embedding experiment using `sentence-transformers/all-MiniLM-L6-v2`

## Project Structure

```text
app/
├── chat/
├── database/
├── extractor/
├── memory/
├── retrieval/
└── utils/

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

- [ ] Improve natural-language memory extraction
- [ ] Integrate embeddings into retrieval
- [ ] Add semantic similarity ranking
- [ ] Add memory conflict resolution
- [ ] Add memory deletion / forgetting
- [ ] Add LLM-based reasoning
- [ ] Add automated tests and evaluation
- [ ] Add API / web interface

## Note

This repository is an active learning project. The current version is a working prototype rather than a production-ready assistant.
