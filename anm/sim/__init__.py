# ============================================================
#  ANM Simulation Engine Package — NEBULA ENGINE
#  V3.0: UNIVERSAL 2D ENGINE
#  
#  Truly general purpose • Simulate ANYTHING
#  50+ entity types • Multiple physics systems
#  Beautiful retro game visuals • Pixel-perfect rendering
# ============================================================

from anm.sim.engine import SimulationEngine
from anm.sim.types import (
    SimulationRequest,
    SimulationResult,
    SimulationFrame,
)

# ============================================================
#  UNIVERSAL ENGINE (Primary — Simulate Anything)
# ============================================================

try:
    from anm.sim.universal_engine import (
        UniversalEngine,
        simulate_anything,
        get_universal_engine,
    )
    from anm.sim.universal_physics import (
        UniversalPhysics,
        PhysicsMode,
        PhysicsConstants,
        detect_physics_mode,
    )
    from anm.sim.universal_renderer import (
        UniversalRenderer,
        ENTITY_VISUALS,
        RETRO_PALETTE,
        get_universal_renderer,
    )
    from anm.sim.scenario_parser import (
        ScenarioParser,
        ParsedScenario,
        parse_scenario,
    )
    UNIVERSAL_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Universal engine import failed: {e}")
    UNIVERSAL_ENGINE_AVAILABLE = False
    UniversalEngine = None
    simulate_anything = None
    get_universal_engine = None
    UniversalPhysics = None
    PhysicsMode = None
    PhysicsConstants = None
    detect_physics_mode = None
    UniversalRenderer = None
    ENTITY_VISUALS = None
    RETRO_PALETTE = None
    get_universal_renderer = None
    ScenarioParser = None
    ParsedScenario = None
    parse_scenario = None

# ============================================================
#  RETRO 2D ENGINE (Legacy compatibility)
# ============================================================

try:
    from anm.sim.engine_2d import SimulationEngine2D
    from anm.sim.renderer_2d import Renderer2D
    ENGINE_2D_AVAILABLE = True
except ImportError as e:
    print(f"Warning: 2D engine import failed: {e}")
    ENGINE_2D_AVAILABLE = False
    SimulationEngine2D = None
    Renderer2D = None

# ============================================================
#  LEGACY RENDERERS (Fallback)
# ============================================================

try:
    from anm.sim.cinematic_renderer import CinematicRenderer
except ImportError:
    CinematicRenderer = None

try:
    from anm.sim.interstellar_renderer import InterstellarRenderer
except ImportError:
    InterstellarRenderer = None

try:
    from anm.sim.metal_gpu_renderer import MetalGPURenderer
except ImportError:
    MetalGPURenderer = None

try:
    from anm.sim.advanced_renderer import AdvancedRenderer
    ADVANCED_RENDERER_AVAILABLE = True
except ImportError:
    ADVANCED_RENDERER_AVAILABLE = False
    AdvancedRenderer = None

try:
    from anm.sim.ray_tracing_renderer import RayTracingRenderer
    RAY_TRACING_AVAILABLE = True
except ImportError:
    RAY_TRACING_AVAILABLE = False
    RayTracingRenderer = None

# ============================================================
#  NEBULA BRIDGE
# ============================================================

from anm.sim.nebula_bridge import get_nebula_bridge, is_nebula_available

# ============================================================
#  EXPORTS
# ============================================================

__all__ = [
    # Core Types
    "SimulationEngine",
    "SimulationRequest",
    "SimulationResult",
    "SimulationFrame",
    
    # Universal Engine (PRIMARY - Use this!)
    "UniversalEngine",
    "simulate_anything",
    "get_universal_engine",
    "UNIVERSAL_ENGINE_AVAILABLE",
    
    # Universal Physics
    "UniversalPhysics",
    "PhysicsMode",
    "PhysicsConstants",
    "detect_physics_mode",
    
    # Universal Renderer
    "UniversalRenderer",
    "ENTITY_VISUALS",
    "RETRO_PALETTE",
    "get_universal_renderer",
    
    # Scenario Parser
    "ScenarioParser",
    "ParsedScenario",
    "parse_scenario",
    
    # 2D Engine (Legacy)
    "SimulationEngine2D",
    "Renderer2D",
    "ENGINE_2D_AVAILABLE",
    
    # Nebula Bridge
    "get_nebula_bridge",
    "is_nebula_available",
    
    # Legacy Renderers
    "CinematicRenderer",
    "InterstellarRenderer",
    "MetalGPURenderer",
    "AdvancedRenderer",
    "RayTracingRenderer",
]


# ============================================================
#  VERSION INFO
# ============================================================

__version__ = "0.1.0-opensource"
__engine_name__ = "Nebula Engine"
__engine_type__ = "Universal 2D"
