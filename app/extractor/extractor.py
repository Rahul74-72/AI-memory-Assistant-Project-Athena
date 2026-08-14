class MemoryExtractor:

    def extract(self, message):

        text = message.strip()
        lower_text = text.lower()

        # -----------------------------
        # Location
        # -----------------------------

        if lower_text.startswith("i live in "):

            value = text[len("I live in "):].strip()

            if value:

                return {
                    "save": True,
                    "subject": "User",
                    "relation": "lives_in",
                    "value": value,
                    "category": "PERSONAL",
                    "importance": 8
                }

        # -----------------------------
        # Likes
        # -----------------------------

        if lower_text.startswith("i like "):

            value = text[len("I like "):].strip()

            if value:

                return {
                    "save": True,
                    "subject": "User",
                    "relation": "likes",
                    "value": value,
                    "category": "PREFERENCE",
                    "importance": 7
                }

        # -----------------------------
        # Loves
        # -----------------------------

        if lower_text.startswith("i love "):

            value = text[len("I love "):].strip()

            if value:

                return {
                    "save": True,
                    "subject": "User",
                    "relation": "loves",
                    "value": value,
                    "category": "PREFERENCE",
                    "importance": 7
                }

        # -----------------------------
        # Goals
        # -----------------------------

        if lower_text.startswith("i want to "):

            value = text[len("I want to "):].strip()

            if value:

                return {
                    "save": True,
                    "subject": "User",
                    "relation": "goal",
                    "value": value,
                    "category": "GOAL",
                    "importance": 10
                }

        # -----------------------------
        # Project
        # -----------------------------

        if lower_text.startswith("i am building "):

            value = text[len("I am building "):].strip()

            if value:

                return {
                    "save": True,
                    "subject": "User",
                    "relation": "building",
                    "value": value,
                    "category": "PROJECT",
                    "importance": 9
                }
        # -----------------------------
        # Education / Studies
        # -----------------------------

        if lower_text.startswith("i study "):

            value = text[len("I study "):].strip()

            if value:

                return {
                "save": True,
                 "subject": "User",
                 "relation": "studies",
                 "value": value,
                 "category": "EDUCATION",
                 "importance": 9
        }        

        # -----------------------------
        # Nothing important
        # -----------------------------

        return {
            "save": False
        }