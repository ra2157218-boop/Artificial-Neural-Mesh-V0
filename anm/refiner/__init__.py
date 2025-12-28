# ============================================================
#  ANM V0-OpenSource — Refiner Module
#  Final Answer Composition
# ============================================================

"""
ANM Refiner - Final Answer Composition Engine

The Refiner takes all domain specialist outputs and composes
a high-quality final answer.

Usage:
    from anm.refiner import Refiner, RefinerConfig
    
    refiner = Refiner()
    answer = refiner.refine(packet)
    
    # Or with full result
    result = refiner.refine_full(packet)
    print(f"Quality: {result.quality.name}")
    print(f"Confidence: {result.confidence:.2f}")
"""

from anm.refiner.refiner import (
    Refiner,
    RefinerConfig,
    RefinedAnswer,
    AnswerQuality,
    AnswerStyle,
)

__all__ = [
    "Refiner",
    "RefinerConfig",
    "RefinedAnswer",
    "AnswerQuality",
    "AnswerStyle",
]

__version__ = "0.1.0-opensource"
