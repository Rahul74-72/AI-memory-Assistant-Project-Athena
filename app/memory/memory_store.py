from datetime import datetime

from sqlalchemy import select
from app.settings import require_user_id

from app.memory.importance_calibrator import ImportanceCalibrator
from app.memory.memory_decay import MemoryDecay
from app.memory.memory_reinforcement import MemoryReinforcement
from app.memory.memory_lifecycle import MemoryLifecycle
from app.memory.adaptive_prioritization import (
    AdaptiveMemoryPrioritization
)
from app.embeddings.embedding_manager import EmbeddingManager
from app.embeddings.memory_text import memory_to_text
from app.database.database import SessionLocal
from app.database.models import Memory


class MemoryStore:

    def __init__(self, user_id):
        self.user_id = require_user_id(user_id)
        self.session = SessionLocal()
        self.importance_calibrator = ImportanceCalibrator()
        self.embedding_manager = EmbeddingManager()
        self.memory_decay = MemoryDecay()
        self.memory_reinforcement = MemoryReinforcement()
        self.memory_lifecycle = MemoryLifecycle()
        # Adaptive prioritization reads Memory rows directly, so it must use
        # the same tenant scope as this store.
        self.adaptive_prioritization = AdaptiveMemoryPrioritization(
            user_id=user_id
        )

    def _owner_filter(self):
        require_user_id(self.user_id)
        return Memory.user_id == self.user_id

    # =====================================================
    # SAVE / UPDATE MEMORY
    # =====================================================

    def save_memory(
        self,
        subject,
        relation,
        value,
        category,
        importance=5,
        valid_from=None,
    ):
        single_value_relations = {
            "lives_in",
            "current_job",
            "age",
            "born_in",
            "current_city",
            "current_country"
        }

        # Validate the supplied validity timestamp
        if valid_from is not None:
            if not isinstance(valid_from, datetime):
                raise TypeError(
                    "valid_from must be a datetime or None"
                )

            if valid_from.tzinfo is not None:
                raise ValueError(
                    "valid_from must be a timezone-naive UTC datetime"
                )

        recorded_at = datetime.utcnow()
        fact_valid_from = (
            valid_from
            if valid_from is not None
            else recorded_at
        )

        # Calibrate importance
        importance = self.importance_calibrator.calibrate(
            relation=relation,
            value=value,
            importance=importance
        )

        # Create natural-language memory representation
        memory_text = memory_to_text(
            subject,
            relation,
            value
        )

        # Create embedding
        embedding = self.embedding_manager.create_embedding(
            memory_text
        )
        embedding_json = self.embedding_manager.serialize(
            embedding
        )

        # Find existing active memories for this subject/relation
        stmt = select(Memory).where(
            self._owner_filter(),
Memory.subject == subject,
            Memory.relation == relation,
            Memory.active.is_(True)
        )
        existing_memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        normalized_value = value.strip().lower()

        # Reject a replacement that predates the current fact
        if (
            relation in single_value_relations
            and existing_memories
            and not any(
                memory.value.strip().lower() == normalized_value
                for memory in existing_memories
            )
        ):
            existing_valid_from = [
                memory.valid_from
                for memory in existing_memories
                if memory.valid_from is not None
            ]

            if existing_valid_from:
                latest_valid_from = max(existing_valid_from)

                if fact_valid_from < latest_valid_from:
                    raise ValueError(
                        "A replacement memory cannot start before "
                        "the current fact's validity start"
                    )

        # -------------------------------------------------
        # Multi-value relation
        # -------------------------------------------------
        if relation not in single_value_relations:
            for memory in existing_memories:
                if memory.value.strip().lower() == normalized_value:
                    if not memory.embedding:
                        memory.embedding = embedding_json
                        memory.updated_at = recorded_at
                        self._commit()

                        return {
                            "action": "updated_embedding",
                            "memory": memory
                        }

                    return {
                        "action": "duplicate",
                        "memory": memory
                    }

            memory = Memory(

                user_id=self.user_id,
                subject=subject,
                relation=relation,
                value=value,
                category=category,
                importance=importance,
                active=True,
                lifecycle_state="active",
                archive_reason=None,
                embedding=embedding_json,
                valid_from=fact_valid_from,
                valid_to=None
            )

            self.session.add(memory)
            self._commit()

            return {
                "action": "created",
                "memory": memory
            }

        # -------------------------------------------------
        # Single-value relation
        # -------------------------------------------------
        matching_memories = [
            memory
            for memory in existing_memories
            if memory.value.strip().lower() == normalized_value
        ]

        # -------------------------------------------------
        # Same value already exists
        # -------------------------------------------------
        if matching_memories:
            current_memory = max(
                matching_memories,
                key=lambda memory: (
                    memory.updated_at or datetime.min
                )
            )
            archived_count = 0

            # Archive conflicting active values
            for memory in existing_memories:
                if memory.id == current_memory.id:
                    continue

                memory.active = False
                memory.lifecycle_state = "archived"
                memory.archive_reason = "replaced"
                memory.updated_at = recorded_at

                if memory.valid_to is None:
                    memory.valid_to = fact_valid_from

                archived_count += 1

            # Refresh metadata without resetting validity dates
            current_memory.category = category
            current_memory.importance = importance
            current_memory.embedding = embedding_json
            current_memory.active = True
            current_memory.lifecycle_state = "active"
            current_memory.updated_at = recorded_at

            self._commit()

            return {
                "action": "duplicate",
                "memory": current_memory,
                "archived_count": archived_count
            }

        # -------------------------------------------------
        # New value: archive old versions and create a new row
        # -------------------------------------------------
        if existing_memories:
            previous_memory = max(
                existing_memories,
                key=lambda memory: (
                    memory.updated_at or datetime.min
                )
            )
            old_value = previous_memory.value
            archived_count = 0

            for memory in existing_memories:
                memory.active = False
                memory.lifecycle_state = "archived"
                memory.archive_reason = "replaced"
                memory.updated_at = recorded_at

                if memory.valid_to is None:
                    memory.valid_to = fact_valid_from

                archived_count += 1

            new_memory = Memory(

                user_id=self.user_id,
                subject=subject,
                relation=relation,
                value=value,
                category=category,
                importance=importance,
                active=True,
                lifecycle_state="active",
                archive_reason=None,
                embedding=embedding_json,
                valid_from=fact_valid_from,
                valid_to=None
            )

            self.session.add(new_memory)
            self._commit()

            return {
                "action": "updated",
                "memory": new_memory,
                "old_value": old_value,
                "archived_count": archived_count
            }

        # -------------------------------------------------
        # First value for this relation
        # -------------------------------------------------
        new_memory = Memory(
            user_id=self.user_id,
            subject=subject,
            relation=relation,
            value=value,
            category=category,
            importance=importance,
            active=True,
            lifecycle_state="active",
            archive_reason=None,
            embedding=embedding_json,
            valid_from=fact_valid_from,
            valid_to=None
        )

        self.session.add(new_memory)
        self._commit()

        return {
            "action": "created",
            "memory": new_memory
        }


    # =====================================================
    # INTELLIGENT SEMANTIC SEARCH
    # =====================================================

    # =====================================================
    # MULTI-MEMORY RETRIEVAL
    # =====================================================


    # =====================================================
    # GET ALL MEMORIES
    # =====================================================


    # =====================================================
    # CLOSE
    # =====================================================


    def forget_memory(
    self,
    subject="User",
    relation=None,
    value=None
):
     """
    Forget matching active long-term memories.

    Forgotten memories are retained as archived history
    but are no longer active or retrievable.
    """

     stmt = select(Memory).where(
        self._owner_filter(),
Memory.subject == subject,
        Memory.active.is_(True)
    )

     if relation is not None:
        stmt = stmt.where(
            Memory.relation == relation
        )

     memories = (
        self.session.execute(stmt)
        .scalars()
        .all()
    )

     normalized_value = (
        value.strip().lower()
        if value is not None
        else None
    )

     forgotten = []

     for memory in memories:

        if (
            normalized_value is not None
            and memory.value.strip().lower()
            != normalized_value
        ):
            continue

        memory.active = False
        memory.lifecycle_state = "archived"
        memory.archive_reason = "forgotten"
        memory.updated_at = datetime.utcnow()

        forgotten.append(memory)

     if forgotten:
        self._commit()

     return forgotten


    def forget_all_memories(self, subject="User"):
        """
    Forget all active long-term memories for a subject.
    """

        stmt = select(Memory).where(
        self._owner_filter(),
Memory.subject == subject,
        Memory.active.is_(True)
    )

        memories = (
        self.session.execute(stmt)
        .scalars()
        .all()
    )

        for memory in memories:

            memory.active = False
            memory.lifecycle_state = "archived"
            memory.archive_reason = "forgotten"
            memory.updated_at = datetime.utcnow()

        if memories:
            self._commit()

        return memories
    # =====================================================
    # INTELLIGENT SEMANTIC SEARCH
    # =====================================================

    def semantic_search(
        self,
        query,
        top_k=5,
        threshold=0.20
    ):

        # -----------------------------------------
        # Create query embedding
        # -----------------------------------------

        query_embedding = (
            self.embedding_manager.create_embedding(
                query
            )
        )

        # -----------------------------------------
        # Get active memories
        # -----------------------------------------

        stmt = select(Memory).where(
            self._owner_filter(),
Memory.active.is_(True)
        )

        memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        results = []

        query_lower = query.lower().strip()

        # -----------------------------------------
        # Detect likely relation
        # -----------------------------------------

        relation_keywords = {

            "lives_in": [
                "live",
                "lives",
                "living",
                "reside",
                "residence",
                "city",
                "location",
                "where do i live"
            ],

            "likes": [
                "like",
                "likes",
                "favorite",
                "favourite",
                "enjoy",
                "interest",
                "interests",
                "what do i like"
            ],

            "studies": [
                "study",
                "studies",
                "studying",
                "education",
                "learn",
                "learning",
                "subject",
                "what do i study"
            ],

            "current_job": [
                "job",
                "work",
                "working",
                "profession",
                "occupation"
            ],

            "goal": [
                "goal",
                "goals",
                "what is my goal",
                "what are my goals",
                "want to achieve",
                "aim",
                "aims"
            ],

            "skills": [
                "skill",
                "skills",
                "good at",
                "know"
            ]
        }

        detected_relations = set()

        # -----------------------------------------
        # Normalize query
        # -----------------------------------------

        query_words = set(
            query_lower
            .replace("?", "")
            .replace(",", "")
            .replace(".", "")
            .replace("!", "")
            .split()
        )

        # -----------------------------------------
        # Detect relations
        # -----------------------------------------

        for relation, keywords in relation_keywords.items():

            for keyword in keywords:

                keyword_lower = keyword.lower()

                # Multi-word phrase

                if " " in keyword_lower:

                    if keyword_lower in query_lower:

                        detected_relations.add(
                            relation
                        )

                        break

                # Single-word keyword

                elif keyword_lower in query_words:

                    detected_relations.add(
                        relation
                    )

                    break

        # -----------------------------------------
        # Keep only relations that exist in memory
        # -----------------------------------------

        available_relations = {

            memory.relation

            for memory in memories
        }

        detected_relations = (
            detected_relations
            & available_relations
        )

        # -----------------------------------------
        # Detect latest memories
        # -----------------------------------------

        single_value_relations = {

            "lives_in",

            "current_job",

            "age",

            "born_in",

            "current_city",

            "current_country"
        }

        latest_memories = {}
        latest_timestamps = {}
        ambiguous_latest_keys = set()
        unknown_timestamp_keys = set()

        for memory in memories:
            if memory.relation not in single_value_relations:
                continue

            key = (memory.subject, memory.relation)
            timestamp = memory.updated_at

            if timestamp is None:
                unknown_timestamp_keys.add(key)
                continue

            if key in unknown_timestamp_keys:
                continue

            current_timestamp = latest_timestamps.get(key)

            if current_timestamp is None or timestamp > current_timestamp:
                latest_memories[key] = memory
                latest_timestamps[key] = timestamp
                ambiguous_latest_keys.discard(key)

            elif timestamp == current_timestamp:
                latest_memories.pop(key, None)
                latest_timestamps.pop(key, None)
                ambiguous_latest_keys.add(key)

        # -----------------------------------------
        # Score memories
        # -----------------------------------------

        now = datetime.utcnow()

        lifecycle_changed = False

        for memory in memories:

            # Skip archived memories

            if (
                memory.lifecycle_state
                == "archived"
            ):

                continue

            # Skip memories without embeddings

            if not memory.embedding:

                continue

            # -------------------------------------
            # Relation filtering
            # -------------------------------------

            if (
                detected_relations
                and memory.relation not in detected_relations
            ):

                continue

            memory_embedding = (
                self.embedding_manager.deserialize(
                    memory.embedding
                )
            )

            # -------------------------------------
            # Semantic similarity
            # -------------------------------------

            similarity = (
                self.embedding_manager.similarity(
                    query_embedding,
                    memory_embedding
                )
            )

            # -------------------------------------
            # Relation bonus
            # -------------------------------------

            relation_bonus = 0.0

            if memory.relation in detected_relations:

                relation_bonus = 0.25

            # -------------------------------------
            # Importance + decay
            # -------------------------------------

            effective_importance = (
                self.memory_decay.calculate_effective_importance(
                    importance=memory.importance,
                    relation=memory.relation,
                    updated_at=memory.updated_at,
                    current_time=now
                )
            )

            importance_bonus = (
                effective_importance / 10
            ) * 0.05

            # -------------------------------------
            # Reinforcement
            # -------------------------------------

            reinforcement = (
                self.memory_reinforcement.calculate_reinforcement(
                    retrieval_count=memory.retrieval_count,
                    last_retrieved_at=memory.last_retrieved_at,
                    current_time=now
                )
            )

            # -------------------------------------
            # Adaptive priority
            # -------------------------------------

            adaptive_priority = (
                self.adaptive_prioritization.calculate_priority(
                    memory=memory,
                    current_time=now
                )
            )

            adaptive_bonus = (
                min(
                    adaptive_priority,
                    1.0
                )
                * 0.05
            )

            # -------------------------------------
            # Lifecycle
            # -------------------------------------

            lifecycle_state = (
                self.memory_lifecycle.determine_state(
                    memory=memory,
                    effective_importance=effective_importance,
                    reinforcement=reinforcement,
                    current_time=now
                )
            )

            if (
                memory.lifecycle_state
                != lifecycle_state
            ):

                memory.lifecycle_state = (
                    lifecycle_state
                )

                lifecycle_changed = True

            # -------------------------------------
            # Archived memories
            # -------------------------------------

            if lifecycle_state == "archived":

                continue

            # -------------------------------------
            # Weakened memory penalty
            # -------------------------------------

            lifecycle_penalty = 0.0

            if lifecycle_state == "weakened":

                lifecycle_penalty = 0.05

            # -------------------------------------
            # Recency bonus
            # -------------------------------------

            recency_bonus = 0.0

            if memory.updated_at:

                age_days = (
                    now - memory.updated_at
                ).total_seconds() / 86400

                recency_bonus = (
                    0.05 / (1 + age_days)
                )

            # -------------------------------------
            # Conflict penalty
            # -------------------------------------

            conflict_penalty = 0.0

            if memory.relation in single_value_relations:
                key = (memory.subject, memory.relation)

                # Do not penalize any candidate when timestamps are unknown
                # or the latest timestamp is ambiguous.
                if (
                    key not in unknown_timestamp_keys
                    and key not in ambiguous_latest_keys
                ):
                    latest_memory = latest_memories.get(key)

                    if latest_memory and latest_memory.id != memory.id:
                        conflict_penalty = 0.10


            # -------------------------------------
            # Final ranking score
            # -------------------------------------

            final_score = (
                similarity
                + relation_bonus
                + importance_bonus
                + reinforcement
                + recency_bonus
                + adaptive_bonus
                - conflict_penalty
                - lifecycle_penalty
            )

            # -------------------------------------
            # Threshold
            # -------------------------------------

            if final_score >= threshold:

                results.append({

                    "memory": memory,

                    "score": final_score,

                    "semantic_score": similarity,

                    "relation_bonus": relation_bonus,

                    "importance_bonus": importance_bonus,

                    "reinforcement": reinforcement,

                    "recency_bonus": recency_bonus,

                    "adaptive_priority":
                        adaptive_priority,

                    "adaptive_bonus":
                        adaptive_bonus,

                    "conflict_penalty": conflict_penalty,

                    "lifecycle_state": lifecycle_state,

                    "lifecycle_penalty": lifecycle_penalty
                })

        # -----------------------------------------
        # Save lifecycle changes
        # -----------------------------------------

        if lifecycle_changed:

            self._commit()

        # -----------------------------------------
        # Sort by final score
        # -----------------------------------------

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        # -----------------------------------------
        # Select final results
        # -----------------------------------------

        final_results = results[:top_k]

        # -----------------------------------------
        # Record successful retrievals
        # -----------------------------------------

        for result in final_results:

            memory = result["memory"]

            self.memory_reinforcement.record_retrieval(
                memory,
                current_time=now
            )

        if final_results:

            self._commit()

        return final_results

    # =====================================================
    # MULTI-MEMORY RETRIEVAL
    # =====================================================

    def search_by_relation(
        self,
        relation,
        limit=10
    ):

        stmt = (
            select(Memory)
            .where(
                self._owner_filter(),
Memory.relation == relation,
                Memory.active.is_(True),
                Memory.lifecycle_state != "archived"
            )
            .order_by(
                Memory.importance.desc(),
                Memory.id.desc()
            )
            .limit(limit)
        )

        return (
            self.session.execute(stmt)
            .scalars()
            .all()
        )
    # =====================================================
    # GET ALL MEMORIES
    # =====================================================

    def get_all_memories(self):

        stmt = (
            select(Memory)
            .where(
                self._owner_filter(),
Memory.active.is_(True),
                Memory.lifecycle_state != "archived"
            )
            .order_by(
                Memory.id
            )
        )

        return (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

    # =====================================================
    # GET MEMORY HISTORY
    # =====================================================

    def get_memory_history(
        self,
        subject="User",
        relation=None
    ):
        """
        Return active and archived memory history.

        History is read-only and does not affect retrieval.
        """

        stmt = select(Memory).where(
            self._owner_filter(),
Memory.subject == subject
        )

        if relation is not None:
            stmt = stmt.where(
                Memory.relation == relation
            )

        stmt = stmt.order_by(
            Memory.created_at.asc(),
            Memory.id.asc()
        )

        return (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

    # =====================================================
    # GET MEMORIES VALID AT A SPECIFIC TIME
    # =====================================================

    def get_memories_valid_at(
        self,
        as_of,
        subject="User",
        relation=None
    ):
        """
        Return memories whose recorded validity interval
        contains the requested time.

        Start is inclusive; end is exclusive.

        Archived memories are eligible only when their
        validity interval is explicitly bounded. This
        avoids treating forgotten memories with unknown
        end dates as historical evidence.
        """

        if not isinstance(as_of, datetime):
            raise TypeError(
                "as_of must be a datetime"
            )

        if as_of.tzinfo is not None:
            raise ValueError(
                "as_of must be a timezone-naive UTC datetime"
            )

        stmt = select(Memory).where(
            self._owner_filter(),
Memory.subject == subject,
            Memory.valid_from.is_not(None),
            Memory.valid_from <= as_of,
            (
                (Memory.valid_to.is_(None))
                | (as_of < Memory.valid_to)
            )
        )

        if relation is not None:
            stmt = stmt.where(
                Memory.relation == relation
            )

        stmt = stmt.order_by(
            Memory.valid_from.desc(),
            Memory.id.desc()
        )

        memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        # Current active memories may have no recorded end.
        # Archived memories must have an explicit end date;
        # otherwise their historical validity is uncertain.
        eligible_memories = [
            memory
            for memory in memories
            if (
                memory.active
                and memory.lifecycle_state != "archived"
            )
            or (
                not memory.active
                and memory.lifecycle_state == "archived"
                and memory.archive_reason == "replaced"
                and memory.valid_to is not None
            )
        ]

        single_value_relations = {
            "lives_in",
            "current_job",
            "age",
            "born_in",
            "current_city",
            "current_country",
        }

        if relation in single_value_relations:
            # Conflicting eligible values are ambiguous.
            # Return no answer rather than choosing one arbitrarily.
            if len({
                memory.value.strip().lower()
                for memory in eligible_memories
                if memory.value
            }) > 1:
                return []

        return eligible_memories


    def get_memories_overlapping_interval(
        self,
        start,
        end,
        subject="User",
        relation=None
    ):
        """
        Return memories whose recorded validity interval
        overlaps [start, end).

        Start is inclusive; end is exclusive.
        Forgotten memories are not historical evidence.
        """
        from datetime import datetime
        from sqlalchemy import select

        if not isinstance(start, datetime):
            raise TypeError("start must be a datetime")
        if not isinstance(end, datetime):
            raise TypeError("end must be a datetime")

        if start.tzinfo is not None or end.tzinfo is not None:
            raise ValueError(
                "start and end must be timezone-naive UTC datetimes"
            )

        if start >= end:
            raise ValueError("start must be earlier than end")

        stmt = select(Memory).where(
            self._owner_filter(),
Memory.subject == subject,
            Memory.valid_from.is_not(None),
            Memory.valid_to.is_not(None),
            Memory.valid_from < end,
            Memory.valid_to > start,
        )

        if relation is not None:
            stmt = stmt.where(Memory.relation == relation)

        stmt = stmt.order_by(
            Memory.valid_from.asc(),
            Memory.id.asc()
        )

        memories = self.session.execute(
            stmt
        ).scalars().all()

        return [
            memory for memory in memories
            if (
                memory.active
                and memory.lifecycle_state != "archived"
            )
            or (
                not memory.active
                and memory.lifecycle_state == "archived"
                and memory.archive_reason == "replaced"
                and memory.valid_to is not None
            )
        ]

    def search_historical_memories(
        self,
        query,
        start,
        end,
        subject="User",
        relation=None,
        top_k=5,
        threshold=0.20,
    ):
        """
        Retrieve relevant memories whose recorded validity
        intervals overlap [start, end).

        Does not update retrieval statistics or lifecycle state.
        """
        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or top_k < 1
        ):
            raise ValueError("top_k must be a positive integer")

        query_embedding = (
            self.embedding_manager.create_embedding(query)
        )

        candidates = self.get_memories_overlapping_interval(
            start,
            end,
            subject=subject,
            relation=relation,
        )

        results = []

        for memory in candidates:
            if not memory.embedding:
                continue

            memory_embedding = (
                self.embedding_manager.deserialize(
                    memory.embedding
                )
            )

            similarity = (
                self.embedding_manager.similarity(
                    query_embedding,
                    memory_embedding,
                )
            )

            if similarity < threshold:
                continue

            results.append({
                "memory": memory,
                "score": similarity,
                "semantic_score": similarity,
                "lifecycle_state": memory.lifecycle_state,
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]

    def _commit(self):
        """Commit changes and recover the session if the commit fails."""
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.adaptive_prioritization.close()

        self.session.close()
