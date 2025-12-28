# ============================================================
#  ANM V0-OpenSource — Physics Specialist
#  Physical Reasoning & Analysis
# ============================================================

"""
ANM Physics Specialist - Physical reasoning and analysis.

Capabilities:
- Classical mechanics
- Electromagnetism
- Thermodynamics
- Quantum mechanics
- Relativity
- Dimensional analysis
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
    from anm.utils.prompts import PHYSICS_PROMPT
except ImportError:
    PHYSICS_PROMPT = ""

__all__ = ["PhysicsLLM"]


class PhysicsLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Physics Specialist.
    
    Handles physics reasoning including:
    - Classical mechanics (Newton, Lagrange, Hamilton)
    - Electromagnetism (Maxwell's equations)
    - Thermodynamics (laws, entropy)
    - Quantum mechanics (wavefunctions, operators)
    - Special and General Relativity
    - Astrophysics and cosmology
    
    Features:
    - Dimensional analysis
    - Conservation law checking
    - Unit conversion
    - Order of magnitude estimates
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.PHYSICS
    
    def _get_system_prompt(self) -> str:
        # Use PHYSICS_PROMPT from prompts.py (single source of truth)
        # PHYSICS_PROMPT already includes META-COGNITION, META-EFFICIENCY, and OUTPUT format
        return PHYSICS_PROMPT if PHYSICS_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with physics-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Physics-specific analysis
        physics_area = self._detect_physics_area(text)
        units_found = self._extract_units(text)
        conservation_check = self._check_conservation_mentions(text)
        
        physics_meta = [
            "",
            "[PHYSICS_ANALYSIS]",
            f"physics_area: {physics_area}",
            f"units_found: {', '.join(units_found[:5]) if units_found else 'none'}",
            f"conservation_mentioned: {', '.join(conservation_check) if conservation_check else 'none'}",
            f"has_dimensional_analysis: {self._has_dimensional_analysis(text)}",
            f"speculation_risk: {self._assess_speculation_risk(text)}",
        ]
        
        return base_meta + "\n".join(physics_meta)
    
    def _detect_physics_area(self, text: str) -> str:
        """Detect which area of physics is being discussed."""
        lower = text.lower()
        
        areas = {
            "quantum_mechanics": ["quantum", "wavefunction", "superposition", "entanglement"],
            "relativity": ["relativity", "spacetime", "geodesic", "lorentz"],
            "thermodynamics": ["entropy", "temperature", "heat", "thermodynamic"],
            "electromagnetism": ["electric", "magnetic", "maxwell", "electromagnetic"],
            "mechanics": ["force", "momentum", "kinetic", "potential energy"],
            "astrophysics": ["star", "galaxy", "black hole", "cosmos"],
            "optics": ["light", "refraction", "diffraction", "photon"],
            "nuclear": ["nuclear", "fission", "fusion", "radioactive"],
        }
        
        for area, keywords in areas.items():
            if any(kw in lower for kw in keywords):
                return area
        
        return "general"
    
    def _extract_units(self, text: str) -> List[str]:
        """Extract physical units from text."""
        units = []
        
        # Common unit patterns
        unit_patterns = [
            r'\b\d+\s*(m|km|cm|mm|nm)\b',
            r'\b\d+\s*(kg|g|mg)\b',
            r'\b\d+\s*(s|ms|ns|hr|min)\b',
            r'\b\d+\s*(J|kJ|eV|keV|MeV)\b',
            r'\b\d+\s*(N|kN)\b',
            r'\b\d+\s*(W|kW|MW)\b',
            r'\b\d+\s*(A|mA)\b',
            r'\b\d+\s*(V|kV|mV)\b',
            r'\b\d+\s*(K|°C|°F)\b',
            r'\b\d+\s*(Pa|kPa|atm|bar)\b',
            r'\bc\b',  # speed of light
            r'\bℏ\b|\bhbar\b',  # reduced Planck
        ]
        
        for pattern in unit_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                units.append(match.group())
        
        return list(set(units))
    
    def _check_conservation_mentions(self, text: str) -> List[str]:
        """Check which conservation laws are mentioned."""
        lower = text.lower()
        conserved = []
        
        if "conservation of energy" in lower or "energy is conserved" in lower:
            conserved.append("energy")
        if "conservation of momentum" in lower or "momentum is conserved" in lower:
            conserved.append("momentum")
        if "conservation of angular momentum" in lower:
            conserved.append("angular_momentum")
        if "conservation of charge" in lower or "charge is conserved" in lower:
            conserved.append("charge")
        if "conservation of mass" in lower:
            conserved.append("mass")
        
        return conserved
    
    def _has_dimensional_analysis(self, text: str) -> bool:
        """Check if dimensional analysis is present."""
        lower = text.lower()
        markers = ["dimension", "units", "[m]", "[kg]", "[s]", "m/s", "kg·m"]
        return any(m in lower for m in markers)
    
    def _assess_speculation_risk(self, text: str) -> str:
        """Assess risk of speculative claims."""
        lower = text.lower()
        
        high_risk = [
            "inside the black hole",
            "inside the event horizon",
            "beyond the singularity",
            "what happens inside",
            "structure of the singularity",
        ]
        
        medium_risk = [
            "theoretically",
            "it is believed",
            "scientists think",
            "might be",
            "could potentially",
        ]
        
        if any(phrase in lower for phrase in high_risk):
            return "high"
        if any(phrase in lower for phrase in medium_risk):
            return "medium"
        return "low"
