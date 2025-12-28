# ============================================================
# ANM V0-OpenSource — WORKING MEMORY V0-OpenSource
#  Ephemeral per-run reasoning buffer (LawBook V0-OpenSource STRICT)
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Any, Dict, List, Optional, Deque
import re


# ------------------------------------------------------------
#  Data Structure
# ------------------------------------------------------------
@dataclass
class WMItem:
    step: int
    domain: str
    role: str
    note: str
    meta: Dict[str, Any] = field(default_factory=dict)


class WorkingMemory:
    """
    WORKING MEMORY V0-OpenSource
    ------------------------
    Ephemeral buffer used ONLY inside a single Router.handle() run.

    Guarantees:
        - No persistence (destroyed each run)
        - No personal user data stored
        - No biometric / identity inference
        - No invented measurements (Hz, dB, etc.)
        - No real-sound claims from simulation
        - No unsafe or hallucinated facts
    """

    MAX_NOTE_LEN = 512
    FORBIDDEN_BIOMETRIC = [
        "recognize", "identity", "identify", "face looks",
        "male", "female", "man", "woman",
        "boy", "girl", "lad", "lady",
        "gentleman", "teen", "teenager",
        "adult male", "adult female",
        "race", "ethnicity", "skin tone", "skin color",
        "he looks", "she looks", "appears to be", "looks like",
        "handsome", "beautiful", "pretty", "ugly"
    ]
    FORBIDDEN_NUMERIC_AUDIO = [
        "hz", "khz", "mhz", "db", "decibel",
        "recorded frequency", "measured frequency"
    ]
    FORBIDDEN_COT_MARKERS = [
        "chain-of-thought", "chain of thought",
        "thought process", "internal reasoning", "step-by-step reasoning",
        "here is my reasoning", "my reasoning is"
    ]

    def __init__(self, max_items: int = 96) -> None:
        self.max_items = max_items
        self._buf: Deque[WMItem] = deque(maxlen=max_items)
        self._step = 0

    def clear(self) -> None:
        """Clear working memory buffer."""
        self._buf.clear()
        self._step = 0
    
    def cleanup(self) -> None:
        """Cleanup method for memory optimization."""
        self.clear()

    # ------------------------------------------------------------
    #  ADD ITEM
    # ------------------------------------------------------------
    def add(
        self,
        *,
        domain: str,
        role: str,
        note: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:

        self._step += 1

        sanitized = self._sanitize(note)
        sanitized = sanitized[: self.MAX_NOTE_LEN]

        safe_meta = self._sanitize_meta(meta or {})

        self._buf.append(
            WMItem(
                step=self._step,
                domain=domain,
                role=role,
                note=sanitized,
                meta=safe_meta,
            )
        )

    # ------------------------------------------------------------
    #  SANITIZER
    # ------------------------------------------------------------
    def _sanitize(self, text: str) -> str:
        if not text:
            return ""

        lower = text.lower()

        # --- Remove COT markers (protect internal reasoning)
        if any(m in lower for m in self.FORBIDDEN_COT_MARKERS):
            return "[WM-SAFE-REDACTED: internal reasoning removed]"

        # --- Block biometric inference
        for bad in self.FORBIDDEN_BIOMETRIC:
            if bad in lower:
                return "[WM-SAFE-REDACTED: biometric/identity inference blocked]"

        # --- Block invented sound measurements
        if any(n in lower for n in self.FORBIDDEN_NUMERIC_AUDIO):
            return "[WM-SAFE-REDACTED: invented numeric audio measurement blocked]"

        # --- If simulation content pretends to be real
        if "simulation" in lower and ("real" in lower or "actual" in lower):
            return text + " (simulated description)"

        return text

    # ------------------------------------------------------------
    #  META SANITIZER (no private data)
    # ------------------------------------------------------------
    def _sanitize_meta(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        safe = {}
        for k, v in meta.items():
            # No raw CoTs or user data
            if isinstance(v, str):
                if any(m in v.lower() for m in self.FORBIDDEN_COT_MARKERS):
                    safe[k] = "[META-REDACTED: internal reasoning]"
                else:
                    safe[k] = v[:256]
            else:
                safe[k] = v
        return safe

    # ------------------------------------------------------------
    #  SNAPSHOT
    # ------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "step": item.step,
                    "domain": item.domain,
                    "role": item.role,
                    "note": item.note,
                    "meta": item.meta,
                }
                for item in list(self._buf)
            ]
        }

    # ------------------------------------------------------------
    #  CLEAR
    # ------------------------------------------------------------
    def clear(self) -> None:
        self._buf.clear()
        self._step = 0

    # ------------------------------------------------------------
    #  PRETTY DEBUG
    # ------------------------------------------------------------
    def pretty(self) -> str:
        return "\n".join(
            f"[{x.step:02d}] {x.domain.upper()} ({x.role}): {x.note}"
            for x in self._buf
        )