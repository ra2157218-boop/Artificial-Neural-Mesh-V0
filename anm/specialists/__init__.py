# ============================================================
#  ANM V0-OpenSource — SPECIALISTS MODULE
#  Domain-Specific LLM Modules • Unified Architecture
# ============================================================

"""
ANM Specialists V0-OpenSource

All specialists now inherit from BaseSpecialist with unified interface.
Each provides domain-specific reasoning within the TrueWoT framework.

Domains:
- General: High-level reasoning and routing
- Math: Mathematical computations and proofs
- Physics: Physical analysis and modeling
- Code: Programming and software engineering
- Chemistry: Chemical reactions and compounds
- Biology: Life sciences and organisms
- Memory: Past interactions and diary
- Research: External research aggregation
- Facts: Fact verification
- Internet: Real-time web search
- Simulation: Physics simulations
- Image: Visual perception
- Sound: Audio processing
"""

__version__ = "0.1.0-opensource"

# Base class (shared by all specialists)
from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistResult,
    SpecialistDomain,
    run_model,
)

# Core specialists
from anm.specialists.general_llm import GeneralLLM
from anm.specialists.math_llm import MathLLM
from anm.specialists.physics_llm import PhysicsLLM
from anm.specialists.code_llm import CodeLLM
from anm.specialists.chemistry_llm import ChemistryLLM
from anm.specialists.biology_llm import BiologyLLM
from anm.specialists.facts_llm import FactsLLM

# Memory specialist
from anm.specialists.memory_llm import MemoryLLM

# Internet specialist
try:
    from anm.specialists.internet_llm import (
        InternetLLM,
        WebSearcher,
        SearchResult,
        SearchResponse,
        SearchBackend,
    )
    INTERNET_LLM_AVAILABLE = True
except ImportError:
    InternetLLM = None
    WebSearcher = None
    SearchResult = None
    SearchResponse = None
    SearchBackend = None
    INTERNET_LLM_AVAILABLE = False

# Research specialist
try:
    from anm.specialists.research_llm import ResearchLLM
    RESEARCH_LLM_AVAILABLE = True
except ImportError:
    ResearchLLM = None
    RESEARCH_LLM_AVAILABLE = False

# Media specialists
from anm.specialists.sound_llm import SoundLLM
from anm.specialists.image_llm import ImageLLM

# Simulation specialist
from anm.specialists.simulation_llm import SimulationLLM

# Self-awareness (meta-specialist)
from anm.specialists.selfawareness_llm import SelfAwarenessLLM

__all__ = [
    # Version
    "__version__",
    
    # Base
    "BaseSpecialist",
    "SpecialistConfig",
    "SpecialistResult",
    "SpecialistDomain",
    "run_model",
    
    # Core Specialists
    "GeneralLLM",
    "MathLLM",
    "PhysicsLLM",
    "CodeLLM",
    "ChemistryLLM",
    "BiologyLLM",
    "FactsLLM",
    "MemoryLLM",
    "ResearchLLM",
    "RESEARCH_LLM_AVAILABLE",
    
    # Internet Specialist
    "InternetLLM",
    "WebSearcher",
    "SearchResult",
    "SearchResponse",
    "SearchBackend",
    "INTERNET_LLM_AVAILABLE",
    
    # Media Specialists
    "SoundLLM",
    "ImageLLM",
    
    # Simulation
    "SimulationLLM",
    
    # Meta-Specialist
    "SelfAwarenessLLM",
]
