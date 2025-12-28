# ============================================================
# ANM V0-OpenSource — EPISODIC MEMORY V0-OpenSource MAX
#  LawBook V0-OpenSource Compliant • DiaryMemory V0-OpenSource MAX Backbone
#  PAST-ONLY Episodic Recall + LFM + Router Integration
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diary_memory import DiaryMemory


class EpisodicMemory:
    """
    EpisodicMemory V0-OpenSource MAX — structured recall layer over Cloud Diary.

    Responsibilities:
      - Log entire ANM sessions as episodic 'episodes'
      - Provide law-compliant PAST-ONLY memory blocks
      - Retrieve relevant diary blocks for:
            • MemoryLLM V0-OpenSource
            • SelfAwarenessLLM
            • Router (context + planning)
            • TrueWoT (extra hints, NOT facts)
      - Never invent, modify, or hallucinate memory.

    Memory retrieved here must ALWAYS be treated as:
        "In the past, ANM noted that..."
    """

    # --------------------------------------------------------
    # INIT
    # --------------------------------------------------------
    def __init__(self, diary: Optional[DiaryMemory] = None) -> None:
        self.diary = diary or DiaryMemory()

    # ============================================================
    #  EPISODE LOGGING
    # ============================================================

    def log_session(
        self,
        *,
        user_query: str,
        final_answer: str,
        verification: Optional[Dict[str, Any]] = None,
        router_plan: Optional[Dict[str, Any]] = None,
        active_domains: Optional[List[str]] = None,
        run_id: Optional[str] = None,
        lfm_learning_entry: Optional[str] = None,
    ) -> None:
        """
        Log a full ANM session as one interaction block in the Diary.

        This is the MAIN episode logger for Router.handle().

        Notes:
          - Strictly PAST-ONLY memory (LawBook 3.x)
          - Stores Verifier + Router context
          - Stores LFM learning snippets (if provided)
          - Never stores raw CoT (Law 3.4)
        """

        tags: List[str] = ["anm_session"]

        if active_domains:
            tags.extend(f"domain:{d}" for d in active_domains)

        # Build notes (safe)
        notes_lines: List[str] = []

        if verification:
            status = verification.get("status", "unknown")
            score = verification.get("score")
            notes_lines.append(f"Verifier status: {status}")
            if score is not None:
                notes_lines.append(f"Verifier score: {score}")
            v_notes = verification.get("notes")
            if v_notes:
                notes_lines.append(f"Verifier notes: {v_notes}")

        if router_plan:
            entry = router_plan.get("entry_specialist")
            max_steps = router_plan.get("max_steps")
            reason = router_plan.get("reason")

            if entry:
                notes_lines.append(f"Entry specialist: {entry}")
            if max_steps:
                notes_lines.append(f"Max steps: {max_steps}")
            if reason:
                notes_lines.append(f"Router reason: {reason}")

        if lfm_learning_entry:
            notes_lines.append("LFM insight included.")

        notes = "\n".join(notes_lines) if notes_lines else None

        # Build extra metadata
        extra: Dict[str, Any] = {}

        if verification:
            extra["verification"] = verification
        if router_plan:
            extra["router_plan"] = router_plan
        if active_domains:
            extra["active_domains"] = active_domains
        if lfm_learning_entry:
            extra["lfm"] = lfm_learning_entry

        # Log to DiaryMemory
        self.diary.log_interaction(
            user_query=user_query,
            assistant_reply=final_answer,
            specialist="Router/Refiner",
            run_id=run_id,
            tags=tags,
            notes=notes,
            title="ANM Session Episode",
            extra=extra,
        )

        # Also store learning entry as a separate LEARNING block (optional)
        if lfm_learning_entry:
            self.diary.log_learning(
                learning_entry=lfm_learning_entry,
                specialist="LFM",
                run_id=run_id,
                tags=["lfm", "learning"],
            )

    # ============================================================
    #  RETRIEVAL / QUERY
    # ============================================================

    def query(
        self,
        user_query: str,
        *,
        limit_blocks: int = 6,
        use_recent_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve episodic PAST-ONLY context related to the user’s new query.

        Returns:
            {
              "query": str,
              "blocks": [ parsed_meta_block ],
              "raw_blocks": [ "<full block text>" ],
            }

        Search order:
          1) Match by text_query over INTERACTIONS + LEARNING + IDEAS
          2) If no hits → fallback to recent blocks
          3) Never fabricate memory
        """

        # Primary search (high signal)
        blocks = self.diary.search_blocks(
            text_query=user_query,
            kinds=["interaction", "learning", "idea"],
            limit=limit_blocks,
        )

        # Fallback for sparse memory
        if not blocks and use_recent_fallback:
            blocks = self.diary.recent_blocks(limit=limit_blocks)

        return {
            "query": user_query,
            "blocks": blocks,
            "raw_blocks": [b.get("raw", "") for b in blocks],
        }

    # ============================================================
    #  QUICK ACCESS HELPERS FOR SPECIALISTS
    # ============================================================

    def recent_learning(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Returns the LAST few LFM learning entries.
        Useful for:
            - SelfAwarenessLLM
            - Router strategy shaping
            - PlannerLLM meta-prior updates
        """
        return self.diary.search_blocks(
            kinds=["learning"],
            limit=limit,
        )

    def recent_episodes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Return only recent ANM session episodes (interaction blocks).
        """
        return self.diary.search_blocks(
            kinds=["interaction"],
            limit=limit,
        )