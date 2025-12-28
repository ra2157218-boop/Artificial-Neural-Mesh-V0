# ============================================================
# ANM V0-OpenSource — UNIFIED METACOGNITION SYSTEM
#  "Thinking About Thinking" - Complete Self-Awareness
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from anm.metacognition.monitor import MetaCognitiveMonitor, CognitiveState, ProcessingPhase
from anm.metacognition.confidence import ConfidenceCalibrator, CalibrationResult, ConfidenceLevel
from anm.metacognition.uncertainty import UncertaintyQuantifier, UncertaintyProfile
from anm.metacognition.cognitive_load import CognitiveLoadTracker, LoadFactors, LoadLevel
from anm.metacognition.reasoning_checker import ReasoningQualityChecker, ReasoningQuality
from anm.metacognition.knowledge_boundary import KnowledgeBoundaryDetector, BoundaryResult, KnowledgeStatus
from anm.metacognition.bias_detector import BiasDetector, BiasAlert
from anm.metacognition.journal import MetaCognitiveJournal, InsightType
from anm.metacognition.strategy_evaluator import StrategyEvaluator, StrategyRecommendation


@dataclass
class MetaCognitiveAssessment:
    """Complete pre-processing assessment."""
    # Summary
    overall_readiness: float         # 0-1, how ready we are to answer
    recommended_approach: str
    
    # Components
    cognitive_load: LoadFactors
    knowledge_boundary: BoundaryResult
    strategy: StrategyRecommendation
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    # Recommendations
    should_proceed: bool = True
    should_simplify: bool = False
    should_decompose: bool = False
    should_defer: bool = False
    
    # Pre-emptive hedging
    uncertainty_preface: Optional[str] = None


@dataclass
class MetaCognitiveReflection:
    """Complete post-processing reflection."""
    # Summary
    overall_quality: float           # 0-1, quality of the response
    calibration_accuracy: str        # How well-calibrated was confidence
    
    # Components
    confidence: CalibrationResult
    uncertainty: UncertaintyProfile
    reasoning_quality: ReasoningQuality
    bias_alerts: List[BiasAlert]
    
    # Insights
    lessons_learned: List[str] = field(default_factory=list)
    
    # Future improvements
    improvements_for_next_time: List[str] = field(default_factory=list)
    
    # Should revise?
    needs_revision: bool = False
    revision_suggestions: List[str] = field(default_factory=list)


class MetaCognition:
    """
    Unified MetaCognition System for ANM.
    
    Provides comprehensive self-awareness through:
    
    1. PRE-ASSESSMENT (before processing)
       - Cognitive load estimation
       - Knowledge boundary detection
       - Strategy recommendation
       - Early warning detection
    
    2. MONITORING (during processing)
       - Real-time state tracking
       - Phase transitions
       - Anomaly detection
    
    3. REFLECTION (after processing)
       - Confidence calibration
       - Uncertainty quantification
       - Reasoning quality check
       - Bias detection
       - Learning extraction
    
    Usage:
        metacog = MetaCognition()
        
        # Before answering
        assessment = metacog.pre_assess(query, domain)
        if not assessment.should_proceed:
            return "I should defer this question"
        
        # During processing
        metacog.monitor.enter_phase(ProcessingPhase.REASONING)
        metacog.monitor.log_step({"action": "applying formula"})
        
        # After answering
        reflection = metacog.reflect(query, reasoning, answer, domain)
        if reflection.needs_revision:
            # Revise answer
    """
    
    def __init__(self, journal_path: str = ".anm_cache/metacog_journal.json"):
        # Initialize all components
        self.monitor = MetaCognitiveMonitor()
        self.confidence = ConfidenceCalibrator()
        self.uncertainty = UncertaintyQuantifier()
        self.cognitive_load = CognitiveLoadTracker()
        self.reasoning = ReasoningQualityChecker()
        self.knowledge = KnowledgeBoundaryDetector()
        self.bias = BiasDetector()
        self.journal = MetaCognitiveJournal(journal_path)
        self.strategy = StrategyEvaluator()
        
        # Session state
        self._current_query: Optional[str] = None
        self._current_domain: Optional[str] = None
        self._current_assessment: Optional[MetaCognitiveAssessment] = None
    
    # ============================================================
    #  PRE-ASSESSMENT
    # ============================================================
    
    def pre_assess(
        self,
        query: str,
        domain: str,
        context_size: int = 0,
    ) -> MetaCognitiveAssessment:
        """
        Assess query before processing.
        
        This is the "think before you act" phase.
        
        Args:
            query: User's query
            domain: Primary domain
            context_size: Size of context in tokens
        
        Returns:
            MetaCognitiveAssessment with recommendations
        """
        warnings = []
        
        # Start monitoring session
        self.monitor.start_session(query)
        self.monitor.enter_phase(ProcessingPhase.PARSING)
        
        # 1. Assess cognitive load
        load = self.cognitive_load.estimate(
            query=query,
            domains=[domain],
            context_tokens=context_size,
        )
        
        if load.level in [LoadLevel.HIGH, LoadLevel.EXTREME]:
            warnings.append(f"High cognitive load detected: {load.level.name}")
        
        # 2. Check knowledge boundaries
        self.monitor.enter_phase(ProcessingPhase.ROUTING)
        boundary = self.knowledge.analyze(query, domain)
        
        if boundary.status in [KnowledgeStatus.UNKNOWN, KnowledgeStatus.UNKNOWABLE]:
            warnings.append(f"Knowledge boundary alert: {boundary.status.name}")
        
        # 3. Get strategy recommendation
        strategy = self.strategy.recommend(
            query=query,
            domain=domain,
            complexity=load.total_load,
            uncertainty=0.5 if boundary.status != KnowledgeStatus.KNOWN_WELL else 0.2,
            cognitive_load=load.total_load,
        )
        
        # 4. Determine recommendations
        should_proceed = boundary.status != KnowledgeStatus.UNKNOWABLE
        should_simplify = load.should_simplify
        should_decompose = load.should_decompose
        should_defer = boundary.should_defer_to_expert
        
        # 5. Generate uncertainty preface if needed
        uncertainty_preface = None
        if boundary.status == KnowledgeStatus.KNOWN_OUTDATED:
            uncertainty_preface = f"Note: My information may be outdated. "
        elif boundary.status == KnowledgeStatus.BOUNDARY_EDGE:
            uncertainty_preface = "I have limited knowledge on this specific topic. "
        
        # 6. Calculate overall readiness
        readiness = 1.0
        readiness -= load.total_load * 0.3
        if boundary.status != KnowledgeStatus.KNOWN_WELL:
            readiness -= 0.2
        if len(warnings) > 0:
            readiness -= len(warnings) * 0.1
        readiness = max(0.1, min(1.0, readiness))
        
        # Generate approach description
        approach = f"{strategy.primary_strategy.name}"
        if strategy.secondary_strategies:
            approach += f" with {strategy.secondary_strategies[0].name}"
        
        assessment = MetaCognitiveAssessment(
            overall_readiness=readiness,
            recommended_approach=approach,
            cognitive_load=load,
            knowledge_boundary=boundary,
            strategy=strategy,
            warnings=warnings,
            should_proceed=should_proceed,
            should_simplify=should_simplify,
            should_decompose=should_decompose,
            should_defer=should_defer,
            uncertainty_preface=uncertainty_preface,
        )
        
        # Store for later reflection
        self._current_query = query
        self._current_domain = domain
        self._current_assessment = assessment
        
        return assessment
    
    # ============================================================
    #  MONITORING (during processing)
    # ============================================================
    
    def start_reasoning(self) -> None:
        """Mark start of reasoning phase."""
        self.monitor.enter_phase(ProcessingPhase.REASONING)
    
    def log_reasoning_step(
        self,
        description: str,
        domain: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> None:
        """Log a reasoning step."""
        self.monitor.log_step({
            "focus": description,
            "domain": domain or self._current_domain,
            "depth": depth,
        })
    
    def start_verification(self) -> None:
        """Mark start of verification phase."""
        self.monitor.enter_phase(ProcessingPhase.VERIFYING)
    
    def get_current_state(self) -> CognitiveState:
        """Get current cognitive state."""
        return self.monitor.get_state()
    
    # ============================================================
    #  POST-REFLECTION
    # ============================================================
    
    def reflect(
        self,
        query: str,
        reasoning: str,
        answer: str,
        domain: str,
        sources_cited: int = 0,
        success: Optional[bool] = None,
    ) -> MetaCognitiveReflection:
        """
        Reflect on completed response.
        
        This is the "learn from what you did" phase.
        
        Args:
            query: Original query
            reasoning: Reasoning chain
            answer: Final answer
            domain: Primary domain
            sources_cited: Number of sources cited
            success: Whether response was successful (if known)
        
        Returns:
            MetaCognitiveReflection with insights
        """
        self.monitor.enter_phase(ProcessingPhase.REFLECTING)
        lessons = []
        improvements = []
        
        # 1. Assess confidence
        confidence_result = self.confidence.assess(
            response=answer,
            query=query,
            domain=domain,
            reasoning_steps=len(reasoning.split('.')),
            sources_cited=sources_cited,
        )
        
        if confidence_result.overconfidence_penalty > 0.1:
            lessons.append("May have been overconfident in response")
            improvements.append("Add more hedging language")
        
        # 2. Quantify uncertainty
        uncertainty_result = self.uncertainty.analyze(
            query=query,
            response=answer,
            domains=[domain],
            confidence_score=confidence_result.score,
            sources_available=sources_cited,
        )
        
        if uncertainty_result.should_qualify:
            for qual in uncertainty_result.qualifications:
                improvements.append(f"Add qualification: {qual}")
        
        # 3. Check reasoning quality
        reasoning_result = self.reasoning.evaluate(
            query=query,
            reasoning=reasoning,
            conclusion=answer,
        )
        
        for fallacy, context in reasoning_result.fallacies_detected:
            lessons.append(f"Potential {fallacy.value} detected")
        
        if reasoning_result.needs_revision:
            improvements.extend(reasoning_result.revision_suggestions)
        
        # 4. Detect biases
        bias_alerts = self.bias.check(
            query=query,
            reasoning=reasoning,
            answer=answer,
            sources_consulted=[],
        )
        
        for alert in bias_alerts:
            lessons.append(f"Bias alert: {alert.bias_type.value}")
            improvements.append(alert.mitigation)
        
        # 5. Calculate overall quality
        overall = (
            0.30 * confidence_result.score +
            0.30 * (1 - uncertainty_result.total_uncertainty) +
            0.40 * reasoning_result.overall_score
        )
        
        # Penalty for issues
        overall -= len(bias_alerts) * 0.05
        overall -= len(reasoning_result.fallacies_detected) * 0.05
        overall = max(0.0, min(1.0, overall))
        
        # 6. Assess calibration
        if success is not None:
            self.confidence.record_outcome(confidence_result.score, 1.0 if success else 0.0)
            calib_stats = self.confidence.get_calibration_stats()
            calibration = calib_stats.get("calibration", "unknown")
        else:
            calibration = "not assessed"
        
        # 7. Record strategy outcome
        if self._current_assessment:
            self.strategy.record_outcome(
                strategy=self._current_assessment.strategy.primary_strategy,
                domain=domain,
                success=overall > 0.6,
            )
        
        # 8. Log to journal
        self.journal.log(
            insight_type=InsightType.REASONING_QUALITY,
            query=query,
            domain=domain,
            observation=f"Quality: {overall:.2f}, Confidence: {confidence_result.score:.2f}",
            metrics={
                "overall_quality": overall,
                "confidence": confidence_result.score,
                "uncertainty": uncertainty_result.total_uncertainty,
                "reasoning_score": reasoning_result.overall_score,
            },
            lesson="; ".join(lessons[:3]) if lessons else "",
        )
        
        # 9. End monitoring session
        session_summary = self.monitor.end_session()
        
        reflection = MetaCognitiveReflection(
            overall_quality=overall,
            calibration_accuracy=calibration,
            confidence=confidence_result,
            uncertainty=uncertainty_result,
            reasoning_quality=reasoning_result,
            bias_alerts=bias_alerts,
            lessons_learned=lessons,
            improvements_for_next_time=improvements,
            needs_revision=reasoning_result.needs_revision or len(bias_alerts) > 2,
            revision_suggestions=reasoning_result.revision_suggestions,
        )
        
        return reflection
    
    # ============================================================
    #  UTILITIES
    # ============================================================
    
    def get_self_model(self) -> Dict[str, Any]:
        """Get a model of ANM's self-awareness."""
        return {
            "knowledge_domains": self.knowledge.get_domain_summary(),
            "calibration": self.confidence.get_calibration_stats(),
            "uncertainty_patterns": self.uncertainty.get_uncertainty_stats(),
            "reasoning_quality": self.reasoning.get_average_quality(),
            "common_biases": self.bias.get_bias_summary(),
            "strategy_effectiveness": self.strategy.get_strategy_report(),
            "journal_insights": self.journal.analyze_patterns(),
            "average_cognitive_load": self.cognitive_load.get_average_load(),
        }
    
    def generate_introspection_report(self) -> str:
        """Generate a human-readable introspection report."""
        model = self.get_self_model()
        
        lines = [
            "=" * 60,
            "ANM METACOGNITIVE INTROSPECTION REPORT",
            "=" * 60,
            "",
            "## KNOWLEDGE BOUNDARIES",
            f"   Knowledge cutoff: {model['knowledge_domains'].get('knowledge_cutoff', 'Unknown')}",
            f"   Well-known topics: {model['knowledge_domains'].get('well_known_count', 0)}",
            "",
            "## CONFIDENCE CALIBRATION",
            f"   Samples: {model['calibration'].get('samples', 0)}",
            f"   Calibration: {model['calibration'].get('calibration', 'Unknown')}",
            f"   Avg error: {model['calibration'].get('avg_error', 0):.2f}",
            "",
            "## REASONING QUALITY",
            f"   Average quality: {model['reasoning_quality']:.2f}",
            "",
            "## COGNITIVE LOAD",
            f"   Average load: {model['average_cognitive_load']:.2f}",
            "",
            "## DETECTED BIASES",
        ]
        
        for bias, count in model['common_biases'].items():
            lines.append(f"   - {bias}: {count} occurrences")
        
        if not model['common_biases']:
            lines.append("   No biases detected")
        
        lines.extend([
            "",
            "## JOURNAL INSIGHTS",
            f"   Total entries: {model['journal_insights'].get('total_entries', 0)}",
            f"   Most common insight type: {model['journal_insights'].get('most_common_type', 'None')}",
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)
    
    def should_i_answer(self, query: str, domain: str) -> Tuple[bool, str]:
        """
        Quick check: Should I attempt to answer this?
        
        Returns:
            (should_answer, reason)
        """
        boundary = self.knowledge.analyze(query, domain)
        
        if boundary.status == KnowledgeStatus.UNKNOWABLE:
            return False, "This question asks for fundamentally unknowable information."
        
        if boundary.should_defer_to_expert:
            return False, f"This requires professional expertise in {domain}."
        
        if boundary.status == KnowledgeStatus.UNKNOWN:
            return False, "This is outside my knowledge area."
        
        return True, "I can attempt to answer this."


# Convenience type alias
from typing import Tuple
