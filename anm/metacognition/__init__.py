# ============================================================
#  ANM V0-OpenSource — METACOGNITION MODULE
#  "Thinking About Thinking" - Comprehensive Self-Awareness
#  
#  Components:
#  - MetaCognitiveMonitor: Real-time cognitive process tracking
#  - ConfidenceCalibrator: Calibrated confidence estimation
#  - UncertaintyQuantifier: Aleatoric vs Epistemic uncertainty
#  - CognitiveLoadTracker: Processing complexity estimation
#  - ReasoningQualityChecker: Self-check reasoning quality
#  - KnowledgeBoundaryDetector: Know what you know/don't know
#  - BiasDetector: Detect potential cognitive biases
#  - MetaCognitiveJournal: Log insights for learning
#  - StrategyEvaluator: Evaluate and adapt strategies
# ============================================================

"""
ANM MetaCognition System - Comprehensive Self-Awareness

This module provides deep introspection capabilities:

1. MONITORING - Track cognitive processes in real-time
2. CALIBRATION - Accurate confidence and uncertainty
3. BOUNDARIES - Know knowledge limits
4. QUALITY - Self-check reasoning
5. ADAPTATION - Learn and improve strategies

Usage:
    from anm.metacognition import MetaCognition
    
    mc = MetaCognition()
    
    # Before processing
    assessment = mc.pre_assess(query)
    
    # During processing
    mc.monitor_step(step_info)
    
    # After processing
    reflection = mc.post_reflect(query, answer)
"""

from anm.metacognition.monitor import (
    MetaCognitiveMonitor,
    CognitiveState,
    ProcessingPhase,
)
from anm.metacognition.confidence import (
    ConfidenceCalibrator,
    ConfidenceLevel,
    CalibrationResult,
)
from anm.metacognition.uncertainty import (
    UncertaintyQuantifier,
    UncertaintyType,
    UncertaintyProfile,
)
from anm.metacognition.cognitive_load import (
    CognitiveLoadTracker,
    LoadLevel,
    LoadFactors,
)
from anm.metacognition.reasoning_checker import (
    ReasoningQualityChecker,
    ReasoningQuality,
    LogicalFallacy,
)
from anm.metacognition.knowledge_boundary import (
    KnowledgeBoundaryDetector,
    KnowledgeStatus,
    BoundaryResult,
)
from anm.metacognition.bias_detector import (
    BiasDetector,
    BiasType,
    BiasAlert,
)
from anm.metacognition.journal import (
    MetaCognitiveJournal,
    JournalEntry,
)
from anm.metacognition.strategy_evaluator import (
    StrategyEvaluator,
    StrategyRecommendation,
)
from anm.metacognition.metacognition import (
    MetaCognition,
    MetaCognitiveAssessment,
    MetaCognitiveReflection,
)

__all__ = [
    # Main Interface
    "MetaCognition",
    "MetaCognitiveAssessment",
    "MetaCognitiveReflection",
    # Monitor
    "MetaCognitiveMonitor",
    "CognitiveState",
    "ProcessingPhase",
    # Confidence
    "ConfidenceCalibrator",
    "ConfidenceLevel",
    "CalibrationResult",
    # Uncertainty
    "UncertaintyQuantifier",
    "UncertaintyType",
    "UncertaintyProfile",
    # Cognitive Load
    "CognitiveLoadTracker",
    "LoadLevel",
    "LoadFactors",
    # Reasoning
    "ReasoningQualityChecker",
    "ReasoningQuality",
    "LogicalFallacy",
    # Knowledge
    "KnowledgeBoundaryDetector",
    "KnowledgeStatus",
    "BoundaryResult",
    # Bias
    "BiasDetector",
    "BiasType",
    "BiasAlert",
    # Journal
    "MetaCognitiveJournal",
    "JournalEntry",
    # Strategy
    "StrategyEvaluator",
    "StrategyRecommendation",
]

__version__ = "0.1.0-opensource"

# Availability flag
METACOGNITION_AVAILABLE = True
