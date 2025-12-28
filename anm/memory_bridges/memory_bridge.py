# ============================================================
# ANM V0-OpenSource — MEMORY BRIDGE V0-OpenSource (V0-OpenSource)
#  HyperMemory V0-OpenSource • PAST-ONLY • LawBook V0-OpenSource STRICT
#  Fully synced with MemoryLLM V0-OpenSource, WM V0-OpenSource, Router V0-OpenSource
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List
from anm.specialists.memory_llm import MemoryLLM


# ------------------------------------------------------------
#  Helper to safely stringify memory blocks
# ------------------------------------------------------------
def _safe_line(x: Any, max_len: int = 240) -> str:
    if x is None:
        return "(none)"
    if isinstance(x, dict):
        # extract a stable safe field
        if "text" in x:
            t = str(x["text"])
        elif "raw" in x:
            t = str(x["raw"])
        elif "description" in x:
            t = str(x["description"])
        else:
            t = str(x)
    else:
        t = str(x)

    # sanitize biometric & unsafe phrases
    forbidden = [
        "recognize", "identity", "male", "female", "age ",
        "race", "ethnicity", "skin color", "looks like",
        "he looks", "she looks", "handsome", "beautiful",
        "pretty", "ugly",
        "hz", "khz", "mhz", "db", "decibel",
    ]
    lower = t.lower()
    if any(f in lower for f in forbidden):
        return "[SAFE-REDACTED]"
    return t[:max_len].strip()


# ------------------------------------------------------------
#  Convert WorkingMemory snapshot to short bullet points
# ------------------------------------------------------------
def _wm_to_bullets(snapshot: Any, max_items: int = 12) -> List[str]:
    out: List[str] = []
    if not isinstance(snapshot, dict):
        return out
    steps = snapshot.get("steps") or []
    for item in steps[:max_items]:
        domain = item.get("domain", "?")
        role   = item.get("role", "?")
        note   = _safe_line(item.get("note", ""))
        out.append(f"- [{domain}/{role}] {note}")
    return out


# ------------------------------------------------------------
#  Main Memory Bridge
# ------------------------------------------------------------
def build_memory_brief(memory_core: MemoryLLM, user_query: str) -> Dict[str, Any]:
    """
    Build STRICT PAST-ONLY HyperMemory brief.

    Returned structure:
        {
           "brief_text": "...",
           "raw_memory": {...}
        }

    This is consumed by:
       - Router V0-OpenSource
       - PlannerLLM V0-OpenSource
       - TrueWoT V0-OpenSource
       - Refiner V0-OpenSource
       - Verifier V0-OpenSource
    """

    # QUERY MemoryLLM V0-OpenSource (HyperMemory V0-OpenSource)
    result = memory_core.query(
        user_query=user_query,
        limit_blocks=12,
        use_recent_fallback=True
    )

    # Extract all modalities safely
    highlights   = result.get("highlights")     or []
    summary      = result.get("memory_summary") or "In the past, ANM found no relevant memory."

    episodic     = result.get("episodic")       or []
    semantic     = result.get("semantic")       or []
    visual       = result.get("visual")         or []
    audio        = result.get("audio")          or []
    simulation   = result.get("simulation")     or []
    meta_raw     = result.get("meta")           or []

    working_raw  = result.get("working_memory") or {}

    # Convert WM snapshot to safe bullets
    wm_bullets = _wm_to_bullets(working_raw, max_items=12)

    # ------------------------------------------------------------
    # BUILD FINAL CLOUD DIARY BRIEF (LawBook V0-OpenSource strict)
    # ------------------------------------------------------------
    out: List[str] = []
    out.append("[CLOUD_DIARY_BRIEF]")
    out.append("NOTE: This is PAST context ONLY — NOT guaranteed current truth.\n")

    # Highlights --------------------------------------------------
    if highlights:
        out.append("PAST HIGHLIGHTS:")
        for h in highlights[:12]:
            out.append(f"- {_safe_line(h)}")
        out.append("")

    # Semantic ----------------------------------------------------
    if semantic:
        out.append("SEMANTIC PATTERNS (past-only):")
        for s in semantic[:8]:
            out.append(f"- {_safe_line(s)}")
        out.append("")

    # Episodic -----------------------------------------------------
    if episodic:
        out.append("EPISODIC TRACE (past interactions):")
        for e in episodic[:8]:
            out.append(f"- {_safe_line(e)}")
        out.append("")

    # Visual -------------------------------------------------------
    if visual:
        out.append("VISUAL MEMORY (textual; past-only; NO pixels):")
        for v in visual[:8]:
            out.append(f"- {_safe_line(v)}")
        out.append("")

    # Audio --------------------------------------------------------
    if audio:
        out.append("AUDIO MEMORY (past-only qualitative descriptions):")
        for a in audio[:8]:
            out.append(f"- {_safe_line(a)}")
        out.append("")

    # Simulation ---------------------------------------------------
    if simulation:
        out.append("SIMULATION HISTORY (past-only; simulated descriptions):")
        for s in simulation[:8]:
            out.append(f"- {_safe_line(s)}")
        out.append("")

    # Meta ---------------------------------------------------------
    if meta_raw:
        # meta_raw can be dict | list | single object
        meta_items: List[Any] = []
        if isinstance(meta_raw, dict):
            # turn into "key: value" strings
            for k, v in meta_raw.items():
                meta_items.append(f"{k}: {v}")
        elif isinstance(meta_raw, (list, tuple)):
            meta_items = list(meta_raw)
        else:
            meta_items = [meta_raw]

        out.append("META-BEHAVIOR (patterns about ANM behaviours, past-only):")
        for m in meta_items[:8]:
            out.append(f"- {_safe_line(m)}")
        out.append("")

    # Working Memory ----------------------------------------------
    if wm_bullets:
        out.append("WORKING MEMORY WINDOW (recent reasoning snapshot; past-only):")
        out.extend(wm_bullets)
        out.append("")

    # Compressed Summary ------------------------------------------
    out.append("SUMMARY (compressed PAST context):")
    for ln in summary.splitlines():
        out.append(_safe_line(ln))

    brief_text = "\n".join(out).strip()

    return {
        "brief_text": brief_text,
        "raw_memory": result,
    }