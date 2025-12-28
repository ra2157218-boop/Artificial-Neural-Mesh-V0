# ============================================================
# ANM V0-OpenSource — IMAGE MEMORY V0-OpenSource MAX
#  LawBook 1.2 • PAST-ONLY • DiaryMemory V0-OpenSource MAX
#
#  Purpose:
#    - Track image assets ANM has seen or generated.
#    - Register image metadata (NOT pixels).
#    - Provide search by id, tag, simulation_id.
#    - Compliant with SimulationLLM, ImageLLM & SoundLLM flows.
#
#  Rules:
#    - Never invent images that do not exist.
#    - Never claim pixel-level access unless explicitly provided.
#    - Store only metadata, tags, captions, and URIs/paths.
#    - All entries are PAST-ONLY context (Law 3.x).
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diary_memory import DiaryMemory


class ImageMemory:
    """
    IMAGE MEMORY V0-OpenSource MAX

    This module records the existence of images ANM has encountered.
    It stores ONLY METADATA, never pixels.

    Stored per-image:
        - image_id (stable string)
        - path / uri (local/remote)
        - source ("user", "simulation", "renderer", ...)
        - caption (past-only textual description)
        - tags
        - simulation_id (link to SimulationLLM outputs)
        - extra fields (safe metadata)

    All diary entries are append-only and treated as PAST experiences.
    No invented images or hallucinated visuals are allowed (Law 2.3, 4.2).
    """

    def __init__(self, diary: Optional[DiaryMemory] = None) -> None:
        self.diary = diary or DiaryMemory()

    # ============================================================
    #  REGISTER IMAGE (WRITE)
    # ============================================================

    def register_image(
        self,
        *,
        image_id: str,
        path: Optional[str] = None,
        uri: Optional[str] = None,
        source: str = "unknown",
        caption: Optional[str] = None,
        tags: Optional[List[str]] = None,
        simulation_id: Optional[str] = None,
        run_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register an image asset in the Cloud Diary.

        LawBook V0-OpenSource Compliance:
          - PAST-ONLY memory
          - No fabricated descriptions
          - No assumptions about pixels, faces, objects, identity
          - Pure metadata: id, path/uri, source, tags, links

        This function is used by:
            - ImageLLM (to log user-provided images)
            - SimulationLLM (to log generated frames)
            - Router/Refiner (for final-answer artifacts)
        """

        # Auto-add structural tags
        all_tags = (tags or []) + ["image_asset"]
        if simulation_id:
            all_tags.append(f"sim:{simulation_id}")

        # Build a safe textual description
        body_lines = []

        if caption:
            body_lines.append(caption.strip())

        body_lines.append("")
        body_lines.append("IMAGE META:")
        body_lines.append(f"- image_id: {image_id}")
        body_lines.append(f"- source: {source}")
        if path:
            body_lines.append(f"- path: {path}")
        if uri:
            body_lines.append(f"- uri: {uri}")
        if simulation_id:
            body_lines.append(f"- simulation_id: {simulation_id}")

        text = "\n".join(body_lines)

        # Additional metadata (never pixels)
        payload = extra.copy() if extra else {}
        payload.update(
            {
                "image_id": image_id,
                "path": path,
                "uri": uri,
                "source": source,
                "simulation_id": simulation_id,
            }
        )

        self.diary.log_observation(
            text=text,
            specialist="ImageMemory",
            run_id=run_id,
            tags=all_tags,
            title=f"Image Asset: {image_id}",
            notes=None,
            extra=payload,
        )

    # ============================================================
    #  RETRIEVE BY IMAGE ID
    # ============================================================

    def by_id(self, image_id: str, *, limit: int = 5) -> Dict[str, Any]:
        """
        Retrieve metadata for an image_id.

        Returns only diary blocks with:
            - TYPE: observation
            - TAG: image_asset
        """
        blocks = self.diary.search_blocks(
            text_query=image_id,
            kinds=["observation"],
            any_tags=["image_asset"],
            limit=limit,
        )
        return {
            "query": image_id,
            "blocks": blocks,
        }

    # ============================================================
    #  GENERAL SEARCH
    # ============================================================

    def search(
        self,
        text_query: str,
        *,
        limit: int = 10,
        simulation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Free-text search over image metadata blocks.

        Search across:
          - caption
          - IMAGE META section
          - tags
          - simulation links

        Does NOT search pixels (Law 2.4).
        """

        tags = ["image_asset"]
        if simulation_id:
            tags.append(f"sim:{simulation_id}")

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

    # ============================================================
    #  SIMULATION-LINKED RETRIEVAL
    # ============================================================

    def frames_for_simulation(
        self,
        simulation_id: str,
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Return all image assets linked to a simulation run.

        Uses tag: sim:<simulation_id>

        Useful for:
          - SimulationLLM
          - ImageLLM
          - SoundLLM (for multimodal audio-video alignment)
          - Router’s SimulationStrategy
        """

        return self.diary.search_blocks(
            kinds=["observation"],
            any_tags=[f"sim:{simulation_id}", "image_asset"],
            limit=limit,
        )

    # ============================================================
    #  SAFE SUMMARY FOR MEMORYLLM / TrueWoT
    # ============================================================

    def summary_for_memory(self, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Return the newest image metadata blocks (not pixels).

        This function feeds:
            - MemoryLLM V0-OpenSource
            - TrueWoT memory sections
            - SelfAwarenessLLM
        """
        return self.diary.search_blocks(
            kinds=["observation"],
            any_tags=["image_asset"],
            limit=limit,
        )