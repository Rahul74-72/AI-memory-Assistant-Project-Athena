from app.memory.memory_store import MemoryStore


class ContextualMemoryRetriever:

    def __init__(self):

        self.memory_store = MemoryStore()

    # =====================================================
    # CONTEXT KEYWORDS
    # =====================================================

    context_keywords = {

        "programming": {

            "python",
            "c",
            "c++",
            "java",
            "javascript",
            "typescript",
            "programming",
            "coding",
            "software",
            "developer",
            "development"
        },

        "data_science_ai": {

            "data science",
            "machine learning",
            "artificial intelligence",
            "ai/ml",
            "deep learning",
            "nlp",
            "data analysis",
            "data analytics"
        },

        "sports": {

            "volleyball",
            "vollyball",
            "football",
            "cricket",
            "basketball",
            "tennis",
            "badminton",
            "sports",
            "sport"
        }
    }

    # =====================================================
    # DETECT CONTEXT
    # =====================================================

    def detect_context(
        self,
        query,
        conversation_context=None
    ):

        text = query.strip().lower()

        if conversation_context:

            text += " " + (
                conversation_context
                .strip()
                .lower()
            )

        detected_contexts = set()

        for context_name, keywords in (
            self.context_keywords.items()
        ):

            for keyword in keywords:

                if keyword == "c":

                    words = set(
                        text
                        .replace("?", "")
                        .replace(",", "")
                        .replace(".", "")
                        .replace("!", "")
                        .split()
                    )

                    if "c" in words:

                        detected_contexts.add(
                            context_name
                        )

                        break

                    continue

                if (
                    keyword in text
                ):

                    detected_contexts.add(
                        context_name
                    )

                    break

        return detected_contexts

    # =====================================================
    # CALCULATE CONTEXT BONUS
    # =====================================================

    def calculate_context_bonus(
        self,
        memory,
        detected_contexts
    ):

        if not detected_contexts:

            return 0.0

        value = (
            memory.value
            .strip()
            .lower()
        )

        relation = (
            memory.relation
            .strip()
            .lower()
        )

        bonus = 0.0

        # -------------------------------------------------
        # Programming context
        # -------------------------------------------------

        if "programming" in detected_contexts:

            programming_keywords = (
                self.context_keywords[
                    "programming"
                ]
            )

            for keyword in programming_keywords:

                if keyword == "c":

                    if value == "c":

                        bonus += 0.10

                        break

                    continue

                if (
                    keyword in value
                    or keyword in relation
                ):

                    bonus += 0.10

                    break

        # -------------------------------------------------
        # Data Science / AI context
        # -------------------------------------------------

        if "data_science_ai" in detected_contexts:

            ai_keywords = (
                self.context_keywords[
                    "data_science_ai"
                ]
            )

            for keyword in ai_keywords:

                if keyword in value:

                    bonus += 0.10

                    break

        # -------------------------------------------------
        # Sports context
        # -------------------------------------------------

        if "sports" in detected_contexts:

            sports_keywords = (
                self.context_keywords[
                    "sports"
                ]
            )

            for keyword in sports_keywords:

                if keyword in value:

                    bonus += 0.10

                    break

        # -------------------------------------------------
        # Abstraction bonus
        # -------------------------------------------------

        if (
            memory.category
            == "ABSTRACTION"
        ):

            bonus += 0.05

        return bonus

    # =====================================================
    # CONTEXTUAL SEARCH
    # =====================================================

    def search(
        self,
        query,
        conversation_context=None,
        top_k=5,
        threshold=0.20
    ):

        detected_contexts = (
            self.detect_context(
                query=query,
                conversation_context=(
                    conversation_context
                )
            )
        )

        results = (
            self.memory_store.semantic_search(
                query=query,
                top_k=top_k * 2,
                threshold=threshold
            )
        )

        contextual_results = []

        for result in results:

            memory = result[
                "memory"
            ]

            context_bonus = (
                self.calculate_context_bonus(
                    memory=memory,
                    detected_contexts=(
                        detected_contexts
                    )
                )
            )

            contextual_score = (
                result["score"]
                + context_bonus
            )

            contextual_result = (
                dict(result)
            )

            contextual_result[
                "context_bonus"
            ] = context_bonus

            contextual_result[
                "contextual_score"
            ] = contextual_score

            contextual_result[
                "detected_contexts"
            ] = list(
                detected_contexts
            )

            contextual_results.append(
                contextual_result
            )

        # -------------------------------------------------
        # Sort by contextual score
        # -------------------------------------------------

        contextual_results.sort(
            key=lambda item:
                item["contextual_score"],
            reverse=True
        )

        # -------------------------------------------------
        # Select final results
        # -------------------------------------------------

        return contextual_results[
            :top_k
        ]

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.memory_store.close()
