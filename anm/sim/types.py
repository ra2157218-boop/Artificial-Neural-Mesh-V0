# ============================================================
# ANM V0-OpenSource — SIMULATION TYPES (Nebula Engine Core)
#  Universal data structures for Nebula Engine integration
# ============================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


# ============================================================
#  SimulationRequest — Input to SimulationEngine
# ============================================================

@dataclass
class SimulationRequest:
    """
    Request for a physics simulation using Nebula Engine.
    
    This is the input that SimulationLLM generates and passes to
    SimulationEngine (which uses Nebula Engine).
    """
    # High-level intent
    scenario_type: str
    params: Dict[str, Any] = field(default_factory=dict)

    # Rendering
    output_resolution: Tuple[int, int] = (1920, 1080)
    target_fps: int = 60
    duration_seconds: float = 5.0

    render_style: str = "auto"
    render_quality: str = "ultra"
    render_passes: List[str] = field(default_factory=lambda: ["beauty"])

    # Sound
    sound_enabled: bool = True

    # Device
    gpu_preference: str = "auto"   # cpu | cuda | metal | auto

    # Streaming
    streaming_mode: bool = False

    # Limits
    max_steps: int = 3000
    max_wallclock_seconds: float = 30.0

    # Metadata / pipeline info
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================
#  SimulationFrame — Per-frame data from Nebula Engine
# ============================================================

@dataclass
class SimulationFrame:
    """
    Single frame of simulation data from Nebula Engine.
    
    Contains:
    - Frame metadata (index, time)
    - Physics state (entities, positions, velocities)
    - Render metadata (camera, lighting)
    """
    index: int
    time_seconds: float
    dt: float = 0.0
    absolute_time: float = 0.0

    # Physics state from Nebula Engine
    state: Dict[str, Any] = field(default_factory=dict)
    
    # Render metadata
    render_meta: Dict[str, Any] = field(default_factory=dict)

    # Backend debug info
    backend_info: Dict[str, Any] = field(default_factory=dict)


# ============================================================
#  SimulationResult — Output from SimulationEngine
# ============================================================

@dataclass
class SimulationResult:
    """
    Complete result from a Nebula Engine simulation run.
    
    Contains:
    - Success status
    - All simulation frames
    - Metrics and diagnostics
    - Video/audio paths (if rendered)
    """
    request: SimulationRequest
    success: bool
    error: Optional[str] = None

    summary: str = ""
    frames: List[SimulationFrame] = field(default_factory=list)
    video_path: Optional[str] = None

    metrics: Dict[str, Any] = field(default_factory=dict)
    debug_info: Dict[str, Any] = field(default_factory=dict)
