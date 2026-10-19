# Athena Roadmap Status

This note records which roadmap items are already represented in the current implementation so the main README roadmap can be reconciled during the next documentation pass.

## Implemented

- Embedding-based semantic retrieval is used by `ChatEngine` through `MemoryStore.semantic_search()`.
- Retrieved memories are passed through `MemoryContextBuilder` to the LLM reasoner.
- `AIReasoner` uses the Ollama client to answer memory questions from retrieved context.
- Core regression tests cover retrieval ranking, memory-question detection, and context-builder validation/formatting.

## October 2026 local-workspace upgrade

- Authenticated web interface with chat, memory management, pictures, coding and reviewed learning examples.
- Local structured NLP extraction with exact evidence checks and rule-based fallback.
- Owner-required memory stores, conversations, contradiction tools and scoped object APIs.
- Local Whisper transcription, system speech output, and vision model integration.
- MFA, session revocation, bounded uploads, request limits and browser security headers.
- Separate Athena Ollama configuration; private fine-tuning tools and a source-code curriculum draft.
- Windows launcher, consistent backup script and container/server deployment instructions.

## Remaining validation / deployment work

- Larger real-language and speech accuracy evaluation; the small local models are not perfectly reliable.
- Training and acceptance testing of private adapters on sufficient reviewed data; no trained adapter is bundled.
- Per-user model adapter serving if desired. The current model is shared non-personal weights with private retrieval.
- Public-server provisioning, TLS, monitoring, quotas and backup restoration tests on that server.
- SQLite does not implement native RLS. Application ownership checks are covered by regression tests.
- Independent security review before sensitive multi-user internet deployment.

See SECURITY.md, TRAINING.md, and DEPLOYMENT.md for exact boundaries.
