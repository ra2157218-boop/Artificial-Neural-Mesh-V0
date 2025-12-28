# ============================================================
#  ANM V0-OpenSource — Self-Awareness Specialist
#  Meta-Cognitive Analysis & Confidence Assessment
# ============================================================

"""
ANM Self-Awareness Specialist - Meta-cognitive analysis.

Capabilities:
- Confidence assessment
- Uncertainty detection
- Reasoning quality evaluation
- Bias detection
- Self-reflection
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import re

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
    run_model,
)

try:
    from anm.utils.prompts import SELF_AWARENESS_PROMPT
except ImportError:
    SELF_AWARENESS_PROMPT = ""

__all__ = ["SelfAwarenessLLM"]


class SelfAwarenessLLM:
    """
    ANM V0-OpenSource Self-Awareness Module.
    
    Meta-specialist that analyzes other specialists' outputs for:
    - Confidence levels
    - Uncertainty markers
    - Reasoning quality
    - Potential biases
    - Areas needing improvement
    
    This is NOT a BaseSpecialist subclass because it
    analyzes outputs rather than processing queries.
    """
    
    VERSION = "0.1.0-opensource"
    
    def __init__(
        self,
        model_name: str = "deepseek-r1:1.5b",
        use_llm: bool = True,
    ):
        self.model = model_name
        self.use_llm = use_llm
        
        # Confidence markers
        self._high_conf = [
            "definitely", "certainly", "proven", "established",
            "clear", "obvious", "known", "verified",
        ]
        self._low_conf = [
            "maybe", "perhaps", "possibly", "might",
            "uncertain", "unclear", "unknown", "guess",
            "not sure", "could be", "seems like",
        ]
        
        # Uncertainty markers
        self._uncertainty = [
            "approximately", "roughly", "about", "around",
            "estimate", "assumption", "hypothesis",
        ]
    
    def analyze(
        self,
        domain: str,
        text: str,
    ) -> Dict[str, Any]:
        """
        Analyze specialist output for self-awareness metrics.
        
        Args:
            domain: The domain that produced the text
            text: The output to analyze
            
        Returns:
            Dict with confidence, uncertainty, and notes
        """
        if not text:
            return {
                "confidence": "unknown",
                "uncertainty": "high",
                "notes": "Empty output",
            }
        
        lower = text.lower()
        
        # Count confidence markers
        high_count = sum(1 for m in self._high_conf if m in lower)
        low_count = sum(1 for m in self._low_conf if m in lower)
        
        # Determine confidence
        if high_count > low_count + 2:
            confidence = "high"
        elif low_count > high_count + 2:
            confidence = "low"
        else:
            confidence = "medium"
        
        # Count uncertainty markers
        unc_count = sum(1 for m in self._uncertainty if m in lower)
        
        if unc_count >= 3:
            uncertainty = "high"
        elif unc_count >= 1:
            uncertainty = "medium"
        else:
            uncertainty = "low"
        
        # Generate notes
        notes = self._generate_notes(text, domain, confidence, uncertainty)
        
        # Use LLM for deeper analysis if enabled
        if self.use_llm and len(text) > 100:
            llm_analysis = self._llm_analyze(text, domain)
            if llm_analysis:
                notes = f"{notes}. LLM: {llm_analysis}"
        
        return {
            "confidence": confidence,
            "uncertainty": uncertainty,
            "notes": notes,
            "domain": domain,
            "high_conf_markers": high_count,
            "low_conf_markers": low_count,
            "uncertainty_markers": unc_count,
        }
    
    def _generate_notes(
        self,
        text: str,
        domain: str,
        confidence: str,
        uncertainty: str,
    ) -> str:
        """Generate analysis notes."""
        notes = []
        
        lower = text.lower()
        
        # Check for hedging
        hedges = ["however", "but", "although", "on the other hand"]
        if any(h in lower for h in hedges):
            notes.append("Contains hedging language")
        
        # Check for errors
        if "[error" in lower or "failed" in lower:
            notes.append("Contains error markers")
        
        # Check for claims
        if "i know" in lower or "i am certain" in lower:
            notes.append("Makes certainty claims")
        
        # Check for questions
        if "?" in text:
            notes.append("Contains questions (possible uncertainty)")
        
        if not notes:
            notes.append(f"{domain} output appears balanced")
        
        return "; ".join(notes)
    
    def _llm_analyze(self, text: str, domain: str) -> Optional[str]:
        """Use LLM for deeper analysis using SELF_AWARENESS_PROMPT."""
        # Use SELF_AWARENESS_PROMPT as base, adapted for output analysis
        base_prompt = SELF_AWARENESS_PROMPT if SELF_AWARENESS_PROMPT else ""
        
        prompt = f"""
{base_prompt}

--- SPECIALIST OUTPUT TO ANALYZE ---
Domain: {domain}
Output (first 1000 chars):
{text[:1000]}

--- ANALYSIS TASK ---
Analyze this {domain} specialist output for:
1. Confidence level (high/medium/low)
2. Main uncertainties
3. Any red flags or quality issues

Provide a brief analysis (1-3 sentences):
"""
        
        try:
            result = run_model(prompt, max_tokens=256)
            if result and not result.startswith("["):
                return result[:200]
        except Exception:
            pass
        
        return None
    
    def quick_check(self, text: str) -> str:
        """Quick confidence check without full analysis."""
        if not text:
            return "unknown"
        
        lower = text.lower()
        
        high = sum(1 for m in self._high_conf if m in lower)
        low = sum(1 for m in self._low_conf if m in lower)
        
        if high > low + 1:
            return "high"
        if low > high + 1:
            return "low"
        return "medium"
