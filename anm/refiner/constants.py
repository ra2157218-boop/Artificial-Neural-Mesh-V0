"""
Refiner module constants.

This module centralizes magic numbers used in the Refiner,
making them configurable and well-documented.
"""

# ============================================================
# ANSWER LENGTH CONSTRAINTS
# ============================================================

# Maximum answer length in characters
# Rationale: Prevents excessively verbose responses that may
# contain redundant information or lose focus
MAX_ANSWER_LENGTH = 4000

# Minimum answer length in characters
# Rationale: Ensures answers have sufficient detail to be useful
# Answers below this threshold likely lack necessary context
MIN_ANSWER_LENGTH = 50


# ============================================================
# CONTENT EXTRACTION LIMITS
# ============================================================

# Maximum number of key points to extract from an answer
# Rationale: Beyond 10 points, readers experience cognitive overload
# Research shows 7±2 items is optimal for human memory
MAX_KEY_POINTS = 10

# Maximum number of conclusions to extract
# Rationale: 3-5 conclusions provide good coverage without
# overwhelming the reader or diluting important findings
MAX_CONCLUSIONS = 5

# Maximum number of formulas/equations to extract
# Rationale: Focus on the most critical mathematical relationships
# Too many formulas reduce readability
MAX_FORMULAS = 10


# ============================================================
# QUALITY CONTROL
# ============================================================

# Minimum confidence threshold for accepting specialist answers
# Rationale: Answers below this threshold may be unreliable
MIN_CONFIDENCE_THRESHOLD = 0.3

# Maximum allowed contradictions before flagging answer as problematic
# Rationale: Some minor contradictions may be acceptable (e.g., acknowledging
# different perspectives), but too many indicate logical issues
MAX_ALLOWED_CONTRADICTIONS = 2


# ============================================================
# STYLE AND COMPOSITION
# ============================================================

# Default style when no specific style is requested
DEFAULT_STYLE = "technical"

# Maximum number of sections in structured output
# Rationale: Beyond 8 sections, the answer becomes fragmented
MAX_SECTIONS = 8

# Minimum words per section to avoid trivial sections
MIN_WORDS_PER_SECTION = 20
