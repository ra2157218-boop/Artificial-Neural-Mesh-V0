# ============================================================
#  ANM-V3 — SIMULATION ENGINE v3.0 (RETRO 2D + NEBULA CORE)
#  Primary: Retro 2D Engine with pixel-perfect visuals
#  Secondary: Nebula Engine C++ physics (for complex scenarios)
#  LawBook v1.2 Compliant • Deterministic • Safe
# ============================================================

from __future__ import annotations

import os
import time
import subprocess
from typing import Dict, Any, Optional, Callable, List

from anm.sim.types import SimulationRequest, SimulationResult, SimulationFrame
from anm.sim.nebula_bridge import get_nebula_bridge, is_nebula_available
from anm.sim.video_renderer import VideoRenderer
from anm.sim.cinematic_renderer import CinematicRenderer
from anm.sim.metal_gpu_renderer import MetalGPURenderer
from anm.sim.interstellar_renderer import InterstellarRenderer
from anm.sim.advanced_renderer import AdvancedRenderer
from anm.sim.ray_tracing_renderer import RayTracingRenderer
from anm.sim.renderer_2d import Renderer2D
from anm.sim.engine_2d import SimulationEngine2D


# ============================================================
#  DEVICE INFO
# ============================================================

class _DeviceInfo:
    def __init__(self, device: str, backend: str, reason: str) -> None:
        self.device = device          # "cpu" | "metal" | "cuda"
        self.backend = backend        # "nebula" (Nebula Engine)
        self.reason = reason

    def as_dict(self) -> Dict[str, Any]:
        return {
            "device": self.device,
            "backend": self.backend,
            "reason": self.reason,
        }


# ============================================================
#  SIMULATION ENGINE (Nebula Engine Core)
# ============================================================

class SimulationEngine:
    """
    ANM Simulation Engine v3.0 — Retro 2D + Nebula Core
    
    PRIMARY: Uses SimulationEngine2D for retro pixel-perfect 2D physics
    SECONDARY: Nebula Engine C++ for complex 3D scenarios
    
    Steps:
        1) Validate SimulationRequest
        2) Route to 2D engine (primary) or Nebula (secondary)
        3) Render with retro 2D visuals
        4) Return SimulationResult
    """
    
    def __init__(
        self,
        output_dir: str = "sim_outputs",
        max_wallclock_seconds: float = float("inf"),
        max_total_frames: int = 10_000_000,
        force_gpu: bool = True,
        prefer_2d: bool = True,  # Prefer 2D engine for general simulations
    ) -> None:
        """
        Initialize SimulationEngine with retro 2D as primary.
        
        Args:
            output_dir: Directory for simulation outputs
            max_wallclock_seconds: Maximum wall-clock time for simulation
            max_total_frames: Maximum number of frames to generate
            force_gpu: Force GPU usage (default: True)
            prefer_2d: Use 2D engine as primary (default: True)
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.max_wallclock_seconds = float(max_wallclock_seconds)
        self.max_total_frames = int(max_total_frames)
        self.force_gpu = force_gpu
        self.prefer_2d = prefer_2d
        
        # PRIMARY: Retro 2D Simulation Engine
        try:
            self.engine_2d = SimulationEngine2D(output_dir=self.output_dir)
        except Exception as e:
            print(f"Warning: 2D engine init failed: {e}")
            self.engine_2d = None
        
        # Nebula Engine bridge (secondary, for complex scenarios)
        self.nebula_bridge = get_nebula_bridge()
        self.nebula_available = is_nebula_available()
        
        # 2D RENDERER (Primary - Retro pixel-perfect visuals)
        try:
            self.renderer_2d = Renderer2D(output_dir=self.output_dir)
            if not self.renderer_2d.available:
                self.renderer_2d = None
        except Exception:
            self.renderer_2d = None
        
        # Legacy 3D renderers (fallback only)
        try:
            self.ray_tracing_renderer = RayTracingRenderer(output_dir=self.output_dir)
            if not self.ray_tracing_renderer.available:
                self.ray_tracing_renderer = None
        except Exception:
            self.ray_tracing_renderer = None
        
        try:
            self.advanced_renderer = AdvancedRenderer(output_dir=self.output_dir)
            if not self.advanced_renderer.available:
                self.advanced_renderer = None
        except Exception:
            self.advanced_renderer = None
        
        try:
            self.interstellar_renderer = InterstellarRenderer(output_dir=self.output_dir)
            if not self.interstellar_renderer.available:
                self.interstellar_renderer = None
        except Exception:
            self.interstellar_renderer = None
        
        try:
            self.metal_gpu_renderer = MetalGPURenderer(output_dir=self.output_dir)
        except Exception:
            self.metal_gpu_renderer = None
        
        # CPU renderers (fallback)
        if self.force_gpu:
            self.cinematic_renderer = None
            self.video_renderer = None
        else:
            try:
                self.cinematic_renderer = CinematicRenderer(output_dir=self.output_dir)
            except Exception:
                self.cinematic_renderer = None
            try:
                self.video_renderer = VideoRenderer(output_dir=self.output_dir)
            except Exception:
                self.video_renderer = None
        
        # Engine is available if 2D engine OR Nebula is available
        if not self.engine_2d and not self.nebula_available:
            raise RuntimeError(
                "SimulationEngine: No simulation backend available. "
                "Either 2D engine or Nebula Engine required."
            )
    
    # --------------------------------------------------------
    #  DEVICE SELECTION
    # --------------------------------------------------------
    
    def _choose_device(self, request: SimulationRequest) -> _DeviceInfo:
        """Choose device - GPU ONLY (no CPU fallback)."""
        # FORCE GPU - ignore CPU preference
        if self.force_gpu:
            return _DeviceInfo("metal", "nebula", "GPU-ONLY: Nebula Engine with Metal GPU rendering.")
        
        # Legacy mode (not recommended)
        pref = str(getattr(request, "gpu_preference", "auto")).lower()
        if pref in {"metal", "mps", "gpu"}:
            return _DeviceInfo("metal", "nebula", "Nebula Engine with Metal rendering.")
        
        # Even in legacy mode, prefer GPU
        return _DeviceInfo("metal", "nebula", "Nebula Engine with GPU acceleration.")
    
    # --------------------------------------------------------
    #  MAIN ENTRY
    # --------------------------------------------------------
    
    def run(
        self,
        request: SimulationRequest,
        backend_fn: Optional[Callable[[SimulationRequest, _DeviceInfo], SimulationResult]] = None,
        frame_callback: Optional[Callable[[SimulationFrame], None]] = None,
    ) -> SimulationResult:
        """
        Run a physics simulation.
        
        PRIMARY: Uses retro 2D engine (SimulationEngine2D)
        SECONDARY: Falls back to Nebula Engine for complex scenarios
        
        Args:
            request: SimulationRequest from SimulationLLM
            backend_fn: Optional custom backend (for backward compatibility)
            frame_callback: Optional callback for each frame
            
        Returns:
            SimulationResult with frames and retro 2D video
        """
        device_info = self._choose_device(request)
        t0 = time.time()
        
        # Check if 2D mode is requested or preferred
        use_2d = self.prefer_2d or self._should_use_2d(request)
        
        # PRIMARY: Use 2D engine for retro pixel-perfect simulations
        if use_2d and self.engine_2d:
            try:
                result = self.engine_2d.run(request)
                
                # Normalize result
                result = self._normalize_result(request, result, t0, device_info)
                result.debug_info["engine_mode"] = "retro_2d"
                result.debug_info["renderer"] = "retro_2d"
                
                # Frame callback
                if frame_callback and result.frames:
                    for frame in result.frames:
                        frame_callback(frame)
                
                return result
            
            except Exception as e:
                print(f"2D engine failed, falling back to Nebula: {e}")
                # Fall through to Nebula engine
        
        # SECONDARY: Use Nebula Engine for complex scenarios
        # Custom backend (for backward compatibility)
        if backend_fn is not None:
            raw_result = backend_fn(request, device_info)
            result = self._normalize_result(request, raw_result, t0, device_info)
            return result
        
        # Use Nebula Engine
        if not self.nebula_available:
            return SimulationResult(
                request=request,
                success=False,
                error="No simulation backend available",
                summary="No simulation backend available (2D engine failed, Nebula not found)",
            )
        
        try:
            frames = self.nebula_bridge.run_simulation(request)
            
            # Cap frames
            if len(frames) > self.max_total_frames:
                frames = frames[:self.max_total_frames]
            
            # Frame callback
            if frame_callback:
                for frame in frames:
                    frame_callback(frame)
            
            # Build result
            result = SimulationResult(
                request=request,
                success=True,
                frames=frames,
                summary=f"Nebula Engine simulation: {request.scenario_type} ({len(frames)} frames)",
            )
            
            # Normalize
            result = self._normalize_result(request, result, t0, device_info)
            
            # Render video with 2D renderer
            if result.frames:
                video_path = self._render_cinematic_video(request, result)
                if video_path:
                    result.video_path = video_path
                    result.summary += f" Video: {video_path}"
            
            return result
        
        except Exception as e:
            return SimulationResult(
                request=request,
                success=False,
                error=str(e),
                summary=f"Simulation failed: {e}",
            )
    
    def _should_use_2d(self, request: SimulationRequest) -> bool:
        """Determine if 2D engine should be used for this request."""
        scenario = (request.scenario_type or "").lower()
        params = request.params or {}
        
        # Explicit 2D request
        if params.get("dimensions") == "2d" or params.get("mode") == "2d":
            return True
        
        # Common 2D-friendly scenarios
        scenarios_2d = [
            "fall", "bounce", "ball", "apple", "gravity", "collision",
            "pendulum", "spring", "projectile", "drop", "throw",
            "orbit", "nbody", "merger", "binary",
        ]
        
        if any(s in scenario for s in scenarios_2d):
            return True
        
        # Default to 2D for general simulations
        return True
    
    # --------------------------------------------------------
    #  RESULT NORMALIZATION
    # --------------------------------------------------------
    
    def _normalize_result(
        self,
        request: SimulationRequest,
        result: SimulationResult,
        start: float,
        device_info: _DeviceInfo,
    ) -> SimulationResult:
        """Normalize and add metadata to SimulationResult."""
        # Frames list normalization
        if result.frames is None:
            result.frames = []
        
        # Frame cap
        if len(result.frames) > self.max_total_frames:
            result.frames = result.frames[:self.max_total_frames]
            result.metrics["frames_truncated_to"] = self.max_total_frames
        
        # Wall clock
        elapsed = time.time() - start
        result.metrics.setdefault("wallclock_seconds", elapsed)
        result.metrics.setdefault("device_info", device_info.as_dict())
        result.metrics.setdefault("frame_count", len(result.frames))
        
        # Timeout handling
        if elapsed > self.max_wallclock_seconds:
            result.metrics["timeout"] = True
            result.success = False
        
        # Ensure success is a proper bool
        if not isinstance(result.success, bool):
            result.success = bool(result.frames) and not result.metrics.get("timeout", False)
        
        # Debug info
        result.debug_info.setdefault("engine_version", "ANM-V3-NEBULA-CORE-v3.0")
        result.debug_info.setdefault("backend", "nebula_engine")
        result.debug_info.setdefault("nebula_available", self.nebula_available)
        result.debug_info.setdefault("backend_device", device_info.as_dict())
        
        return result
    
    # --------------------------------------------------------
    #  VIDEO RENDERING
    # --------------------------------------------------------
    
    def _render_cinematic_video(
        self,
        request: SimulationRequest,
        result: SimulationResult,
    ) -> Optional[str]:
        """
        Render SimulationFrames to video with retro 2D visuals.
        
        PRIMARY: Retro 2D renderer (pixel-perfect game visuals)
        FALLBACK: Legacy 3D renderers
        
        Args:
            request: Original SimulationRequest
            result: SimulationResult with frames
            
        Returns:
            Path to video file, or None if failed
        """
        if not result.frames:
            return None
        
        timestamp = int(time.time())
        scenario = request.scenario_type.replace("_", "-")
        
        try:
            # PRIMARY: Retro 2D Renderer (pixel-perfect game visuals)
            if self.renderer_2d and self.renderer_2d.available:
                filename = f"retro2d_{scenario}_{timestamp}.mp4"
                
                video_path = self.renderer_2d.render_frames_to_video(
                    frames=result.frames,
                    request=request,
                    output_filename=filename,
                )
                
                if video_path:
                    result.metrics["video_rendered"] = True
                    result.metrics["video_path"] = video_path
                    result.metrics["video_frames"] = len(result.frames)
                    result.metrics["video_quality"] = "retro_2d"
                    result.metrics["gpu_accelerated"] = True
                    result.metrics["renderer"] = "retro_2d"
                    result.metrics["dimensions"] = "2D"
                    result.metrics["style"] = "retro_pixel"
                    return video_path
            
            # FALLBACK: Legacy 3D renderers
            renderers = [
                (self.interstellar_renderer, "interstellar"),
                (self.advanced_renderer, "advanced"),
                (self.ray_tracing_renderer, "raytraced"),
                (self.metal_gpu_renderer, "gpu_metal"),
                (self.cinematic_renderer, "cinematic"),
                (self.video_renderer, "standard"),
            ]
            
            for renderer, quality_name in renderers:
                if renderer and getattr(renderer, 'available', False):
                    try:
                        filename = f"{quality_name}_{scenario}_{timestamp}.mp4"
                        
                        # Some renderers support pov_entity_id
                        if hasattr(renderer, 'render_frames_to_video'):
                            try:
                                video_path = renderer.render_frames_to_video(
                                    frames=result.frames,
                                    request=request,
                                    output_filename=filename,
                                    pov_entity_id=None,
                                )
                            except TypeError:
                                # Renderer doesn't support pov_entity_id
                                video_path = renderer.render_frames_to_video(
                                    frames=result.frames,
                                    request=request,
                                    output_filename=filename,
                                )
                            
                            if video_path:
                                result.metrics["video_rendered"] = True
                                result.metrics["video_path"] = video_path
                                result.metrics["video_frames"] = len(result.frames)
                                result.metrics["video_quality"] = quality_name
                                result.metrics["renderer"] = quality_name
                                return video_path
                    except Exception:
                        continue
            
            # No renderer available
            result.metrics["video_rendered"] = False
            result.metrics["video_error"] = "No renderer available"
            return None
        
        except Exception as e:
            result.metrics["video_rendered"] = False
            result.metrics["video_error"] = str(e)
            return None
