# ============================================================
#  ANM V0-OpenSource — WoT Utilities
#  Common WoT-related functions extracted for reuse
# ============================================================

"""
WoT Utilities

Common functions for WoT packet processing:
- WOT_REQUEST extraction and manipulation
- Packet building
- Output cleaning
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import re

__all__ = [
    "extract_wot_request",
    "strip_all_wot_requests",
    "ensure_wot_request",
    "normalize_wot_request",
    "build_wot_packet",
    "build_full_context_packet",
]


def extract_wot_request(text: str) -> str:
    """
    Extract WOT_REQUEST value from text.
    
    Normalization rules:
    - If token is NONE → returns "NONE"
    - If token is MEMORY → returns "MEMORY"
    - Otherwise returns lowercase domain name
    
    Args:
        text: Text containing WOT_REQUEST line
    
    Returns:
        Extracted WOT_REQUEST value or "NONE" if not found
    """
    if not text or "WOT_REQUEST:" not in text:
        return "NONE"
    
    # Try to find the line
    for line in text.split("\n"):
        if line.strip().startswith("WOT_REQUEST:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                return "NONE"
            
            upper = value.upper()
            if upper in ("NONE", "MEMORY"):
                return upper
            
            return value.lower()
    
    # Fallback: split method
    try:
        line = text.split("WOT_REQUEST:", 1)[1].split("\n", 1)[0].strip()
        if not line:
            return "NONE"
        
        upper = line.upper()
        if upper in ("NONE", "MEMORY"):
            return upper
        
        return line.lower()
    except (IndexError, AttributeError):
        return "NONE"


def strip_all_wot_requests(text: str) -> str:
    """
    Remove ALL lines that start with 'WOT_REQUEST:' (case-insensitive).
    
    Args:
        text: Text to process
    
    Returns:
        Text with all WOT_REQUEST lines removed
    """
    if not text:
        return ""
    
    lines = []
    for line in text.splitlines():
        if not line.strip().upper().startswith("WOT_REQUEST:"):
            lines.append(line)
    
    return "\n".join(lines)


def ensure_wot_request(text: str, default: str = "NONE", require: bool = True) -> str:
    """
    Ensure output has exactly one WOT_REQUEST line.
    
    Args:
        text: Text to process
        default: Default WOT_REQUEST value if missing
        require: Whether to add WOT_REQUEST if missing
    
    Returns:
        Text with exactly one WOT_REQUEST line
    """
    if not text:
        return f"WOT_REQUEST: {default}" if require else ""
    
    lines = text.strip().split("\n")
    
    # Check if WOT_REQUEST exists
    has_wot = any(ln.strip().upper().startswith("WOT_REQUEST:") for ln in lines)
    
    # Strip all existing WOT_REQUEST lines
    cleaned_lines = []
    for line in lines:
        if not line.strip().upper().startswith("WOT_REQUEST:"):
            cleaned_lines.append(line)
    
    # Add single WOT_REQUEST if required
    if require:
        cleaned_lines.append(f"WOT_REQUEST: {default}")
    
    return "\n".join(cleaned_lines)


def normalize_wot_request(value: str) -> str:
    """
    Normalize WOT_REQUEST value.
    
    Args:
        value: WOT_REQUEST value to normalize
    
    Returns:
        Normalized value (NONE, MEMORY, or lowercase domain)
    """
    if not value:
        return "NONE"
    
    upper = value.upper().strip()
    if upper in ("NONE", "MEMORY"):
        return upper
    
    return value.lower().strip()


def build_wot_packet(
    query: str,
    memory_brief: Optional[str] = None,
    cots: Optional[Dict[str, str]] = None,
) -> str:
    """
    Build initial WoT packet.
    
    Args:
        query: User query
        memory_brief: Optional memory context
        cots: Optional domain CoTs
    
    Returns:
        Formatted WoT packet
    """
    parts = []
    
    parts.append("=== USER QUERY ===")
    parts.append(query)
    parts.append("")
    
    if memory_brief:
        parts.append("=== MEMORY CONTEXT ===")
        parts.append(memory_brief)
        parts.append("")
    
    if cots:
        parts.append("=== DOMAIN REASONING ===")
        for domain, cot in cots.items():
            if cot:
                parts.append(f"[{domain.upper()}]")
                parts.append(cot)
                parts.append("")
    
    return "\n".join(parts)


def build_full_context_packet(
    query: str,
    memory_brief: Optional[str] = None,
    cots: Optional[Dict[str, str]] = None,
    domain_stats: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Build full context packet with all domain CoTs.
    
    Args:
        query: User query
        memory_brief: Optional memory context
        cots: Domain CoTs dictionary
        domain_stats: Optional domain statistics
    
    Returns:
        Formatted full context packet
    """
    parts = []
    
    parts.append("=== USER QUERY ===")
    parts.append(query)
    parts.append("")
    
    if memory_brief:
        parts.append("=== MEMORY CONTEXT ===")
        parts.append(memory_brief)
        parts.append("")
    
    if cots:
        parts.append("=== ALL DOMAIN REASONING ===")
        for domain, cot in cots.items():
            if cot and cot.strip():
                parts.append(f"[{domain.upper()}]")
                parts.append(cot)
                parts.append("")
    
    if domain_stats:
        parts.append("=== DOMAIN STATISTICS ===")
        for domain, stats in domain_stats.items():
            if stats:
                parts.append(f"[{domain.upper()}]")
                parts.append(f"Calls: {stats.get('calls', 0)}")
                parts.append(f"Avg Confidence: {stats.get('avg_confidence', 0.0):.2f}")
                parts.append("")
    
    return "\n".join(parts)

