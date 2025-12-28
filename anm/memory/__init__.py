# ============================================================
# ANM V0-OpenSource — MEMORY MODULE (EPISTEMIC HUMILITY)
#  Multi-Layer Memory System • Behavioral Learning • Pattern Recognition
#  
#  CORE PRINCIPLE: Learn BEHAVIORS, not "truths"
#  All memories are OBSERVATIONS, not verified facts
# ============================================================

"""
ANM Memory System V2 — EPISTEMIC HUMILITY

Core Principle: Store OBSERVATIONS and BEHAVIORS, not "truths"

✅ What we store and learn:
- Behavioral patterns (what approaches work)
- Process observations (what happened)
- Success/failure outcomes (objective signals)
- Domain performance stats (objective metrics)

❌ What we NEVER treat as truth:
- Query content (users may be wrong)
- Answer content (answers may be wrong)
- User corrections (users may be mistaken)

Provides:
- DiaryMemory: Long-term observation storage
- WorkingMemory: Session context
- EpisodicMemory: Past interaction observations
- SemanticMemory: Concept storage (marked as unverified)
- MetaMemory: Behavioral self-awareness
- MemoryHub: Unified orchestrator (epistemic-aware)
- LearningEngine: Behavioral learning (not content learning)

Usage:
    from anm.memory import MemoryHub, LearningEngine
    
    hub = MemoryHub()
    context = hub.get_context("query")  # Returns OBSERVATIONS, not facts
    hub.record_session_behavior(...)     # Records BEHAVIOR, not content truth
"""

from anm.memory.diary_memory import DiaryMemory
from anm.memory.working_memory import WorkingMemory
from anm.memory.episodic_memory import EpisodicMemory
from anm.memory.semantic_memory import SemanticMemory
from anm.memory.meta_memory import MetaMemory

# V2: Unified Memory Hub (Epistemic Humility)
from anm.memory.memory_hub import (
    MemoryHub,
    MemoryContext,
    BehavioralInsight,
    ObservationType,
)

# V2: Learning Engine (Behavioral, not content)
from anm.memory.learning_engine import (
    LearningEngine,
    StrategyRule,
    EpistemicStatus,
    LearningEvent,
)

# Optional specialized memory modules
try:
    from anm.memory.simulation_memory import SimulationMemory
except ImportError:
    SimulationMemory = None  # type: ignore

try:
    from anm.memory.image_memory import ImageMemory
except ImportError:
    ImageMemory = None  # type: ignore

try:
    from anm.memory.sound_memory import SoundMemory
except ImportError:
    SoundMemory = None  # type: ignore

try:
    from anm.memory.visual_memory import VisualMemory
except ImportError:
    VisualMemory = None  # type: ignore

__all__ = [
    # Core Memory
    "DiaryMemory",
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "MetaMemory",
    # V2 Unified Systems (Epistemic Humility)
    "MemoryHub",
    "MemoryContext",
    "BehavioralInsight",
    "ObservationType",
    # V2 Learning Engine (Behavioral)
    "LearningEngine",
    "StrategyRule",
    "EpistemicStatus",
    "LearningEvent",
    # Specialized Memory
    "SimulationMemory",
    "ImageMemory",
    "SoundMemory",
    "VisualMemory",
]
