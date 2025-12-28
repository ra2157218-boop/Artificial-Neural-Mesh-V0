# ============================================================
# ANM V0-OpenSource — CONFIDENCE CALIBRATOR
#  Calibrated confidence estimation with multiple signals
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import re


class ConfidenceLevel(Enum):
    """Discrete confidence levels."""
    VERY_LOW = 0.1
    LOW = 0.3
    MODERATE = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class CalibrationResult:
    """Calibrated confidence assessment."""
    # Primary score (0-1)
    score: float
    level: ConfidenceLevel
    
    # Component scores
    linguistic_confidence: float       # From language cues
    consistency_confidence: float      # From internal consistency
    domain_confidence: float           # From domain expertise
    source_confidence: float           # From information sources
    
    # Calibration adjustments
    overconfidence_penalty: float = 0.0
    underconfidence_boost: float = 0.0
    
    # Explanations
    factors_raising: List[str] = field(default_factory=list)
    factors_lowering: List[str] = field(default_factory=list)
    
    # Metacognitive notes
    should_express_uncertainty: bool = False
    suggested_hedging: Optional[str] = None
    needs_verification: bool = False


class ConfidenceCalibrator:
    """
    Calibrated confidence estimation system.
    
    Unlike raw model confidence, this system:
    1. Uses multiple signals (linguistic, consistency, domain, source)
    2. Applies calibration to avoid over/under-confidence
    3. Provides actionable recommendations
    4. Tracks calibration history for improvement
    
    Usage:
        calibrator = ConfidenceCalibrator()
        
        result = calibrator.assess(
            response="The answer is definitely 42.",
            query="What is the meaning of life?",
            domain="philosophy",
            reasoning_steps=5,
        )
        
        print(f"Confidence: {result.score:.2f}")
        print(f"Should hedge: {result.should_express_uncertainty}")
    """
    
    # Linguistic markers of confidence
    HIGH_CONFIDENCE_MARKERS = [
        "definitely", "certainly", "absolutely", "clearly", "obviously",
        "undoubtedly", "without doubt", "proven", "established fact",
        "it is known", "always", "never", "must be", "guaranteed",
    ]
    
    LOW_CONFIDENCE_MARKERS = [
        "maybe", "perhaps", "possibly", "might", "could be",
        "uncertain", "unsure", "I think", "I believe", "seems like",
        "appears to", "likely", "probably", "not sure", "hard to say",
        "it depends", "in some cases", "generally", "typically",
    ]
    
    # Domain expertise levels (can be updated from learning)
    DEFAULT_DOMAIN_CONFIDENCE = {
        "math": 0.8,
        "physics": 0.75,
        "chemistry": 0.7,
        "biology": 0.7,
        "code": 0.8,
        "general": 0.6,
        "facts": 0.5,      # Facts can be outdated
        "research": 0.5,   # Research depends on sources
        "creative": 0.7,
        "philosophy": 0.5,
        "speculation": 0.3,
    }
    
    # Hedging suggestions
    HEDGING_PHRASES = {
        0.9: None,  # Very high - no hedging needed
        0.7: "Based on my analysis, ",
        0.5: "I believe that ",
        0.3: "I'm not entirely certain, but ",
        0.1: "This is speculative, but ",
    }
    
    def __init__(self):
        self._calibration_history: List[Tuple[float, float]] = []  # (predicted, actual)
        self._domain_confidence = self.DEFAULT_DOMAIN_CONFIDENCE.copy()
    
    def assess(
        self,
        response: str,
        query: str,
        domain: str = "general",
        reasoning_steps: int = 0,
        sources_cited: int = 0,
        internal_consistency: float = 1.0,
        specialist_agreement: float = 1.0,
    ) -> CalibrationResult:
        """
        Assess confidence with calibration.
        
        Args:
            response: The generated response
            query: Original query
            domain: Primary domain
            reasoning_steps: Number of reasoning steps taken
            sources_cited: Number of sources cited
            internal_consistency: 0-1 consistency score
            specialist_agreement: 0-1 agreement between specialists
        
        Returns:
            CalibrationResult with calibrated confidence
        """
        factors_raising = []
        factors_lowering = []
        
        # 1. Linguistic confidence (from response text)
        linguistic_conf = self._assess_linguistic_confidence(response)
        if linguistic_conf > 0.7:
            factors_raising.append("Uses confident language")
        elif linguistic_conf < 0.4:
            factors_lowering.append("Uses hedging language")
        
        # 2. Domain confidence
        domain_conf = self._domain_confidence.get(domain.lower(), 0.5)
        if domain_conf > 0.7:
            factors_raising.append(f"Strong in {domain} domain")
        elif domain_conf < 0.4:
            factors_lowering.append(f"Weak in {domain} domain")
        
        # 3. Consistency confidence
        consistency_conf = internal_consistency * specialist_agreement
        if consistency_conf > 0.8:
            factors_raising.append("High internal consistency")
        elif consistency_conf < 0.5:
            factors_lowering.append("Low consistency detected")
        
        # 4. Source confidence
        source_conf = self._assess_source_confidence(sources_cited, reasoning_steps)
        if source_conf > 0.7:
            factors_raising.append("Well-supported with sources/reasoning")
        elif source_conf < 0.4:
            factors_lowering.append("Limited supporting evidence")
        
        # 5. Query complexity adjustment
        query_complexity = self._estimate_query_complexity(query)
        if query_complexity > 0.7:
            factors_lowering.append("Complex query increases uncertainty")
        
        # Combine scores with weights
        raw_score = (
            0.20 * linguistic_conf +
            0.25 * domain_conf +
            0.30 * consistency_conf +
            0.25 * source_conf
        )
        
        # Apply complexity penalty
        raw_score *= (1.0 - 0.2 * query_complexity)
        
        # Calibration adjustments
        overconf_penalty, underconf_boost = self._calibrate(raw_score, linguistic_conf)
        
        calibrated_score = raw_score - overconf_penalty + underconf_boost
        calibrated_score = max(0.05, min(0.95, calibrated_score))  # Clamp
        
        # Determine level
        level = self._score_to_level(calibrated_score)
        
        # Generate recommendations
        should_hedge = calibrated_score < 0.7
        suggested_hedging = self._get_hedging(calibrated_score)
        needs_verification = calibrated_score < 0.5 or domain in ["facts", "research", "speculation"]
        
        return CalibrationResult(
            score=calibrated_score,
            level=level,
            linguistic_confidence=linguistic_conf,
            consistency_confidence=consistency_conf,
            domain_confidence=domain_conf,
            source_confidence=source_conf,
            overconfidence_penalty=overconf_penalty,
            underconfidence_boost=underconf_boost,
            factors_raising=factors_raising,
            factors_lowering=factors_lowering,
            should_express_uncertainty=should_hedge,
            suggested_hedging=suggested_hedging,
            needs_verification=needs_verification,
        )
    
    def _assess_linguistic_confidence(self, text: str) -> float:
        """Assess confidence from linguistic cues."""
        text_lower = text.lower()
        
        high_count = sum(1 for marker in self.HIGH_CONFIDENCE_MARKERS if marker in text_lower)
        low_count = sum(1 for marker in self.LOW_CONFIDENCE_MARKERS if marker in text_lower)
        
        # Normalize
        total = high_count + low_count + 1  # +1 to avoid division by zero
        
        # Base confidence
        if high_count > low_count:
            return 0.5 + 0.4 * (high_count / total)
        elif low_count > high_count:
            return 0.5 - 0.3 * (low_count / total)
        else:
            return 0.5
    
    def _assess_source_confidence(self, sources_cited: int, reasoning_steps: int) -> float:
        """Assess confidence from sources and reasoning."""
        # Sources contribute up to 0.5
        source_score = min(0.5, sources_cited * 0.1)
        
        # Reasoning steps contribute up to 0.5 (but diminishing returns)
        reasoning_score = min(0.5, 0.1 * math.log1p(reasoning_steps))
        
        return source_score + reasoning_score + 0.3  # Base of 0.3
    
    def _estimate_query_complexity(self, query: str) -> float:
        """Estimate query complexity (0-1)."""
        complexity = 0.0
        
        # Length factor
        if len(query) > 200:
            complexity += 0.2
        
        # Question markers
        if query.count("?") > 1:
            complexity += 0.1
        
        # Multi-part indicators
        multi_indicators = ["and", "also", "additionally", "furthermore", "as well as"]
        for ind in multi_indicators:
            if ind in query.lower():
                complexity += 0.1
        
        # Speculative indicators
        speculative = ["what if", "hypothetically", "imagine", "suppose", "could"]
        for spec in speculative:
            if spec in query.lower():
                complexity += 0.15
        
        # Abstract concepts
        abstract = ["meaning", "purpose", "consciousness", "existence", "infinity"]
        for ab in abstract:
            if ab in query.lower():
                complexity += 0.2
        
        return min(1.0, complexity)
    
    def _calibrate(self, raw_score: float, linguistic_conf: float) -> Tuple[float, float]:
        """
        Apply calibration based on historical data.
        
        Returns:
            (overconfidence_penalty, underconfidence_boost)
        """
        overconf_penalty = 0.0
        underconf_boost = 0.0
        
        # If linguistic confidence is much higher than domain support,
        # apply overconfidence penalty
        if linguistic_conf > raw_score + 0.2:
            overconf_penalty = 0.15 * (linguistic_conf - raw_score)
        
        # Use historical calibration if available
        if len(self._calibration_history) >= 10:
            avg_predicted = sum(p for p, _ in self._calibration_history[-10:]) / 10
            avg_actual = sum(a for _, a in self._calibration_history[-10:]) / 10
            
            if avg_predicted > avg_actual + 0.1:
                # Historically overconfident
                overconf_penalty += 0.1
            elif avg_actual > avg_predicted + 0.1:
                # Historically underconfident
                underconf_boost += 0.1
        
        return overconf_penalty, underconf_boost
    
    def record_outcome(self, predicted: float, actual: float) -> None:
        """Record actual outcome for calibration learning."""
        self._calibration_history.append((predicted, actual))
        
        # Keep last 100 entries
        if len(self._calibration_history) > 100:
            self._calibration_history = self._calibration_history[-100:]
    
    def update_domain_confidence(self, domain: str, confidence: float) -> None:
        """Update domain confidence based on performance."""
        current = self._domain_confidence.get(domain.lower(), 0.5)
        # Exponential moving average
        self._domain_confidence[domain.lower()] = 0.8 * current + 0.2 * confidence
    
    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Convert score to discrete level."""
        if score >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.6:
            return ConfidenceLevel.HIGH
        elif score >= 0.4:
            return ConfidenceLevel.MODERATE
        elif score >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _get_hedging(self, score: float) -> Optional[str]:
        """Get appropriate hedging phrase."""
        for threshold, phrase in sorted(self.HEDGING_PHRASES.items(), reverse=True):
            if score >= threshold:
                return phrase
        return self.HEDGING_PHRASES[0.1]
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get calibration statistics."""
        if not self._calibration_history:
            return {"samples": 0, "calibration": "unknown"}
        
        predictions = [p for p, _ in self._calibration_history]
        actuals = [a for _, a in self._calibration_history]
        
        avg_error = sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)
        
        return {
            "samples": len(self._calibration_history),
            "avg_prediction": sum(predictions) / len(predictions),
            "avg_actual": sum(actuals) / len(actuals),
            "avg_error": avg_error,
            "calibration": "good" if avg_error < 0.15 else "needs improvement",
        }
