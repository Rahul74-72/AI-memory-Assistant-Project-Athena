# Athena Memory Retrieval

Athena's retrieval layer turns a natural-language question into a ranked list of active memories.

## Current retrieval flow

1. The question is normalized to lowercase.
2. Punctuation is removed and tokens shorter than four characters are ignored.
3. Active memories are loaded from the database.
4. Each memory is searched across `subject`, `relation`, `value`, and `category`.
5. A memory receives a relevance score based on the number of unique query words it matches.
6. `importance` is used as the secondary ranking factor.
7. The highest-scoring memories are returned first.

## Example

For a question such as:

`What machine learning project does Rahul like?`

Athena searches meaningful terms such as `what`, `machine`, `learning`, `project`, and `rahul`. A memory matching more of those terms ranks above a memory matching fewer terms. If two memories match the same number of terms, the more important memory ranks first.

## Design notes

The current scorer uses whole-word matching rather than substring matching. This helps avoid accidental matches such as `art` matching `earth`.

The retrieval tests in `tests/test_retriever_tokens.py` and `tests/test_retriever_ranking.py` document the expected tokenization and ranking behavior. Future improvements can build on this contract when field-specific weights, semantic similarity, or context-aware retrieval are introduced.
