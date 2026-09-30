from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryAbstraction:

    def __init__(self):

        self.session = SessionLocal()

        # =================================================
        # ABSTRACTION GROUPS
        # =================================================

        self.abstraction_groups = {

            "programming": {

                "keywords": {

                    "python",

                    "c",

                    "c++",

                    "java",

                    "javascript",

                    "typescript",

                    "sql",

                    "programming",

                    "coding",

                    "software",

                    "developer",

                    "development"
                }
            },

            "data_science_ai": {

                "keywords": {

                    "data science",

                    "machine learning",

                    "artificial intelligence",

                    "ai/ml",

                    "deep learning",

                    "nlp",

                    "data analysis",

                    "data analytics"
                }
            },

            "sports": {

                "keywords": {

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
        }

    # =====================================================
    # GET ACTIVE MEMORIES
    # =====================================================

    def get_active_memories(
        self,
        limit=100
    ):

        stmt = (
            select(Memory)
            .where(
                Memory.active.is_(True)
            )
            .order_by(
                Memory.id
            )
            .limit(limit)
        )

        return (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

    # =====================================================
    # CLASSIFY MEMORY
    # =====================================================

    def classify_memory(
        self,
        memory
    ):

        value = (
            memory.value
            .strip()
            .lower()
        )

        classifications = []

        for group_name, rules in (
            self.abstraction_groups.items()
        ):

            for keyword in rules[
                "keywords"
            ]:

                if keyword == "c":

                    if value == "c":

                        classifications.append(
                            group_name
                        )

                        break

                    continue

                if (
                    value == keyword
                    or keyword in value
                ):

                    classifications.append(
                        group_name
                    )

                    break

        return classifications

    # =====================================================
    # GROUP MEMORIES
    # =====================================================

    def group_memories(
        self,
        memories
    ):

        groups = {}

        for memory in memories:

            classifications = (
                self.classify_memory(
                    memory
                )
            )

            for group_name in classifications:

                if group_name not in groups:

                    groups[group_name] = []

                groups[group_name].append(
                    memory
                )

        return groups

    # =====================================================
    # FIND ABSTRACTION CANDIDATES
    # =====================================================

    def find_candidates(
        self,
        limit=100
    ):

        memories = self.get_active_memories(
            limit=limit
        )

        groups = self.group_memories(
            memories
        )

        candidates = []

        for group_name, group in groups.items():

            unique_memories = {}

            for memory in group:

                unique_memories[
                    memory.id
                ] = memory

            group = list(
                unique_memories.values()
            )

            if len(group) < 2:

                continue

            candidates.append({

                "group": group_name,

                "memories": group,

                "memory_count": len(group),

                "action":
                    "abstraction_candidate"
            })

        return candidates

    # =====================================================
    # BUILD ABSTRACTION
    # =====================================================

    def build_abstraction(
        self,
        candidate
    ):

        group_name = candidate[
            "group"
        ]

        values = []

        for memory in candidate[
            "memories"
        ]:

            values.append(
                memory.value
            )

        abstraction_text = (
            "User shows interest or "
            "experience in "
            f"{group_name.replace('_', ' ')}."
        )

        return {

            "group": group_name,

            "memory_count":
                candidate[
                    "memory_count"
                ],

            "values": values,

            "abstraction":
                abstraction_text,

            "action":
                "review_required"
        }

    # =====================================================
    # CREATE ABSTRACTION
    # =====================================================

    def create_abstraction(
        self,
        candidate
    ):

        abstraction = (
            self.build_abstraction(
                candidate
            )
        )

        group_name = abstraction[
            "group"
        ]

        value = abstraction[
            "abstraction"
        ]

        # -------------------------------------------------
        # Prevent duplicate abstractions
        # -------------------------------------------------

        stmt = (
            select(Memory)
            .where(
                Memory.subject == "User",
                Memory.relation == (
                    "abstract_" + group_name
                ),
                Memory.value == value,
                Memory.active.is_(True)
            )
        )

        existing = (
            self.session.execute(stmt)
            .scalars()
            .first()
        )

        if existing:

            return {

                "action": "duplicate",

                "memory": existing
            }

        # -------------------------------------------------
        # Create abstraction memory
        # -------------------------------------------------

        memory = Memory(

            subject="User",

            relation=(
                "abstract_" + group_name
            ),

            value=value,

            category="ABSTRACTION",

            importance=6,

            active=True
        )

        self.session.add(
            memory
        )

        self.session.commit()

        return {

            "action": "created",

            "memory": memory
        }

    # =====================================================
    # GET SUMMARY
    # =====================================================

    def summarize(
        self,
        limit=100
    ):

        candidates = self.find_candidates(
            limit=limit
        )

        abstractions = []

        for candidate in candidates:

            abstractions.append(
                self.build_abstraction(
                    candidate
                )
            )

        return {

            "candidate_count":
                len(candidates),

            "candidates":
                abstractions
        }

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.session.close()
