# ============================================================
#  ANM V0-OpenSource — Output Processing Utilities
#  Common output cleaning and analysis functions
# ============================================================

"""
Output Processing Utilities

Common functions for output processing:
- Output cleaning
- Confidence estimation
- Output analysis
- Text normalization
"""

from __future__ import annotations
from typing import Dict, Any, List
import re

__all__ = [
    "clean_output",
    "clean_thinking_tags",
    "estimate_confidence",
    "analyze_output",
    "normalize_text",
    "remove_prefixes",
]


def clean_thinking_tags(text: str) -> str:
    """
    Remove thinking tags and markers from text.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    patterns = [
        r"<think>.*?</think>",
        r"<\|begin_of_text\|>",
        r"<\|end_of_text\|>",
        r"Thinking\.\.\..*?\n",
        r"THINKING\.\.\..*?\n",
        r"<think>.*?</think>",
        r"\[THINKING\].*?\[/THINKING\]",
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    
    return text


def remove_prefixes(text: str, prefixes: List[str]) -> str:
    """
    Remove common prefixes from text.
    
    Args:
        text: Text to process
        prefixes: List of prefixes to remove
    
    Returns:
        Text with prefixes removed
    """
    if not text:
        return ""
    
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    return text


def normalize_text(text: str) -> str:
    """
    Normalize text by compressing whitespace.
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Compress multiple newlines
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    
    # Compress multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")
    
    return text.strip()


def clean_output(
    text: str,
    domain_name: str = "",
    clean_thinking: bool = True,
    remove_role_prefixes: bool = True,
) -> str:
    """
    Clean LLM output with common patterns.
    
    Args:
        text: Raw output text
        domain_name: Domain name for prefix removal
        clean_thinking: Whether to remove thinking tags
        remove_role_prefixes: Whether to remove role prefixes
    
    Returns:
        Cleaned output
    """
    if not text:
        return f"[{domain_name.upper()} produced no output]" if domain_name else ""
    
    # Remove thinking tags
    if clean_thinking:
        text = clean_thinking_tags(text)
    
    # Remove role prefixes
    if remove_role_prefixes and domain_name:
        prefixes = [
            f"{domain_name.title()} reasoning:",
            f"[{domain_name.upper()}]",
            "Reasoning:",
            "Here is my reasoning:",
            f"{domain_name.title()}:",
        ]
        text = remove_prefixes(text, prefixes)
    
    # Normalize whitespace
    text = normalize_text(text)
    
    return text


def estimate_confidence(text: str) -> float:
    """
    Estimate confidence from output text.
    
    Args:
        text: Output text
    
    Returns:
        Confidence score (0.0-1.0)
    """
    if not text:
        return 0.1
    
    lower = text.lower()
    conf = 0.7  # Base confidence
    
    # High confidence markers
    high_markers = ["definitely", "certainly", "clearly", "proven", "obvious", "confirmed"]
    for marker in high_markers:
        if marker in lower:
            conf += 0.05
    
    # Low confidence markers
    low_markers = ["maybe", "possibly", "uncertain", "not sure", "might", "perhaps", "probably"]
    for marker in low_markers:
        if marker in lower:
            conf -= 0.1
    
    # Error indicators
    if "[ERROR" in text or "error" in lower[:100]:
        conf -= 0.3
    
    # Uncertainty phrases
    uncertainty_phrases = ["i'm not sure", "i don't know", "uncertain", "unclear"]
    for phrase in uncertainty_phrases:
        if phrase in lower:
            conf -= 0.15
    
    return max(0.1, min(1.0, conf))


def analyze_output(domain: str, text: str) -> Dict[str, Any]:
    """
    Analyze output for various characteristics.
    
    Args:
        domain: Domain name
        text: Output text
    
    Returns:
        Analysis dictionary
    """
    if not text:
        return {
            "needs_help": True,
            "uncertain_phrases": 0,
            "has_cannot_do": False,
            "has_error": False,
            "confidence": 0.1,
            "length": 0,
        }
    
    lower = text.lower()
    
    # Count uncertainty phrases
    uncertainty_phrases = [
        "not sure", "uncertain", "don't know", "cannot", "can't",
        "unable", "not able", "don't understand", "confused",
    ]
    uncertain_count = sum(1 for phrase in uncertainty_phrases if phrase in lower)
    
    # Check for "cannot do" indicators
    cannot_do = any(phrase in lower for phrase in [
        "cannot", "can't", "unable", "not able", "don't know how",
    ])
    
    # Check for errors
    has_error = "[ERROR" in text or "error:" in lower
    
    # Estimate confidence
    confidence = estimate_confidence(text)
    
    # Determine if help is needed
    needs_help = (
        uncertain_count > 2 or
        cannot_do or
        has_error or
        confidence < 0.4 or
        len(text) < 50
    )
    
    return {
        "needs_help": needs_help,
        "uncertain_phrases": uncertain_count,
        "has_cannot_do": cannot_do,
        "has_error": has_error,
        "confidence": confidence,
        "length": len(text),
        "has_wot_request": "WOT_REQUEST:" in text,
    }

