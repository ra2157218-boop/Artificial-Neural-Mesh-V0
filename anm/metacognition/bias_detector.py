# ============================================================
# ANM V0-OpenSource — BIAS DETECTOR
#  Detects potential cognitive biases in reasoning
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import re


class BiasType(Enum):
    """Types of cognitive biases."""
    # Selection biases
    CONFIRMATION = "confirmation"         # Seeking confirming evidence
    SELECTION = "selection"               # Cherry-picking data
    SURVIVORSHIP = "survivorship"         # Only seeing survivors
    
    # Attribution biases
    FUNDAMENTAL_ATTRIBUTION = "fundamental_attribution"  # Over-attributing to personality
    SELF_SERVING = "self_serving"         # Attributing success to self
    
    # Memory biases
    HINDSIGHT = "hindsight"               # "I knew it all along"
    RECENCY = "recency"                   # Overweighting recent info
    AVAILABILITY = "availability"         # Overweighting available info
    
    # Judgment biases
    ANCHORING = "anchoring"               # Over-relying on first info
    FRAMING = "framing"                   # Affected by presentation
    OVERCONFIDENCE = "overconfidence"     # Too confident
    
    # Social biases
    AUTHORITY = "authority"               # Trusting authority too much
    BANDWAGON = "bandwagon"               # Following the crowd
    
    # Reasoning biases
    SUNK_COST = "sunk_cost"               # Can't let go of past investment
    STATUS_QUO = "status_quo"             # Preferring current state
    ZERO_RISK = "zero_risk"               # Preferring zero risk options


@dataclass
class BiasAlert:
    """Alert about potential bias."""
    bias_type: BiasType
    severity: str               # low, medium, high
    confidence: float           # 0-1, confidence in detection
    context: str                # Where bias was detected
    explanation: str            # Why this might be a bias
    mitigation: str             # How to address it


class BiasDetector:
    """
    Detects potential cognitive biases in ANM's processing.
    
    Monitors for:
    - Confirmation bias (seeking confirming evidence)
    - Anchoring (over-relying on initial information)
    - Availability bias (overweighting recent/available info)
    - Framing effects (affected by how question is posed)
    - Overconfidence (excessive certainty)
    
    Usage:
        detector = BiasDetector()
        
        alerts = detector.check(
            query="Isn't it true that X causes Y?",
            reasoning="Studies confirm that X causes Y...",
            sources_consulted=["pro_X_study"],
        )
        
        for alert in alerts:
            print(f"Bias: {alert.bias_type.name}, Severity: {alert.severity}")
    """
    
    # Confirmation bias indicators in queries
    LEADING_PATTERNS = [
        r"isn't it (true|obvious|clear) that",
        r"don't you (think|agree|believe)",
        r"surely",
        r"obviously",
        r"everyone knows",
        r"it's (well-known|common knowledge)",
    ]
    
    # Overconfidence indicators
    OVERCONFIDENCE_MARKERS = [
        "definitely", "certainly", "absolutely", "undoubtedly",
        "without question", "guaranteed", "100%", "always", "never",
        "impossible", "certain", "proof", "proven",
    ]
    
    # Anchoring indicators
    ANCHORING_MARKERS = [
        "first", "initially", "original", "starting point",
        "based on the initial", "compared to the first",
    ]
    
    def __init__(self):
        self._alerts_history: List[List[BiasAlert]] = []
    
    def check(
        self,
        query: str,
        reasoning: str,
        answer: str = "",
        sources_consulted: Optional[List[str]] = None,
        alternatives_considered: int = 0,
    ) -> List[BiasAlert]:
        """
        Check for potential biases.
        
        Args:
            query: Original query
            reasoning: Reasoning process
            answer: Final answer
            sources_consulted: Sources used
            alternatives_considered: Number of alternatives considered
        
        Returns:
            List of BiasAlert objects
        """
        alerts = []
        sources = sources_consulted or []
        combined = f"{query} {reasoning} {answer}".lower()
        
        # 1. Check for leading questions (confirmation bias risk)
        leading = self._check_leading_question(query)
        if leading:
            alerts.append(BiasAlert(
                bias_type=BiasType.CONFIRMATION,
                severity="medium",
                confidence=0.7,
                context="Query contains leading language",
                explanation="The question may be framed to confirm a particular view.",
                mitigation="Consider alternative perspectives before answering.",
            ))
        
        # 2. Check for one-sided sources
        if len(sources) > 0 and len(sources) < 3:
            alerts.append(BiasAlert(
                bias_type=BiasType.SELECTION,
                severity="low",
                confidence=0.5,
                context="Limited sources consulted",
                explanation="Few sources may lead to selection bias.",
                mitigation="Consult additional sources for balance.",
            ))
        
        # 3. Check for overconfidence
        overconf = self._check_overconfidence(reasoning + answer)
        if overconf > 0.5:
            alerts.append(BiasAlert(
                bias_type=BiasType.OVERCONFIDENCE,
                severity="medium" if overconf > 0.7 else "low",
                confidence=overconf,
                context="Strong certainty markers detected",
                explanation="Language suggests more certainty than may be warranted.",
                mitigation="Add appropriate hedging and acknowledge uncertainty.",
            ))
        
        # 4. Check for anchoring
        anchor = self._check_anchoring(reasoning)
        if anchor:
            alerts.append(BiasAlert(
                bias_type=BiasType.ANCHORING,
                severity="low",
                confidence=0.6,
                context="Heavy reliance on initial information",
                explanation="May be over-anchored on first piece of information.",
                mitigation="Re-evaluate conclusion independent of initial info.",
            ))
        
        # 5. Check for lack of alternatives
        if alternatives_considered < 2:
            alerts.append(BiasAlert(
                bias_type=BiasType.CONFIRMATION,
                severity="low",
                confidence=0.4,
                context="Few alternatives considered",
                explanation="Not considering alternatives may confirm initial view.",
                mitigation="Explicitly consider 2-3 alternative explanations.",
            ))
        
        # 6. Check for framing effects
        framing = self._check_framing(query, answer)
        if framing:
            alerts.append(BiasAlert(
                bias_type=BiasType.FRAMING,
                severity="low",
                confidence=0.5,
                context="Answer may be affected by question framing",
                explanation="The way the question was framed may have influenced the answer.",
                mitigation="Reframe the question neutrally and reconsider.",
            ))
        
        # 7. Check for authority bias
        authority = self._check_authority_bias(reasoning)
        if authority:
            alerts.append(BiasAlert(
                bias_type=BiasType.AUTHORITY,
                severity="low",
                confidence=0.5,
                context="Heavy reliance on authority",
                explanation="May be accepting claims based on source authority alone.",
                mitigation="Evaluate claims on their merit, not just the source.",
            ))
        
        self._alerts_history.append(alerts)
        return alerts
    
    def _check_leading_question(self, query: str) -> bool:
        """Check if query is leading."""
        query_lower = query.lower()
        
        for pattern in self.LEADING_PATTERNS:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _check_overconfidence(self, text: str) -> float:
        """Check for overconfidence markers."""
        text_lower = text.lower()
        count = sum(1 for marker in self.OVERCONFIDENCE_MARKERS if marker in text_lower)
        
        # Normalize: 3+ markers = high overconfidence
        return min(1.0, count / 3)
    
    def _check_anchoring(self, reasoning: str) -> bool:
        """Check for anchoring bias."""
        lower = reasoning.lower()
        
        # Check for anchoring markers
        anchor_count = sum(1 for marker in self.ANCHORING_MARKERS if marker in lower)
        
        return anchor_count >= 2
    
    def _check_framing(self, query: str, answer: str) -> bool:
        """Check for framing effects."""
        # Positive framing
        positive = ["benefit", "advantage", "gain", "save", "success"]
        negative = ["risk", "loss", "cost", "danger", "failure"]
        
        query_lower = query.lower()
        
        pos_in_query = sum(1 for p in positive if p in query_lower)
        neg_in_query = sum(1 for n in negative if n in query_lower)
        
        # If query is strongly framed one way, check if answer follows
        if pos_in_query > neg_in_query + 1:
            answer_lower = answer.lower()
            pos_in_answer = sum(1 for p in positive if p in answer_lower)
            if pos_in_answer > 1:
                return True
        elif neg_in_query > pos_in_query + 1:
            answer_lower = answer.lower()
            neg_in_answer = sum(1 for n in negative if n in answer_lower)
            if neg_in_answer > 1:
                return True
        
        return False
    
    def _check_authority_bias(self, reasoning: str) -> bool:
        """Check for over-reliance on authority."""
        authority_markers = [
            "expert", "authority", "professor", "scientist",
            "according to", "study shows", "research proves",
        ]
        
        lower = reasoning.lower()
        count = sum(1 for marker in authority_markers if marker in lower)
        
        return count >= 3  # Multiple authority references
    
    def get_bias_summary(self) -> Dict[str, int]:
        """Get summary of detected biases."""
        counts: Dict[str, int] = {}
        
        for alerts in self._alerts_history:
            for alert in alerts:
                bias_name = alert.bias_type.value
                counts[bias_name] = counts.get(bias_name, 0) + 1
        
        return counts
    
    def generate_debiasing_prompt(self, alerts: List[BiasAlert]) -> str:
        """Generate a prompt to help debias reasoning."""
        if not alerts:
            return ""
        
        lines = ["Before finalizing your response, consider:"]
        
        for alert in alerts:
            lines.append(f"- {alert.mitigation}")
        
        return "\n".join(lines)
