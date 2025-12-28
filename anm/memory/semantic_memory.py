# ============================================================
# ANM V0-OpenSource — SEMANTIC MEMORY V0-OpenSource MAX
#  Long-lived Concepts • Meta-Patterns • Lawbook Compliant
#  Partners: DiaryMemory V0-OpenSource • MetaMemory V0-OpenSource • MemoryLLM V0-OpenSource
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diary_memory import DiaryMemory


class SemanticMemory:
    """
    SEMANTIC MEMORY V0-OpenSource MAX
    ------------------------
    Stores ONLY PAST-ONLY, HIGH-LEVEL CONCEPTS:

        - Stable preferences ("In the past, ANM observed the user prefers X")
        - Architecture patterns
        - Module limitations
        - Conceptual rules
        - Reasoning strategies
        - Version lineage ("v12 → V0-OpenSource change in WoT coordination")
        - Domain specialties & weaknesses
        - Non-personal user patterns (learning style, topic trends)

    NEVER STORES:
        - private user facts
        - hallucinated memories
        - event-level facts (EpisodicMemory does that)
        - claims about the real world unless user explicitly stated them
        - simulated content as literal truth

    Stores concepts as:
        - idea blocks
        - observation blocks

    All tagged with ["semantic"] for safe retrieval.
    """

    def __init__(self, diary: Optional[DiaryMemory] = None) -> None:
        self.diary = diary or DiaryMemory()

    # ============================================================
    #  STORE CONCEPTS (TIMELESS KNOWLEDGE)
    # ============================================================

    def store_concept(
        self,
        *,
        title: str,
        text: str,
        tags: Optional[List[str]] = None,
        specialist: Optional[str] = None,
        run_id: Optional[str] = None,
        lineage: Optional[str] = None,
        notes: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a conceptual note with high-level abstraction.
        Suitable for patterns, design reasoning, strategy notes.
        """

        safe_text = text.strip()

        body_lines = [safe_text]
        if lineage:
            body_lines.append(f"\nConcept Lineage: {lineage}")

        idea_block = "\n".join(body_lines)

        payload = extra or {}
        payload.update(
            {
                "semantic_title": title,
                "lineage": lineage,
                "kind": "concept",
            }
        )

        self.diary.log_idea(
            idea=idea_block,
            specialist=specialist,
            run_id=run_id,
            tags=(tags or []) + ["semantic"],
            notes=notes,
            extra=payload,
        )

    # ============================================================
    #  STORE SEMANTIC OBSERVATIONS
    # ============================================================

    def store_observation(
        self,
        *,
        text: str,
        tags: Optional[List[str]] = None,
        specialist: Optional[str] = None,
        run_id: Optional[str] = None,
        notes: Optional[str] = None,
        drift_tag: Optional[str] = None,
        stability: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store general semantic observations:

            - user learning patterns (safe, non-personal)
            - module collaboration notes
            - WoT behaviour notes
            - domain weaknesses
            - stable tendencies

        drift_tag: optional special marker for patterns like:
            - "hallucination_spike"
            - "missing_wot_requests"
            - "physics_math_disagreement"
        """

        content_lines = [text]

        if drift_tag:
            content_lines.append(f"\nDrift Pattern: {drift_tag}")
        if stability:
            content_lines.append(f"\nStability Snapshot:\n{stability}")

        payload = extra or {}
        payload.update(
            {
                "semantic_type": "observation",
                "drift_tag": drift_tag,
                "stability": stability,
            }
        )

        self.diary.log_observation(
            text="\n".join(content_lines),
            specialist=specialist,
            run_id=run_id,
            tags=(tags or []) + ["semantic"],
            title="Semantic Observation",
            notes=notes,
            extra=payload,
        )

    # ============================================================
    #  RETRIEVAL (FOR MemoryLLM / SelfAwarenessLLM / Router)
    # ============================================================

    def query(
        self,
        text_query: str,
        *,
        limit: int = 12,
        include_concepts: bool = True,
        include_observations: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve semantic knowledge related to a keyword.

        Filters:
            - semantic idea blocks (concepts)
            - semantic observation blocks

        Returns:
            {
              "query": str,
              "blocks": [ {...}, ... ],
            }
        """

        kinds = []
        if include_concepts:
            kinds.append("idea")
        if include_observations:
            kinds.append("observation")

        if not kinds:
            kinds = ["idea", "observation"]

        blocks = self.diary.search_blocks(
            text_query=text_query,
            kinds=kinds,
            any_tags=["semantic"],
            limit=limit,
        )

        return {
            "query": text_query,
            "blocks": blocks,
        }

    # ============================================================
    #  HIGH-LEVEL API FOR SELF-AWARENESS LLM
    # ============================================================

    def list_recent_concepts(self, limit: int = 12) -> List[Dict[str, Any]]:
        """
        Useful for SelfAwarenessLLM to inspect top-level conceptual memory.
        """
        return self.diary.search_blocks(
            kinds=["idea"],
            any_tags=["semantic"],
            limit=limit,
        )

    def list_recent_observations(self, limit: int = 12) -> List[Dict[str, Any]]:
        """
        Useful for detecting reasoning trends.
        """
        return self.diary.search_blocks(
            kinds=["observation"],
            any_tags=["semantic"],
            limit=limit,
        )