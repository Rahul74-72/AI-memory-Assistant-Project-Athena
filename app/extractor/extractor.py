import re


class MemoryExtractor:

    def _result(
        self,
        relation,
        value,
        category,
        importance
    ):

        value = value.strip()

        if not value:
            return None

        return {
            "save": True,
            "subject": "User",
            "relation": relation,
            "value": value,
            "category": category,
            "importance": importance
        }

    def _match_value(
        self,
        text,
        patterns
    ):

        for pattern in patterns:

            match = re.match(
                pattern,
                text,
                re.IGNORECASE
            )

            if not match:
                continue

            value = match.group(1).strip()

            if value:
                return value

        return None

    def extract(self, message):

        if not message:
            return {
                "save": False
            }

        text = message.strip()

        if not text:
            return {
                "save": False
            }

        # Remove trailing whitespace but preserve the
        # user's original value text.
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        # =================================================
        # Location
        # =================================================

        value = self._match_value(
            text,
            [

                r"^i\s+live\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+currently\s+live\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+live\s+at\s+(.+?)\s*[.!?]?$",

                r"^i\s+currently\s+live\s+at\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+living\s+in\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+living\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+currently\s+live\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+reside\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+currently\s+reside\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+based\s+in\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+based\s+in\s+(.+?)\s*[.!?]?$"

            ]
        )

        if value:
            return self._result(
                relation="lives_in",
                value=value,
                category="PERSONAL",
                importance=8
            )

        # =================================================
        # Likes
        # =================================================

        value = self._match_value(
            text,
            [

                r"^i\s+like\s+(.+?)\s*[.!?]?$",

                r"^i\s+really\s+like\s+(.+?)\s*[.!?]?$",

                r"^i\s+enjoy\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+interested\s+in\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+interested\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+have\s+an\s+interest\s+in\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+a\s+fan\s+of\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+a\s+fan\s+of\s+(.+?)\s*[.!?]?$"

            ]
        )

        if value:
            return self._result(
                relation="likes",
                value=value,
                category="PREFERENCE",
                importance=7
            )

        # =================================================
        # Loves
        # =================================================

        value = self._match_value(
            text,
            [

                r"^i\s+love\s+(.+?)\s*[.!?]?$",

                r"^i\s+really\s+love\s+(.+?)\s*[.!?]?$",

                r"^i\s+adore\s+(.+?)\s*[.!?]?$"

            ]
        )

        if value:
            return self._result(
                relation="loves",
                value=value,
                category="PREFERENCE",
                importance=7
            )

        # =================================================
        # Goals
        # =================================================

        value = self._match_value(
            text,
            [

                r"^i\s+want\s+to\s+(.+?)\s*[.!?]?$",

                r"^i\s+plan\s+to\s+(.+?)\s*[.!?]?$",

                r"^i\s+aim\s+to\s+(.+?)\s*[.!?]?$",

                r"^i\s+hope\s+to\s+(.+?)\s*[.!?]?$",

                r"^my\s+goal\s+is\s+to\s+(.+?)\s*[.!?]?$",

                r"^my\s+goal\s+is\s+(.+?)\s*[.!?]?$"

            ]
        )

        if value:
            return self._result(
                relation="goal",
                value=value,
                category="GOAL",
                importance=10
            )

        # =================================================
        # Project / Building
        # =================================================

        value = self._match_value(
            text,
            [

                r"^i\s+am\s+building\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+building\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+working\s+on\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+working\s+on\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+developing\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+developing\s+(.+?)\s*[.!?]?$"

            ]
        )

        if value:
            return self._result(
                relation="building",
                value=value,
                category="PROJECT",
                importance=9
            )

        # =================================================
        # Education / Studies
        # =================================================

        value = self._match_value(
            text,
            [

                r"^i\s+study\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+studying\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+studying\s+(.+?)\s*[.!?]?$",

                r"^i\s+currently\s+study\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+currently\s+studying\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+currently\s+studying\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+learning\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+learning\s+(.+?)\s*[.!?]?$",

                r"^i\s+am\s+currently\s+learning\s+(.+?)\s*[.!?]?$",

                r"^i'm\s+currently\s+learning\s+(.+?)\s*[.!?]?$"

            ]
        )

        if value:
            return self._result(
                relation="studies",
                value=value,
                category="EDUCATION",
                importance=9
            )

        # =================================================
        # Nothing important
        # =================================================

        return {
            "save": False
        }