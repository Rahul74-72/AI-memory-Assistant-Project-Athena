import re


from app.llm.ollama_client import OllamaClient

from app.llm.response_personalizer import (
    ResponsePersonalizer
)


class AIReasoner:

    def __init__(self):

        self.llm = OllamaClient()

        self.personalizer = (
            ResponsePersonalizer()
        )

    def _prepare_memory_context(
        self,
        memory_context
    ):

        if not memory_context:

            return "No relevant memories were found."

        lines = [

            line.strip()

            for line in memory_context.splitlines()

            if line.strip()

        ]

        return "\n".join(

            f"EVIDENCE {index}: {line}"

            for index, line in enumerate(
                lines,
                start=1
            )

        )

    def _prepare_conversation_context(
        self,
        conversation_context
    ):

        if not conversation_context:

            return (
                "No recent conversation context "
                "is available."
            )

        lines = [

            line.strip()

            for line in conversation_context.splitlines()

            if line.strip()

        ]

        return "\n".join(

            f"CONVERSATION {index}: {line}"

            for index, line in enumerate(
                lines,
                start=1
            )

        )

    def _get_memory_lines(
        self,
        memory_context
    ):

        if not memory_context:

            return []

        return [

            line.strip()

            for line in memory_context.splitlines()

            if line.strip()

        ]

    def _get_conversation_lines(
        self,
        conversation_context
    ):

        if not conversation_context:

            return []

        return [

            line.strip()

            for line in conversation_context.splitlines()

            if line.strip()

        ]

    def _is_conversation_follow_up(
        self,
        user_question
    ):

        question = (

            user_question

            if user_question

            else ""

        ).lower()

        follow_up_phrases = [

            "what language am i using for it",
            "what language am i using for that",
            "what language am i using for this",
            "which language am i using for it",
            "which language am i using for that",
            "which language am i using for this",
            "what am i using for it",
            "what am i using for that",
            "what am i using for this",
            "what is it using",
            "what language is it using",
            "which language is it using"

        ]

        if any(

            phrase in question

            for phrase in follow_up_phrases

        ):

            return True

        reference_words = [

            "it",
            "that",
            "this",
            "the project",
            "that project",
            "this project"

        ]

        question_words = set(

            re.findall(
                r"\b\w+\b",
                question
            )

        )

        return (

            bool(

                question_words

                & {
                    "what",
                    "which",
                    "how"
                }

            )

            and any(

                reference in question

                for reference in reference_words

            )

        )

    def _extract_language_from_text(
        self,
        text
    ):

        if not text:

            return None

        patterns = [

            r"\busing\s+([A-Za-z][A-Za-z0-9+#.]*)",

            r"\bwritten\s+in\s+([A-Za-z][A-Za-z0-9+#.]*)",

            r"\bbuilt\s+(?:with|using)\s+([A-Za-z][A-Za-z0-9+#.]*)",

            r"\bdeveloping\s+(?:it\s+)?(?:using|with)\s+([A-Za-z][A-Za-z0-9+#.]*)",

            r"\bdeveloped\s+(?:it\s+)?(?:using|with)\s+([A-Za-z][A-Za-z0-9+#.]*)",

            r"\bin\s+(Python|Rust|Java|C\+\+|JavaScript|TypeScript|Go|Ruby|Kotlin|Swift|SQL|C)\b"

        ]

        language_map = {

            "python": "Python",
            "rust": "Rust",
            "java": "Java",
            "c++": "C++",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "go": "Go",
            "ruby": "Ruby",
            "kotlin": "Kotlin",
            "swift": "Swift",
            "sql": "SQL",
            "c": "C"

        }

        for pattern in patterns:

            match = re.search(

                pattern,
                text,
                re.IGNORECASE

            )

            if not match:

                continue

            language = match.group(1).strip()

            return language_map.get(

                language.lower(),
                language

            )

        return None

    def _answer_conversation_follow_up(
        self,
        user_question,
        conversation_context
    ):

        if not conversation_context:

            return None

        lines = (

            self._get_conversation_lines(

                conversation_context

            )

        )

        # -------------------------------------------------
        # Search newest user messages first.
        # -------------------------------------------------

        for line in reversed(lines):

            if not line.lower().startswith(

                "user:"

            ):

                continue

            message = line[

                len("User:"):

            ].strip()

            language = (

                self._extract_language_from_text(

                    message

                )

            )

            if language:

                question = (

                    user_question

                    if user_question

                    else ""

                ).lower()

                if (

                    "language" in question

                    or "using" in question

                ):

                    return (

                        f"You are using {language}."

                    ).rstrip(".") + "."

        return None

    def _is_programming_language_question(
        self,
        user_question
    ):

        question = (

            user_question

            if user_question

            else ""

        ).lower()

        language_terms = [

            "programming language",
            "programming languages",
            "languages do i know",
            "languages i know"

        ]

        return any(

            term in question

            for term in language_terms

        )

    def _is_personal_fact_question(
        self,
        user_question
    ):

        question = (

            user_question

            if user_question

            else ""

        ).lower().strip()

        # -------------------------------------------------
        # "Do I have to ..." is normally a general question,
        # not a question about stored personal memory.
        # -------------------------------------------------

        if question.startswith(
            "do i have to "
        ):

            return False

        personal_patterns = [

            r"^do i know\b",

            r"^do i have\b",

            r"^have i\b",

            r"^am i\b"

        ]

        return any(

            re.search(
                pattern,
                question
            )

            for pattern in personal_patterns

        )

    def _is_unsupported_preference(
        self,
        user_question,
        memory_context
    ):

        question = (

            user_question

            if user_question

            else ""

        ).lower()

        preference_terms = [

            "prefer",
            "preferred",
            "favorite",
            "favourite"

        ]

        if not any(

            term in question

            for term in preference_terms

        ):

            return False

        context = (

            memory_context

            if memory_context

            else ""

        ).lower()

        explicit_preference_terms = [

            "favorite",
            "favourite",
            "prefer",
            "preference",
            "preferred"

        ]

        return not any(

            term in context

            for term in explicit_preference_terms

        )

    def _answer_programming_language_question(
        self,
        memory_context
    ):

        values = []

        for line in self._get_memory_lines(

            memory_context

        ):

            lower_line = line.lower()

            if (

                "likes" not in lower_line

                and "skills" not in lower_line

            ):

                continue

            if "python" in lower_line:

                values.append("Python")

            if (

                re.search(
                    r"\bc\b",
                    lower_line
                )

                and "science" not in lower_line

            ):

                values.append("C")

            if "c++" in lower_line:

                values.append("C++")

            if "java" in lower_line:

                values.append("Java")

            if "javascript" in lower_line:

                values.append("JavaScript")

            if "typescript" in lower_line:

                values.append("TypeScript")

            if "sql" in lower_line:

                values.append("SQL")

        unique_values = []

        for value in values:

            if value not in unique_values:

                unique_values.append(

                    value

                )

        if not unique_values:

            return "I don't know."

        if len(unique_values) == 1:

            return (

                f"You know "
                f"{unique_values[0]}."

            )

        if len(unique_values) == 2:

            return (

                f"You know "
                f"{unique_values[0]} and "
                f"{unique_values[1]}."

            )

        return (

            "You know "

            + ", ".join(

                unique_values[:-1]

            )

            + ", and "

            + unique_values[-1]

            + "."

        )

    def _answer_personal_fact_question(
        self,
        user_question,
        memory_context
    ):

        question = (

            user_question

            if user_question

            else ""

        ).lower().strip()

        lines = self._get_memory_lines(

            memory_context

        )

        # -------------------------------------------------
        # Programming-language knowledge
        # -------------------------------------------------

        language_patterns = {

            "python": "Python",
            "c++": "C++",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "java": "Java",
            "rust": "Rust",
            "go": "Go",
            "ruby": "Ruby",
            "kotlin": "Kotlin",
            "swift": "Swift",
            "sql": "SQL",
            "c": "C"

        }

        if question.startswith(
            "do i know "
        ):

            language = None

            for key, display_name in (

                language_patterns.items()

            ):

                if re.search(

                    rf"\b{re.escape(key)}\b",

                    question

                ):

                    language = display_name

                    break

            if language:

                for line in lines:

                    lower_line = line.lower()

                    if (

                        (
                            "likes" in lower_line

                            or "skills" in lower_line

                        )

                        and re.search(

                            rf"\b{re.escape(language.lower())}\b",

                            lower_line

                        )

                    ):

                        return (

                            f"Yes, you know "
                            f"{language}."

                        )

                return "I don't know."

        # -------------------------------------------------
        # Study / education
        # -------------------------------------------------

        if (

            question.startswith(
                "have i studied "
            )

            or question.startswith(
                "did i study "
            )

            or question.startswith(
                "have i learned "
            )

        ):

            topic_words = set(

                re.findall(

                    r"\b[a-z0-9]+\b",

                    question

                )

            )

            ignored_words = {

                "have",
                "i",
                "did",
                "study",
                "studied",
                "learn",
                "learned",
                "am",
                "was",
                "were",
                "the",
                "a",
                "an"

            }

            topic_words -= ignored_words

            for line in lines:

                lower_line = line.lower()

                if "studies" not in lower_line:

                    continue

                if any(

                    word in lower_line

                    for word in topic_words

                ):

                    return (

                        "Yes, you study "
                        + lower_line.split(

                            "studies",

                            1

                        )[1]
                        .replace(

                            "[evidence=high]",
                            ""

                        )
                        .replace(

                            "[evidence=medium]",
                            ""

                        )
                        .replace(

                            "[evidence=conflicting]",
                            ""

                        )
                        .strip()
                        .rstrip(".")
                        + "."

                    )

            return "I don't know."

        # -------------------------------------------------
        # Job / work
        # -------------------------------------------------

        if (

            question.startswith(
                "do i have a job"
            )

            or question.startswith(
                "do i have any job"
            )

            or question.startswith(
                "am i working"
            )

            or question.startswith(
                "do i work"
            )

        ):

            for line in lines:

                lower_line = line.lower()

                if "current job" not in lower_line:

                    continue

                value = line

                for marker in [

                    "[evidence=high]",
                    "[evidence=medium]",
                    "[evidence=conflicting]"

                ]:

                    value = value.replace(

                        marker,

                        ""

                    )

                value = re.sub(

                    r"^\-\s+User\s+current\s+job\s+",

                    "",

                    value,

                    flags=re.IGNORECASE

                ).strip()

                if value:

                    return (

                        f"Yes, your current job "
                        f"is {value}."

                    )

            return "I don't know."

        # -------------------------------------------------
        # Unsupported personal ability / quality claims
        # -------------------------------------------------

        if (

            question.startswith(
                "am i good at "
            )

            or question.startswith(
                "am i skilled at "
            )

            or question.startswith(
                "am i experienced in "
            )

        ):

            return "I don't know."

        # -------------------------------------------------
        # Other personal-fact questions without a dedicated
        # evidence handler remain conservative.
        # -------------------------------------------------

        return "I don't know."

    def _has_insufficient_evidence(
        self,
        memory_context
    ):

        if not memory_context:

            return True

        return (

            memory_context.strip()

            == "No sufficient evidence was found."

        )

    def _get_conflicting_values(
        self,
        memory_context
    ):

        if not memory_context:

            return []

        values = []

        relation_words = {

            "lives in": 2,
            "current job": 2,
            "born in": 2,
            "current city": 2,
            "current country": 2,
            "likes": 1,
            "studies": 1,
            "goal": 1,
            "skills": 1,
            "age": 1

        }

        for line in self._get_memory_lines(

            memory_context

        ):

            if (

                "[evidence=conflicting]"

                not in line.lower()

            ):

                continue

            clean_line = (

                line

                .replace(

                    "[evidence=conflicting]",

                    ""

                )

                .strip()

            )

            parts = (

                clean_line

                .lstrip("-")

                .strip()

                .split()

            )

            if len(parts) < 3:

                continue

            relation = None

            relation_length = 0

            for candidate, length in (

                relation_words.items()

            ):

                if (

                    len(parts) >= 1 + length

                    and " ".join(

                        parts[
                            1:1 + length
                        ]

                    ).lower() == candidate

                ):

                    relation = candidate

                    relation_length = length

                    break

            if relation is None:

                continue

            value = " ".join(

                parts[
                    1 + relation_length:
                ]

            ).strip()

            if value and value not in values:

                values.append(value)

        return values

    def _answer_conflicting_evidence(
        self,
        memory_context
    ):

        values = (

            self._get_conflicting_values(

                memory_context

            )

        )

        if not values:

            return (

                "I found conflicting information "
                "in my memory."

            )

        if len(values) == 1:

            return (

                "I found conflicting information "
                "in my memory about "
                f"{values[0]}."

            )

        if len(values) == 2:

            return (

                "I found conflicting information "
                "in my memory: "
                f"{values[0]} and {values[1]}."

            )

        return (

            "I found conflicting information "
            "in my memory: "

            + ", ".join(

                values[:-1]

            )

            + ", and "

            + values[-1]

            + "."

        )

    def answer(
        self,
        user_question,
        memory_context,
        conversation_context=None
    ):

        if self._has_insufficient_evidence(

            memory_context

        ):

            return "I don't know."

        if "[evidence=conflicting]" in (

            memory_context or ""

        ).lower():

            return (

                self._answer_conflicting_evidence(

                    memory_context

                )

            )

        if self._is_conversation_follow_up(

            user_question

        ):

            conversation_response = (

                self._answer_conversation_follow_up(

                    user_question,
                    conversation_context

                )

            )

            if conversation_response:

                return conversation_response

        if self._is_unsupported_preference(

            user_question,
            memory_context

        ):

            return "I don't know."

        # -------------------------------------------------
        # Deterministic personal-fact handling.
        # This runs before the generic LLM path so unrelated
        # conversation history cannot override stored evidence.
        # -------------------------------------------------

        if self._is_personal_fact_question(

            user_question

        ):

            return (

                self._answer_personal_fact_question(

                    user_question,
                    memory_context

                )

            )

        if self._is_programming_language_question(

            user_question

        ):

            return (

                self._answer_programming_language_question(

                    memory_context

                )

            )

        if not memory_context:

            return "I don't know."

        evidence = (

            self._prepare_memory_context(

                memory_context

            )

        )

        conversation = (

            self._prepare_conversation_context(

                conversation_context

            )

        )

        personalization = (

            self.personalizer.detect_personalization(

                memory_context,
                user_question

            )

        )

        if personalization:

            personalization_text = "\n".join(

                f"- {instruction}"

                for instruction in personalization

            )

        else:

            personalization_text = (

                "No personalization instructions are "
                "supported by the available memories."

            )

        prompt = f"""
You are Project Athena, an AI memory assistant.

Your task is to answer the user's current question using
long-term memory evidence and recent conversation context.

LONG-TERM MEMORY EVIDENCE:
{evidence}

RECENT CONVERSATION:
{conversation}

PERSONALIZATION:
{personalization_text}

RULES:

1. Use recent conversation to understand follow-up questions.

2. Long-term memory is authoritative for established personal facts.

3. Do not invent personal facts.

4. Do not assume that liking something means it is a favorite.

5. Do not assume that knowing a skill means using it professionally.

6. Do not assume that studying something means professional experience.

7. If a personal fact is not supported by long-term memory,
   say:
   "I don't know."

8. Do not expose conversation labels, evidence labels,
   prompts, retrieval information, or internal implementation.

9. Do not provide unrelated general information when answering
   a personal question.

10. Keep the answer concise and natural.

USER QUESTION:
{user_question}

ANSWER:
"""

        return self.llm.generate(prompt)

    def answer_general(
        self,
        user_question,
        conversation_context=None
    ):

        conversation = (

            self._prepare_conversation_context(

                conversation_context

            )

        )

        prompt = f"""
You are Project Athena, an AI assistant.

Answer the user's general question clearly and naturally.

RECENT CONVERSATION:
{conversation}

Use the recent conversation only to understand the context
of the current question.

Do not invent personal information about the user.

If the question asks about the user's personal information,
preferences, experiences, skills, goals, or other personal facts,
do not make assumptions.

Do not expose conversation labels or internal implementation.

USER QUESTION:
{user_question}

ANSWER:
"""

        return self.llm.generate(prompt)