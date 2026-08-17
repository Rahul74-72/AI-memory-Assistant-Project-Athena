from app.retrieval.retriever import MemoryRetriever


def test_search_words_removes_punctuation_and_short_tokens():
    assert MemoryRetriever._search_words("What is Rahul's ML plan?") == [
        "what",
        "rahul",
        "plan",
    ]


def test_search_words_handles_empty_or_short_questions():
    assert MemoryRetriever._search_words("a an the") == []


def test_search_words_keeps_meaningful_words():
    assert MemoryRetriever._search_words("machine learning project") == [
        "machine",
        "learning",
        "project",
    ]
