# ============================================================
#  ANM V0-OpenSource — Simulation Specialist
#  Physics Simulation & Scenario Design
# ============================================================

"""
ANM Simulation Specialist - Physics simulation support.

Capabilities:
- Simulation scenario design
- Physics parameter setup
- Visualization guidance
- Scenario parsing
- Result interpretation
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import re

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
)

try:
    from anm.utils.prompts import SIMULATION_PROMPT
except ImportError:
    SIMULATION_PROMPT = ""

__all__ = ["SimulationLLM"]


class SimulationLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Simulation Specialist.
    
    Handles simulation support including:
    - Scenario design and parsing
    - Physics parameter guidance
    - Visualization recommendations
    - Result interpretation
    - Animation blueprints
    
    Works with the ANM simulation engine.
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.SIMULATION
    
    def _get_system_prompt(self) -> str:
        # Use SIMULATION_PROMPT from prompts.py
        return SIMULATION_PROMPT if SIMULATION_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with simulation-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Simulation-specific analysis
        sim_type = self._detect_sim_type(text)
        objects = self._count_objects(text)
        
        sim_meta = [
            "",
            "[SIMULATION_ANALYSIS]",
            f"simulation_type: {sim_type}",
            f"objects_defined: {objects}",
            f"has_scenario: {self._has_scenario(text)}",
            f"physics_model: {self._detect_physics(text)}",
        ]
        
        return base_meta + "\n".join(sim_meta)
    
    def _detect_sim_type(self, text: str) -> str:
        """Detect simulation type."""
        lower = text.lower()
        
        types = {
            "orbital": ["orbit", "kepler", "binary", "planet"],
            "black_hole": ["black hole", "schwarzschild", "event horizon"],
            "merger": ["merger", "inspiral", "gravitational wave"],
            "particle": ["particle", "collision", "swarm"],
            "field": ["field", "vector", "potential"],
        }
        
        for sim_type, keywords in types.items():
            if any(kw in lower for kw in keywords):
                return sim_type
        
        return "general"
    
    def _count_objects(self, text: str) -> int:
        """Count simulation objects defined."""
        patterns = [
            r'object[s]?:',
            r'- name:',
            r'mass:',
            r'position:',
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return min(count // 2, 20)  # Rough estimate
    
    def _has_scenario(self, text: str) -> bool:
        """Check if scenario is defined."""
        lower = text.lower()
        return "scenario:" in lower or "simulation:" in lower
    
    def _detect_physics(self, text: str) -> str:
        """Detect physics model used."""
        lower = text.lower()
        
        if "relativistic" in lower or "einstein" in lower:
            return "relativistic"
        if "quantum" in lower:
            return "quantum"
        if "newtonian" in lower or "classical" in lower:
            return "newtonian"
        
        return "newtonian"
