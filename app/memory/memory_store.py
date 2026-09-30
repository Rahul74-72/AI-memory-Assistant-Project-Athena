from datetime import datetime

from sqlalchemy import select

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

    def __init__(self):

        self.session = SessionLocal()

        self.importance_calibrator = ImportanceCalibrator()

        self.embedding_manager = EmbeddingManager()

        self.memory_decay = MemoryDecay()

        self.memory_reinforcement = MemoryReinforcement()

        self.memory_lifecycle = MemoryLifecycle()

        self.adaptive_prioritization = (
            AdaptiveMemoryPrioritization()
        )

    # =====================================================
    # SAVE / UPDATE MEMORY
    # =====================================================

    def save_memory(
        self,
        subject,
        relation,
        value,
        category,
        importance=5
    ):

        single_value_relations = {

            "lives_in",

            "current_job",

            "age",

            "born_in",

            "current_city",

            "current_country"
        }

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

        # Find existing active memories

        stmt = select(Memory).where(
            Memory.subject == subject,
            Memory.relation == relation,
            Memory.active.is_(True)
        )

        existing_memories = (
            self.session.execute(stmt)
            .scalars()
            .all()
        )

        # -------------------------------------------------
        # Duplicate
        # -------------------------------------------------

        for memory in existing_memories:

            if (
                memory.value.strip().lower()
                == value.strip().lower()
            ):

                # Repair old memories without embeddings

                if not memory.embedding:

                    memory.embedding = embedding_json

                    self.session.commit()

                    return {
                        "action": "updated_embedding",
                        "memory": memory
                    }

                return {
                    "action": "duplicate",
                    "memory": memory
                }

        # -------------------------------------------------
        # Multi-value relation
        # -------------------------------------------------

        if relation not in single_value_relations:

            memory = Memory(
                subject=subject,
                relation=relation,
                value=value,
                category=category,
                importance=importance,
                active=True,
                lifecycle_state="active",
                embedding=embedding_json
            )

            self.session.add(memory)

            self.session.commit()

            return {
                "action": "created",
                "memory": memory
            }

        # -------------------------------------------------
        # Single-value relation
        # -------------------------------------------------

        if existing_memories:

            old_memory = existing_memories[0]

            old_value = old_memory.value

            old_memory.value = value

            old_memory.category = category

            old_memory.importance = importance

            old_memory.embedding = embedding_json

            old_memory.lifecycle_state = "active"

            self.session.commit()

            return {
                "action": "updated",
                "memory": old_memory,
                "old_value": old_value
            }

        # -------------------------------------------------
        # New memory
        # -------------------------------------------------

        memory = Memory(
            subject=subject,
            relation=relation,
            value=value,
            category=category,
            importance=importance,
            active=True,
            lifecycle_state="active",
            embedding=embedding_json
        )

        self.session.add(memory)

        self.session.commit()

        return {
            "action": "created",
            "memory": memory
        }

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

        for memory in memories:

            if memory.relation not in single_value_relations:

                continue

            key = (
                memory.subject,
                memory.relation
            )

            if key not in latest_memories:

                latest_memories[key] = memory

            elif (
                memory.updated_at
                and latest_memories[key].updated_at
                and memory.updated_at
                > latest_memories[key].updated_at
            ):

                latest_memories[key] = memory

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

                key = (
                    memory.subject,
                    memory.relation
                )

                latest_memory = latest_memories.get(
                    key
                )

                if (
                    latest_memory
                    and latest_memory.id != memory.id
                ):

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

            self.session.commit()

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

            self.session.commit()

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
    # CLOSE
    # =====================================================

    def close(self):

        self.adaptive_prioritization.close()

        self.session.close()
