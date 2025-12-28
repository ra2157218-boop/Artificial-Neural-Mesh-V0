# ============================================================
#  ANM-V3 — UNIVERSAL PHYSICS ENGINE
#  Simulate ANY physical phenomenon with accuracy
#  Gravity • Collisions • Fluids • Springs • Electricity • Magnetism
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import math


# ============================================================
#  PHYSICS CONSTANTS (Real-world scaled for visibility)
# ============================================================

class PhysicsConstants:
    """Physical constants scaled for simulation visibility."""
    
    # Gravitational constant (scaled)
    G = 6.674e-2
    
    # Earth surface gravity (scaled)
    g = 98.0  # 9.8 * 10 for visibility
    
    # Speed of light (for relativistic effects)
    c = 300.0
    
    # Coulomb constant (scaled for electric forces)
    k_e = 8.99e1
    
    # Magnetic permeability (scaled)
    mu_0 = 1.257e-3
    
    # Default damping
    DAMPING = 0.999
    
    # Default restitution (bounciness)
    RESTITUTION = 0.7
    
    # Default friction
    FRICTION = 0.3
    
    # Air resistance coefficient
    AIR_RESISTANCE = 0.01
    
    # Water density (kg/m³, scaled)
    WATER_DENSITY = 10.0


class PhysicsMode(Enum):
    """Available physics simulation modes."""
    UNIFORM_GRAVITY = "uniform_gravity"
    N_BODY = "n_body"
    PENDULUM = "pendulum"
    SPRING = "spring"
    FLUID = "fluid"
    PARTICLE = "particle"
    ELECTRIC = "electric"
    MAGNETIC = "magnetic"
    WAVE = "wave"
    PROJECTILE = "projectile"
    ORBITAL = "orbital"
    EXPLOSION = "explosion"


# ============================================================
#  VECTOR MATH
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


def vec2_rotate(v: List[float], angle: float) -> List[float]:
    """Rotate 2D vector by angle (radians)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return [
        v[0] * cos_a - v[1] * sin_a,
        v[0] * sin_a + v[1] * cos_a,
    ]


def vec2_perpendicular(v: List[float]) -> List[float]:
    """Get perpendicular vector."""
    return [-v[1], v[0]]


# ============================================================
#  FORCE FUNCTIONS
# ============================================================

def gravitational_force(
    e1: Dict,
    e2: Dict,
    g_constant: float = PhysicsConstants.G,
) -> List[float]:
    """Calculate gravitational force between two entities (N-body)."""
    pos1 = e1["position"]
    pos2 = e2["position"]
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist_sq = dx*dx + dy*dy
    dist = math.sqrt(dist_sq) + 1e-6
    
    # F = G * m1 * m2 / r^2
    force_mag = g_constant * e1["mass"] * e2["mass"] / dist_sq
    
    # Limit force to prevent numerical explosion
    max_force = e1["mass"] * 1000
    force_mag = min(force_mag, max_force)
    
    return [force_mag * dx / dist, force_mag * dy / dist]


def uniform_gravity_force(
    entity: Dict,
    gravity: Tuple[float, float] = (0.0, PhysicsConstants.g),
) -> List[float]:
    """Apply uniform gravity (like Earth's surface)."""
    return [gravity[0] * entity["mass"], gravity[1] * entity["mass"]]


def spring_force(
    e1: Dict,
    e2: Dict,
    rest_length: float,
    stiffness: float = 100.0,
    damping: float = 0.5,
) -> List[float]:
    """Calculate spring force between two entities (Hooke's Law)."""
    pos1 = e1["position"]
    pos2 = e2["position"]
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = math.sqrt(dx*dx + dy*dy) + 1e-6
    
    # Spring force: F = -k * (d - rest_length)
    stretch = dist - rest_length
    force_mag = stiffness * stretch
    
    # Damping force
    if "velocity" in e1 and "velocity" in e2:
        rel_vel = vec2_subtract(e2["velocity"], e1["velocity"])
        normal = [dx / dist, dy / dist]
        damping_force = damping * vec2_dot(rel_vel, normal)
        force_mag += damping_force
    
    return [force_mag * dx / dist, force_mag * dy / dist]


def electric_force(
    e1: Dict,
    e2: Dict,
    k: float = PhysicsConstants.k_e,
) -> List[float]:
    """Calculate electric force between charged entities (Coulomb's Law)."""
    pos1 = e1["position"]
    pos2 = e2["position"]
    
    q1 = e1.get("charge", 0)
    q2 = e2.get("charge", 0)
    
    if q1 == 0 or q2 == 0:
        return [0.0, 0.0]
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist_sq = dx*dx + dy*dy
    dist = math.sqrt(dist_sq) + 1e-6
    
    # F = k * q1 * q2 / r^2 (negative = attractive)
    force_mag = k * q1 * q2 / dist_sq
    
    # Limit
    force_mag = max(-1000, min(1000, force_mag))
    
    return [force_mag * dx / dist, force_mag * dy / dist]


def magnetic_force(
    entity: Dict,
    field_strength: Tuple[float, float] = (0.0, 0.0),
) -> List[float]:
    """Calculate magnetic force on moving charged particle."""
    charge = entity.get("charge", 0)
    velocity = entity.get("velocity", [0, 0])
    
    if charge == 0 or (velocity[0] == 0 and velocity[1] == 0):
        return [0.0, 0.0]
    
    # F = q * (v × B) — in 2D, B is perpendicular to plane
    # Simplified: F perpendicular to velocity
    vel_perp = vec2_perpendicular(velocity)
    force = vec2_scale(vel_perp, charge * math.sqrt(field_strength[0]**2 + field_strength[1]**2))
    
    return force


def drag_force(
    entity: Dict,
    fluid_density: float = PhysicsConstants.WATER_DENSITY,
    drag_coefficient: float = 0.47,  # Sphere
) -> List[float]:
    """Calculate fluid drag force."""
    velocity = entity.get("velocity", [0, 0])
    speed = vec2_length(velocity)
    
    if speed < 0.1:
        return [0.0, 0.0]
    
    radius = entity.get("radius", 10)
    area = math.pi * radius * radius * 0.001  # Cross-sectional area (scaled)
    
    # F = 0.5 * rho * v^2 * Cd * A
    drag_mag = 0.5 * fluid_density * speed * speed * drag_coefficient * area
    
    # Apply opposite to velocity
    direction = vec2_normalize(velocity)
    return [-drag_mag * direction[0], -drag_mag * direction[1]]


def buoyancy_force(
    entity: Dict,
    fluid_density: float = PhysicsConstants.WATER_DENSITY,
    fluid_level: float = 100.0,
) -> List[float]:
    """Calculate buoyancy force when submerged."""
    pos = entity["position"]
    radius = entity.get("radius", 10)
    
    # How much is submerged
    depth = pos[1] + radius - fluid_level
    if depth < 0:
        return [0.0, 0.0]  # Not in fluid
    
    # Submerged fraction
    submerged = min(1.0, depth / (2 * radius))
    
    # Volume (simplified as sphere)
    volume = (4/3) * math.pi * (radius ** 3) * 0.0001  # Scaled
    
    # F = rho * V * g (upward)
    buoyancy = fluid_density * volume * submerged * PhysicsConstants.g
    
    return [0.0, -buoyancy]


def air_resistance_force(
    entity: Dict,
    coefficient: float = PhysicsConstants.AIR_RESISTANCE,
) -> List[float]:
    """Calculate air resistance."""
    velocity = entity.get("velocity", [0, 0])
    speed = vec2_length(velocity)
    
    if speed < 0.1:
        return [0.0, 0.0]
    
    # F = -b * v^2
    drag = coefficient * speed * speed
    direction = vec2_normalize(velocity)
    
    return [-drag * direction[0], -drag * direction[1]]


# ============================================================
#  COLLISION DETECTION
# ============================================================

def check_circle_collision(e1: Dict, e2: Dict) -> Optional[Dict]:
    """Check collision between two circular entities."""
    pos1 = e1["position"]
    pos2 = e2["position"]
    r1 = e1.get("radius", 10)
    r2 = e2.get("radius", 10)
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist_sq = dx*dx + dy*dy
    min_dist = r1 + r2
    
    if dist_sq < min_dist * min_dist:
        dist = math.sqrt(dist_sq) + 1e-6
        return {
            "normal": [dx / dist, dy / dist],
            "penetration": min_dist - dist,
            "entity1": e1,
            "entity2": e2,
        }
    return None


def check_ground_collision(entity: Dict, ground_y: float) -> Optional[Dict]:
    """Check collision with ground plane."""
    pos = entity["position"]
    radius = entity.get("radius", 10)
    
    if pos[1] + radius > ground_y:
        return {
            "normal": [0.0, -1.0],
            "penetration": pos[1] + radius - ground_y,
            "ground_y": ground_y,
        }
    return None


def check_wall_collision(
    entity: Dict,
    wall_x: float,
    wall_side: str = "left",
) -> Optional[Dict]:
    """Check collision with vertical wall."""
    pos = entity["position"]
    radius = entity.get("radius", 10)
    
    if wall_side == "left" and pos[0] - radius < wall_x:
        return {
            "normal": [1.0, 0.0],
            "penetration": wall_x - (pos[0] - radius),
        }
    elif wall_side == "right" and pos[0] + radius > wall_x:
        return {
            "normal": [-1.0, 0.0],
            "penetration": (pos[0] + radius) - wall_x,
        }
    return None


def check_ceiling_collision(entity: Dict, ceiling_y: float) -> Optional[Dict]:
    """Check collision with ceiling."""
    pos = entity["position"]
    radius = entity.get("radius", 10)
    
    if pos[1] - radius < ceiling_y:
        return {
            "normal": [0.0, 1.0],
            "penetration": ceiling_y - (pos[1] - radius),
        }
    return None


# ============================================================
#  COLLISION RESOLUTION
# ============================================================

def resolve_circle_collision(
    e1: Dict,
    e2: Dict,
    collision: Dict,
    restitution: float = PhysicsConstants.RESTITUTION,
):
    """Resolve collision between two circular entities."""
    normal = collision["normal"]
    penetration = collision["penetration"]
    
    # Separate objects based on mass
    m1, m2 = e1["mass"], e2["mass"]
    total_mass = m1 + m2
    
    if e1.get("fixed"):
        ratio1 = 0
        ratio2 = 1
    elif e2.get("fixed"):
        ratio1 = 1
        ratio2 = 0
    else:
        ratio1 = m2 / total_mass
        ratio2 = m1 / total_mass
    
    e1["position"][0] -= normal[0] * penetration * ratio1
    e1["position"][1] -= normal[1] * penetration * ratio1
    e2["position"][0] += normal[0] * penetration * ratio2
    e2["position"][1] += normal[1] * penetration * ratio2
    
    # Skip velocity changes for fixed objects
    if e1.get("fixed") and e2.get("fixed"):
        return
    
    # Calculate relative velocity
    v1, v2 = e1.get("velocity", [0, 0]), e2.get("velocity", [0, 0])
    rel_vel = vec2_subtract(v1, v2)
    vel_along_normal = vec2_dot(rel_vel, normal)
    
    # Don't resolve if separating
    if vel_along_normal > 0:
        return
    
    # Calculate impulse
    j = -(1 + restitution) * vel_along_normal
    
    if e1.get("fixed"):
        j /= 1 / m2
    elif e2.get("fixed"):
        j /= 1 / m1
    else:
        j /= 1 / m1 + 1 / m2
    
    # Apply impulse
    impulse = vec2_scale(normal, j)
    
    if not e1.get("fixed"):
        e1["velocity"][0] += impulse[0] / m1
        e1["velocity"][1] += impulse[1] / m1
    
    if not e2.get("fixed"):
        e2["velocity"][0] -= impulse[0] / m2
        e2["velocity"][1] -= impulse[1] / m2


def resolve_boundary_collision(
    entity: Dict,
    collision: Dict,
    restitution: float = PhysicsConstants.RESTITUTION,
    friction: float = PhysicsConstants.FRICTION,
):
    """Resolve collision with boundary (ground, wall, ceiling)."""
    if entity.get("fixed"):
        return
    
    normal = collision["normal"]
    penetration = collision["penetration"]
    
    # Push out
    entity["position"][0] += normal[0] * penetration
    entity["position"][1] += normal[1] * penetration
    
    # Reflect velocity
    vel = entity.get("velocity", [0, 0])
    vel_normal = vec2_dot(vel, normal)
    
    if vel_normal < 0:  # Moving into boundary
        # Normal component (bounce)
        entity["velocity"][0] -= (1 + restitution) * vel_normal * normal[0]
        entity["velocity"][1] -= (1 + restitution) * vel_normal * normal[1]
        
        # Tangent component (friction)
        tangent = vec2_perpendicular(normal)
        vel_tangent = vec2_dot(vel, tangent)
        entity["velocity"][0] -= friction * vel_tangent * tangent[0]
        entity["velocity"][1] -= friction * vel_tangent * tangent[1]


# ============================================================
#  INTEGRATION METHODS
# ============================================================

def euler_integrate(
    entity: Dict,
    force: List[float],
    dt: float,
    damping: float = PhysicsConstants.DAMPING,
):
    """Simple Euler integration."""
    if entity.get("fixed"):
        return
    
    mass = entity["mass"]
    
    # Acceleration
    ax = force[0] / mass
    ay = force[1] / mass
    
    # Update velocity
    entity["velocity"][0] += ax * dt
    entity["velocity"][1] += ay * dt
    
    # Apply damping
    entity["velocity"][0] *= damping
    entity["velocity"][1] *= damping
    
    # Update position
    entity["position"][0] += entity["velocity"][0] * dt
    entity["position"][1] += entity["velocity"][1] * dt


def rk4_integrate(
    entity: Dict,
    force_func: Callable[[Dict], List[float]],
    dt: float,
    damping: float = PhysicsConstants.DAMPING,
):
    """Runge-Kutta 4th order integration (more accurate)."""
    if entity.get("fixed"):
        return
    
    mass = entity["mass"]
    
    # Save initial state
    x0 = entity["position"][0]
    y0 = entity["position"][1]
    vx0 = entity["velocity"][0]
    vy0 = entity["velocity"][1]
    
    # K1
    f1 = force_func(entity)
    ax1, ay1 = f1[0] / mass, f1[1] / mass
    
    # K2
    entity["position"] = [x0 + vx0 * dt/2, y0 + vy0 * dt/2]
    entity["velocity"] = [vx0 + ax1 * dt/2, vy0 + ay1 * dt/2]
    f2 = force_func(entity)
    ax2, ay2 = f2[0] / mass, f2[1] / mass
    
    # K3
    entity["position"] = [x0 + (vx0 + ax1*dt/2) * dt/2, y0 + (vy0 + ay1*dt/2) * dt/2]
    entity["velocity"] = [vx0 + ax2 * dt/2, vy0 + ay2 * dt/2]
    f3 = force_func(entity)
    ax3, ay3 = f3[0] / mass, f3[1] / mass
    
    # K4
    entity["position"] = [x0 + (vx0 + ax2*dt/2) * dt, y0 + (vy0 + ay2*dt/2) * dt]
    entity["velocity"] = [vx0 + ax3 * dt, vy0 + ay3 * dt]
    f4 = force_func(entity)
    ax4, ay4 = f4[0] / mass, f4[1] / mass
    
    # Combine
    ax = (ax1 + 2*ax2 + 2*ax3 + ax4) / 6
    ay = (ay1 + 2*ay2 + 2*ay3 + ay4) / 6
    
    vx = vx0 + ax * dt
    vy = vy0 + ay * dt
    
    # Update
    entity["velocity"] = [vx * damping, vy * damping]
    entity["position"] = [x0 + vx * dt, y0 + vy * dt]


# ============================================================
#  UNIVERSAL PHYSICS ENGINE
# ============================================================

class UniversalPhysics:
    """
    Universal Physics Engine for ANY physical phenomenon.
    
    Supports:
    - Uniform gravity (falling, bouncing)
    - N-body gravity (orbital mechanics)
    - Spring physics (pendulums, oscillations)
    - Fluid dynamics (buoyancy, drag)
    - Electric forces (charged particles)
    - Magnetic forces (moving charges)
    - Projectile motion
    - Collisions (elastic, inelastic)
    """
    
    def __init__(
        self,
        mode: PhysicsMode = PhysicsMode.UNIFORM_GRAVITY,
        gravity: Tuple[float, float] = (0.0, PhysicsConstants.g),
        damping: float = PhysicsConstants.DAMPING,
        restitution: float = PhysicsConstants.RESTITUTION,
        friction: float = PhysicsConstants.FRICTION,
        use_rk4: bool = False,
    ):
        self.mode = mode
        self.gravity = gravity
        self.damping = damping
        self.restitution = restitution
        self.friction = friction
        self.use_rk4 = use_rk4
        
        # Additional parameters
        self.fluid_density = PhysicsConstants.WATER_DENSITY
        self.fluid_level = None
        self.electric_field = (0.0, 0.0)
        self.magnetic_field = (0.0, 0.0)
        self.springs = []  # List of spring connections
        
        # Boundaries
        self.ground_y = None
        self.ceiling_y = None
        self.left_wall = None
        self.right_wall = None
    
    def update(
        self,
        entities: List[Dict],
        dt: float,
    ) -> None:
        """Update all entities for one time step."""
        # Calculate and apply forces
        for entity in entities:
            if entity.get("fixed"):
                continue
            
            force = self._calculate_total_force(entity, entities)
            
            # Integration
            if self.use_rk4:
                rk4_integrate(
                    entity,
                    lambda e: self._calculate_total_force(e, entities),
                    dt,
                    self.damping,
                )
            else:
                euler_integrate(entity, force, dt, self.damping)
        
        # Handle collisions
        self._handle_collisions(entities)
    
    def _calculate_total_force(
        self,
        entity: Dict,
        all_entities: List[Dict],
    ) -> List[float]:
        """Calculate total force on entity based on physics mode."""
        fx, fy = 0.0, 0.0
        
        if self.mode == PhysicsMode.UNIFORM_GRAVITY:
            f = uniform_gravity_force(entity, self.gravity)
            fx += f[0]
            fy += f[1]
            
            # Air resistance
            f = air_resistance_force(entity)
            fx += f[0]
            fy += f[1]
        
        elif self.mode == PhysicsMode.N_BODY:
            for other in all_entities:
                if other is entity:
                    continue
                f = gravitational_force(entity, other)
                fx += f[0]
                fy += f[1]
        
        elif self.mode == PhysicsMode.ORBITAL:
            for other in all_entities:
                if other is entity:
                    continue
                f = gravitational_force(entity, other)
                fx += f[0]
                fy += f[1]
        
        elif self.mode == PhysicsMode.PENDULUM:
            # Gravity + spring to fixed point
            f = uniform_gravity_force(entity, self.gravity)
            fx += f[0]
            fy += f[1]
        
        elif self.mode == PhysicsMode.SPRING:
            # Gravity + all springs
            f = uniform_gravity_force(entity, self.gravity)
            fx += f[0]
            fy += f[1]
            
            for spring in self.springs:
                if spring["entity1"] is entity or spring["entity2"] is entity:
                    other = spring["entity2"] if spring["entity1"] is entity else spring["entity1"]
                    f = spring_force(entity, other, 
                                    spring.get("rest_length", 50),
                                    spring.get("stiffness", 100))
                    fx += f[0]
                    fy += f[1]
        
        elif self.mode == PhysicsMode.FLUID:
            # Gravity + drag + buoyancy
            f = uniform_gravity_force(entity, self.gravity)
            fx += f[0]
            fy += f[1]
            
            f = drag_force(entity, self.fluid_density)
            fx += f[0]
            fy += f[1]
            
            if self.fluid_level is not None:
                f = buoyancy_force(entity, self.fluid_density, self.fluid_level)
                fx += f[0]
                fy += f[1]
        
        elif self.mode == PhysicsMode.PARTICLE:
            # Light particles with inter-particle forces
            for other in all_entities:
                if other is entity:
                    continue
                
                # Short-range repulsion
                pos = entity["position"]
                opos = other["position"]
                dx = opos[0] - pos[0]
                dy = opos[1] - pos[1]
                dist = math.sqrt(dx*dx + dy*dy) + 1e-6
                
                if dist < 30:  # Repulsion range
                    force_mag = 100 / (dist * dist)
                    fx -= force_mag * dx / dist
                    fy -= force_mag * dy / dist
        
        elif self.mode == PhysicsMode.ELECTRIC:
            # Electric forces
            for other in all_entities:
                if other is entity:
                    continue
                f = electric_force(entity, other)
                fx += f[0]
                fy += f[1]
            
            # External electric field
            charge = entity.get("charge", 0)
            fx += charge * self.electric_field[0]
            fy += charge * self.electric_field[1]
        
        elif self.mode == PhysicsMode.MAGNETIC:
            # Magnetic force + electric
            f = magnetic_force(entity, self.magnetic_field)
            fx += f[0]
            fy += f[1]
            
            for other in all_entities:
                if other is entity:
                    continue
                f = electric_force(entity, other)
                fx += f[0]
                fy += f[1]
        
        elif self.mode == PhysicsMode.PROJECTILE:
            # Gravity + air resistance
            f = uniform_gravity_force(entity, self.gravity)
            fx += f[0]
            fy += f[1]
            
            f = air_resistance_force(entity, coefficient=0.05)
            fx += f[0]
            fy += f[1]
        
        elif self.mode == PhysicsMode.EXPLOSION:
            # Radial forces from center
            center = all_entities[0]["position"] if all_entities else [0, 0]
            pos = entity["position"]
            dx = pos[0] - center[0]
            dy = pos[1] - center[1]
            dist = math.sqrt(dx*dx + dy*dy) + 1e-6
            
            force_mag = 5000 / (dist + 10)
            fx += force_mag * dx / dist
            fy += force_mag * dy / dist
            
            # Plus some gravity
            f = uniform_gravity_force(entity, (0, self.gravity[1] * 0.3))
            fx += f[0]
            fy += f[1]
        
        return [fx, fy]
    
    def _handle_collisions(self, entities: List[Dict]) -> None:
        """Handle all collisions."""
        # Boundary collisions
        for entity in entities:
            if entity.get("fixed") or entity.get("type") == "ground":
                continue
            
            # Ground
            if self.ground_y is not None:
                collision = check_ground_collision(entity, self.ground_y)
                if collision:
                    resolve_boundary_collision(entity, collision, self.restitution, self.friction)
            
            # Ceiling
            if self.ceiling_y is not None:
                collision = check_ceiling_collision(entity, self.ceiling_y)
                if collision:
                    resolve_boundary_collision(entity, collision, self.restitution, self.friction)
            
            # Walls
            if self.left_wall is not None:
                collision = check_wall_collision(entity, self.left_wall, "left")
                if collision:
                    resolve_boundary_collision(entity, collision, self.restitution, self.friction)
            
            if self.right_wall is not None:
                collision = check_wall_collision(entity, self.right_wall, "right")
                if collision:
                    resolve_boundary_collision(entity, collision, self.restitution, self.friction)
        
        # Entity-entity collisions
        for i in range(len(entities)):
            e1 = entities[i]
            if e1.get("type") == "ground":
                continue
            
            for j in range(i + 1, len(entities)):
                e2 = entities[j]
                if e2.get("type") == "ground":
                    continue
                
                collision = check_circle_collision(e1, e2)
                if collision:
                    resolve_circle_collision(e1, e2, collision, self.restitution)
    
    def set_boundaries(
        self,
        ground_y: Optional[float] = None,
        ceiling_y: Optional[float] = None,
        left_wall: Optional[float] = None,
        right_wall: Optional[float] = None,
    ) -> None:
        """Set simulation boundaries."""
        self.ground_y = ground_y
        self.ceiling_y = ceiling_y
        self.left_wall = left_wall
        self.right_wall = right_wall
    
    def add_spring(
        self,
        entity1: Dict,
        entity2: Dict,
        rest_length: float,
        stiffness: float = 100.0,
    ) -> None:
        """Add spring connection between entities."""
        self.springs.append({
            "entity1": entity1,
            "entity2": entity2,
            "rest_length": rest_length,
            "stiffness": stiffness,
        })
    
    def set_fluid(
        self,
        level: float,
        density: float = PhysicsConstants.WATER_DENSITY,
    ) -> None:
        """Set fluid parameters for buoyancy."""
        self.fluid_level = level
        self.fluid_density = density
    
    def set_fields(
        self,
        electric: Tuple[float, float] = (0.0, 0.0),
        magnetic: Tuple[float, float] = (0.0, 0.0),
    ) -> None:
        """Set electric and magnetic fields."""
        self.electric_field = electric
        self.magnetic_field = magnetic


# ============================================================
#  PHYSICS MODE DETECTION
# ============================================================

def detect_physics_mode(
    scenario: str,
    entities: List[Dict],
    environment: Dict,
) -> PhysicsMode:
    """Detect appropriate physics mode from scenario."""
    scenario_lower = scenario.lower()
    
    # Keywords mapping
    if any(k in scenario_lower for k in ["orbit", "planet", "star", "galaxy", "cosmic", "satellite"]):
        return PhysicsMode.ORBITAL
    
    if any(k in scenario_lower for k in ["nbody", "n-body", "merger", "black hole"]):
        return PhysicsMode.N_BODY
    
    if any(k in scenario_lower for k in ["pendulum", "swing"]):
        return PhysicsMode.PENDULUM
    
    if any(k in scenario_lower for k in ["spring", "oscillate", "bounce"]):
        return PhysicsMode.SPRING
    
    if any(k in scenario_lower for k in ["water", "fluid", "swim", "float", "sink", "buoy"]):
        return PhysicsMode.FLUID
    
    if any(k in scenario_lower for k in ["particle", "atom", "molecule", "electron"]):
        return PhysicsMode.PARTICLE
    
    if any(k in scenario_lower for k in ["electric", "charge", "coulomb"]):
        return PhysicsMode.ELECTRIC
    
    if any(k in scenario_lower for k in ["magnetic", "magnet"]):
        return PhysicsMode.MAGNETIC
    
    if any(k in scenario_lower for k in ["projectile", "throw", "launch", "shoot"]):
        return PhysicsMode.PROJECTILE
    
    if any(k in scenario_lower for k in ["explode", "explosion", "blast"]):
        return PhysicsMode.EXPLOSION
    
    # Check entity categories
    categories = [e.get("category", "") for e in entities]
    if "cosmic" in categories:
        return PhysicsMode.N_BODY
    if "particle" in categories:
        return PhysicsMode.PARTICLE
    
    # Default
    return PhysicsMode.UNIFORM_GRAVITY
