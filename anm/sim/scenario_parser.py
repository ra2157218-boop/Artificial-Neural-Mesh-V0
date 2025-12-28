# ============================================================
#  ANM-V3 — UNIVERSAL SCENARIO PARSER
#  Parse ANY natural language description into simulation entities
#  Truly general purpose - simulate ANYTHING
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import re
import math


@dataclass
class ParsedScenario:
    """Result of parsing a scenario description."""
    scenario_type: str
    physics_mode: str
    entities: List[Dict[str, Any]]
    environment: Dict[str, Any]
    parameters: Dict[str, Any]
    duration: float
    description: str


class ScenarioParser:
    """
    Universal Scenario Parser.
    
    Parses natural language descriptions into simulation parameters.
    Can understand and create scenarios for ANYTHING:
    - Physics: falling, bouncing, orbiting, colliding, floating
    - Chemistry: reactions, molecules, particles
    - Biology: cells, organisms, growth
    - Astronomy: planets, stars, black holes, galaxies
    - Everyday: sports, vehicles, machines, people
    - Abstract: data flow, networks, systems
    
    Example inputs:
    - "An apple falls from a tree onto grass"
    - "Two planets orbiting a sun"
    - "A ball bouncing on a trampoline"
    - "Water flowing through pipes"
    - "Electrons orbiting an atom nucleus"
    - "Cars on a highway"
    - "A pendulum swinging"
    """
    
    # Entity type keywords
    ENTITY_KEYWORDS = {
        # Fruits & food
        "apple": {"type": "apple", "mass": 0.2, "radius": 12, "category": "organic"},
        "orange": {"type": "orange", "mass": 0.25, "radius": 14, "category": "organic"},
        "banana": {"type": "banana", "mass": 0.15, "radius": 10, "category": "organic"},
        "watermelon": {"type": "watermelon", "mass": 5.0, "radius": 30, "category": "organic"},
        "grape": {"type": "grape", "mass": 0.01, "radius": 5, "category": "organic"},
        "egg": {"type": "egg", "mass": 0.06, "radius": 8, "category": "fragile"},
        
        # Balls & sports
        "ball": {"type": "ball", "mass": 0.5, "radius": 15, "category": "sports"},
        "basketball": {"type": "basketball", "mass": 0.6, "radius": 24, "category": "sports"},
        "football": {"type": "football", "mass": 0.45, "radius": 20, "category": "sports"},
        "soccer ball": {"type": "soccer_ball", "mass": 0.43, "radius": 22, "category": "sports"},
        "tennis ball": {"type": "tennis_ball", "mass": 0.057, "radius": 6, "category": "sports"},
        "golf ball": {"type": "golf_ball", "mass": 0.046, "radius": 4, "category": "sports"},
        "bowling ball": {"type": "bowling_ball", "mass": 6.0, "radius": 22, "category": "sports"},
        "marble": {"type": "marble", "mass": 0.01, "radius": 3, "category": "toy"},
        
        # Vehicles
        "car": {"type": "car", "mass": 1500, "radius": 40, "category": "vehicle"},
        "truck": {"type": "truck", "mass": 5000, "radius": 60, "category": "vehicle"},
        "bike": {"type": "bike", "mass": 15, "radius": 25, "category": "vehicle"},
        "motorcycle": {"type": "motorcycle", "mass": 200, "radius": 30, "category": "vehicle"},
        "rocket": {"type": "rocket", "mass": 500, "radius": 35, "category": "vehicle"},
        "airplane": {"type": "airplane", "mass": 50000, "radius": 80, "category": "vehicle"},
        "boat": {"type": "boat", "mass": 1000, "radius": 50, "category": "vehicle"},
        "train": {"type": "train", "mass": 100000, "radius": 100, "category": "vehicle"},
        
        # Astronomy
        "planet": {"type": "planet", "mass": 1e5, "radius": 25, "category": "cosmic"},
        "earth": {"type": "earth", "mass": 1e6, "radius": 30, "category": "cosmic"},
        "moon": {"type": "moon", "mass": 1e4, "radius": 15, "category": "cosmic"},
        "sun": {"type": "sun", "mass": 1e8, "radius": 50, "category": "cosmic"},
        "star": {"type": "star", "mass": 1e7, "radius": 40, "category": "cosmic"},
        "black hole": {"type": "black_hole", "mass": 1e9, "radius": 30, "category": "cosmic"},
        "neutron star": {"type": "neutron_star", "mass": 1e7, "radius": 15, "category": "cosmic"},
        "asteroid": {"type": "asteroid", "mass": 1e3, "radius": 10, "category": "cosmic"},
        "comet": {"type": "comet", "mass": 1e2, "radius": 12, "category": "cosmic"},
        "satellite": {"type": "satellite", "mass": 500, "radius": 8, "category": "cosmic"},
        "meteor": {"type": "meteor", "mass": 10, "radius": 6, "category": "cosmic"},
        "galaxy": {"type": "galaxy", "mass": 1e12, "radius": 100, "category": "cosmic"},
        
        # Physics objects
        "pendulum": {"type": "pendulum", "mass": 1.0, "radius": 15, "category": "physics"},
        "spring": {"type": "spring", "mass": 0.5, "radius": 10, "category": "physics"},
        "weight": {"type": "weight", "mass": 10, "radius": 20, "category": "physics"},
        "pulley": {"type": "pulley", "mass": 0.5, "radius": 15, "category": "physics"},
        "lever": {"type": "lever", "mass": 2.0, "radius": 40, "category": "physics"},
        "magnet": {"type": "magnet", "mass": 0.5, "radius": 15, "category": "physics"},
        "battery": {"type": "battery", "mass": 0.1, "radius": 10, "category": "physics"},
        
        # Particles
        "particle": {"type": "particle", "mass": 0.001, "radius": 3, "category": "particle"},
        "electron": {"type": "electron", "mass": 0.0001, "radius": 4, "category": "particle"},
        "proton": {"type": "proton", "mass": 0.001, "radius": 5, "category": "particle"},
        "neutron": {"type": "neutron", "mass": 0.001, "radius": 5, "category": "particle"},
        "atom": {"type": "atom", "mass": 0.01, "radius": 15, "category": "particle"},
        "molecule": {"type": "molecule", "mass": 0.02, "radius": 12, "category": "particle"},
        "photon": {"type": "photon", "mass": 0.0, "radius": 3, "category": "particle"},
        
        # Nature
        "rock": {"type": "rock", "mass": 5.0, "radius": 18, "category": "nature"},
        "boulder": {"type": "boulder", "mass": 100, "radius": 40, "category": "nature"},
        "stone": {"type": "stone", "mass": 1.0, "radius": 10, "category": "nature"},
        "leaf": {"type": "leaf", "mass": 0.005, "radius": 8, "category": "nature"},
        "feather": {"type": "feather", "mass": 0.001, "radius": 10, "category": "nature"},
        "raindrop": {"type": "raindrop", "mass": 0.001, "radius": 3, "category": "nature"},
        "snowflake": {"type": "snowflake", "mass": 0.0001, "radius": 6, "category": "nature"},
        "bubble": {"type": "bubble", "mass": 0.0001, "radius": 10, "category": "nature"},
        "drop": {"type": "drop", "mass": 0.001, "radius": 5, "category": "fluid"},
        "wave": {"type": "wave", "mass": 100, "radius": 50, "category": "fluid"},
        
        # Animals (simplified as circles)
        "bird": {"type": "bird", "mass": 0.1, "radius": 10, "category": "animal"},
        "fish": {"type": "fish", "mass": 0.5, "radius": 12, "category": "animal"},
        "insect": {"type": "insect", "mass": 0.001, "radius": 3, "category": "animal"},
        "butterfly": {"type": "butterfly", "mass": 0.0005, "radius": 8, "category": "animal"},
        "bee": {"type": "bee", "mass": 0.0001, "radius": 4, "category": "animal"},
        
        # Structures
        "box": {"type": "box", "mass": 2.0, "radius": 20, "category": "structure"},
        "crate": {"type": "crate", "mass": 10, "radius": 30, "category": "structure"},
        "barrel": {"type": "barrel", "mass": 20, "radius": 25, "category": "structure"},
        "block": {"type": "block", "mass": 5.0, "radius": 25, "category": "structure"},
        "cube": {"type": "cube", "mass": 3.0, "radius": 20, "category": "structure"},
        "pyramid": {"type": "pyramid", "mass": 10, "radius": 30, "category": "structure"},
        "dome": {"type": "dome", "mass": 50, "radius": 40, "category": "structure"},
        "tower": {"type": "tower", "mass": 1000, "radius": 50, "category": "structure"},
        
        # People (simplified)
        "person": {"type": "person", "mass": 70, "radius": 15, "category": "human"},
        "athlete": {"type": "athlete", "mass": 75, "radius": 15, "category": "human"},
        "robot": {"type": "robot", "mass": 100, "radius": 20, "category": "machine"},
        
        # Abstract
        "node": {"type": "node", "mass": 1.0, "radius": 10, "category": "abstract"},
        "data": {"type": "data", "mass": 0.1, "radius": 8, "category": "abstract"},
        "signal": {"type": "signal", "mass": 0.01, "radius": 5, "category": "abstract"},
        "energy": {"type": "energy", "mass": 0.001, "radius": 15, "category": "abstract"},
        "force": {"type": "force", "mass": 0, "radius": 10, "category": "abstract"},
        
        # Default
        "object": {"type": "object", "mass": 1.0, "radius": 15, "category": "default"},
        "thing": {"type": "thing", "mass": 1.0, "radius": 15, "category": "default"},
    }
    
    # Environment keywords
    ENVIRONMENT_KEYWORDS = {
        "ground": {"type": "ground", "material": "earth"},
        "floor": {"type": "ground", "material": "floor"},
        "grass": {"type": "ground", "material": "grass"},
        "sand": {"type": "ground", "material": "sand"},
        "water": {"type": "fluid", "material": "water"},
        "ocean": {"type": "fluid", "material": "ocean"},
        "pool": {"type": "fluid", "material": "water"},
        "air": {"type": "gas", "material": "air"},
        "space": {"type": "vacuum", "material": "space"},
        "vacuum": {"type": "vacuum", "material": "vacuum"},
        "room": {"type": "enclosed", "material": "room"},
        "outdoor": {"type": "open", "material": "outdoor"},
        "sky": {"type": "open", "material": "sky"},
        "table": {"type": "surface", "material": "table"},
        "ramp": {"type": "slope", "material": "ramp"},
        "hill": {"type": "slope", "material": "hill"},
        "cliff": {"type": "drop", "material": "cliff"},
        "pipe": {"type": "channel", "material": "pipe"},
        "tube": {"type": "channel", "material": "tube"},
        "track": {"type": "path", "material": "track"},
        "road": {"type": "path", "material": "road"},
        "ice": {"type": "surface", "material": "ice"},
        "trampoline": {"type": "elastic", "material": "trampoline"},
        "spring board": {"type": "elastic", "material": "spring"},
    }
    
    # Action keywords
    ACTION_KEYWORDS = {
        "fall": {"motion": "fall", "physics": "uniform_gravity"},
        "falls": {"motion": "fall", "physics": "uniform_gravity"},
        "falling": {"motion": "fall", "physics": "uniform_gravity"},
        "drop": {"motion": "fall", "physics": "uniform_gravity"},
        "drops": {"motion": "fall", "physics": "uniform_gravity"},
        "bounce": {"motion": "bounce", "physics": "uniform_gravity"},
        "bounces": {"motion": "bounce", "physics": "uniform_gravity"},
        "bouncing": {"motion": "bounce", "physics": "uniform_gravity"},
        "roll": {"motion": "roll", "physics": "uniform_gravity"},
        "rolls": {"motion": "roll", "physics": "uniform_gravity"},
        "rolling": {"motion": "roll", "physics": "uniform_gravity"},
        "slide": {"motion": "slide", "physics": "uniform_gravity"},
        "slides": {"motion": "slide", "physics": "uniform_gravity"},
        "orbit": {"motion": "orbit", "physics": "n_body"},
        "orbits": {"motion": "orbit", "physics": "n_body"},
        "orbiting": {"motion": "orbit", "physics": "n_body"},
        "rotate": {"motion": "rotate", "physics": "n_body"},
        "rotates": {"motion": "rotate", "physics": "n_body"},
        "spin": {"motion": "spin", "physics": "uniform_gravity"},
        "spins": {"motion": "spin", "physics": "uniform_gravity"},
        "swing": {"motion": "swing", "physics": "pendulum"},
        "swings": {"motion": "swing", "physics": "pendulum"},
        "swinging": {"motion": "swing", "physics": "pendulum"},
        "oscillate": {"motion": "oscillate", "physics": "spring"},
        "oscillates": {"motion": "oscillate", "physics": "spring"},
        "collide": {"motion": "collision", "physics": "uniform_gravity"},
        "collides": {"motion": "collision", "physics": "uniform_gravity"},
        "collision": {"motion": "collision", "physics": "uniform_gravity"},
        "crash": {"motion": "collision", "physics": "uniform_gravity"},
        "crashes": {"motion": "collision", "physics": "uniform_gravity"},
        "hit": {"motion": "collision", "physics": "uniform_gravity"},
        "hits": {"motion": "collision", "physics": "uniform_gravity"},
        "float": {"motion": "float", "physics": "fluid"},
        "floats": {"motion": "float", "physics": "fluid"},
        "floating": {"motion": "float", "physics": "fluid"},
        "sink": {"motion": "sink", "physics": "fluid"},
        "sinks": {"motion": "sink", "physics": "fluid"},
        "fly": {"motion": "fly", "physics": "uniform_gravity"},
        "flies": {"motion": "fly", "physics": "uniform_gravity"},
        "flying": {"motion": "fly", "physics": "uniform_gravity"},
        "throw": {"motion": "projectile", "physics": "uniform_gravity"},
        "throws": {"motion": "projectile", "physics": "uniform_gravity"},
        "thrown": {"motion": "projectile", "physics": "uniform_gravity"},
        "launch": {"motion": "projectile", "physics": "uniform_gravity"},
        "launches": {"motion": "projectile", "physics": "uniform_gravity"},
        "shoot": {"motion": "projectile", "physics": "uniform_gravity"},
        "shoots": {"motion": "projectile", "physics": "uniform_gravity"},
        "explode": {"motion": "explosion", "physics": "n_body"},
        "explodes": {"motion": "explosion", "physics": "n_body"},
        "merge": {"motion": "merge", "physics": "n_body"},
        "merges": {"motion": "merge", "physics": "n_body"},
        "attract": {"motion": "attract", "physics": "n_body"},
        "attracts": {"motion": "attract", "physics": "n_body"},
        "repel": {"motion": "repel", "physics": "electric"},
        "repels": {"motion": "repel", "physics": "electric"},
        "flow": {"motion": "flow", "physics": "fluid"},
        "flows": {"motion": "flow", "physics": "fluid"},
        "pour": {"motion": "pour", "physics": "fluid"},
        "pours": {"motion": "pour", "physics": "fluid"},
        "wave": {"motion": "wave", "physics": "wave"},
        "waves": {"motion": "wave", "physics": "wave"},
    }
    
    # Number words
    NUMBER_WORDS = {
        "one": 1, "a": 1, "an": 1, "single": 1,
        "two": 2, "couple": 2, "pair": 2,
        "three": 3, "few": 3,
        "four": 4, "several": 4,
        "five": 5, "many": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "dozen": 12, "hundred": 100, "thousand": 1000,
    }
    
    def parse(self, description: str, duration: float = 10.0) -> ParsedScenario:
        """
        Parse a natural language scenario description.
        
        Args:
            description: Natural language description of the scenario
            duration: Default simulation duration
        
        Returns:
            ParsedScenario with all parameters for simulation
        """
        desc_lower = description.lower()
        
        # Extract entities
        entities = self._extract_entities(desc_lower)
        
        # Extract environment
        environment = self._extract_environment(desc_lower)
        
        # Determine physics mode
        physics_mode = self._determine_physics_mode(desc_lower, entities, environment)
        
        # Determine scenario type
        scenario_type = self._determine_scenario_type(desc_lower, entities, physics_mode)
        
        # Extract numerical parameters
        parameters = self._extract_parameters(desc_lower, entities, environment, physics_mode)
        
        # Set up initial positions and velocities
        entities = self._setup_initial_conditions(entities, environment, physics_mode, parameters)
        
        # Add environment as ground entity if needed
        if environment.get("type") in ("ground", "surface", "elastic"):
            entities.append({
                "type": "ground",
                "material": environment.get("material", "earth"),
                "position": [0.0, 150.0],
                "velocity": [0.0, 0.0],
                "mass": 1e10,
                "radius": 1000.0,
                "fixed": True,
            })
        
        return ParsedScenario(
            scenario_type=scenario_type,
            physics_mode=physics_mode,
            entities=entities,
            environment=environment,
            parameters=parameters,
            duration=duration,
            description=description,
        )
    
    def _extract_entities(self, desc: str) -> List[Dict[str, Any]]:
        """Extract entities from description."""
        entities = []
        
        # Check for each entity type
        for keyword, defaults in self.ENTITY_KEYWORDS.items():
            # Check if keyword is in description
            pattern = r'(\d+|' + '|'.join(self.NUMBER_WORDS.keys()) + r')?\s*' + re.escape(keyword) + r's?'
            match = re.search(pattern, desc)
            
            if match or keyword in desc:
                # Determine count
                count = 1
                if match and match.group(1):
                    count_str = match.group(1)
                    if count_str.isdigit():
                        count = int(count_str)
                    else:
                        count = self.NUMBER_WORDS.get(count_str, 1)
                
                # Create entities
                for i in range(min(count, 20)):  # Limit to 20
                    entity = {
                        "type": defaults["type"],
                        "mass": defaults["mass"],
                        "radius": defaults["radius"],
                        "category": defaults["category"],
                        "position": [0.0, 0.0],  # Will be set later
                        "velocity": [0.0, 0.0],
                        "fixed": False,
                    }
                    entities.append(entity)
        
        # If no entities found, create a default
        if not entities:
            entities.append({
                "type": "object",
                "mass": 1.0,
                "radius": 15,
                "category": "default",
                "position": [0.0, 0.0],
                "velocity": [0.0, 0.0],
                "fixed": False,
            })
        
        return entities
    
    def _extract_environment(self, desc: str) -> Dict[str, Any]:
        """Extract environment from description."""
        environment = {"type": "open", "material": "air"}
        
        for keyword, env_data in self.ENVIRONMENT_KEYWORDS.items():
            if keyword in desc:
                environment = env_data.copy()
                break
        
        # Check for space-related
        if any(w in desc for w in ["space", "orbit", "cosmic", "star", "planet", "galaxy", "black hole"]):
            environment = {"type": "vacuum", "material": "space"}
        
        return environment
    
    def _determine_physics_mode(
        self,
        desc: str,
        entities: List[Dict],
        environment: Dict,
    ) -> str:
        """Determine the physics mode."""
        # Check actions
        for action, data in self.ACTION_KEYWORDS.items():
            if action in desc:
                return data["physics"]
        
        # Check entity categories
        categories = [e.get("category") for e in entities]
        
        if "cosmic" in categories:
            return "n_body"
        elif "particle" in categories:
            return "particle"
        elif "fluid" in categories or environment.get("type") == "fluid":
            return "fluid"
        
        # Default based on environment
        if environment.get("type") == "vacuum":
            return "n_body"
        
        return "uniform_gravity"
    
    def _determine_scenario_type(
        self,
        desc: str,
        entities: List[Dict],
        physics_mode: str,
    ) -> str:
        """Determine scenario type name."""
        entity_types = [e.get("type") for e in entities]
        
        # Check for specific scenarios
        if "apple" in entity_types and "fall" in desc:
            return "apple-fall"
        elif "ball" in entity_types and "bounce" in desc:
            return "ball-bounce"
        elif "pendulum" in entity_types or "swing" in desc:
            return "pendulum"
        elif physics_mode == "n_body":
            if "black_hole" in entity_types:
                return "black-hole-merger"
            elif "planet" in entity_types or "orbit" in desc:
                return "orbital-mechanics"
            else:
                return "n-body"
        elif "collision" in desc or "crash" in desc:
            return "collision"
        elif "projectile" in physics_mode or "throw" in desc or "launch" in desc:
            return "projectile"
        else:
            return "physics-simulation"
    
    def _extract_parameters(
        self,
        desc: str,
        entities: List[Dict],
        environment: Dict,
        physics_mode: str,
    ) -> Dict[str, Any]:
        """Extract simulation parameters."""
        params = {}
        
        # Extract height
        height_match = re.search(r'(\d+\.?\d*)\s*(m|meter|meters|ft|feet)', desc)
        if height_match:
            height = float(height_match.group(1))
            if height_match.group(2) in ("ft", "feet"):
                height *= 0.3048
            params["height"] = height
        else:
            params["height"] = 50.0  # Default
        
        # Extract speed/velocity
        speed_match = re.search(r'(\d+\.?\d*)\s*(m/s|mph|km/h|kmh)', desc)
        if speed_match:
            speed = float(speed_match.group(1))
            unit = speed_match.group(2)
            if unit == "mph":
                speed *= 0.447
            elif unit in ("km/h", "kmh"):
                speed *= 0.278
            params["initial_speed"] = speed
        
        # Extract angle
        angle_match = re.search(r'(\d+\.?\d*)\s*(degree|degrees|°)', desc)
        if angle_match:
            params["launch_angle"] = float(angle_match.group(1))
        
        # Physics-specific parameters
        if physics_mode == "uniform_gravity":
            params["gravity"] = [0.0, 98.0]  # Scaled for visual effect
            params["damping"] = 0.999
            params["restitution"] = 0.7
            
            if environment.get("material") == "ice":
                params["damping"] = 0.9999
            elif environment.get("material") == "trampoline":
                params["restitution"] = 0.95
        
        elif physics_mode == "n_body":
            params["gravity"] = [0.0, 0.0]
            params["damping"] = 0.9999
        
        elif physics_mode == "fluid":
            params["gravity"] = [0.0, 49.0]
            params["damping"] = 0.95
            params["buoyancy"] = True
        
        return params
    
    def _setup_initial_conditions(
        self,
        entities: List[Dict],
        environment: Dict,
        physics_mode: str,
        params: Dict,
    ) -> List[Dict]:
        """Set up initial positions and velocities."""
        height = params.get("height", 50.0)
        num_entities = len(entities)
        
        if physics_mode == "n_body":
            # Orbital setup
            center_x, center_y = 0.0, 0.0
            
            # Find most massive as center
            max_mass_idx = max(range(num_entities), key=lambda i: entities[i]["mass"])
            entities[max_mass_idx]["position"] = [center_x, center_y]
            entities[max_mass_idx]["velocity"] = [0.0, 0.0]
            entities[max_mass_idx]["fixed"] = True
            
            # Set others in orbit
            orbit_radius = 100.0
            for i, entity in enumerate(entities):
                if i == max_mass_idx:
                    continue
                
                angle = 2 * math.pi * i / max(num_entities - 1, 1)
                r = orbit_radius + i * 30
                
                entity["position"] = [
                    center_x + r * math.cos(angle),
                    center_y + r * math.sin(angle),
                ]
                
                # Orbital velocity
                center_mass = entities[max_mass_idx]["mass"]
                orbital_vel = math.sqrt(6.674e-2 * center_mass / r) * 0.8
                
                entity["velocity"] = [
                    -orbital_vel * math.sin(angle),
                    orbital_vel * math.cos(angle),
                ]
        
        elif physics_mode == "uniform_gravity":
            # Arrange entities for gravity simulation
            spacing = 60.0
            start_x = -((num_entities - 1) * spacing) / 2
            
            for i, entity in enumerate(entities):
                entity["position"] = [
                    start_x + i * spacing,
                    -height,  # Above ground
                ]
                
                # Set initial velocity if specified
                if "initial_speed" in params:
                    angle = math.radians(params.get("launch_angle", 45))
                    speed = params["initial_speed"]
                    entity["velocity"] = [
                        speed * math.cos(angle),
                        -speed * math.sin(angle),  # Negative Y is up
                    ]
        
        else:
            # Default arrangement
            spacing = 50.0
            for i, entity in enumerate(entities):
                entity["position"] = [
                    (i - num_entities / 2) * spacing,
                    -height / 2,
                ]
        
        return entities


# Convenience function
def parse_scenario(description: str, duration: float = 10.0) -> ParsedScenario:
    """Parse a scenario description."""
    parser = ScenarioParser()
    return parser.parse(description, duration)
