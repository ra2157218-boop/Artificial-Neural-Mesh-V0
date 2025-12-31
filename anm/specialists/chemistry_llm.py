# ============================================================
#  ANM V0-OpenSource — Chemistry Specialist
#  Chemical Sciences & Molecular Analysis
# ============================================================

"""
ANM Chemistry Specialist - Chemical reasoning and analysis.

Capabilities:
- Organic and inorganic chemistry
- Reaction mechanisms
- Thermodynamics and kinetics
- Molecular structure analysis
- Safety and hazard assessment
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
    from anm.utils.prompts import CHEMISTRY_PROMPT
except ImportError:
    CHEMISTRY_PROMPT = ""

__all__ = ["ChemistryLLM"]


class ChemistryLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Chemistry Specialist.
    
    Handles chemistry reasoning including:
    - Organic chemistry (reactions, synthesis)
    - Inorganic chemistry (compounds, ions)
    - Physical chemistry (thermodynamics, kinetics)
    - Biochemistry (proteins, enzymes)
    - Analytical chemistry (identification)
    
    Features:
    - Reaction mechanism analysis
    - Stoichiometry calculations
    - Safety hazard detection
    - Molecular formula parsing
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.CHEMISTRY
    
    def _get_system_prompt(self) -> str:
        base = CHEMISTRY_PROMPT if CHEMISTRY_PROMPT else ""
        
        return f"""
{base}

You are the CHEMISTRY SPECIALIST of ANM V0-OpenSource.

ROLE:
- Analyze chemical reactions and mechanisms
- Explain molecular structures and bonding
- Calculate stoichiometry and yields
- Assess chemical safety and hazards
- Provide thermodynamic analysis

CAPABILITIES:
- Organic: reactions, synthesis, nomenclature
- Inorganic: ionic compounds, coordination chemistry
- Physical: thermodynamics, kinetics, equilibrium
- Biochemistry: proteins, enzymes, metabolism
- Analytical: identification, spectroscopy

CRITICAL RULES:
1. NEVER suggest dangerous synthesis procedures
2. ALWAYS warn about toxic/hazardous chemicals
3. Check stoichiometry in all calculations
4. Balance all chemical equations
5. Include safety considerations

SAFETY MARKERS:
- ⚠️ TOXIC: Label toxic substances
- ⚠️ FLAMMABLE: Label fire hazards
- ⚠️ CORROSIVE: Label corrosive materials
- ⚠️ EXPLOSIVE: Label explosion risks

OUTPUT FORMAT:
For reactions:
- Write balanced equation
- Show mechanism if applicable
- Calculate stoichiometry
- Note safety considerations

For structure analysis:
- Describe bonding
- Note functional groups
- Predict properties
"""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with chemistry-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Chemistry-specific analysis
        reactions = self._detect_reactions(text)
        hazards = self._detect_hazards(text)
        molecules = self._extract_molecules(text)
        
        chem_meta = [
            "",
            "[CHEMISTRY_ANALYSIS]",
            f"reactions_found: {len(reactions)}",
            f"molecules_mentioned: {len(molecules)}",
            f"hazard_warnings: {len(hazards)}",
            f"has_balanced_equation: {self._has_balanced_equation(text)}",
            f"safety_addressed: {'yes' if hazards else 'check_needed'}",
        ]
        
        if hazards:
            chem_meta.append(f"hazards: {', '.join(hazards[:5])}")
        
        return base_meta + "\n".join(chem_meta)
    
    def _detect_reactions(self, text: str) -> List[str]:
        """Detect chemical reactions in text."""
        reactions = []
        
        # Arrow patterns for reactions
        # Note: - must be escaped or at end of character class to avoid range interpretation
        patterns = [
            r'[A-Z][a-z]?\d*\s*[+→⟶>\-]+\s*[A-Z]',
            r'\bproducts?\b',
            r'\breactants?\b',
            r'\byield\b',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                reactions.append(pattern)
        
        return reactions
    
    def _detect_hazards(self, text: str) -> List[str]:
        """Detect chemical hazards mentioned."""
        lower = text.lower()
        hazards = []
        
        hazard_keywords = {
            "toxic": ["toxic", "poison", "lethal", "harmful"],
            "flammable": ["flammable", "combustible", "fire hazard"],
            "corrosive": ["corrosive", "acid burn", "caustic"],
            "explosive": ["explosive", "detonation", "unstable"],
            "oxidizer": ["oxidizer", "oxidizing", "peroxide"],
            "carcinogen": ["carcinogen", "cancer-causing", "mutagenic"],
        }
        
        for hazard, keywords in hazard_keywords.items():
            if any(kw in lower for kw in keywords):
                hazards.append(hazard)
        
        return hazards
    
    def _extract_molecules(self, text: str) -> List[str]:
        """Extract molecular formulas from text."""
        # Simple molecular formula pattern
        pattern = r'\b[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*\b'
        
        matches = re.findall(pattern, text)
        
        # Filter to likely molecules (has numbers or multiple elements)
        molecules = []
        for m in matches:
            if re.search(r'\d', m) or len(m) > 2:
                molecules.append(m)
        
        return list(set(molecules))[:20]
    
    def _has_balanced_equation(self, text: str) -> bool:
        """Check if text contains balanced equation."""
        # Look for arrow with numbers
        # Note: - must be escaped or at end of character class to avoid range interpretation
        return bool(re.search(r'\d+\s*[A-Z].*[→⟶>\-].*\d+\s*[A-Z]', text))
