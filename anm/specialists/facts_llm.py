# ============================================================
#  ANM V0-OpenSource — Facts Specialist
#  Fact Verification & Truth Assessment
# ============================================================

"""
ANM Facts Specialist - Fact checking and verification.

Capabilities:
- Claim verification
- Source assessment
- Contradiction detection
- Confidence scoring
- Citation tracking
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
    from anm.utils.prompts import FACTS_PROMPT
except ImportError:
    FACTS_PROMPT = ""

__all__ = ["FactsLLM"]


class FactsLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Facts Specialist.
    
    Handles fact verification including:
    - Claim assessment
    - Source credibility
    - Contradiction detection
    - Confidence scoring
    - Evidence tracking
    
    Features:
    - Multi-source verification
    - Uncertainty quantification
    - Bias detection
    - Citation validation
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.FACTS
    
    def _get_system_prompt(self) -> str:
        # Use FACTS_PROMPT from prompts.py (single source of truth)
        # FACTS_PROMPT already includes META-COGNITION, META-EFFICIENCY, and OUTPUT format
        return FACTS_PROMPT if FACTS_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with facts-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Facts-specific analysis
        verdict = self._extract_verdict(text)
        confidence = self._extract_confidence(text)
        claims = self._count_claims(text)
        
        facts_meta = [
            "",
            "[FACTS_ANALYSIS]",
            f"verdict: {verdict}",
            f"confidence: {confidence}",
            f"claims_assessed: {claims}",
            f"has_evidence: {self._has_evidence(text)}",
            f"has_sources: {self._has_sources(text)}",
            f"contradictions_noted: {self._has_contradictions(text)}",
        ]
        
        return base_meta + "\n".join(facts_meta)
    
    def _extract_verdict(self, text: str) -> str:
        """Extract verdict from text."""
        lower = text.lower()
        
        if "verified" in lower and "unverified" not in lower:
            return "VERIFIED"
        if "partially" in lower or "partly" in lower:
            return "PARTIALLY_TRUE"
        if "false" in lower or "incorrect" in lower:
            return "FALSE"
        if "outdated" in lower or "no longer" in lower:
            return "OUTDATED"
        if "unverified" in lower or "cannot verify" in lower:
            return "UNVERIFIED"
        
        return "PENDING"
    
    def _extract_confidence(self, text: str) -> str:
        """Extract confidence level from text."""
        lower = text.lower()
        
        high = ["definitely", "certainly", "clearly", "proven", "established"]
        low = ["possibly", "maybe", "uncertain", "unclear", "might"]
        
        if any(h in lower for h in high):
            return "HIGH"
        if any(l in lower for l in low):
            return "LOW"
        
        return "MEDIUM"
    
    def _count_claims(self, text: str) -> int:
        """Count number of claims being assessed."""
        # Look for claim markers
        patterns = [
            r'\bclaim\b',
            r'\bstatement\b',
            r'\bassertion\b',
            r'\d+\.',  # Numbered lists
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        return min(count, 20)
    
    def _has_evidence(self, text: str) -> bool:
        """Check if evidence is provided."""
        lower = text.lower()
        markers = ["evidence", "source", "according to", "shows that", "demonstrates"]
        return any(m in lower for m in markers)
    
    def _has_sources(self, text: str) -> bool:
        """Check if sources are cited."""
        lower = text.lower()
        markers = ["source:", "citation", "reference", "according to", "study"]
        return any(m in lower for m in markers)
    
    def _has_contradictions(self, text: str) -> bool:
        """Check if contradictions are noted."""
        lower = text.lower()
        markers = ["contradiction", "conflicts with", "inconsistent", "disagrees"]
        return any(m in lower for m in markers)
