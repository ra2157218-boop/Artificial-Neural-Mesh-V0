# ============================================================
# ANM V0-OpenSource — SIMULATION MEMORY V0-OpenSource MAX
#  Tracks simulation runs, branches, frames, metadata
#  Cross-links with ImageMemory + SoundMemory + MetaMemory
#  Fully LawBook V0-OpenSource compliant (simulations ≠ real-world data)
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diary_memory import DiaryMemory


class SimulationMemory:
    """
    SIMULATION MEMORY V0-OpenSource MAX
    -------------------------

    Purpose:
        Store past simulation runs created by:
            - SimulationLLM
            - PhysicsLLM (generated scenarios)
            - CodeLLM (algorithmic simulations)
            - Renderer / ImageLLM / SoundLLM (derived visuals/audio)

    Each simulation run stores:
        - simulation_id (stable key)
        - description (what scenario was imagined)
        - parameters (lightweight configs)
        - numeric notes (only qualitative unless user provides real numbers)
        - result_summary (PAST-ONLY description)
        - linked image frames
        - linked sound assets
        - optional data/video paths (NEVER treated as real world)

    All entries:
        - are PAST CONTEXT
        - are NOT guaranteed true
        - must follow LawBook rules on speculative physics
    """

    def __init__(self, diary: Optional[DiaryMemory] = None) -> None:
        self.diary = diary or DiaryMemory()

    # ============================================================
    #  LOGGING MAIN SIMULATION RUN
    # ============================================================

    def log_simulation(
        self,
        *,
        simulation_id: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        result_summary: Optional[str] = None,
        sim_type: Optional[str] = None,       # "physics", "code", "fluid", "orbit", etc.
        lineage: Optional[str] = None,        # v1 → v2 → V0-OpenSource evolution
        tags: Optional[List[str]] = None,
        run_id: Optional[str] = None,
        video_path: Optional[str] = None,
        data_path: Optional[str] = None,
        stability: Optional[Dict[str, Any]] = None,   # WoT stability snapshot
        notes: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a full simulation run.

        description:
            High-level verbal description of what was simulated.

        result_summary:
            MUST follow LawBook:
                - past-only
                - no claim of real experimental measurements
                - no fictional physics presented as real
        """

        safe_desc = description.strip()
        safe_result = (result_summary or "").strip()

        body_lines = [safe_desc]

        if lineage:
            body_lines.append(f"\nLINEAGE: {lineage}")

        if sim_type:
            body_lines.append(f"\nSIMULATION TYPE: {sim_type}")

        if safe_result:
            body_lines.append("\nRESULT SUMMARY:")
            body_lines.append(safe_result)

        # Simulation stability snapshot (from TrueWoT)
        if stability:
            body_lines.append("\nSTABILITY SNAPSHOT:")
            for k, v in stability.items():
                body_lines.append(f"  - {k}: {v}")

        # Assemble block content
        text = "\n".join(body_lines)

        all_tags = (tags or []) + ["simulation", f"sim:{simulation_id}"]

        payload = extra or {}
        payload.update(
            {
                "simulation_id": simulation_id,
                "parameters": parameters or {},
                "video_path": video_path,
                "data_path": data_path,
                "lineage": lineage,
                "sim_type": sim_type,
                "stability": stability,
            }
        )

        self.diary.log_observation(
            text=text,
            specialist="SimulationEngine",
            run_id=run_id,
            tags=all_tags,
            title=f"Simulation Run: {simulation_id}",
            notes=notes,
            extra=payload,
        )

    # ============================================================
    #  LOG INDIVIDUAL FRAMES / KEYFRAMES (image-linked)
    # ============================================================

    def log_frame(
        self,
        *,
        simulation_id: str,
        frame_id: str,
        description: str,
        image_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        tags: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Store a frame extracted from simulation:
            - visual snapshot
            - structural description
            - optional linked image_id

        Tagged with:
            ["simulation", f"sim:{simulation_id}", f"frame:{frame_id}"]
        """

        safe_desc = description.strip()

        all_tags = (tags or []) + [
            "simulation",
            f"sim:{simulation_id}",
            f"frame:{frame_id}",
        ]

        body = [
            safe_desc,
            "",
            "FRAME META:",
            f"  - frame_id: {frame_id}",
            f"  - simulation_id: {simulation_id}",
        ]

        if timestamp:
            body.append(f"  - sim_timestamp: {timestamp}")

        if image_id:
            body.append(f"  - linked_image_id: {image_id}")

        text = "\n".join(body)

        payload = extra or {}
        payload.update(
            {
                "frame_id": frame_id,
                "simulation_id": simulation_id,
                "linked_image_id": image_id,
                "sim_timestamp": timestamp,
            }
        )

        self.diary.log_observation(
            text=text,
            specialist="SimFrame",
            run_id=run_id,
            tags=all_tags,
            title=f"Simulation Frame: {frame_id}",
            extra=payload,
        )

    # ============================================================
    #  LOG SOUND BLUEPRINT LINKS (sound-linked)
    # ============================================================

    def log_sound(
        self,
        *,
        simulation_id: str,
        sound_id: str,
        blueprint: str,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Link a SoundLLM blueprint to a simulation.
        """

        safe_blueprint = blueprint.strip()

        all_tags = (tags or []) + [
            "simulation",
            f"sim:{simulation_id}",
            f"sound:{sound_id}",
        ]

        body = [
            "SIMULATION SOUND BLUEPRINT",
            f"Simulation ID: {simulation_id}",
            "",
            safe_blueprint,
        ]

        payload = extra or {}
        payload.update(
            {
                "sound_id": sound_id,
                "simulation_id": simulation_id,
            }
        )

        self.diary.log_observation(
            text="\n".join(body),
            specialist="SimulationSound",
            tags=all_tags,
            run_id=run_id,
            title=f"Sound Blueprint: {sound_id}",
            notes=notes,
            extra=payload,
        )

    # ============================================================
    #  RETRIEVAL
    # ============================================================

    def query(
        self,
        text_query: str,
        *,
        limit: int = 10,
        simulation_id: Optional[str] = None,
        include_frames: bool = True,
        include_sound: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve simulation runs and optional frame/sound links.
        """

        tags = ["simulation"]
        if simulation_id:
            tags.append(f"sim:{simulation_id}")

        # Fetch main runs
        blocks = self.diary.search_blocks(
            text_query=text_query,
            kinds=["observation"],
            any_tags=tags,
            limit=limit,
        )

        # Fetch frame/sound details
        extras: List[Dict[str, Any]] = []
        if include_frames:
            frames = self.diary.search_blocks(
                text_query=text_query,
                kinds=["observation"],
                any_tags=["simulation", "frame"],
                limit=limit,
            )
            extras.extend(frames)

        if include_sound:
            snd = self.diary.search_blocks(
                text_query=text_query,
                kinds=["observation"],
                any_tags=["simulation", "sound"],
                limit=limit,
            )
            extras.extend(snd)

        return {
            "query": text_query,
            "blocks": blocks,
            "extra_blocks": extras,
        }

    def by_id(
        self,
        simulation_id: str,
        *,
        limit: int = 12,
        include_frames: bool = True,
        include_sound: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve everything tied to a simulation ID:
            - runs
            - frames
            - sound assets
            - metadata
        """

        # Main simulation runs
        runs = self.diary.search_blocks(
            text_query=simulation_id,
            kinds=["observation"],
            specialists=["SimulationEngine"],
            any_tags=[f"sim:{simulation_id}"],
            limit=limit,
        )

        frames: List[Dict[str, Any]] = []
        sounds: List[Dict[str, Any]] = []

        if include_frames:
            frames = self.diary.search_blocks(
                text_query=simulation_id,
                kinds=["observation"],
                specialists=["SimFrame"],
                any_tags=[f"sim:{simulation_id}"],
                limit=limit,
            )

        if include_sound:
            sounds = self.diary.search_blocks(
                text_query=simulation_id,
                kinds=["observation"],
                specialists=["SimulationSound"],
                any_tags=[f"sim:{simulation_id}"],
                limit=limit,
            )

        return {
            "simulation_id": simulation_id,
            "runs": runs,
            "frames": frames,
            "sound": sounds,
        }