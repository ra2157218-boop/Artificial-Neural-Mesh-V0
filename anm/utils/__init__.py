# ============================================================
#  ANM V0-OpenSource — Utilities Module
#  Common utility functions
# ============================================================

"""
ANM Utilities Module

Provides common utility functions extracted from duplicated code:
- WoT utilities (packet building, WOT_REQUEST handling)
- Output processing (cleaning, confidence estimation)
- Hash utilities (query hashing, key generation)
"""

# WoT Utilities
from anm.utils.wot_utils import (
    extract_wot_request,
    strip_all_wot_requests,
    ensure_wot_request,
    normalize_wot_request,
    build_wot_packet,
    build_full_context_packet,
)

# Output Utilities
from anm.utils.output_utils import (
    clean_output,
    clean_thinking_tags,
    estimate_confidence,
    analyze_output,
    normalize_text,
    remove_prefixes,
)

# Hash Utilities
from anm.utils.hash_utils import (
    hash_query,
    hash_string,
    generate_cache_key,
)

# Logger (existing)
from anm.utils.logger import ANMLogger

__all__ = [
    # WoT Utilities
    "extract_wot_request",
    "strip_all_wot_requests",
    "ensure_wot_request",
    "normalize_wot_request",
    "build_wot_packet",
    "build_full_context_packet",
    
    # Output Utilities
    "clean_output",
    "clean_thinking_tags",
    "estimate_confidence",
    "analyze_output",
    "normalize_text",
    "remove_prefixes",
    
    # Hash Utilities
    "hash_query",
    "hash_string",
    "generate_cache_key",
    
    # Logger
    "ANMLogger",
]

