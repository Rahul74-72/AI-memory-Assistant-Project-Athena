# Athena Roadmap Status

This note records which roadmap items are already represented in the current implementation so the main README roadmap can be reconciled during the next documentation pass.

## Implemented

- Embedding-based semantic retrieval is used by `ChatEngine` through `MemoryStore.semantic_search()`.
- Retrieved memories are passed through `MemoryContextBuilder` to the LLM reasoner.
- `AIReasoner` uses the Ollama client to answer memory questions from retrieved context.
- Core regression tests cover retrieval ranking, memory-question detection, and context-builder validation/formatting.

## Still to improve

- Natural-language memory extraction remains rule-based and should handle more varied phrasing.
- Memory conflict resolution needs explicit policies for contradictory facts.
- Memory deletion/forgetting is not yet exposed as a user-facing operation.
- End-to-end evaluation should cover extraction, retrieval, context construction, and reasoning together.
- An API/web interface is still pending.
