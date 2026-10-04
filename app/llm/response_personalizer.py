class ResponsePersonalizer:

    def __init__(self):

        self.personalization_rules = {

            "python": [
                "Python"
            ],

            "data_science": [
                "data science",
                "machine learning",
                "artificial intelligence",
                "ai/ml",
                "data analysis"
            ],

            "volleyball": [
                "volleyball",
                "vollyball"
            ]
        }

    def detect_personalization(
        self,
        memory_context,
        user_question
    ):

        context = (
            memory_context
            if memory_context
            else ""
        )

        question = (
            user_question
            if user_question
            else ""
        )

        combined_text = (
            context + " " + question
        ).lower()

        instructions = []

        if (
            "python" in combined_text
            and self._is_technically_relevant(question)
        ):

            instructions.append(
                "When providing technical examples, "
                "Python examples may be used because "
                "the user explicitly knows Python."
            )

        if (
            self._contains_any(
                question,
                self.personalization_rules[
                    "data_science"
                ]
            )
            and self._contains_any(
                context,
                self.personalization_rules[
                    "data_science"
                ]
            )
        ):

            instructions.append(
                "When relevant, explain concepts using "
                "data science or machine learning terminology "
                "because the user explicitly studies this area."
            )

        return instructions

    def _is_technically_relevant(
        self,
        question
    ):

        technical_terms = [
            "code",
            "coding",
            "program",
            "programming",
            "python",
            "machine learning",
            "data science",
            "algorithm",
            "function",
            "class",
            "model",
            "api",
            "database"
        ]

        return self._contains_any(
            question,
            technical_terms
        )

    def _contains_any(
        self,
        text,
        terms
    ):

        text = text.lower()

        return any(
            term.lower() in text
            for term in terms
        )