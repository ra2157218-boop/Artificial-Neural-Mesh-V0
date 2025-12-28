# ============================================================
#  ANM V0-OpenSource — WEB-OF-THOUGHT MODULE
#  Multi-domain reasoning engine
# ============================================================

"""
ANM Web-of-Thought (WoT) Engine

Provides multi-domain reasoning through:
- Dynamic domain routing
- Cross-domain context sharing
- Metacognitive integration
- Self-correction and backtracking
- Parallel and beam search modes

Usage:
    from anm.wot import TrueWoTMax, WoTConfig, WoTMode
    
    # Basic usage (backward compatible)
    wot = TrueWoTMax(["general", "math", "physics"])
    cots = wot.run("general", "What is 2+2?", specialists)
    
    # Advanced usage
    config = WoTConfig(
        mode=WoTMode.METACOGNITIVE,
        enable_self_correction=True,
        enable_backtracking=True,
    )
    result = wot.run_full("general", "Explain relativity", specialists, config=config)
"""

# V0-OpenSource (Primary)
from anm.wot.wot_engine_v15 import (
    TrueWoTMax,
    WoTMode,
    WoTConfig,
    ReasoningPath,
    WoTResult,
)

# Legacy (for backward compatibility only)
from anm.wot.wot_engine import TrueWoT as TrueWoTLegacy

# Default to V0-OpenSource Max
TrueWoT = TrueWoTMax

__all__ = [
    # V0-OpenSource (Primary)
    "TrueWoTMax",
    "TrueWoT",
    "WoTMode",
    "WoTConfig",
    "ReasoningPath",
    "WoTResult",
    # Legacy (backward compatibility)
    "TrueWoTLegacy",
]

__version__ = "0.1.0-opensource"
