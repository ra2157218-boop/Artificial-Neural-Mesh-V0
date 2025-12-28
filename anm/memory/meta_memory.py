# ============================================================
# ANM V0-OpenSource — META MEMORY V0-OpenSource MAX
#  LawBook 1.2 • Drift Detector • Stability Monitor
#  Self-awareness patterns across all memory & reasoning systems
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diary_memory import DiaryMemory


class MetaMemory:
    """
    META MEMORY V0-OpenSource MAX
    --------------------
    Meta-Memory stores PAST-ONLY patterns about ANM itself.

    It NEVER stores:
        - user personal facts
        - hallucinated external events
        - simulated experiences as real experiences

    It ONLY stores:
        - patterns about specialists
        - conflicts between modules
        - behaviour drift
        - upgrades + migrations
        - stability notes
        - reasoning trends (WoT patterns, domain stats)

    Uses DiaryMemory with tags: ["meta", ...]
    """

    def __init__(self, diary: Optional[DiaryMemory] = None):
        self.diary = diary or DiaryMemory()

    # ============================================================
    #  CORE LOGGING: PATTERNS
    # ============================================================

    def log_pattern(
        self,
        *,
        title: str,
        pattern: str,
        modules: Optional[List[str]] = None,
        version: Optional[str] = None,
        stability: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a stable pattern ANM has detected in itself.
        Example:
            - "PhysicsLLM repeatedly requests MathLLM for unit checks."
            - "ImageLLM outputs missing WOT_REQUEST in 3/10 sessions."
            - "Router v12 prefers facts+research for risky GR tasks."
        """

        tags = ["meta", "pattern"]

        body = [pattern]
        if modules:
            body.append(f"\nModules involved: {', '.join(modules)}")
        if version:
            body.append(f"Version: {version}")
        if stability:
            body.append(f"\nStability Snapshot:\n{stability}")

        text = "\n".join(body)

        payload = extra or {}
        payload.update(
            {
                "pattern_title": title,
                "modules": modules or [],
                "version": version,
                "stability": stability,
            }
        )

        self.diary.log_observation(
            text=text,
            specialist="MetaMemory",
            tags=tags,
            title=title,
            extra=payload,
        )

    # ============================================================
    #  CONFLICT LOGGING
    # ============================================================

    def log_conflict(
        self,
        *,
        modules: List[str],
        description: str,
        run_id: Optional[str] = None,
        consistency: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log disagreements between specialists.
        LawBook Compliant:
            - Records only the disagreement pattern
            - Never claims which one is "right" unless Verifier decided
        """

        tags = ["meta", "conflict"]

        snapshot = {
            "modules_involved": modules,
            "run_id": run_id,
            "consistency": consistency,
        }

        if extra:
            snapshot.update(extra)

        text = (
            f"Conflict detected between: {', '.join(modules)}\n\n"
            f"{description}"
        )

        self.diary.log_observation(
            text=text,
            specialist="MetaMemory",
            tags=tags,
            title="Module Conflict",
            extra=snapshot,
        )

    # ============================================================
    #  VERSION & MIGRATION LOGGING
    # ============================================================

    def log_version_change(
        self,
        *,
        version_from: str,
        version_to: str,
        changes: str,
        router_plan_snapshot: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log version upgrades in ANM.
        This is crucial for SelfAwarenessLLM.
        """

        tags = ["meta", "version"]

        payload = extra or {}
        payload.update(
            {
                "from": version_from,
                "to": version_to,
                "router_plan": router_plan_snapshot,
            }
        )

        text = (
            f"ANM upgraded from {version_from} → {version_to}\n\n"
            f"Changes:\n{changes}"
        )

        self.diary.log_system(
            message=text,
            tags=tags,
            extra=payload,
        )

    # ============================================================
    #  DRIFT & STABILITY LOGGING
    # ============================================================

    def log_drift(
        self,
        *,
        drift_type: str,
        description: str,
        vfl_meta: Optional[Dict[str, Any]] = None,
        recent_stats: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log behavioural drift, e.g.:

            - hallucination spike in physics domain
            - repeated missing WOT_REQUEST markers
            - unstable loop patterns detected by TrueWoT

        """

        tags = ["meta", "drift"]

        payload = extra or {}
        payload.update(
            {
                "drift_type": drift_type,
                "vfl_meta": vfl_meta,
                "recent_stats": recent_stats,
            }
        )

        body = [f"DRIFT TYPE: {drift_type}", "", description]

        if vfl_meta:
            body.append(f"\nVFL META: {vfl_meta}")
        if recent_stats:
            body.append(f"\nSTATS: {recent_stats}")

        text = "\n".join(body)

        self.diary.log_observation(
            text=text,
            specialist="MetaMemory",
            tags=tags,
            title=f"Drift: {drift_type}",
            extra=payload,
        )

    # ============================================================
    #  RETRIEVAL
    # ============================================================

    def search(
        self,
        *,
        text_query: str,
        limit: int = 12,
        kinds: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search meta-memory notes.
        """
        kinds = kinds or ["observation", "idea", "system"]

        blocks = self.diary.search_blocks(
            text_query=text_query,
            kinds=kinds,
            any_tags=["meta"],
            limit=limit,
        )

        return {
            "query": text_query,
            "blocks": blocks,
        }

    def recent(self, limit: int = 12) -> List[Dict[str, Any]]:
        """
        Return newest meta-level entries.
        """
        return self.diary.search_blocks(
            kinds=["observation", "system", "idea"],
            any_tags=["meta"],
            limit=limit,
        )