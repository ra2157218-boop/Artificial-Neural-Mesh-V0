# ============================================================
#  ANM V0-OpenSource — Sanity Check Module
# ============================================================

"""
ANM Sanity Check Module - Pre-startup validation and auto-fixing.
"""

from anm.sanity.sanity_checker import (
    SanityChecker,
    SanityResult,
    SanityIssue,
    IssueSeverity,
    IssueCategory,
)

try:
    from anm.sanity.auto_fixer import AutoFixer
except ImportError:
    # AutoFixer is optional - create a stub if missing
    class AutoFixer:
        """Stub AutoFixer for when auto_fixer.py is not available."""
        def __init__(self, verbose: bool = True):
            self.verbose = verbose
        
        def fix_all_issues(self, issues):
            """Stub method - returns empty results."""
            if self.verbose:
                print("⚠️  AutoFixer not available - skipping auto-fix")
            return [], False

__all__ = [
    "SanityChecker",
    "SanityResult",
    "SanityIssue",
    "IssueSeverity",
    "IssueCategory",
    "AutoFixer",
]

