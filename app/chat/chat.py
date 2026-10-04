from app.memory.memory import MemoryManager
from app.memory.memory_store import MemoryStore
from app.extractor.extractor import MemoryExtractor
from app.context.context_builder import MemoryContextBuilder
from app.llm.reasoner import AIReasoner
import re


class ChatEngine:

    def __init__(self):
        self.memory = MemoryManager()
        self.memory_store = MemoryStore()
        self.extractor = MemoryExtractor()
        self.context_builder = MemoryContextBuilder(
            max_memories=5
        )
        self.reasoner = AIReasoner()

    def is_memory_question(self, text):
        memory_phrases = [
            "do you remember",
            "what do you remember",
            "what do i like",
            "what do i know",
            "what am i studying",
            "where do i live",
            "what is my goal",
            "what are my goals",
            "what is my favorite",
            "what do you know about me",
            "tell me about myself",
            "about me",
            "what programming languages do i know",
            "what programming language do i know",
            "which programming languages do i know",
            "which programming language do i know",
            "what languages do i know",
            "which languages do i know"
        ]

        text_lower = (
            text
            if text
            else ""
        ).lower().strip()

        if any(
            phrase in text_lower
            for phrase in memory_phrases
        ):
            return True

        keywords = {
            "remember",
            "favorite",
            "likes",
            "like",
            "study",
            "studying",
            "live",
            "goal",
            "goals",
            "skill",
            "skills",
            "programming",
            "language"
        }

        words = set(
            re.findall(
                r"\b\w+\b",
                text_lower
            )
        )

        # -------------------------------------------------
        # PERSONAL STATUS / PERSONAL FACT QUESTIONS
        # -------------------------------------------------

        personal_status_terms = {
            "professional",
            "developer",
            "programmer",
            "student",
            "employee",
            "engineer",
            "skilled",
            "experienced",
            "experience",
            "working",
            "work",
            "studying",
            "studied",
            "study",
            "living",
            "live",
            "job",
            "occupation",
            "profession",
            "degree",
            "education",
            "knowledge",
            "skills",
            "skill",
            "good"
        }

        # Examples:
        #   Do I know Python?
        #   Do I know C?
        #
        # This is intentionally narrower than simply checking
        # for the word "do", so general questions are not captured.

        do_i_know_question = (
            text_lower.startswith(
                "do i know "
            )
            or text_lower == "do i know"
        )

        # Examples:
        #   Do I have a job?
        #   Do I have any skills?
        #   Do I have experience?
        #
        # Do not classify phrases such as:
        #   Do I have to learn Python?
        #   Do I have to use Python?
        #
        # as personal-memory questions.

        do_i_have_question = (
            (
                text_lower.startswith(
                    "do i have "
                )
                or text_lower == "do i have"
            )
            and "to" not in words
            and bool(
                words & personal_status_terms
            )
        )

        # Examples:
        #   Have I studied AI/ML?
        #   Have I learned Python?
        #   Have I worked with Python?

        have_i_question = (
            text_lower.startswith(
                "have i "
            )
            and bool(
                words & personal_status_terms
            )
        )

        # Examples:
        #   Am I a professional developer?
        #   Am I good at Python?
        #   Am I a student?

        am_i_question = (
            text_lower.startswith(
                "am i "
            )
            and bool(
                words & personal_status_terms
            )
        )

        if (
            do_i_know_question
            or do_i_have_question
            or have_i_question
            or am_i_question
        ):
            return True

        # -------------------------------------------------
        # EXISTING MEMORY KEYWORD DETECTION
        # -------------------------------------------------

        return bool(
            words & keywords
        )

    def is_general_question(self, text):
        question_words = {
            "what",
            "why",
            "how",
            "when",
            "where",
            "who",
            "which",
            "can",
            "could",
            "should",
            "would",
            "is",
            "are",
            "does",
            "do"
        }

        request_words = {
            "give",
            "explain",
            "show",
            "write",
            "create",
            "generate",
            "describe",
            "provide",
            "help",
            "list",
            "suggest",
            "teach"
        }

        words = set(
            re.findall(
                r"\b\w+\b",
                text.lower()
            )
        )

        return bool(
            words & (
                question_words |
                request_words
            )
        )

    def generate_response(self, user_message):

        recent_messages = self.memory.get_recent_messages(
            limit=6
        )

        conversation_lines = []

        for message in reversed(
            recent_messages
        ):
            conversation_lines.append(
                f"{message.speaker}: "
                f"{message.message}"
            )

        conversation_context = "\n".join(
            conversation_lines
        )

        if self.is_memory_question(
            user_message
        ):

            results = self.memory_store.semantic_search(
                user_message,
                top_k=3,
                threshold=0.20
            )

            context = self.context_builder.build(
                results,
                user_message
            )

            response = self.reasoner.answer(
                user_question=user_message,
                memory_context=context,
                conversation_context=conversation_context
            )

            return response

        if self.is_general_question(
            user_message
        ):

            response = self.reasoner.answer_general(
                user_question=user_message,
                conversation_context=conversation_context
            )

            return response

        return "I'll remember that."
    def handle_forget_request(self, user_message):
     """
    Detect and execute explicit user requests to forget memories.
    """

     text = (
        user_message
        or ""
    ).strip()

     lower = text.lower()

    # -----------------------------------------
    # Forget everything
    # -----------------------------------------

     all_memory_phrases = [
        "forget everything you remember about me",
        "forget everything about me",
        "forget all my memories",
        "forget everything you know about me",
        "forget what you know about me"
    ]

     if any(
        phrase in lower
        for phrase in all_memory_phrases
    ):

        forgotten = (
            self.memory_store.forget_all_memories(
                subject="User"
            )
        )

        if forgotten:
            return (
                f"I forgot {len(forgotten)} "
                "memories about you."
            )

        return "I don't have any active memories about you."

    # -----------------------------------------
    # Forget location
    # -----------------------------------------

     location_phrases = [
        "forget where i live",
        "forget my location",
        "forget where i am living",
        "forget my city"
    ]

     if any(
        phrase in lower
        for phrase in location_phrases
    ):

        forgotten = (
            self.memory_store.forget_memory(
                subject="User",
                relation="lives_in"
            )
        )

        if forgotten:
            return "I've forgotten where you live."

        return "I don't have an active memory about where you live."

    # -----------------------------------------
    # Forget preferences
    # -----------------------------------------

     like_match = re.match(
        r"^forget that i (?:really )?like (.+?)[.!?]?$",
        text,
        re.IGNORECASE
    )

     if like_match:

        value = like_match.group(1).strip()

        forgotten = (
            self.memory_store.forget_memory(
                subject="User",
                relation="likes",
                value=value
            )
        )

        if forgotten:
            return f"I've forgotten that you like {value}."

        return f"I don't have an active memory that you like {value}."

    # -----------------------------------------
    # Forget love
    # -----------------------------------------

     love_match = re.match(
        r"^forget that i (?:really )?love (.+?)[.!?]?$",
        text,
        re.IGNORECASE
    )

     if love_match:

        value = love_match.group(1).strip()

        forgotten = (
            self.memory_store.forget_memory(
                subject="User",
                relation="loves",
                value=value
            )
        )

        if forgotten:
            return f"I've forgotten that you love {value}."

        return f"I don't have an active memory that you love {value}."

    # -----------------------------------------
    # Forget studies
    # -----------------------------------------

     study_phrases = [
        "forget what i study",
        "forget what i'm studying",
        "forget what i am studying",
        "forget what i learn",
        "forget what i'm learning"
    ]

     if any(
        phrase in lower
        for phrase in study_phrases
    ):

        forgotten = (
            self.memory_store.forget_memory(
                subject="User",
                relation="studies"
            )
        )

        if forgotten:
            return "I've forgotten what you study."

        return "I don't have an active memory about what you study."

    # -----------------------------------------
    # Forget goal
    # -----------------------------------------

     goal_phrases = [
        "forget my goal",
        "forget my goals",
        "forget what i want to achieve"
    ]

     if any(
        phrase in lower
        for phrase in goal_phrases
    ):

        forgotten = (
            self.memory_store.forget_memory(
                subject="User",
                relation="goal"
            )
        )

        if forgotten:
            return "I've forgotten your goal."

        return "I don't have an active memory about your goal."

     return None

    def chat(self):

        print("=" * 50)
        print("       PROJECT ATHENA")
        print("       AI MEMORY ASSISTANT")
        print("=" * 50)
        print("Type 'exit' to quit.")
        print()

        while True:

            user = input(
                "You : "
            ).strip()

            if not user:
                continue

            if user.lower() == "exit":

                print(
                    "\nGoodbye!"
                )

                break

            self.memory.save_message(
                "User",
                user
            )

            memory_data = self.extractor.extract(
                user
            )

            memory_action = None

            if memory_data["save"]:

                result = self.memory_store.save_memory(
                    subject=memory_data["subject"],
                    relation=memory_data["relation"],
                    value=memory_data["value"],
                    category=memory_data["category"],
                    importance=memory_data["importance"]
                )

                memory_action = result["action"]

            response = self.generate_response(
                user
            )

            self.memory.save_message(
                "AI",
                response
            )

            print(
                "\nAI :",
                response
            )

            if memory_action == "created":

                print(
                    "   [Memory saved]"
                )

            elif memory_action == "duplicate":

                print(
                    "   [Duplicate memory ignored]"
                )

            elif memory_action == "updated":

                print(
                    "   [Memory updated]"
                )

            elif memory_action == "updated_embedding":

                print(
                    "   [Memory embedding repaired]"
                )

        self.memory.close()
        self.memory_store.close()