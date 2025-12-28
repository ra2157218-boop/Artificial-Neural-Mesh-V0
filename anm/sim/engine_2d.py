# ============================================================
#  ANM-V3 — GENERAL PURPOSE 2D SIMULATION ENGINE
#  Retro-style physics simulation for any scenario
#  Flexible, extensible, and visually appealing
# ============================================================

from __future__ import annotations

import os
import time
import math
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field

from anm.sim.types import SimulationRequest, SimulationResult, SimulationFrame
from anm.sim.nebula_bridge import get_nebula_bridge, is_nebula_available
from anm.sim.renderer_2d import Renderer2D


# ============================================================
#  PHYSICS CONSTANTS
# ============================================================

# Gravitational constant (scaled for simulation)
G_CONSTANT = 6.674e-2  # Adjusted for visible effects

# Default damping for realistic motion
DEFAULT_DAMPING = 0.999

# Collision restitution (bounciness)
DEFAULT_RESTITUTION = 0.7


# ============================================================
#  PHYSICS HELPERS
# ============================================================

def vec2_length(v: List[float]) -> float:
    """Calculate 2D vector length."""
    return math.sqrt(v[0]**2 + v[1]**2)


def vec2_normalize(v: List[float]) -> List[float]:
    """Normalize 2D vector."""
    length = vec2_length(v)
    if length < 1e-10:
        return [0.0, 0.0]
    return [v[0] / length, v[1] / length]


def vec2_dot(a: List[float], b: List[float]) -> float:
    """Dot product of 2D vectors."""
    return a[0] * b[0] + a[1] * b[1]


def vec2_subtract(a: List[float], b: List[float]) -> List[float]:
    """Subtract 2D vectors."""
    return [a[0] - b[0], a[1] - b[1]]


def vec2_add(a: List[float], b: List[float]) -> List[float]:
    """Add 2D vectors."""
    return [a[0] + b[0], a[1] + b[1]]


def vec2_scale(v: List[float], s: float) -> List[float]:
    """Scale 2D vector."""
    return [v[0] * s, v[1] * s]


# ============================================================
#  FORCE FUNCTIONS
# ============================================================

def gravity_force(
    entity1: Dict,
    entity2: Dict,
    g_constant: float = G_CONSTANT,
) -> List[float]:
    """Calculate gravitational force between two entities."""
    pos1 = entity1["position"]
    pos2 = entity2["position"]
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist_sq = dx*dx + dy*dy
    dist = math.sqrt(dist_sq) + 1e-6
    
    # F = G * m1 * m2 / r^2
    force_mag = g_constant * entity1["mass"] * entity2["mass"] / dist_sq
    
    # Limit force to prevent numerical explosion
    force_mag = min(force_mag, entity1["mass"] * 1000)
    
    return [force_mag * dx / dist, force_mag * dy / dist]


def uniform_gravity_force(
    entity: Dict,
    gravity: Tuple[float, float] = (0.0, 9.8),
) -> List[float]:
    """Apply uniform gravity (like Earth's surface)."""
    return [gravity[0] * entity["mass"], gravity[1] * entity["mass"]]


def spring_force(
    entity1: Dict,
    entity2: Dict,
    rest_length: float,
    stiffness: float = 100.0,
) -> List[float]:
    """Calculate spring force between two entities."""
    pos1 = entity1["position"]
    pos2 = entity2["position"]
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = math.sqrt(dx*dx + dy*dy) + 1e-6
    
    # F = -k * (d - rest_length)
    stretch = dist - rest_length
    force_mag = stiffness * stretch
    
    return [force_mag * dx / dist, force_mag * dy / dist]


# ============================================================
#  COLLISION DETECTION
# ============================================================

def check_circle_collision(entity1: Dict, entity2: Dict) -> Optional[Dict]:
    """Check collision between two circular entities."""
    pos1 = entity1["position"]
    pos2 = entity2["position"]
    r1 = entity1.get("radius", 10)
    r2 = entity2.get("radius", 10)
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist_sq = dx*dx + dy*dy
    
    min_dist = r1 + r2
    
    if dist_sq < min_dist * min_dist:
        dist = math.sqrt(dist_sq) + 1e-6
        # Collision normal
        nx = dx / dist
        ny = dy / dist
        # Penetration depth
        penetration = min_dist - dist
        
        return {
            "normal": [nx, ny],
            "penetration": penetration,
            "entity1": entity1,
            "entity2": entity2,
        }
    
    return None


def check_ground_collision(entity: Dict, ground_y: float) -> Optional[Dict]:
    """Check collision with ground plane."""
    pos = entity["position"]
    radius = entity.get("radius", 10)
    
    if pos[1] + radius > ground_y:
        penetration = pos[1] + radius - ground_y
        return {
            "normal": [0.0, -1.0],
            "penetration": penetration,
            "ground_y": ground_y,
        }
    
    return None


# ============================================================
#  COLLISION RESOLUTION
# ============================================================

def resolve_circle_collision(
    entity1: Dict,
    entity2: Dict,
    collision: Dict,
    restitution: float = DEFAULT_RESTITUTION,
):
    """Resolve collision between two circular entities."""
    normal = collision["normal"]
    penetration = collision["penetration"]
    
    # Separate objects
    total_mass = entity1["mass"] + entity2["mass"]
    ratio1 = entity2["mass"] / total_mass
    ratio2 = entity1["mass"] / total_mass
    
    entity1["position"][0] -= normal[0] * penetration * ratio1
    entity1["position"][1] -= normal[1] * penetration * ratio1
    entity2["position"][0] += normal[0] * penetration * ratio2
    entity2["position"][1] += normal[1] * penetration * ratio2
    
    # Calculate relative velocity
    rel_vel = vec2_subtract(entity1["velocity"], entity2["velocity"])
    vel_along_normal = vec2_dot(rel_vel, normal)
    
    # Don't resolve if velocities are separating
    if vel_along_normal > 0:
        return
    
    # Calculate impulse
    j = -(1 + restitution) * vel_along_normal
    j /= 1 / entity1["mass"] + 1 / entity2["mass"]
    
    # Apply impulse
    impulse = vec2_scale(normal, j)
    entity1["velocity"][0] += impulse[0] / entity1["mass"]
    entity1["velocity"][1] += impulse[1] / entity1["mass"]
    entity2["velocity"][0] -= impulse[0] / entity2["mass"]
    entity2["velocity"][1] -= impulse[1] / entity2["mass"]


def resolve_ground_collision(
    entity: Dict,
    collision: Dict,
    restitution: float = DEFAULT_RESTITUTION,
):
    """Resolve collision with ground plane."""
    penetration = collision["penetration"]
    ground_y = collision["ground_y"]
    
    # Push out of ground
    entity["position"][1] = ground_y - entity.get("radius", 10)
    
    # Bounce velocity
    if entity["velocity"][1] > 0:
        entity["velocity"][1] *= -restitution
        
        # Apply friction to horizontal velocity
        entity["velocity"][0] *= 0.95


# ============================================================
#  2D SIMULATION ENGINE
# ============================================================

class SimulationEngine2D:
    """
    ANM General Purpose 2D Simulation Engine
    
    Features:
    - Multiple physics modes (n-body, uniform gravity, springs)
    - Collision detection and response
    - Flexible entity system
    - Retro-style visualization
    - Works with any scenario
    """
    
    def __init__(
        self,
        output_dir: str = "sim_outputs",
        force_gpu: bool = True,
    ):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.force_gpu = force_gpu
        
        # Nebula Engine bridge
        self.nebula_bridge = None
        if is_nebula_available():
            try:
                self.nebula_bridge = get_nebula_bridge()
            except Exception as e:
                print(f"Warning: Nebula Engine bridge unavailable: {e}")
        
        # Retro 2D Renderer
        try:
            self.renderer_2d = Renderer2D(
                output_dir=self.output_dir,
                pixel_scale=4,
                enable_scanlines=False,
                enable_shadows=True,
            )
            if not self.renderer_2d.available:
                print("Warning: Renderer2D not fully available")
        except Exception as e:
            print(f"Warning: Renderer2D init failed: {e}")
            self.renderer_2d = None
        
        self.engine_version = "ANM-V3-RETRO-2D"
    
    def run(self, request: SimulationRequest) -> SimulationResult:
        """Run 2D simulation with retro visuals."""
        start_time = time.time()
        
        # Determine physics mode from scenario
        physics_mode = self._determine_physics_mode(request)
        
        # Run physics simulation
        frames = self._simulate_2d(request, physics_mode)
        
        # Render video
        video_path = self._render_2d_video(frames, request)
        
        elapsed = time.time() - start_time
        
        return SimulationResult(
            request=request,
            success=True,
            frames=frames,
            summary=f"Retro 2D simulation: {request.scenario_type} ({len(frames)} frames, {physics_mode} physics)",
            metrics={
                "simulation_time": elapsed,
                "frames_generated": len(frames),
                "video_rendered": video_path is not None,
                "video_path": video_path,
                "engine_version": self.engine_version,
                "physics_mode": physics_mode,
                "dimensions": "2D",
            }
        )
    
    def _determine_physics_mode(self, request: SimulationRequest) -> str:
        """Determine the physics mode based on scenario."""
        scenario = request.scenario_type.lower()
        params = request.params or {}
        
        # Explicit physics mode
        if "physics_mode" in params:
            return params["physics_mode"]
        
        # Infer from scenario
        if any(k in scenario for k in ["orbit", "nbody", "merger", "cosmic", "space"]):
            return "n_body"
        elif any(k in scenario for k in ["fall", "drop", "gravity", "bounce", "ball"]):
            return "uniform_gravity"
        elif "spring" in scenario or "pendulum" in scenario:
            return "spring"
        else:
            return "uniform_gravity"  # Default for most cases
    
    def _simulate_2d(
        self,
        request: SimulationRequest,
        physics_mode: str,
    ) -> List[SimulationFrame]:
        """Run 2D physics simulation."""
        frames = []
        dt = 1.0 / request.target_fps
        total_steps = int(request.duration_seconds * request.target_fps)
        
        # Initialize entities
        entities = self._initialize_entities(request)
        
        # Get physics parameters
        params = request.params or {}
        damping = params.get("damping", DEFAULT_DAMPING)
        restitution = params.get("restitution", DEFAULT_RESTITUTION)
        gravity = tuple(params.get("gravity", [0.0, 98.0]))  # Default: downward
        
        # Find ground level
        ground_y = None
        for e in entities:
            if e.get("type") == "ground":
                ground_y = e["position"][1]
                break
        
        for step in range(total_steps):
            # Update physics based on mode
            if physics_mode == "n_body":
                self._update_nbody_physics(entities, dt, damping)
            elif physics_mode == "uniform_gravity":
                self._update_uniform_gravity(entities, dt, gravity, damping)
            elif physics_mode == "spring":
                self._update_spring_physics(entities, dt, damping, params)
            else:
                self._update_uniform_gravity(entities, dt, gravity, damping)
            
            # Collision detection and resolution
            self._handle_collisions(entities, ground_y, restitution)
            
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
    
    def _initialize_entities(self, request: SimulationRequest) -> List[Dict]:
        """Initialize entities (GENERAL PURPOSE)."""
        entities = []
        params = request.params or {}
        
        # Check for explicit entities in params
        if "entities" in params:
            for entity_data in params["entities"]:
                entity = {
                    "type": entity_data.get("type", "ball"),
                    "position": list(entity_data.get("position", [0.0, 0.0])),
                    "velocity": list(entity_data.get("velocity", [0.0, 0.0])),
                    "mass": entity_data.get("mass", 1.0),
                    "radius": entity_data.get("radius", 10.0),
                    "fixed": entity_data.get("fixed", False),
                }
                # Copy any additional properties
                for key, value in entity_data.items():
                    if key not in entity:
                        entity[key] = value
                entities.append(entity)
            return entities
        
        # Scenario-specific initialization
        scenario = request.scenario_type.lower()
        
        if "apple" in scenario or "fall" in scenario:
            # Apple falling scenario
            entities.append({
                "type": "apple",
                "position": [0.0, -100.0],  # Above ground
                "velocity": [0.0, 0.0],
                "mass": 0.5,
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
        
        elif "bounce" in scenario or "ball" in scenario:
            # Bouncing ball
            entities.append({
                "type": "ball",
                "position": [0.0, -100.0],
                "velocity": [50.0, 0.0],
                "mass": 1.0,
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
        
        elif "orbit" in scenario or "nbody" in scenario:
            # Orbital mechanics
            num_bodies = params.get("num_bodies", 5)
            center_mass = params.get("center_mass", 1e6)
            
            # Central body
            entities.append({
                "type": "star",
                "position": [0.0, 0.0],
                "velocity": [0.0, 0.0],
                "mass": center_mass,
                "radius": 30.0,
                "fixed": True,
            })
            
            # Orbiting bodies
            for i in range(num_bodies - 1):
                angle = 2 * math.pi * i / (num_bodies - 1)
                orbit_radius = 100.0 + i * 30.0
                # Calculate orbital velocity
                orbital_vel = math.sqrt(G_CONSTANT * center_mass / orbit_radius)
                
                entities.append({
                    "type": "planet",
                    "position": [
                        orbit_radius * math.cos(angle),
                        orbit_radius * math.sin(angle),
                    ],
                    "velocity": [
                        -orbital_vel * math.sin(angle),
                        orbital_vel * math.cos(angle),
                    ],
                    "mass": 100.0,
                    "radius": 10.0,
                    "fixed": False,
                })
        
        elif "merger" in scenario or "black" in scenario:
            # Black hole / neutron star merger
            entities.append({
                "type": "black_hole",
                "position": [0.0, 0.0],
                "velocity": [0.0, 0.0],
                "mass": params.get("bh_mass", 1e6),
                "radius": 25.0,
                "schwarzschild_radius": 20.0,
                "fixed": False,
            })
            
            sep = params.get("separation", 100.0)
            orbital_vel = math.sqrt(G_CONSTANT * 1e6 / sep) * 0.8
            
            entities.append({
                "type": "neutron_star",
                "position": [sep, 0.0],
                "velocity": [0.0, -orbital_vel],
                "mass": params.get("ns_mass", 1e5),
                "radius": 15.0,
                "fixed": False,
            })
        
        else:
            # Generic: single falling object
            entities.append({
                "type": "ball",
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
    
    def _update_nbody_physics(
        self,
        entities: List[Dict],
        dt: float,
        damping: float,
    ):
        """N-body gravitational physics."""
        # Calculate forces
        for i, e1 in enumerate(entities):
            if e1.get("fixed", False):
                continue
            
            fx, fy = 0.0, 0.0
            
            for j, e2 in enumerate(entities):
                if i == j:
                    continue
                
                force = gravity_force(e1, e2)
                fx += force[0]
                fy += force[1]
            
            # Update velocity
            ax = fx / e1["mass"]
            ay = fy / e1["mass"]
            e1["velocity"][0] += ax * dt
            e1["velocity"][1] += ay * dt
            
            # Apply damping
            e1["velocity"][0] *= damping
            e1["velocity"][1] *= damping
        
        # Update positions
        for e in entities:
            if not e.get("fixed", False):
                e["position"][0] += e["velocity"][0] * dt
                e["position"][1] += e["velocity"][1] * dt
    
    def _update_uniform_gravity(
        self,
        entities: List[Dict],
        dt: float,
        gravity: Tuple[float, float],
        damping: float,
    ):
        """Uniform gravity physics (surface gravity)."""
        for e in entities:
            if e.get("fixed", False):
                continue
            
            # Apply gravity force
            force = uniform_gravity_force(e, gravity)
            
            # Update velocity
            ax = force[0] / e["mass"]
            ay = force[1] / e["mass"]
            e["velocity"][0] += ax * dt
            e["velocity"][1] += ay * dt
            
            # Apply damping
            e["velocity"][0] *= damping
            e["velocity"][1] *= damping
            
            # Update position
            e["position"][0] += e["velocity"][0] * dt
            e["position"][1] += e["velocity"][1] * dt
    
    def _update_spring_physics(
        self,
        entities: List[Dict],
        dt: float,
        damping: float,
        params: Dict,
    ):
        """Spring-based physics."""
        springs = params.get("springs", [])
        gravity = tuple(params.get("gravity", [0.0, 98.0]))
        
        for e in entities:
            if e.get("fixed", False):
                continue
            
            # Apply gravity
            force = uniform_gravity_force(e, gravity)
            fx, fy = force[0], force[1]
            
            # Apply spring forces
            for spring in springs:
                i1, i2 = spring.get("entities", [0, 1])
                rest_len = spring.get("rest_length", 50.0)
                stiffness = spring.get("stiffness", 100.0)
                
                if entities.index(e) == i1:
                    sf = spring_force(e, entities[i2], rest_len, stiffness)
                    fx += sf[0]
                    fy += sf[1]
            
            # Update velocity
            ax = fx / e["mass"]
            ay = fy / e["mass"]
            e["velocity"][0] += ax * dt
            e["velocity"][1] += ay * dt
            
            # Apply damping
            e["velocity"][0] *= damping
            e["velocity"][1] *= damping
            
            # Update position
            e["position"][0] += e["velocity"][0] * dt
            e["position"][1] += e["velocity"][1] * dt
    
    def _handle_collisions(
        self,
        entities: List[Dict],
        ground_y: Optional[float],
        restitution: float,
    ):
        """Handle all collisions."""
        # Ground collisions
        if ground_y is not None:
            for e in entities:
                if e.get("type") == "ground" or e.get("fixed", False):
                    continue
                
                collision = check_ground_collision(e, ground_y)
                if collision:
                    resolve_ground_collision(e, collision, restitution)
        
        # Entity-entity collisions
        for i in range(len(entities)):
            if entities[i].get("type") == "ground":
                continue
            
            for j in range(i + 1, len(entities)):
                if entities[j].get("type") == "ground":
                    continue
                
                collision = check_circle_collision(entities[i], entities[j])
                if collision:
                    resolve_circle_collision(
                        entities[i], entities[j], collision, restitution
                    )
    
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
    
    def _render_2d_video(
        self,
        frames: List[SimulationFrame],
        request: SimulationRequest,
    ) -> Optional[str]:
        """Render video with retro 2D graphics."""
        if not frames:
            return None
        
        if self.renderer_2d and self.renderer_2d.available:
            timestamp = int(time.time())
            scenario = request.scenario_type.replace("_", "-")
            filename = f"retro2d_{scenario}_{timestamp}.mp4"
            
            video_path = self.renderer_2d.render_frames_to_video(
                frames=frames,
                request=request,
                output_filename=filename,
            )
            
            return video_path
        
        return None
