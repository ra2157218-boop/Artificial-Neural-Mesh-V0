# ============================================================
#  ANM-V3 — UNIVERSAL SIMULATION ENGINE
#  Simulate ANYTHING with accuracy and beautiful retro visuals
#  The most general-purpose 2D simulation engine
# ============================================================

from __future__ import annotations

import os
import time
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

from anm.sim.types import SimulationRequest, SimulationResult, SimulationFrame
from anm.sim.scenario_parser import ScenarioParser, ParsedScenario, parse_scenario
from anm.sim.universal_physics import (
    UniversalPhysics, PhysicsMode, PhysicsConstants,
    detect_physics_mode, vec2_length,
)
from anm.sim.universal_renderer import (
    UniversalRenderer, ENTITY_VISUALS, RETRO_PALETTE, get_universal_renderer,
)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None


# ============================================================
#  UNIVERSAL SIMULATION ENGINE
# ============================================================

class UniversalEngine:
    """
    ANM Universal Simulation Engine.
    
    This engine can simulate LITERALLY ANYTHING:
    - Natural language scenario input
    - Automatic physics mode detection
    - 50+ entity types with unique visuals
    - Multiple physics systems
    - Beautiful retro game graphics
    
    Examples:
    - "An apple falls from a tree"
    - "Two planets orbiting a star"
    - "A ball bouncing on a trampoline"
    - "Electrons orbiting an atom"
    - "Water drops falling into a pool"
    - "A rocket launching into space"
    - "Pendulum swinging back and forth"
    - "Two cars colliding"
    - "Particles exploding outward"
    """
    
    VERSION = "ANM-V3-UNIVERSAL"
    
    def __init__(
        self,
        output_dir: str = "sim_outputs",
        enable_shadows: bool = True,
        enable_glow: bool = True,
        enable_scanlines: bool = False,
        use_rk4_physics: bool = False,
    ):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Components
        self.parser = ScenarioParser()
        self.renderer = UniversalRenderer(
            output_dir=output_dir,
            enable_shadows=enable_shadows,
            enable_glow=enable_glow,
            enable_scanlines=enable_scanlines,
        )
        
        self.use_rk4 = use_rk4_physics
        
        # Rendering availability
        self.render_available = NUMPY_AVAILABLE and CV2_AVAILABLE
    
    def simulate(
        self,
        scenario: str,
        duration: float = 10.0,
        fps: int = 30,
        resolution: Tuple[int, int] = (800, 600),
        output_video: bool = True,
    ) -> SimulationResult:
        """
        Run a simulation from natural language description.
        
        Args:
            scenario: Natural language description of what to simulate
            duration: Duration in seconds
            fps: Frames per second
            resolution: Output resolution (width, height)
            output_video: Whether to render video
        
        Returns:
            SimulationResult with frames and video path
        """
        start_time = time.time()
        
        # Parse scenario
        parsed = self.parser.parse(scenario, duration)
        
        # Create simulation request
        request = SimulationRequest(
            scenario_type=parsed.scenario_type,
            duration_seconds=duration,
            target_fps=fps,
            output_resolution=resolution,
            params={
                "entities": parsed.entities,
                "environment": parsed.environment,
                "physics_mode": parsed.physics_mode,
                **parsed.parameters,
            }
        )
        
        # Run simulation
        return self.run(request, output_video=output_video)
    
    def run(
        self,
        request: SimulationRequest,
        output_video: bool = True,
    ) -> SimulationResult:
        """
        Run simulation from SimulationRequest.
        
        Args:
            request: Simulation request with all parameters
            output_video: Whether to render video
        
        Returns:
            SimulationResult
        """
        start_time = time.time()
        
        params = request.params or {}
        
        # Get entities
        entities = self._initialize_entities(request)
        
        # Determine physics mode
        physics_mode_str = params.get("physics_mode", "uniform_gravity")
        physics_mode = PhysicsMode(physics_mode_str) if physics_mode_str in [m.value for m in PhysicsMode] else PhysicsMode.UNIFORM_GRAVITY
        
        # Create physics engine
        physics = UniversalPhysics(
            mode=physics_mode,
            gravity=tuple(params.get("gravity", [0.0, PhysicsConstants.g])),
            damping=params.get("damping", PhysicsConstants.DAMPING),
            restitution=params.get("restitution", PhysicsConstants.RESTITUTION),
            friction=params.get("friction", PhysicsConstants.FRICTION),
            use_rk4=self.use_rk4,
        )
        
        # Set boundaries
        ground_y = self._find_ground_y(entities)
        physics.set_boundaries(
            ground_y=ground_y,
            ceiling_y=params.get("ceiling_y"),
            left_wall=params.get("left_wall"),
            right_wall=params.get("right_wall"),
        )
        
        # Set fluid if present
        environment = params.get("environment", {})
        if environment.get("type") == "fluid":
            physics.set_fluid(
                level=params.get("water_level", 100.0),
                density=params.get("fluid_density", PhysicsConstants.WATER_DENSITY),
            )
        
        # Run physics simulation
        frames = self._run_simulation(request, entities, physics)
        
        # Render video
        video_path = None
        if output_video and self.render_available:
            video_path = self._render_video(frames, request)
        
        elapsed = time.time() - start_time
        
        return SimulationResult(
            request=request,
            success=True,
            frames=frames,
            summary=f"Universal simulation: {request.scenario_type} ({len(frames)} frames, {physics_mode.value})",
            metrics={
                "simulation_time": elapsed,
                "frames_generated": len(frames),
                "video_rendered": video_path is not None,
                "video_path": video_path,
                "engine_version": self.VERSION,
                "physics_mode": physics_mode.value,
                "entity_count": len(entities),
            }
        )
    
    def _initialize_entities(self, request: SimulationRequest) -> List[Dict]:
        """Initialize entities from request."""
        params = request.params or {}
        
        # Check for explicit entities
        if "entities" in params:
            entities = []
            for e in params["entities"]:
                entity = {
                    "type": e.get("type", "object"),
                    "position": list(e.get("position", [0.0, 0.0])),
                    "velocity": list(e.get("velocity", [0.0, 0.0])),
                    "mass": e.get("mass", 1.0),
                    "radius": e.get("radius", 15.0),
                    "fixed": e.get("fixed", False),
                }
                # Copy additional properties
                for key, value in e.items():
                    if key not in entity:
                        entity[key] = value
                entities.append(entity)
            return entities
        
        # Fallback: create default based on scenario
        scenario = request.scenario_type.lower()
        return self._create_default_entities(scenario, params)
    
    def _create_default_entities(
        self,
        scenario: str,
        params: Dict,
    ) -> List[Dict]:
        """Create default entities for scenario."""
        entities = []
        
        if "apple" in scenario or "fall" in scenario:
            entities.append({
                "type": "apple",
                "position": [0.0, -100.0],
                "velocity": [0.0, 0.0],
                "mass": 0.2,
                "radius": 15.0,
                "fixed": False,
            })
            entities.append({
                "type": "ground",
                "position": [0.0, 150.0],
                "velocity": [0.0, 0.0],
                "mass": 1e10,
                "radius": 1000.0,
                "fixed": True,
            })
        
        elif "ball" in scenario or "bounce" in scenario:
            entities.append({
                "type": "ball",
                "position": [0.0, -100.0],
                "velocity": [50.0, 0.0],
                "mass": 0.5,
                "radius": 20.0,
                "fixed": False,
            })
            entities.append({
                "type": "ground",
                "position": [0.0, 150.0],
                "velocity": [0.0, 0.0],
                "mass": 1e10,
                "radius": 1000.0,
                "fixed": True,
            })
        
        elif "orbit" in scenario or "planet" in scenario:
            # Solar system
            entities.append({
                "type": "sun",
                "position": [0.0, 0.0],
                "velocity": [0.0, 0.0],
                "mass": 1e8,
                "radius": 40.0,
                "fixed": True,
            })
            
            num_planets = params.get("num_planets", 3)
            for i in range(num_planets):
                angle = 2 * math.pi * i / num_planets
                orbit_r = 100 + i * 50
                orbital_v = math.sqrt(6.674e-2 * 1e8 / orbit_r)
                
                entities.append({
                    "type": "planet",
                    "position": [orbit_r * math.cos(angle), orbit_r * math.sin(angle)],
                    "velocity": [-orbital_v * math.sin(angle), orbital_v * math.cos(angle)],
                    "mass": 1e4,
                    "radius": 12.0 + i * 3,
                    "fixed": False,
                })
        
        else:
            # Generic object
            entities.append({
                "type": "object",
                "position": [0.0, -50.0],
                "velocity": [0.0, 0.0],
                "mass": 1.0,
                "radius": 15.0,
                "fixed": False,
            })
            entities.append({
                "type": "ground",
                "position": [0.0, 150.0],
                "velocity": [0.0, 0.0],
                "mass": 1e10,
                "radius": 1000.0,
                "fixed": True,
            })
        
        return entities
    
    def _find_ground_y(self, entities: List[Dict]) -> Optional[float]:
        """Find ground Y position from entities."""
        for e in entities:
            if e.get("type") == "ground":
                return e["position"][1]
        return None
    
    def _run_simulation(
        self,
        request: SimulationRequest,
        entities: List[Dict],
        physics: UniversalPhysics,
    ) -> List[SimulationFrame]:
        """Run physics simulation."""
        frames = []
        dt = 1.0 / request.target_fps
        total_steps = int(request.duration_seconds * request.target_fps)
        
        for step in range(total_steps):
            # Update physics
            physics.update(entities, dt)
            
            # Create frame
            frame = SimulationFrame(
                index=step,
                time_seconds=step * dt,
                dt=dt,
                absolute_time=step * dt,
                state={"entities": self._copy_entities(entities)}
            )
            frames.append(frame)
        
        return frames
    
    def _copy_entities(self, entities: List[Dict]) -> List[Dict]:
        """Deep copy entities for frame storage."""
        return [
            {
                **e,
                "position": list(e["position"]),
                "velocity": list(e["velocity"]),
            }
            for e in entities
        ]
    
    def _render_video(
        self,
        frames: List[SimulationFrame],
        request: SimulationRequest,
    ) -> Optional[str]:
        """Render frames to video."""
        if not frames or not self.render_available:
            return None
        
        if cv2 is None or np is None:
            return None
        
        timestamp = int(time.time())
        scenario = request.scenario_type.replace("_", "-").replace(" ", "-")
        filename = f"universal_{scenario}_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, filename)
        
        width, height = request.output_resolution
        fps = request.target_fps
        
        # Create video writer
        codecs = [('avc1', 'H.264'), ('mp4v', 'MPEG-4')]
        video_writer = None
        
        for fourcc_str, _ in codecs:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            video_writer = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))
            if video_writer.isOpened():
                break
        
        if video_writer is None or not video_writer.isOpened():
            return None
        
        try:
            for i, frame in enumerate(frames):
                image = self._render_frame(frame, request, width, height, i, len(frames))
                if image is not None:
                    video_writer.write(image)
            
            video_writer.release()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            return None
        
        except Exception as e:
            if video_writer.isOpened():
                video_writer.release()
            return None
    
    def _render_frame(
        self,
        frame: SimulationFrame,
        request: SimulationRequest,
        width: int,
        height: int,
        frame_index: int,
        total_frames: int,
    ) -> Optional[np.ndarray]:
        """Render a single frame."""
        if np is None or cv2 is None:
            return None
        
        image = np.zeros((height, width, 3), dtype=np.uint8)
        entities = frame.state.get("entities", [])
        
        # Detect scene type
        scene_type = self._detect_scene_type(entities, request)
        
        # Render background
        self._render_background(image, scene_type, width, height)
        
        # Calculate camera
        camera_pos, camera_scale = self._calculate_camera(entities, width, height)
        
        # Render grid
        self._render_grid(image, camera_pos, camera_scale, width, height, scene_type)
        
        # Render environment (ground)
        self._render_environment(image, entities, camera_pos, camera_scale, width, height)
        
        # Sort and render entities
        sorted_entities = sorted(
            [e for e in entities if e.get("type") not in ("ground", "wall", "floor")],
            key=lambda e: e.get("position", [0, 0])[1],
            reverse=True,
        )
        
        for entity in sorted_entities:
            self._render_entity(image, entity, camera_pos, camera_scale, width, height)
        
        # Render UI
        self._render_ui(image, frame, frame_index, total_frames, width, height)
        
        # Convert to BGR
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    def _detect_scene_type(self, entities: List[Dict], request: SimulationRequest) -> str:
        """Detect scene type for background styling."""
        types = [e.get("type", "").lower() for e in entities]
        scenario = request.scenario_type.lower()
        
        if any(t in types for t in ["black_hole", "neutron_star", "sun", "star", "planet", "moon", "comet", "asteroid", "galaxy"]):
            return "space"
        elif any(t in types for t in ["ground", "floor", "grass"]):
            return "outdoor"
        elif any(k in scenario for k in ["space", "orbit", "cosmic", "star"]):
            return "space"
        else:
            return "default"
    
    def _render_background(
        self,
        image: np.ndarray,
        scene_type: str,
        width: int,
        height: int,
    ):
        """Render background."""
        if scene_type == "space":
            # Deep space gradient
            for y in range(height):
                t = y / height
                r = int(10 + t * 15)
                g = int(10 + t * 10)
                b = int(30 + t * 20)
                image[y, :] = [r, g, b]
            
            # Stars
            np.random.seed(42)
            for _ in range(100):
                sx = np.random.randint(0, width)
                sy = np.random.randint(0, height)
                brightness = np.random.choice([150, 200, 255])
                size = np.random.choice([1, 2])
                if size == 1:
                    image[sy, sx] = [brightness, brightness, brightness]
                else:
                    y1, y2 = max(0, sy-1), min(height, sy+2)
                    x1, x2 = max(0, sx-1), min(width, sx+2)
                    image[y1:y2, x1:x2] = [brightness, brightness, brightness]
        
        elif scene_type == "outdoor":
            # Sky gradient
            bands = 8
            for band in range(bands):
                y_start = int(band * height * 0.6 / bands)
                y_end = int((band + 1) * height * 0.6 / bands)
                t = band / bands
                r = int(135 - t * 50)
                g = int(206 - t * 50)
                b = int(250 - t * 20)
                image[y_start:y_end, :] = [r, g, b]
            
            ground_start = int(height * 0.6)
            image[ground_start:, :] = RETRO_PALETTE["grass"]
        
        else:
            for y in range(height):
                t = y / height
                r = int(60 + t * 30)
                g = int(60 + t * 40)
                b = int(80 + t * 40)
                image[y, :] = [r, g, b]
    
    def _calculate_camera(
        self,
        entities: List[Dict],
        width: int,
        height: int,
    ) -> Tuple[List[float], float]:
        """Calculate camera position and scale."""
        if not entities:
            return [0.0, 0.0], 1.0
        
        positions = [e.get("position", [0, 0]) for e in entities]
        radii = [e.get("radius", 10) for e in entities]
        
        min_x = min(p[0] - r for p, r in zip(positions, radii))
        max_x = max(p[0] + r for p, r in zip(positions, radii))
        min_y = min(p[1] - r for p, r in zip(positions, radii))
        max_y = max(p[1] + r for p, r in zip(positions, radii))
        
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        
        entity_width = max_x - min_x + 100
        entity_height = max_y - min_y + 100
        
        scale_x = (width * 0.7) / entity_width if entity_width > 0 else 1.0
        scale_y = (height * 0.7) / entity_height if entity_height > 0 else 1.0
        scale = min(scale_x, scale_y)
        scale = max(0.5, min(scale, 10.0))
        
        return [center_x, center_y], scale
    
    def _render_grid(
        self,
        image: np.ndarray,
        camera_pos: List[float],
        camera_scale: float,
        width: int,
        height: int,
        scene_type: str,
    ):
        """Render grid overlay."""
        if cv2 is None:
            return
        
        if scene_type == "space":
            grid_color = (30, 30, 50)
        else:
            grid_color = (200, 220, 200)
        
        grid_spacing = 50.0
        center_x = width // 2
        center_y = height // 2
        
        # Vertical lines
        world_x = camera_pos[0] - (width / 2) / camera_scale
        world_x = math.floor(world_x / grid_spacing) * grid_spacing
        while world_x < camera_pos[0] + (width / 2) / camera_scale:
            screen_x = int((world_x - camera_pos[0]) * camera_scale + center_x)
            if 0 <= screen_x < width:
                for y in range(0, height, 8):
                    if y + 2 < height:
                        image[y:y+2, screen_x] = grid_color
            world_x += grid_spacing
        
        # Horizontal lines
        world_y = camera_pos[1] - (height / 2) / camera_scale
        world_y = math.floor(world_y / grid_spacing) * grid_spacing
        while world_y < camera_pos[1] + (height / 2) / camera_scale:
            screen_y = int((world_y - camera_pos[1]) * camera_scale + center_y)
            if 0 <= screen_y < height:
                for x in range(0, width, 8):
                    if x + 2 < width:
                        image[screen_y, x:x+2] = grid_color
            world_y += grid_spacing
    
    def _render_environment(
        self,
        image: np.ndarray,
        entities: List[Dict],
        camera_pos: List[float],
        camera_scale: float,
        width: int,
        height: int,
    ):
        """Render environment entities."""
        if cv2 is None:
            return
        
        for entity in entities:
            entity_type = entity.get("type", "").lower()
            
            if entity_type in ("ground", "floor"):
                pos = entity.get("position", [0, 100])
                screen_y = int((pos[1] - camera_pos[1]) * camera_scale + height / 2)
                
                if screen_y < height:
                    material = entity.get("material", "earth")
                    
                    # Top layer
                    grass_height = 8
                    if screen_y - grass_height >= 0:
                        image[screen_y-grass_height:screen_y, :] = RETRO_PALETTE["grass"]
                    
                    # Ground fill
                    if screen_y < height:
                        image[screen_y:, :] = RETRO_PALETTE["ground"]
                    
                    # Brick pattern
                    brick_h = 16
                    brick_w = 32
                    for by in range(screen_y, height, brick_h):
                        offset = (by // brick_h % 2) * (brick_w // 2)
                        for bx in range(offset, width, brick_w):
                            if by + brick_h < height:
                                cv2.rectangle(
                                    image,
                                    (bx, by),
                                    (min(bx + brick_w, width), min(by + brick_h, height)),
                                    RETRO_PALETTE["ground_dark"],
                                    1
                                )
    
    def _render_entity(
        self,
        image: np.ndarray,
        entity: Dict,
        camera_pos: List[float],
        camera_scale: float,
        width: int,
        height: int,
    ):
        """Render an entity using universal renderer."""
        pos = entity.get("position", [0, 0])
        base_radius = entity.get("radius", 10)
        
        screen_x = int((pos[0] - camera_pos[0]) * camera_scale + width / 2)
        screen_y = int((pos[1] - camera_pos[1]) * camera_scale + height / 2)
        radius = max(20, int(base_radius * camera_scale))
        
        # Use universal renderer
        self.renderer.render_entity(image, entity, screen_x, screen_y, radius)
        
        # Draw velocity arrow
        velocity = entity.get("velocity", [0, 0])
        vel_mag = vec2_length(velocity)
        if vel_mag > 1.0:
            self._draw_velocity_arrow(image, screen_x, screen_y, velocity, vel_mag, camera_scale)
    
    def _draw_velocity_arrow(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        velocity: List[float],
        vel_mag: float,
        camera_scale: float,
    ):
        """Draw velocity arrow."""
        if cv2 is None:
            return
        
        arrow_len = min(60, max(20, vel_mag * camera_scale * 0.3))
        dx = velocity[0] / vel_mag
        dy = velocity[1] / vel_mag
        
        end_x = int(x + dx * arrow_len)
        end_y = int(y + dy * arrow_len)
        
        # Arrow line
        cv2.line(image, (x, y), (end_x, end_y), RETRO_PALETTE["black"], 6)
        cv2.line(image, (x, y), (end_x, end_y), RETRO_PALETTE["yellow"], 4)
        
        # Arrow head
        head_len = 10
        angle = math.atan2(dy, dx)
        for offset in [-0.5, 0.5]:
            hx = int(end_x - head_len * math.cos(angle + offset))
            hy = int(end_y - head_len * math.sin(angle + offset))
            cv2.line(image, (end_x, end_y), (hx, hy), RETRO_PALETTE["black"], 6)
            cv2.line(image, (end_x, end_y), (hx, hy), RETRO_PALETTE["yellow"], 4)
    
    def _render_ui(
        self,
        image: np.ndarray,
        frame: SimulationFrame,
        frame_index: int,
        total_frames: int,
        width: int,
        height: int,
    ):
        """Render UI overlay."""
        if cv2 is None:
            return
        
        # Top panel
        panel_height = 40
        cv2.rectangle(image, (0, 0), (width, panel_height), RETRO_PALETTE["ui_bg"], -1)
        cv2.line(image, (0, panel_height), (width, panel_height), RETRO_PALETTE["ui_border"], 2)
        
        # Time
        time_text = f"TIME: {frame.time_seconds:.2f}s"
        self._draw_text(image, time_text, 10, 28, RETRO_PALETTE["text"])
        
        # Frame counter
        frame_text = f"FRAME: {frame_index + 1}/{total_frames}"
        self._draw_text(image, frame_text, width - 200, 28, RETRO_PALETTE["text"])
        
        # Progress bar
        bar_width = 200
        bar_height = 8
        bar_x = (width - bar_width) // 2
        bar_y = 16
        
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     RETRO_PALETTE["gray_dark"], -1)
        
        progress = (frame_index + 1) / max(total_frames, 1)
        fill_width = int(bar_width * progress)
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                     RETRO_PALETTE["green"], -1)
        
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     RETRO_PALETTE["ui_border"], 1)
    
    def _draw_text(
        self,
        image: np.ndarray,
        text: str,
        x: int,
        y: int,
        color: Tuple,
    ):
        """Draw text with shadow."""
        if cv2 is None:
            return
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.6
        thickness = 2
        
        cv2.putText(image, text, (x + 2, y + 2), font, scale, RETRO_PALETTE["text_shadow"], thickness)
        cv2.putText(image, text, (x, y), font, scale, color, thickness)


# ============================================================
#  CONVENIENCE FUNCTIONS
# ============================================================

def simulate_anything(
    scenario: str,
    duration: float = 10.0,
    fps: int = 30,
    resolution: Tuple[int, int] = (800, 600),
    output_dir: str = "sim_outputs",
) -> SimulationResult:
    """
    Simulate ANY scenario from natural language.
    
    Args:
        scenario: Natural language description
        duration: Duration in seconds
        fps: Frames per second
        resolution: Output resolution
        output_dir: Output directory for video
    
    Returns:
        SimulationResult with video path
    
    Examples:
        simulate_anything("An apple falls from a tree onto grass")
        simulate_anything("Two planets orbiting a star")
        simulate_anything("A ball bouncing on a trampoline")
    """
    engine = UniversalEngine(output_dir=output_dir)
    return engine.simulate(scenario, duration, fps, resolution)


# Shared engine instance
_universal_engine: Optional[UniversalEngine] = None


def get_universal_engine() -> UniversalEngine:
    """Get shared universal engine instance."""
    global _universal_engine
    if _universal_engine is None:
        _universal_engine = UniversalEngine()
    return _universal_engine
