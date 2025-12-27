# ============================================================
# ANM V0-OpenSource — CONFIGURATION SETTINGS (v5.0 — 9 Specialist Edition)
#  TrueWoT Engine v6 + Router v5 + Refiner v7 + Verifier v7
#  MemoryLLM + ResearchLLM + FactsLLM + Cloud Diary V0-OpenSource
# ============================================================

"""
Central configuration for ANM V0-OpenSource.

Supports:
- 9 Specialists:
      general, math, physics, code, chemistry, biology,
      memory, research, facts
- TrueWoT v6 Polymath Engine
- Router v5
- ResearchLLM + FactsLLM
- Refiner v7
- Verifier v7
- Cloud Diary Memory (DiaryMemory + MemoryLLM)
- Expansion engine (future)
"""

# ============================================================
#  True Web-of-Thought (WoT) Controls
# ============================================================

# Maximum dynamic specialist hops (TrueWoT v6)
WOT_MAX_STEPS = 20        # previously 12, now 20 for polymath mode

# Enable Polymath TrueWoT engine
ENABLE_TRUE_WOT = True

# Legacy WoT rounds (router history compatibility)
WOT_ROUNDS = 1            # for JSON compatibility only


# ============================================================
#  Model Configuration — 9 Specialists + Executive Modules
# ============================================================

# Core specialists
# NOTE: MODEL_CODE uses Stable-Code-3B (domain-specific model) instead of DeepSeek-R1-1.5B
# NOTE: MODEL_MATH, MODEL_PHYSICS, MODEL_CHEMISTRY, MODEL_BIOLOGY use Nanbeige4-3B for better science/math reasoning
MODEL_GENERAL      = "deepseek-r1:1.5b"
MODEL_MATH         = "nanbeige4-3b"  # Uses Nanbeige4-3B for superior mathematical reasoning
MODEL_PHYSICS      = "nanbeige4-3b"  # Uses Nanbeige4-3B for superior scientific understanding
MODEL_CODE         = "stable-code-3b"  # Uses Stable-Code-3B for better code generation
MODEL_CHEMISTRY    = "nanbeige4-3b"  # Uses Nanbeige4-3B for superior scientific understanding
MODEL_BIOLOGY      = "nanbeige4-3b"  # Uses Nanbeige4-3B for superior scientific understanding

# Memory specialist
MODEL_MEMORY       = "deepseek-r1:1.5b"

# Meta-specialists
MODEL_RESEARCH     = "deepseek-r1:1.5b"
MODEL_FACTS        = "deepseek-r1:1.5b"

# Executive modules
MODEL_REFINER      = "deepseek-r1:1.5b"
MODEL_VERIFIER     = "deepseek-r1:1.5b"
MODEL_ROUTER       = "deepseek-r1:1.5b"
MODEL_EXPANSION    = "deepseek-r1:1.5b"  # Future creative engine


# ============================================================
#  Cloud Diary Memory Settings (DiaryMemory V0-OpenSource)
# ============================================================

MEMORY_ENABLED            = True
DIARY_FILE                = "anm_diary.txt"

# How many diary blocks MemoryLLM loads
MEMORY_MAX_BLOCKS         = 10

# Fallback: tail of diary for missing data
MEMORY_TAIL_CHARS         = 7000

# Strict: treat memory as PAST ONLY (never truth)
MEMORY_ENFORCE_HISTORICAL = True


# ============================================================
#  Logging Configuration (Behaviour Logger v5)
# ============================================================

LOG_DIR                = "logs"
LOG_JSONL              = True
LOG_TIMESTAMP          = True
LOG_MAX_FILES          = 5000   # ANM V0-OpenSource is very verbose
LOG_STORE_PACKETS      = True
LOG_STORE_WOT_GRAPH    = True


# ============================================================
#  Router Behaviour (Router v5)
# ============================================================

ROUTER_STRICT_MODE         = True
ROUTER_INTERNAL_DEBUG      = False
ROUTER_ALLOW_MEMORY_CALLS  = True
ROUTER_ALLOW_RESEARCH      = True
ROUTER_ALLOW_FACTS         = True

# ============================================================
#  Simulation Engine Settings (Nebula Engine Core)
# ============================================================

# Nebula Engine is now the core simulation engine
# Auto-detect availability
try:
    from anm.sim.nebula_bridge import is_nebula_available  # type: ignore
    NEBULA_ENABLED = is_nebula_available()
except (ImportError, Exception):
    NEBULA_ENABLED = False

# Allow RouterLLM to modify max_steps
ROUTER_DYNAMIC_STEPS       = True


# ============================================================
#  Safety Filters
# ============================================================

SAFETY_CHECKS = {
    # Domain-level safety
    "math": True,
    "physics": True,
    "chemistry": True,
    "biology": True,
    "code": True,
    "general": True,

    # Meta-safety
    "hallucinations": True,
    "consistency": True,
    "dimensions": True,
    "memory_past_only": True,
    "factual_alignment": True
}


# ============================================================
#  EXPORT CONFIG
# ============================================================

def get_config() -> dict:
    """Return the complete ANM V0-OpenSource configuration."""
    return {
        # True WoT
        "enable_true_wot": ENABLE_TRUE_WOT,
        "wot_max_steps": WOT_MAX_STEPS,
        "wot_rounds": WOT_ROUNDS,

        # Models — 9 specialists
        "model_general": MODEL_GENERAL,
        "model_math": MODEL_MATH,
        "model_physics": MODEL_PHYSICS,
        "model_code": MODEL_CODE,
        "model_chemistry": MODEL_CHEMISTRY,
        "model_biology": MODEL_BIOLOGY,
        "model_memory": MODEL_MEMORY,
        "model_research": MODEL_RESEARCH,
        "model_facts": MODEL_FACTS,

        # Executive modules
        "model_refiner": MODEL_REFINER,
        "model_verifier": MODEL_VERIFIER,
        "model_router": MODEL_ROUTER,
        "model_expansion": MODEL_EXPANSION,

        # Diary memory system
        "memory_enabled": MEMORY_ENABLED,
        "diary_file": DIARY_FILE,
        "memory_max_blocks": MEMORY_MAX_BLOCKS,
        "memory_tail_chars": MEMORY_TAIL_CHARS,
        "memory_historical_enforced": MEMORY_ENFORCE_HISTORICAL,

        # Logging
        "log_dir": LOG_DIR,
        "log_jsonl": LOG_JSONL,
        "log_timestamp": LOG_TIMESTAMP,
        "log_max_files": LOG_MAX_FILES,
        "log_store_packets": LOG_STORE_PACKETS,
        "log_store_wot_graph": LOG_STORE_WOT_GRAPH,

        # Router behaviour
        "router_strict_mode": ROUTER_STRICT_MODE,
        "router_internal_debug": ROUTER_INTERNAL_DEBUG,
        "router_allow_memory": ROUTER_ALLOW_MEMORY_CALLS,
        "router_allow_research": ROUTER_ALLOW_RESEARCH,
        "router_allow_facts": ROUTER_ALLOW_FACTS,
        "router_dynamic_steps": ROUTER_DYNAMIC_STEPS,

        # Simulation Engine settings (Nebula Engine is core)
        "nebula_enabled": NEBULA_ENABLED,

        # Safety filters
        "safety_checks": SAFETY_CHECKS,
    }
