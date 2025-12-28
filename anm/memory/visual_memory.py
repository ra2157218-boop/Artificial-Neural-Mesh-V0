# ============================================================
# ANM V0-OpenSource — VISUAL MEMORY V0-OpenSource MAX (ULTRA-SAFE EDITION)
#  LawBook V0-OpenSource • Zero-Biometric • PAST-ONLY Visual Memory
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diary_memory import DiaryMemory


class VisualMemory:
    """
    VISUAL MEMORY V0-OpenSource MAX — ULTRA-SAFE
    ----------------------------------
    Purely textual visual recall:
        - diagram descriptions
        - simulation frame descriptions
        - user-uploaded image descriptions
        - LLM-generated visual summaries

    HARD RESTRICTIONS:
        - No biometric interpretation
        - No gender / race / identity / age inference
        - No “person detection” beyond “a human figure”
        - Never invent missing visual details
        - Simulations must be labeled "(simulated)"
    """

    # Expanded, lawbook-safe biometric filters
    FORBIDDEN_BIOMETRIC = [
        # identity & recognition
        "face recognition", "recognize", "identity", "identify",

        # direct biometrics
        "gender", "age", "ethnicity", "race", "skin tone", "skin color",

        # gendered terms (blocked)
        "male", "female", "man", "woman", "boy", "girl",
        "lad", "lady", "gentleman", "teen", "teenager",
        "adult male", "adult female",

        # appearance-based human judgments
        "handsome", "beautiful", "pretty", "ugly",
        "caucasian", "asian", "indian", "african",

        # explicit human state detection
        "the person is", "person is", "person looks",
    ]

    # Allowed neutral phrase
    GENERIC_HUMAN_REPLACEMENT = (
        "A human figure is present, but biometric interpretation "
        "is forbidden. Only non-biometric structural details are kept."
    )

    def __init__(self, diary: Optional[DiaryMemory] = None) -> None:
        self.diary = diary or DiaryMemory()

    # ------------------------------------------------------------
    #  SAFE LOGGING
    # ------------------------------------------------------------
    def index_image(
        self,
        *,
        image_id: str,
        description: str,
        tags: Optional[List[str]] = None,
        source: str = "unknown",       # "user" | "simulation" | "renderer" | "llm"
        simulation_id: Optional[str] = None,
        run_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:

        desc = (description or "").strip()
        lower = desc.lower()

        # ---------- 1. FULL biometric safety filter ----------
        biometric_hit = any(bad in lower for bad in self.FORBIDDEN_BIOMETRIC)

        if biometric_hit:
            desc = self.GENERIC_HUMAN_REPLACEMENT

        # ---------- 2. Simulation flag ----------
        if source.lower() in ("simulation", "renderer"):
            desc = desc + " (simulated visual description)"

        # ---------- 3. Metadata + tags ----------
        all_tags = (tags or []) + ["visual"]
        if simulation_id:
            all_tags.append(f"sim:{simulation_id}")

        extra_payload = extra or {}
        extra_payload.update(
            {
                "image_id": image_id,
                "source": source,
                "simulation_id": simulation_id,
            }
        )

        # ---------- 4. Write to Diary ----------
        self.diary.log_observation(
            text=desc,
            specialist="VisualMemory",
            run_id=run_id,
            tags=all_tags,
            title=f"Visual Item: {image_id}",
            notes=None,
            extra=extra_payload,
        )

    # ------------------------------------------------------------
    #  SEARCH
    # ------------------------------------------------------------
    def search(
        self,
        text_query: Optional[str],
        *,
        limit: int = 12,
        simulation_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        tags = ["visual"]
        if simulation_id:
            tags.append(f"sim:{simulation_id}")

        if not text_query:
            # Return recent entries
            blocks = self.diary.search_blocks(
                kinds=["observation"],
                any_tags=tags,
                limit=limit,
            )
        else:
            blocks = self.diary.search_blocks(
                text_query=text_query,
                kinds=["observation"],
                any_tags=tags,
                limit=limit,
            )

        return {
            "query": text_query,
            "blocks": blocks,
        }

    # ------------------------------------------------------------
    #  MEMORYLLM INGESTION
    # ------------------------------------------------------------
    def collect_for_memory(
        self,
        *,
        limit: int = 12,
        simulation_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        tags = ["visual"]
        if simulation_id:
            tags.append(f"sim:{simulation_id}")

        blocks = self.diary.search_blocks(
            kinds=["observation"],
            any_tags=tags,
            limit=limit,
        )

        raw = [b.get("raw", "") for b in blocks]

        return {
            "visual_descriptions": raw,
            "count": len(raw),
        }