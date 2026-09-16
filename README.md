# Project Athena — AI Memory Assistant

Project Athena is an AI memory system that stores conversation history and structured long-term memories, then retrieves relevant memories from user queries.

## Current status

**Active development — retrieval and reasoning are integrated; extraction and memory management are still being expanded.**

### Current capabilities

- Persistent conversation storage with SQLite + SQLAlchemy
- Structured long-term memory using subject / relation / value
- Single-value relationship updates (for example, `lives_in`)
- Multi-value relationships (for example, `likes`)
- Duplicate-memory detection
- Rule-based memory extraction
- Embedding-based semantic retrieval
- Semantic similarity ranking of retrieved memories
- LLM-based reasoning over retrieved memory context
- Automated regression tests for core retrieval, context, and chat behavior

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

- [ ] Improve natural-language memory extraction
- [x] Integrate embeddings into retrieval
- [x] Add semantic similarity ranking
- [ ] Add memory conflict resolution
- [ ] Add memory deletion / forgetting
- [x] Add LLM-based reasoning
- [x] Add automated tests and evaluation
- [ ] Add API / web interface

See [`docs/ROADMAP_STATUS.md`](docs/ROADMAP_STATUS.md) for the implementation details and remaining work.

## Note

This repository is an active learning project. The current implementation is beyond the initial prototype, but it is not yet production-ready.
