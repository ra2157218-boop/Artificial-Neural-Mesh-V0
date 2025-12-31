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

Environment Variables:
- All settings can be overridden via environment variables
- Format: ANM_<SETTING_NAME> (e.g., ANM_MODEL_GENERAL, ANM_WOT_MAX_STEPS)
- Paths can use ~ for home directory expansion
"""

import os

# ============================================================
#  True Web-of-Thought (WoT) Controls
# ============================================================

# Maximum dynamic specialist hops (TrueWoT v6)
WOT_MAX_STEPS = int(os.getenv("ANM_WOT_MAX_STEPS", "20"))

# Enable Polymath TrueWoT engine
ENABLE_TRUE_WOT = os.getenv("ANM_ENABLE_TRUE_WOT", "true").lower() in ("true", "1", "yes")

# Legacy WoT rounds (router history compatibility)
WOT_ROUNDS = int(os.getenv("ANM_WOT_ROUNDS", "1"))


# ============================================================
#  Model Configuration — 9 Specialists + Executive Modules
# ============================================================

# Core specialists
# NOTE: MODEL_CODE uses Stable-Code-3B (domain-specific model) instead of DeepSeek-R1-1.5B
# NOTE: MODEL_MATH, MODEL_PHYSICS, MODEL_CHEMISTRY, MODEL_BIOLOGY use Nanbeige4-3B for better science/math reasoning
MODEL_GENERAL      = os.getenv("ANM_MODEL_GENERAL", "deepseek-r1:1.5b")
MODEL_MATH         = os.getenv("ANM_MODEL_MATH", "nanbeige4-3b")
MODEL_PHYSICS      = os.getenv("ANM_MODEL_PHYSICS", "nanbeige4-3b")
MODEL_CODE         = os.getenv("ANM_MODEL_CODE", "stable-code-3b")
MODEL_CHEMISTRY    = os.getenv("ANM_MODEL_CHEMISTRY", "nanbeige4-3b")
MODEL_BIOLOGY      = os.getenv("ANM_MODEL_BIOLOGY", "nanbeige4-3b")

# Memory specialist
MODEL_MEMORY       = os.getenv("ANM_MODEL_MEMORY", "deepseek-r1:1.5b")

# Meta-specialists
MODEL_RESEARCH     = os.getenv("ANM_MODEL_RESEARCH", "deepseek-r1:1.5b")
MODEL_FACTS        = os.getenv("ANM_MODEL_FACTS", "deepseek-r1:1.5b")
MODEL_RESEARCH_INTERNET = os.getenv("ANM_MODEL_RESEARCH_INTERNET", "qwen2.5-3b-instruct")

# Executive modules
MODEL_REFINER      = os.getenv("ANM_MODEL_REFINER", "deepseek-r1:1.5b")
MODEL_VERIFIER     = os.getenv("ANM_MODEL_VERIFIER", "deepseek-r1:1.5b")
MODEL_ROUTER       = os.getenv("ANM_MODEL_ROUTER", "deepseek-r1:1.5b")
MODEL_EXPANSION    = os.getenv("ANM_MODEL_EXPANSION", "deepseek-r1:1.5b")


# ============================================================
#  Research Mode Configuration
# ============================================================

RESEARCH_MODE_CONFIGS = {
    # Authority model assignments (LOCKED - no voting override)
    "authority_models": {
        "math": MODEL_MATH,           # nanbeige4-3b
        "physics": MODEL_PHYSICS,     # nanbeige4-3b
        "chemistry": MODEL_CHEMISTRY, # nanbeige4-3b
        "biology": MODEL_BIOLOGY,     # nanbeige4-3b
        "code": MODEL_CODE,           # stable-code-3b
        "internet": MODEL_RESEARCH_INTERNET,  # qwen2.5-3b-instruct
        "metacognition": MODEL_GENERAL,  # deepseek-r1:1.5b
    },

    # Deterministic routing
    "deterministic_routing": True,
    "hard_domain_binding": True,
    "no_fast_fallback": True,

    # Parallelism (dynamic 4-10 modules based on query)
    "max_parallelism": True,
    "min_parallel_modules": 4,    # Minimum 4 specialists run in parallel
    "max_parallel_modules": 10,   # Maximum 10 specialists can run concurrently
    "workers_per_module": 1,      # Each specialist runs once (no ensemble in research mode)

    # WoT configuration
    "wot_mandatory": True,
    "wot_min_depth": 3,
    "wot_max_steps": 20,

    # Failure policy
    "explicit_reporting": True,
    "retries_allowed": 2,
    "return_uncertainty": True,

    # PDF output
    "pdf_output": True,
    "markdown_fallback": True,  # If PDF generation fails, save as structured markdown
}


# ============================================================
#  Cloud Diary Memory Settings (DiaryMemory V0-OpenSource)
# ============================================================

MEMORY_ENABLED            = os.getenv("ANM_MEMORY_ENABLED", "true").lower() in ("true", "1", "yes")
DIARY_FILE                = os.path.expanduser(os.getenv("ANM_DIARY_FILE", "anm_diary.txt"))

# How many diary blocks MemoryLLM loads
MEMORY_MAX_BLOCKS         = int(os.getenv("ANM_MEMORY_MAX_BLOCKS", "10"))

# Fallback: tail of diary for missing data
MEMORY_TAIL_CHARS         = int(os.getenv("ANM_MEMORY_TAIL_CHARS", "7000"))

# Strict: treat memory as PAST ONLY (never truth)
MEMORY_ENFORCE_HISTORICAL = os.getenv("ANM_MEMORY_ENFORCE_HISTORICAL", "true").lower() in ("true", "1", "yes")


# ============================================================
#  Logging Configuration (Behaviour Logger v5)
# ============================================================

LOG_DIR                = os.path.expanduser(os.getenv("ANM_LOG_DIR", "logs"))
LOG_JSONL              = os.getenv("ANM_LOG_JSONL", "true").lower() in ("true", "1", "yes")
LOG_TIMESTAMP          = os.getenv("ANM_LOG_TIMESTAMP", "true").lower() in ("true", "1", "yes")
LOG_MAX_FILES          = int(os.getenv("ANM_LOG_MAX_FILES", "5000"))
LOG_STORE_PACKETS      = os.getenv("ANM_LOG_STORE_PACKETS", "true").lower() in ("true", "1", "yes")
LOG_STORE_WOT_GRAPH    = os.getenv("ANM_LOG_STORE_WOT_GRAPH", "true").lower() in ("true", "1", "yes")


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
#  Vector Store & RAG Configuration
# ============================================================

# Enable vector search for semantic memory
VECTOR_SEARCH_ENABLED = os.getenv("ANM_VECTOR_SEARCH_ENABLED", "true").lower() in ("true", "1", "yes")

# Vector database directory
VECTOR_DB_DIR = os.path.expanduser(os.getenv("ANM_VECTOR_DB_DIR", ".anm_cache/chroma"))

# Embedding model (sentence-transformers)
EMBEDDING_MODEL = os.getenv("ANM_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Chunk size for long documents
CHUNK_SIZE = int(os.getenv("ANM_CHUNK_SIZE", "512"))

# Enable Research Knowledge Base
RESEARCH_KB_ENABLED = os.getenv("ANM_RESEARCH_KB_ENABLED", "true").lower() in ("true", "1", "yes")


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

        # Research mode
        "research_mode_configs": RESEARCH_MODE_CONFIGS,
        "model_research_internet": MODEL_RESEARCH_INTERNET,

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

        # Vector Store & RAG settings
        "vector_search_enabled": VECTOR_SEARCH_ENABLED,
        "vector_db_dir": VECTOR_DB_DIR,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "research_kb_enabled": RESEARCH_KB_ENABLED,
    }
