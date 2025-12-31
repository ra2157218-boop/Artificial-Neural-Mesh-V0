# ============================================================
# ANM V0-OpenSource — SOUND MEMORY V0-OpenSource MAX (ULTRA-SAFE EDITION)
#  Fully LawBook 1.2 Compliant • Anti-Numeric • No Fake Audio
# ============================================================

from __future__ import annotations

import re
from typing import List, Dict, Optional


class SoundMemory:
    """
    SOUND MEMORY V0-OpenSource MAX — ULTRA-SAFE
    ---------------------------------
    Extracts only *qualitative* audio concepts from text.

    Fixes over V0-OpenSource:
        ✓ No false positives from "sim" inside words
        ✓ Regex-based detection of forbidden numeric claims
        ✓ Safer simulated-tag logic
        ✓ Better phrase-level extraction
        ✓ Stronger LawBook 2.3 anti-hallucination defense
    """

    # Qualitative markers (SAFE)
    SOUND_KEYWORDS = [
        "sound", "audio", "noise", "timbre",
        "hum", "buzz", "whirr", "whir", "whistle",
        "rumble", "roar", "boom", "shockwave", "thump",
        "vibration", "pulsing", "resonance", "harmonic",
        "echo", "reverb", "hiss", "airflow", "wind noise",
        "footsteps", "breathing", "heartbeat",
        "drone", "thrum", "low-frequency", "deep tone",
        "metallic scrape", "crackle", "pop", "snap",
        "sonic boom", "growl",
    ]

    # Numeric-frequency bans (regex)
    FORBIDDEN_PATTERNS = [
        r"\b\d+\s*hz\b",
        r"\b\d+\s*khz\b",
        r"\b\d+\s*mhz\b",
        r"\b\d+\s*db\b",
        r"decibel",
        r"measured\s+frequency",
        r"recorded\s+frequency",
        r"actual\s+audio",
        r"captured\s+sound",
    ]

    # Regex precompiled
    FORBIDDEN_REGEX = re.compile(
        "|".join(FORBIDDEN_PATTERNS),
        flags=re.IGNORECASE
    )

    def __init__(self):
        # TODO: Initialize sound memory state/cache if needed for audio processing
        # Currently stateless - no initialization required
        pass

    # ---------------------------------------------------------
    #  MAIN EXTRACTOR
    # ---------------------------------------------------------
    def extract(self, text: str) -> Dict[str, List[str]]:
        if not isinstance(text, str) or not text.strip():
            return {"audio_concepts": []}

        # Remove numeric forbidden claims
        lower = text.lower()
        has_forbidden = bool(self.FORBIDDEN_REGEX.search(lower))

        results: List[str] = []

        # Split on . and newlines
        sentences = [
            s.strip() for s in re.split(r"[.\n]", text)
            if s.strip()
        ]

        for s in sentences:
            ls = s.lower()

            # Skip sentences with illegal numeric audio claims
            if self.FORBIDDEN_REGEX.search(ls):
                continue

            # Keyword hit?
            if not any(k in ls for k in self.SOUND_KEYWORDS):
                continue

            # Safe simulated tagging:
            # Only tag if the sentence explicitly contains:
            #   "simulation", "simulated", "in the simulation"
            simulated = False
            if re.search(r"\bsimulation\b|\bsimulated\b|\bin the simulation\b", ls):
                simulated = True

            safe_sentence = s + (" (simulated description)" if simulated else "")
            results.append(safe_sentence)

        # Deduplicate + cap
        final = []
        seen = set()
        for r in results:
            if r not in seen:
                final.append(r)
                seen.add(r)

        return {"audio_concepts": final[:16]}

    # ---------------------------------------------------------
    #  BULK EXTRACTOR
    # ---------------------------------------------------------
    def extract_from_blocks(self, blocks: List[Dict[str, str]]) -> Dict[str, List[str]]:
        collected: List[str] = []

        for blk in blocks:
            raw = blk.get("raw", "") or ""
            out = self.extract(raw).get("audio_concepts", [])
            collected.extend(out)

        # Deduplicate + cap
        final = []
        seen = set()
        for a in collected:
            if a not in seen:
                final.append(a)
                seen.add(a)

        return {"audio_concepts": final[:16]}

    # ---------------------------------------------------------
    #  MERGE MULTIPLE SETS
    # ---------------------------------------------------------
    def merge(self, *mems: Dict[str, List[str]]) -> Dict[str, List[str]]:
        collected = []
        for m in mems:
            collected.extend(m.get("audio_concepts", []))

        seen = set()
        final = []
        for a in collected:
            if a not in seen:
                final.append(a)
                seen.add(a)

        return {"audio_concepts": final[:16]}