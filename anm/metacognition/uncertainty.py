# ============================================================
# ANM V0-OpenSource — UNCERTAINTY QUANTIFIER
#  Distinguishes between different types of uncertainty
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum


class UncertaintyType(Enum):
    """Types of uncertainty."""
    # Aleatoric (irreducible, inherent randomness)
    ALEATORIC_DATA = "aleatoric_data"           # Noisy/ambiguous input
    ALEATORIC_OUTCOME = "aleatoric_outcome"     # Inherently random outcome
    
    # Epistemic (reducible, lack of knowledge)
    EPISTEMIC_MODEL = "epistemic_model"         # Model limitations
    EPISTEMIC_KNOWLEDGE = "epistemic_knowledge" # Missing knowledge
    EPISTEMIC_TRAINING = "epistemic_training"   # Training data gaps
    
    # Ontological (nature of reality)
    ONTOLOGICAL = "ontological"                 # Fundamental unknowability
    
    # Practical
    TEMPORAL = "temporal"                       # May change over time
    CONTEXTUAL = "contextual"                   # Depends on context
    DEFINITIONAL = "definitional"               # Ambiguous definitions


@dataclass
class UncertaintyProfile:
    """Complete uncertainty profile for a response."""
    # Total uncertainty (0-1)
    total_uncertainty: float
    
    # Breakdown by type
    aleatoric: float = 0.0      # Can't be reduced
    epistemic: float = 0.0      # Could be reduced with more info
    temporal: float = 0.0       # Time-sensitive
    contextual: float = 0.0     # Context-dependent
    
    # Specific sources
    sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Actionable insights
    can_reduce: bool = False
    reduction_strategies: List[str] = field(default_factory=list)
    
    # Risk assessment
    impact_if_wrong: str = "low"  # low, medium, high, critical
    reversibility: str = "reversible"  # reversible, partially, irreversible
    
    # Recommendations
    should_defer: bool = False     # Defer to human/expert
    should_qualify: bool = False   # Add qualifications to answer
    should_verify: bool = False    # Verify before responding
    qualifications: List[str] = field(default_factory=list)


class UncertaintyQuantifier:
    """
    Quantifies and categorizes uncertainty in ANM's responses.
    
    Key distinctions:
    - Aleatoric: Inherent randomness, can't be reduced
    - Epistemic: Lack of knowledge, can be reduced
    - Temporal: Information may be outdated
    - Contextual: Depends on unspecified context
    
    Usage:
        quantifier = UncertaintyQuantifier()
        
        profile = quantifier.analyze(
            query="Will it rain tomorrow?",
            response="There's a 60% chance of rain.",
            domains=["weather"],
        )
        
        print(f"Total uncertainty: {profile.total_uncertainty:.2f}")
        print(f"Aleatoric: {profile.aleatoric:.2f}")
        print(f"Epistemic: {profile.epistemic:.2f}")
    """
    
    # Indicators of different uncertainty types
    ALEATORIC_INDICATORS = {
        "random", "chance", "probability", "likely", "odds",
        "unpredictable", "stochastic", "variable", "fluctuate",
        "quantum", "chaos", "turbulent", "weather",
    }
    
    EPISTEMIC_INDICATORS = {
        "unknown", "unclear", "uncertain", "don't know", "not sure",
        "limited data", "insufficient", "speculation", "estimate",
        "assumption", "hypothesis", "theory", "believe",
    }
    
    TEMPORAL_INDICATORS = {
        "current", "now", "today", "recent", "latest",
        "as of", "at the time", "may change", "subject to",
        "temporary", "evolving", "developing",
    }
    
    CONTEXTUAL_INDICATORS = {
        "depends", "context", "situation", "case by case",
        "varies", "it depends", "depending on", "in some cases",
        "typically", "usually", "generally", "often",
    }
    
    # High-stakes domains where uncertainty matters more
    HIGH_STAKES_DOMAINS = {
        "medical", "health", "legal", "financial", "safety",
        "security", "critical", "life-or-death",
    }
    
    def __init__(self):
        self._uncertainty_log: List[UncertaintyProfile] = []
    
    def analyze(
        self,
        query: str,
        response: str,
        domains: List[str],
        confidence_score: float = 0.5,
        reasoning_chain_length: int = 0,
        sources_available: int = 0,
    ) -> UncertaintyProfile:
        """
        Analyze uncertainty in a query-response pair.
        
        Args:
            query: The user's query
            response: ANM's response
            domains: Active domains
            confidence_score: Initial confidence (0-1)
            reasoning_chain_length: Number of reasoning steps
            sources_available: Number of sources consulted
        
        Returns:
            Complete UncertaintyProfile
        """
        sources = []
        reduction_strategies = []
        qualifications = []
        
        combined_text = (query + " " + response).lower()
        
        # 1. Analyze aleatoric uncertainty
        aleatoric = self._assess_aleatoric(combined_text, query, domains)
        if aleatoric > 0.3:
            sources.append({
                "type": UncertaintyType.ALEATORIC_OUTCOME.value,
                "magnitude": aleatoric,
                "reason": "Inherent randomness in the phenomenon",
            })
            qualifications.append("This involves inherent randomness")
        
        # 2. Analyze epistemic uncertainty
        epistemic = self._assess_epistemic(
            combined_text, confidence_score, sources_available
        )
        if epistemic > 0.3:
            sources.append({
                "type": UncertaintyType.EPISTEMIC_KNOWLEDGE.value,
                "magnitude": epistemic,
                "reason": "Limited knowledge or training data",
            })
            reduction_strategies.append("Consult authoritative sources")
            reduction_strategies.append("Gather more specific information")
        
        # 3. Analyze temporal uncertainty
        temporal = self._assess_temporal(combined_text, domains)
        if temporal > 0.2:
            sources.append({
                "type": UncertaintyType.TEMPORAL.value,
                "magnitude": temporal,
                "reason": "Information may be time-sensitive",
            })
            qualifications.append("This may have changed since my last update")
            reduction_strategies.append("Verify current information")
        
        # 4. Analyze contextual uncertainty
        contextual = self._assess_contextual(combined_text, query)
        if contextual > 0.2:
            sources.append({
                "type": UncertaintyType.CONTEXTUAL.value,
                "magnitude": contextual,
                "reason": "Answer depends on specific context",
            })
            qualifications.append("This depends on specific circumstances")
            reduction_strategies.append("Ask for more context")
        
        # Calculate total uncertainty
        # Use quadratic mean for combination
        total = (
            aleatoric**2 + epistemic**2 + temporal**2 + contextual**2
        ) ** 0.5 / 2  # Normalize
        total = min(1.0, total + (1 - confidence_score) * 0.3)
        
        # Determine if uncertainty can be reduced
        can_reduce = epistemic > 0.2 or temporal > 0.2
        
        # Assess impact
        is_high_stakes = any(d in self.HIGH_STAKES_DOMAINS for d in domains)
        impact = self._assess_impact(query, domains, is_high_stakes)
        
        # Determine recommendations
        should_defer = total > 0.7 and is_high_stakes
        should_qualify = total > 0.4
        should_verify = epistemic > 0.4 or temporal > 0.3
        
        profile = UncertaintyProfile(
            total_uncertainty=total,
            aleatoric=aleatoric,
            epistemic=epistemic,
            temporal=temporal,
            contextual=contextual,
            sources=sources,
            can_reduce=can_reduce,
            reduction_strategies=reduction_strategies,
            impact_if_wrong=impact,
            reversibility=self._assess_reversibility(query, domains),
            should_defer=should_defer,
            should_qualify=should_qualify,
            should_verify=should_verify,
            qualifications=qualifications,
        )
        
        self._uncertainty_log.append(profile)
        return profile
    
    def _assess_aleatoric(
        self,
        text: str,
        query: str,
        domains: List[str],
    ) -> float:
        """Assess inherent randomness uncertainty."""
        score = 0.0
        
        # Check for aleatoric indicators
        indicator_count = sum(1 for ind in self.ALEATORIC_INDICATORS if ind in text)
        score += min(0.4, indicator_count * 0.1)
        
        # Certain domains have inherent randomness
        random_domains = {"weather", "stocks", "gambling", "quantum"}
        if any(d in random_domains for d in domains):
            score += 0.3
        
        # Questions about future have aleatoric component
        future_indicators = ["will", "tomorrow", "next", "future", "predict"]
        if any(ind in query.lower() for ind in future_indicators):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_epistemic(
        self,
        text: str,
        confidence: float,
        sources: int,
    ) -> float:
        """Assess knowledge-gap uncertainty."""
        score = 0.0
        
        # Check for epistemic indicators
        indicator_count = sum(1 for ind in self.EPISTEMIC_INDICATORS if ind in text)
        score += min(0.4, indicator_count * 0.1)
        
        # Low confidence suggests epistemic uncertainty
        if confidence < 0.5:
            score += 0.3 * (1 - confidence * 2)
        
        # Few sources increases epistemic uncertainty
        if sources == 0:
            score += 0.2
        elif sources < 3:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_temporal(self, text: str, domains: List[str]) -> float:
        """Assess time-sensitive uncertainty."""
        score = 0.0
        
        # Check for temporal indicators
        indicator_count = sum(1 for ind in self.TEMPORAL_INDICATORS if ind in text)
        score += min(0.4, indicator_count * 0.1)
        
        # Certain domains are more time-sensitive
        time_sensitive = {"news", "current_events", "stocks", "weather", "politics", "technology"}
        if any(d in time_sensitive for d in domains):
            score += 0.3
        
        return min(1.0, score)
    
    def _assess_contextual(self, text: str, query: str) -> float:
        """Assess context-dependent uncertainty."""
        score = 0.0
        
        # Check for contextual indicators
        indicator_count = sum(1 for ind in self.CONTEXTUAL_INDICATORS if ind in text)
        score += min(0.5, indicator_count * 0.1)
        
        # Vague queries increase contextual uncertainty
        vague_markers = ["best", "should", "good", "right", "correct"]
        if any(marker in query.lower() for marker in vague_markers):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_impact(
        self,
        query: str,
        domains: List[str],
        is_high_stakes: bool,
    ) -> str:
        """Assess impact if answer is wrong."""
        if is_high_stakes:
            return "critical"
        
        critical_keywords = ["emergency", "danger", "urgent", "life", "death", "safety"]
        if any(kw in query.lower() for kw in critical_keywords):
            return "critical"
        
        high_keywords = ["important", "significant", "major", "decision"]
        if any(kw in query.lower() for kw in high_keywords):
            return "high"
        
        return "low"
    
    def _assess_reversibility(self, query: str, domains: List[str]) -> str:
        """Assess if wrong answer consequences are reversible."""
        irreversible = ["legal", "medical", "safety", "surgery", "contract"]
        if any(d in irreversible for d in domains):
            return "irreversible"
        
        partial = ["financial", "career", "relationship"]
        if any(d in partial for d in domains):
            return "partially"
        
        return "reversible"
    
    def get_uncertainty_stats(self) -> Dict[str, Any]:
        """Get aggregate uncertainty statistics."""
        if not self._uncertainty_log:
            return {"samples": 0}
        
        return {
            "samples": len(self._uncertainty_log),
            "avg_total": sum(p.total_uncertainty for p in self._uncertainty_log) / len(self._uncertainty_log),
            "avg_aleatoric": sum(p.aleatoric for p in self._uncertainty_log) / len(self._uncertainty_log),
            "avg_epistemic": sum(p.epistemic for p in self._uncertainty_log) / len(self._uncertainty_log),
            "defer_rate": sum(1 for p in self._uncertainty_log if p.should_defer) / len(self._uncertainty_log),
        }
