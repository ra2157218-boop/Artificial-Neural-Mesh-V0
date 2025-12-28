# ============================================================
#  ANM V0-OpenSource — Image Specialist
#  Visual Analysis & Image Understanding
# ============================================================

"""
ANM Image Specialist - Visual perception and analysis.

Capabilities:
- Image description
- Scene understanding
- Object detection (text-based)
- Visual reasoning
- Image-to-text conversion
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import re

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
)

# Import prompt
try:
    from anm.utils.prompts import IMAGE_PROMPT
except ImportError:
    IMAGE_PROMPT = ""

__all__ = ["ImageLLM"]


class ImageLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Image Specialist.
    
    Handles visual analysis including:
    - Image description
    - Scene understanding
    - Object identification
    - Visual reasoning
    - Composition analysis
    
    Note: Works with text descriptions of images.
    Actual image processing requires vision models.
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.IMAGE
    
    def _get_system_prompt(self) -> str:
        # Use IMAGE_PROMPT from prompts.py (single source of truth)
        return IMAGE_PROMPT if IMAGE_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with image-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Image-specific analysis
        img_meta = [
            "",
            "[IMAGE_ANALYSIS]",
            f"has_description: {self._has_description(text)}",
            f"objects_mentioned: {self._count_objects(text)}",
            f"safety_check: {self._check_safety(text)}",
        ]
        
        return base_meta + "\n".join(img_meta)
    
    def _has_description(self, text: str) -> bool:
        """Check if image description exists."""
        lower = text.lower()
        return "image" in lower or "scene" in lower or "shows" in lower
    
    def _count_objects(self, text: str) -> int:
        """Count mentioned objects."""
        # Simple object counting
        objects = re.findall(r'\b(?:a|an|the)\s+(\w+)', text.lower())
        return min(len(objects), 20)
    
    def _check_safety(self, text: str) -> str:
        """Check for safety violations."""
        lower = text.lower()
        
        # Forbidden patterns
        forbidden = [
            "this person is",
            "appears to be [name]",
            "identified as",
            "age is",
            "gender is",
        ]
        
        if any(f in lower for f in forbidden):
            return "WARNING"
        
        return "CLEAN"
