# ============================================================
# ANM V0-OpenSource — STRATEGY EVALUATOR
#  Evaluates and adapts cognitive strategies
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


class StrategyType(Enum):
    """Types of cognitive strategies."""
    # Decomposition
    DECOMPOSE = "decompose"          # Break into sub-problems
    SIMPLIFY = "simplify"            # Simplify the problem
    
    # Approach
    DIRECT = "direct"                # Direct answer
    STEP_BY_STEP = "step_by_step"    # Step-by-step reasoning
    ANALOGY = "analogy"              # Use analogies
    EXAMPLE = "example"              # Use examples
    
    # Verification
    VERIFY = "verify"                # Verify answer
    CROSS_CHECK = "cross_check"      # Cross-check with other domains
    
    # Uncertainty handling
    HEDGE = "hedge"                  # Add uncertainty qualifiers
    DEFER = "defer"                  # Defer to expert/user
    
    # Information
    RESEARCH = "research"            # Seek more information
    RECALL = "recall"                # Use memory
    
    # Meta
    REFLECT = "reflect"              # Reflect on reasoning
    REVISE = "revise"                # Revise approach


@dataclass
class StrategyRecommendation:
    """Recommended cognitive strategy."""
    primary_strategy: StrategyType
    secondary_strategies: List[StrategyType] = field(default_factory=list)
    
    # Confidence in recommendation
    confidence: float = 0.7
    
    # Reasoning
    rationale: str = ""
    
    # Conditions
    when_to_use: List[str] = field(default_factory=list)
    when_not_to_use: List[str] = field(default_factory=list)
    
    # Predicted effectiveness
    predicted_effectiveness: float = 0.7
    
    # Alternative if primary fails
    fallback: Optional[StrategyType] = None


class StrategyEvaluator:
    """
    Evaluates and recommends cognitive strategies.
    
    Functions:
    1. Recommend strategy based on query characteristics
    2. Evaluate strategy effectiveness
    3. Adapt strategies based on outcomes
    4. Track strategy success rates
    
    Usage:
        evaluator = StrategyEvaluator()
        
        rec = evaluator.recommend(
            query="Explain the proof of Fermat's Last Theorem",
            domain="math",
            complexity=0.9,
            uncertainty=0.3,
        )
        
        print(f"Use {rec.primary_strategy.name}")
        
        # After answer
        evaluator.record_outcome(
            strategy=rec.primary_strategy,
            domain="math",
            success=True,
        )
    """
    
    # Strategy effectiveness history: strategy -> (successes, total)
    _strategy_stats: Dict[str, Tuple[int, int]] = {}
    
    # Domain-strategy affinity
    DOMAIN_STRATEGY_AFFINITY = {
        "math": [StrategyType.STEP_BY_STEP, StrategyType.VERIFY],
        "physics": [StrategyType.STEP_BY_STEP, StrategyType.ANALOGY],
        "code": [StrategyType.DECOMPOSE, StrategyType.EXAMPLE],
        "creative": [StrategyType.ANALOGY, StrategyType.EXAMPLE],
        "research": [StrategyType.RESEARCH, StrategyType.CROSS_CHECK],
        "facts": [StrategyType.DIRECT, StrategyType.VERIFY],
        "philosophy": [StrategyType.STEP_BY_STEP, StrategyType.REFLECT],
    }
    
    def __init__(self):
        self._outcome_history: List[Dict[str, Any]] = []
    
    def recommend(
        self,
        query: str,
        domain: str,
        complexity: float = 0.5,
        uncertainty: float = 0.5,
        cognitive_load: float = 0.5,
    ) -> StrategyRecommendation:
        """
        Recommend a cognitive strategy.
        
        Args:
            query: The user's query
            domain: Primary domain
            complexity: Query complexity (0-1)
            uncertainty: Uncertainty level (0-1)
            cognitive_load: Current cognitive load (0-1)
        
        Returns:
            StrategyRecommendation
        """
        strategies = []
        rationale_parts = []
        
        # 1. High complexity → decompose
        if complexity > 0.7:
            strategies.append((StrategyType.DECOMPOSE, 0.9))
            rationale_parts.append("Complex query benefits from decomposition")
        
        # 2. High uncertainty → hedge or defer
        if uncertainty > 0.7:
            strategies.append((StrategyType.HEDGE, 0.8))
            if uncertainty > 0.85:
                strategies.append((StrategyType.DEFER, 0.7))
            rationale_parts.append("High uncertainty requires acknowledgment")
        
        # 3. High cognitive load → simplify
        if cognitive_load > 0.7:
            strategies.append((StrategyType.SIMPLIFY, 0.8))
            rationale_parts.append("High cognitive load suggests simplification")
        
        # 4. Domain-specific strategies
        domain_strategies = self.DOMAIN_STRATEGY_AFFINITY.get(domain.lower(), [])
        for strat in domain_strategies:
            strategies.append((strat, 0.7))
        if domain_strategies:
            rationale_parts.append(f"Domain {domain} works well with {domain_strategies[0].name}")
        
        # 5. Historical performance
        for strat_type in StrategyType:
            success_rate = self._get_success_rate(strat_type, domain)
            if success_rate > 0.7:
                strategies.append((strat_type, success_rate))
        
        # Select best strategy
        if not strategies:
            strategies.append((StrategyType.STEP_BY_STEP, 0.6))
        
        # Sort by score
        strategies.sort(key=lambda x: x[1], reverse=True)
        
        primary = strategies[0][0]
        secondary = [s[0] for s in strategies[1:4] if s[0] != primary]
        
        # Determine fallback
        fallback = None
        if primary == StrategyType.DIRECT:
            fallback = StrategyType.STEP_BY_STEP
        elif primary == StrategyType.STEP_BY_STEP:
            fallback = StrategyType.DECOMPOSE
        
        return StrategyRecommendation(
            primary_strategy=primary,
            secondary_strategies=secondary,
            confidence=strategies[0][1],
            rationale=" | ".join(rationale_parts) if rationale_parts else "Default strategy",
            when_to_use=self._get_use_conditions(primary),
            when_not_to_use=self._get_avoid_conditions(primary),
            predicted_effectiveness=self._get_success_rate(primary, domain) or 0.6,
            fallback=fallback,
        )
    
    def record_outcome(
        self,
        strategy: StrategyType,
        domain: str,
        success: bool,
        notes: str = "",
    ) -> None:
        """Record the outcome of a strategy."""
        key = f"{strategy.value}:{domain.lower()}"
        
        current = self._strategy_stats.get(key, (0, 0))
        new_successes = current[0] + (1 if success else 0)
        new_total = current[1] + 1
        self._strategy_stats[key] = (new_successes, new_total)
        
        self._outcome_history.append({
            "strategy": strategy.value,
            "domain": domain,
            "success": success,
            "notes": notes,
        })
    
    def _get_success_rate(
        self,
        strategy: StrategyType,
        domain: str,
    ) -> float:
        """Get success rate for strategy in domain."""
        key = f"{strategy.value}:{domain.lower()}"
        stats = self._strategy_stats.get(key)
        
        if not stats or stats[1] < 3:  # Need at least 3 samples
            return 0.0
        
        return stats[0] / stats[1]
    
    def _get_use_conditions(self, strategy: StrategyType) -> List[str]:
        """Get conditions when strategy should be used."""
        conditions = {
            StrategyType.DECOMPOSE: ["Complex multi-part questions", "Large scope problems"],
            StrategyType.SIMPLIFY: ["High cognitive load", "Overwhelmingly complex"],
            StrategyType.DIRECT: ["Simple factual questions", "Low complexity"],
            StrategyType.STEP_BY_STEP: ["Logical reasoning needed", "Math/physics problems"],
            StrategyType.ANALOGY: ["Abstract concepts", "Teaching/explaining"],
            StrategyType.EXAMPLE: ["Concepts need illustration", "Learning context"],
            StrategyType.VERIFY: ["High stakes answers", "Math calculations"],
            StrategyType.CROSS_CHECK: ["Multiple domains involved", "Conflicting info"],
            StrategyType.HEDGE: ["High uncertainty", "Speculative content"],
            StrategyType.DEFER: ["Outside expertise", "Professional advice needed"],
            StrategyType.RESEARCH: ["Need current information", "Fact-checking"],
            StrategyType.RECALL: ["Past context relevant", "Personal history"],
            StrategyType.REFLECT: ["Complex reasoning", "After initial answer"],
            StrategyType.REVISE: ["Initial approach failed", "New information"],
        }
        return conditions.get(strategy, [])
    
    def _get_avoid_conditions(self, strategy: StrategyType) -> List[str]:
        """Get conditions when strategy should be avoided."""
        avoid = {
            StrategyType.DECOMPOSE: ["Simple questions", "Time-critical"],
            StrategyType.DIRECT: ["Complex reasoning needed", "High uncertainty"],
            StrategyType.HEDGE: ["Clear factual answers", "User needs certainty"],
            StrategyType.DEFER: ["Within clear expertise", "Simple questions"],
        }
        return avoid.get(strategy, [])
    
    def get_strategy_report(self) -> Dict[str, Any]:
        """Get report on strategy effectiveness."""
        if not self._strategy_stats:
            return {"total_recorded": 0}
        
        report = {
            "total_recorded": sum(s[1] for s in self._strategy_stats.values()),
            "strategies": {},
        }
        
        for key, (successes, total) in self._strategy_stats.items():
            strategy, domain = key.split(":")
            rate = successes / total if total > 0 else 0
            
            if strategy not in report["strategies"]:
                report["strategies"][strategy] = {"domains": {}}
            
            report["strategies"][strategy]["domains"][domain] = {
                "success_rate": rate,
                "samples": total,
            }
        
        return report
    
    def adapt(self, feedback: str, strategy: StrategyType, domain: str) -> None:
        """Adapt strategy weights based on feedback."""
        # This could be expanded to learn from feedback
        positive_indicators = ["good", "correct", "helpful", "accurate"]
        negative_indicators = ["wrong", "incorrect", "unhelpful", "bad"]
        
        feedback_lower = feedback.lower()
        
        is_positive = any(ind in feedback_lower for ind in positive_indicators)
        is_negative = any(ind in feedback_lower for ind in negative_indicators)
        
        if is_positive:
            self.record_outcome(strategy, domain, success=True, notes=feedback[:50])
        elif is_negative:
            self.record_outcome(strategy, domain, success=False, notes=feedback[:50])
