# ============================================================
#  ANM V0-OpenSource — Sound Specialist
#  Audio Analysis & Sonification Design
# ============================================================

"""
ANM Sound Specialist - Audio and sonification design.

Capabilities:
- Sound design blueprints
- Sonification mapping
- Audio event description
- Musical structure analysis
- Acoustic safety awareness
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
    from anm.utils.prompts import SOUND_PROMPT
except ImportError:
    SOUND_PROMPT = ""

__all__ = ["SoundLLM"]


class SoundLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Sound Specialist.
    
    Handles sound/audio design including:
    - Sonification blueprints
    - Sound design descriptions
    - Audio event mapping
    - Musical structure
    
    Note: This is a DESIGN specialist.
    It creates blueprints and descriptions,
    NOT actual audio generation.
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.SOUND
    
    def _get_system_prompt(self) -> str:
        # Use SOUND_PROMPT from prompts.py (single source of truth)
        # SOUND_PROMPT already includes META-COGNITION, META-EFFICIENCY, and OUTPUT format
        return SOUND_PROMPT if SOUND_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with sound-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Sound-specific analysis
        mode = self._detect_mode(text)
        layers = self._count_layers(text)
        
        sound_meta = [
            "",
            "[SOUND_ANALYSIS]",
            f"mode: {mode}",
            f"layers_defined: {layers}",
            f"has_blueprint: {self._has_blueprint(text)}",
            f"safety_noted: {self._has_safety(text)}",
        ]
        
        return base_meta + "\n".join(sound_meta)
    
    def _detect_mode(self, text: str) -> str:
        """Detect sonification mode."""
        lower = text.lower()
        
        if "cinematic" in lower or "scene" in lower or "film" in lower:
            return "cinematic"
        if "symbolic" in lower or "data" in lower or "abstract" in lower:
            return "symbolic"
        if "mixed" in lower or "hybrid" in lower:
            return "mixed"
        
        return "general"
    
    def _count_layers(self, text: str) -> int:
        """Count sound layers defined."""
        # Look for layer markers
        patterns = [
            r'layer[s]?:',
            r'- name:',
            r'bass|mid|high|ambient|fx',
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return min(count, 20)
    
    def _has_blueprint(self, text: str) -> bool:
        """Check if blueprint structure exists."""
        lower = text.lower()
        return "blueprint" in lower or "layers:" in lower
    
    def _has_safety(self, text: str) -> bool:
        """Check if safety considerations noted."""
        lower = text.lower()
        markers = ["safety", "loud", "hearing", "volume", "caution"]
        return any(m in lower for m in markers)
