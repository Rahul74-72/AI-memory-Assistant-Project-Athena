class QueryIntent:

    MEMORY = "memory"
    MULTI_MEMORY = "multi_memory"
    PERSONAL_SUMMARY = "personal_summary"
    UNKNOWN = "unknown"


class QueryIntentDetector:

    def detect(self, query):

        query = query.lower().strip()

        # -----------------------------------------
        # Personal summary
        # -----------------------------------------

        summary_phrases = [
            "what do you know about me",
            "what do you remember about me",
            "tell me about myself",
            "tell me what you know about me",
            "what can you tell me about myself"
        ]

        if any(
            phrase in query
            for phrase in summary_phrases
        ):
            return QueryIntent.PERSONAL_SUMMARY

        # -----------------------------------------
        # Multi-memory / preferences
        # -----------------------------------------

        multi_phrases = [
            "what do i like",
            "what are my interests",
            "what are my hobbies",
            "what things do i like",
            "what do i enjoy"
        ]

        if any(
            phrase in query
            for phrase in multi_phrases
        ):
            return QueryIntent.MULTI_MEMORY

        # -----------------------------------------
        # Normal memory question
        # -----------------------------------------

        memory_keywords = [
            "what",
            "where",
            "who",
            "when",
            "which",
            "remember",
            "favorite",
            "like",
            "study",
            "live",
            "goal",
            "skill"
        ]

        if any(
            keyword in query
            for keyword in memory_keywords
        ):
            return QueryIntent.MEMORY

        # -----------------------------------------
        # Unknown
        # -----------------------------------------

        return QueryIntent.UNKNOWN