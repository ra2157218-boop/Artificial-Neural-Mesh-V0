# ============================================================
#  ANM V0-OpenSource — Math Specialist
#  Mathematical Reasoning & Computation
# ============================================================

"""
ANM Math Specialist - Mathematical reasoning and computation.

Capabilities:
- Algebraic manipulation
- Calculus operations
- Linear algebra
- Probability and statistics
- Proofs and derivations
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
    from anm.utils.prompts import MATH_PROMPT
except ImportError:
    MATH_PROMPT = ""

__all__ = ["MathLLM"]


class MathLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Math Specialist.
    
    Handles mathematical reasoning including:
    - Algebra and equation solving
    - Calculus (derivatives, integrals)
    - Linear algebra (matrices, vectors)
    - Probability and statistics
    - Number theory
    - Proofs and derivations
    
    Features:
    - Step-by-step solutions
    - Formula verification
    - Dimensional analysis
    - Error checking
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.MATH
    
    def _get_system_prompt(self) -> str:
        # Use MATH_PROMPT from prompts.py (single source of truth)
        # MATH_PROMPT already includes META-COGNITION, META-EFFICIENCY, and OUTPUT format
        return MATH_PROMPT if MATH_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with math-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Extract math-specific metrics
        formulas = self._extract_formulas(text)
        operations = self._detect_operations(text)
        
        math_meta = [
            "",
            "[MATH_ANALYSIS]",
            f"formulas_found: {len(formulas)}",
            f"operations: {', '.join(operations) if operations else 'none'}",
            f"has_proof: {self._has_proof_structure(text)}",
            f"has_steps: {self._has_step_structure(text)}",
        ]
        
        return base_meta + "\n".join(math_meta)
    
    def _extract_formulas(self, text: str) -> List[str]:
        """Extract mathematical formulas."""
        formulas = []
        
        # LaTeX style
        for match in re.finditer(r'\$(.+?)\$', text):
            formulas.append(match.group(1))
        
        # Equation patterns
        for match in re.finditer(r'([A-Za-z_]+\s*=\s*[^,\n]{3,50})', text):
            formulas.append(match.group(1))
        
        return formulas[:20]
    
    def _detect_operations(self, text: str) -> List[str]:
        """Detect mathematical operations used."""
        lower = text.lower()
        ops = []
        
        operation_keywords = {
            "derivative": ["derivative", "differentiate", "d/dx"],
            "integral": ["integral", "integrate", "∫"],
            "limit": ["limit", "lim", "approaches"],
            "matrix": ["matrix", "matrices", "determinant"],
            "probability": ["probability", "p(", "expected value"],
            "summation": ["sum", "summation", "Σ", "∑"],
            "product": ["product", "Π", "∏"],
        }
        
        for op, keywords in operation_keywords.items():
            if any(kw in lower for kw in keywords):
                ops.append(op)
        
        return ops
    
    def _has_proof_structure(self, text: str) -> bool:
        """Check if text has proof structure."""
        lower = text.lower()
        proof_markers = ["proof", "theorem", "lemma", "qed", "∎", "therefore", "hence"]
        return any(m in lower for m in proof_markers)
    
    def _has_step_structure(self, text: str) -> bool:
        """Check if text has step-by-step structure."""
        return bool(re.search(r'step\s*\d|^\d+[.)]\s', text, re.MULTILINE | re.IGNORECASE))
