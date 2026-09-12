# README Roadmap Reconciliation

The main README roadmap should reflect the current implementation rather than the original prototype checklist.

## Implemented roadmap items

- Embeddings are integrated into semantic retrieval through `MemoryStore.semantic_search()`.
- Semantic similarity ranking is part of memory retrieval.
- `AIReasoner` uses the Ollama client to answer questions from retrieved memory context.
- Regression tests cover retrieval ranking, memory-question detection, and context-builder behavior.

## Remaining roadmap items

- Improve natural-language memory extraction beyond the current rule-based approach.
- Add explicit conflict-resolution policies for contradictory memories.
- Expose memory deletion/forgetting as a user-facing operation.
- Add end-to-end evaluation spanning extraction, retrieval, context construction, and reasoning.
- Add an API or web interface.

This file is a companion to `docs/ROADMAP_STATUS.md` and is intended to keep the README reconciliation work explicit until the README itself is updated through the normal repository editing workflow.
