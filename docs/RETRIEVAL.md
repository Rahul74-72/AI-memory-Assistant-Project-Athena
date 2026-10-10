# Athena Memory Retrieval

Athena's retrieval layer turns a natural-language question into a ranked list of active memories.

## Current retrieval flow

1. The question is normalized to lowercase, with underscores treated as spaces.
2. Punctuation is removed and tokens shorter than four characters are ignored.
3. Active memories are loaded from the database.
4. Each memory is searched across `subject`, `relation`, `value`, and `category`.
5. A memory receives a relevance score based on the unique query words it matches, using field weights: subject and relation (3), value (2), category (1).
6. `importance` is the secondary ranking factor.
7. When relevance and importance are both tied, the lower memory ID ranks first, so identical searches return a stable order.
8. An optional non-negative integer limit caps the returned results. A zero limit or a question with no meaningful tokens returns an empty list.

## Example

For a question such as:

`What machine learning project does Rahul like?`

Athena searches meaningful terms such as `what`, `machine`, `learning`, `project`, and `rahul`. A memory matching more highly weighted terms ranks above a memory matching fewer or lower-weighted terms. If two memories have the same relevance score, the more important memory ranks first; if that is also tied, the lower memory ID wins.

## Design notes

The current scorer uses whole-word matching rather than substring matching. This helps avoid accidental matches such as `art` matching `earth`. Invalid question types and invalid limits raise clear exceptions rather than being silently coerced.

The retrieval tests in `tests/test_retriever_tokens.py` and `tests/test_retriever_ranking.py` document the expected tokenization, validation, and ranking behavior. Future improvements can build on this contract when semantic similarity or context-aware retrieval is introduced.
