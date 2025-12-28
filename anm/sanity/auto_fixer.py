# ============================================================
# ANM V0-OpenSource — AUTO FIXER
#  Automatic Issue Resolution System
# ============================================================

"""
ANM Auto Fixer - Automatically fixes common sanity check issues.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from anm.sanity.sanity_checker import SanityIssue, IssueCategory, IssueSeverity


class AutoFixer:
    """
    Automatic issue fixer for sanity check problems.
    
    Attempts to fix common issues like:
    - Missing __init__.py files
    - Import errors
    - Configuration issues
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize AutoFixer.
        
        Args:
            verbose: Print progress messages
        """
        self.verbose = verbose
        self.fixes_applied = []
        self.fixes_failed = []
    
    def fix_all_issues(self, issues: List[SanityIssue]) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Attempt to fix all auto-fixable issues.
        
        Args:
            issues: List of SanityIssue objects to fix
        
        Returns:
            Tuple of (fix_results, all_fixed)
            - fix_results: List of fix result dictionaries
            - all_fixed: True if all issues were fixed
        """
        if not issues:
            return [], True
        
        fix_results = []
        all_fixed = True
        
        for issue in issues:
            if not issue.auto_fixable:
                continue
            
            result = self._fix_issue(issue)
            fix_results.append(result)
            
            if not result.get("success", False):
                all_fixed = False
        
        return fix_results, all_fixed
    
    def _fix_issue(self, issue: SanityIssue) -> Dict[str, Any]:
        """
        Fix a single issue.
        
        Args:
            issue: SanityIssue to fix
        
        Returns:
            Dictionary with fix result:
            {
                "issue": issue,
                "success": bool,
                "message": str,
                "action": str
            }
        """
        result = {
            "issue": issue,
            "success": False,
            "message": "",
            "action": "none",
        }
        
        try:
            # Handle different issue categories
            if issue.category == IssueCategory.IMPORT:
                result = self._fix_import_issue(issue)
            elif issue.category == IssueCategory.SYNC:
                result = self._fix_sync_issue(issue)
            elif issue.category == IssueCategory.CONFIG:
                result = self._fix_config_issue(issue)
            else:
                result["message"] = f"Auto-fix not implemented for {issue.category.value} issues"
            
            if result["success"]:
                self.fixes_applied.append(result)
                if self.verbose:
                    print(f"  ✓ Fixed: {issue.message}")
            else:
                self.fixes_failed.append(result)
                if self.verbose:
                    print(f"  ✗ Could not fix: {issue.message}")
        
        except Exception as e:
            result["success"] = False
            result["message"] = f"Error during fix: {e}"
            self.fixes_failed.append(result)
        
        return result
    
    def _fix_import_issue(self, issue: SanityIssue) -> Dict[str, Any]:
        """Fix import-related issues."""
        result = {
            "issue": issue,
            "success": False,
            "message": "",
            "action": "import_fix",
        }
        
        # Check if it's a missing __init__.py issue
        if "__init__" in issue.message.lower() or "cannot import" in issue.message.lower():
            # Try to create missing __init__.py files
            module_path = issue.module.replace(".", "/")
            if "/" in module_path:
                # This is a submodule
                init_path = f"{module_path}/__init__.py"
                try:
                    from pathlib import Path
                    init_file = Path(init_path)
                    if not init_file.exists():
                        init_file.parent.mkdir(parents=True, exist_ok=True)
                        init_file.write_text("# Auto-generated __init__.py\n")
                        result["success"] = True
                        result["message"] = f"Created missing {init_path}"
                except Exception as e:
                    result["message"] = f"Failed to create {init_path}: {e}"
        
        return result
    
    def _fix_sync_issue(self, issue: SanityIssue) -> Dict[str, Any]:
        """Fix sync-related issues (missing exports, etc.)."""
        result = {
            "issue": issue,
            "success": False,
            "message": "",
            "action": "sync_fix",
        }
        
        # Most sync issues require manual intervention
        result["message"] = "Sync issues typically require code changes"
        
        return result
    
    def _fix_config_issue(self, issue: SanityIssue) -> Dict[str, Any]:
        """Fix configuration-related issues."""
        result = {
            "issue": issue,
            "success": False,
            "message": "",
            "action": "config_fix",
        }
        
        # Config issues may be fixable if we know the fix
        if issue.suggested_fix:
            result["message"] = f"Suggested fix: {issue.suggested_fix}"
        
        return result


__all__ = ["AutoFixer"]

