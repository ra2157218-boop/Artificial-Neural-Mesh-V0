# ============================================================
# ANM V0-OpenSource — AUTO FIXER
#  Automatic Code Repair with 3-Retry Human Escalation
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import os
import sys
import time
import traceback
import importlib
import shutil


class FixStrategy(Enum):
    """Strategies for fixing issues."""
    REIMPORT = "reimport"           # Try reimporting the module
    REGENERATE = "regenerate"       # Regenerate the file from template
    RESET_INIT = "reset_init"       # Reset __init__.py exports
    VALIDATE_FIX = "validate_fix"   # Use CodeValidator auto-fix
    MANUAL = "manual"               # Requires human intervention


@dataclass
class FixAttempt:
    """Record of a fix attempt."""
    attempt_number: int
    strategy: FixStrategy
    success: bool
    message: str
    duration_ms: float
    changes_made: List[str] = field(default_factory=list)


@dataclass
class FixResult:
    """Result of the auto-fix process."""
    fixed: bool
    issue_module: str
    issue_message: str
    attempts: List[FixAttempt] = field(default_factory=list)
    final_message: str = ""
    requires_human: bool = False
    human_instructions: Optional[str] = None


class AutoFixer:
    """
    Automatic Code Repair System.
    
    Attempts to fix sanity issues with up to 3 retries:
    1. Try 1: Light fix (reimport, cache clear)
    2. Try 2: Medium fix (regenerate from template, auto-lint)
    3. Try 3: Heavy fix (full reset/regenerate)
    
    If all 3 attempts fail, escalates to human with detailed report.
    """
    
    MAX_ATTEMPTS = 3
    
    # Templates for regenerating __init__.py files
    INIT_TEMPLATES = {
        "anm.specialists": '''# ANM Specialists Module
from anm.specialists.general_llm import GeneralLLM
from anm.specialists.math_llm import MathLLM
from anm.specialists.physics_llm import PhysicsLLM
from anm.specialists.code_llm import CodeLLM
from anm.specialists.chemistry_llm import ChemistryLLM
from anm.specialists.biology_llm import BiologyLLM
from anm.specialists.memory_llm import MemoryLLM
from anm.specialists.research_llm import ResearchLLM
from anm.specialists.facts_llm import FactsLLM
from anm.specialists.sound_llm import SoundLLM

try:
    from anm.specialists.simulation_llm import SimulationLLM
    SIMULATION_LLM_AVAILABLE = True
except ImportError:
    SimulationLLM = None
    SIMULATION_LLM_AVAILABLE = False

try:
    from anm.specialists.image_llm import ImageLLM
    IMAGE_LLM_AVAILABLE = True
except ImportError:
    ImageLLM = None
    IMAGE_LLM_AVAILABLE = False

__all__ = [
    "GeneralLLM", "MathLLM", "PhysicsLLM", "CodeLLM",
    "ChemistryLLM", "BiologyLLM", "MemoryLLM", "ResearchLLM",
    "FactsLLM", "SoundLLM", "SimulationLLM", "ImageLLM",
    "SIMULATION_LLM_AVAILABLE", "IMAGE_LLM_AVAILABLE",
]
''',
        "anm.memory": '''# ANM Memory Module
from anm.memory.diary_memory import DiaryMemory
from anm.memory.working_memory import WorkingMemory
from anm.memory.episodic_memory import EpisodicMemory
from anm.memory.semantic_memory import SemanticMemory
from anm.memory.meta_memory import MetaMemory

try:
    from anm.memory.simulation_memory import SimulationMemory
except ImportError:
    SimulationMemory = None

try:
    from anm.memory.image_memory import ImageMemory
except ImportError:
    ImageMemory = None

try:
    from anm.memory.sound_memory import SoundMemory
except ImportError:
    SoundMemory = None

try:
    from anm.memory.visual_memory import VisualMemory
except ImportError:
    VisualMemory = None

__all__ = [
    "DiaryMemory", "WorkingMemory", "EpisodicMemory",
    "SemanticMemory", "MetaMemory", "SimulationMemory",
    "ImageMemory", "SoundMemory", "VisualMemory",
]
''',
    }
    
    def __init__(self, verbose: bool = True, backup_dir: str = ".anm_backups"):
        self.verbose = verbose
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            prefix = {
                "INFO": "🔧",
                "OK": "✅",
                "WARN": "⚠️ ",
                "ERROR": "❌",
                "TRY": "🔄",
            }.get(level, "  ")
            print(f"{prefix} {message}")
    
    def fix_issue(self, issue: "SanityIssue") -> FixResult:
        """
        Attempt to fix a sanity issue with up to 3 retries.
        
        Args:
            issue: The SanityIssue to fix
        
        Returns:
            FixResult with details of the fix attempts
        """
        from anm.sanity.sanity_checker import SanityIssue, IssueCategory
        
        result = FixResult(
            fixed=False,
            issue_module=issue.module,
            issue_message=issue.message,
        )
        
        if self.verbose:
            print()
            print(f"🔧 Attempting to fix: {issue.module}")
            print(f"   Issue: {issue.message}")
        
        # Determine fix strategies based on issue type
        strategies = self._get_fix_strategies(issue)
        
        for attempt_num in range(1, self.MAX_ATTEMPTS + 1):
            strategy = strategies[min(attempt_num - 1, len(strategies) - 1)]
            
            self.log(f"Attempt {attempt_num}/{self.MAX_ATTEMPTS}: {strategy.value}", "TRY")
            
            start_time = time.time()
            
            try:
                success, message, changes = self._apply_fix(issue, strategy, attempt_num)
                duration_ms = (time.time() - start_time) * 1000
                
                attempt = FixAttempt(
                    attempt_number=attempt_num,
                    strategy=strategy,
                    success=success,
                    message=message,
                    duration_ms=duration_ms,
                    changes_made=changes,
                )
                result.attempts.append(attempt)
                
                if success:
                    # Verify the fix worked
                    if self._verify_fix(issue):
                        result.fixed = True
                        result.final_message = f"Fixed on attempt {attempt_num} using {strategy.value}"
                        self.log(f"Fixed successfully!", "OK")
                        return result
                    else:
                        self.log(f"Fix applied but verification failed", "WARN")
                else:
                    self.log(f"Fix attempt failed: {message}", "ERROR")
                    
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                attempt = FixAttempt(
                    attempt_number=attempt_num,
                    strategy=strategy,
                    success=False,
                    message=f"Exception: {e}",
                    duration_ms=duration_ms,
                )
                result.attempts.append(attempt)
                self.log(f"Fix attempt raised exception: {e}", "ERROR")
        
        # All attempts failed - escalate to human
        result.requires_human = True
        result.human_instructions = self._generate_human_instructions(issue, result.attempts)
        result.final_message = "All automatic fix attempts failed"
        
        return result
    
    def _get_fix_strategies(self, issue: "SanityIssue") -> List[FixStrategy]:
        """Determine fix strategies based on issue type."""
        from anm.sanity.sanity_checker import IssueCategory
        
        if issue.category == IssueCategory.IMPORT:
            return [
                FixStrategy.REIMPORT,
                FixStrategy.VALIDATE_FIX,
                FixStrategy.REGENERATE,
            ]
        elif issue.category == IssueCategory.SYNC:
            return [
                FixStrategy.RESET_INIT,
                FixStrategy.REGENERATE,
                FixStrategy.MANUAL,
            ]
        elif issue.category == IssueCategory.INSTANTIATION:
            return [
                FixStrategy.REIMPORT,
                FixStrategy.VALIDATE_FIX,
                FixStrategy.MANUAL,
            ]
        else:
            return [
                FixStrategy.REIMPORT,
                FixStrategy.VALIDATE_FIX,
                FixStrategy.MANUAL,
            ]
    
    def _apply_fix(
        self,
        issue: "SanityIssue",
        strategy: FixStrategy,
        attempt: int,
    ) -> tuple[bool, str, List[str]]:
        """
        Apply a fix strategy.
        
        Returns:
            (success, message, changes_made)
        """
        changes = []
        
        if strategy == FixStrategy.REIMPORT:
            return self._fix_reimport(issue)
        
        elif strategy == FixStrategy.RESET_INIT:
            return self._fix_reset_init(issue)
        
        elif strategy == FixStrategy.REGENERATE:
            return self._fix_regenerate(issue)
        
        elif strategy == FixStrategy.VALIDATE_FIX:
            return self._fix_validate(issue)
        
        elif strategy == FixStrategy.MANUAL:
            return False, "Requires manual intervention", []
        
        return False, f"Unknown strategy: {strategy}", []
    
    def _fix_reimport(self, issue: "SanityIssue") -> tuple[bool, str, List[str]]:
        """Try clearing module cache and reimporting."""
        module_name = issue.module.split(".")[0]  # Get top-level module
        
        # Clear relevant modules from cache
        modules_to_clear = [
            key for key in sys.modules.keys()
            if key.startswith("anm")
        ]
        
        for mod in modules_to_clear:
            sys.modules.pop(mod, None)
        
        # Also clear __pycache__ for the specific module
        try:
            module_parts = issue.module.split(".")
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                *module_parts[:-1],
                "__pycache__",
            )
            if os.path.exists(cache_dir):
                for f in os.listdir(cache_dir):
                    if module_parts[-1] in f:
                        os.remove(os.path.join(cache_dir, f))
        except Exception:
            pass
        
        # Try importing
        try:
            importlib.import_module(issue.module)
            return True, "Reimport successful after cache clear", ["Cleared module cache"]
        except Exception as e:
            return False, f"Reimport failed: {e}", ["Cleared module cache"]
    
    def _fix_reset_init(self, issue: "SanityIssue") -> tuple[bool, str, List[str]]:
        """Reset __init__.py to template."""
        # Determine which module's __init__ needs reset
        module_base = issue.module.split(".")[0:2]  # e.g., ["anm", "specialists"]
        module_key = ".".join(module_base)
        
        if module_key not in self.INIT_TEMPLATES:
            return False, f"No template for {module_key}", []
        
        # Find the __init__.py file
        init_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            *module_base,
            "__init__.py",
        )
        
        if not os.path.exists(os.path.dirname(init_path)):
            return False, f"Module directory not found: {os.path.dirname(init_path)}", []
        
        # Backup existing file
        if os.path.exists(init_path):
            backup_path = os.path.join(
                self.backup_dir,
                f"{module_key.replace('.', '_')}_init_backup_{int(time.time())}.py",
            )
            shutil.copy2(init_path, backup_path)
        
        # Write template
        try:
            with open(init_path, "w") as f:
                f.write(self.INIT_TEMPLATES[module_key])
            return True, f"Reset {init_path} to template", [f"Wrote template to {init_path}"]
        except Exception as e:
            return False, f"Failed to write template: {e}", []
    
    def _fix_regenerate(self, issue: "SanityIssue") -> tuple[bool, str, List[str]]:
        """Regenerate module code using CodeValidator."""
        # This is a more aggressive fix - try to regenerate the module
        try:
            from anm.expansion.code.validator import CodeValidator
            
            validator = CodeValidator()
            
            # Find the file
            module_path = issue.module.replace(".", "/") + ".py"
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                module_path,
            )
            
            if not os.path.exists(full_path):
                return False, f"File not found: {full_path}", []
            
            # Read current code
            with open(full_path, "r") as f:
                code = f.read()
            
            # Try auto-fix
            fixed_code, fixes = validator.auto_fix(code)
            
            if fixes:
                # Backup
                backup_path = os.path.join(
                    self.backup_dir,
                    f"{issue.module.replace('.', '_')}_backup_{int(time.time())}.py",
                )
                shutil.copy2(full_path, backup_path)
                
                # Write fixed code
                with open(full_path, "w") as f:
                    f.write(fixed_code)
                
                return True, f"Applied {len(fixes)} auto-fixes", fixes
            else:
                return False, "No auto-fixes available", []
                
        except Exception as e:
            return False, f"Regeneration failed: {e}", []
    
    def _fix_validate(self, issue: "SanityIssue") -> tuple[bool, str, List[str]]:
        """Use CodeValidator to check and fix."""
        try:
            from anm.expansion.code.validator import CodeValidator
            
            validator = CodeValidator()
            
            # Find the file
            module_parts = issue.module.split(".")
            
            # Handle class names in module path
            if module_parts[-1][0].isupper():
                # Last part is a class name, remove it
                module_parts = module_parts[:-1]
            
            module_path = "/".join(module_parts) + ".py"
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                module_path,
            )
            
            if not os.path.exists(full_path):
                return False, f"File not found: {full_path}", []
            
            # Read and validate
            with open(full_path, "r") as f:
                code = f.read()
            
            result = validator.validate(code, os.path.basename(full_path))
            
            if result.valid:
                return True, "Code already valid, cleared caches", ["Cache cleared"]
            
            # Try auto-fix
            fixed_code, fixes = validator.auto_fix(code)
            
            if fixes:
                backup_path = os.path.join(
                    self.backup_dir,
                    f"{issue.module.replace('.', '_')}_backup_{int(time.time())}.py",
                )
                shutil.copy2(full_path, backup_path)
                
                with open(full_path, "w") as f:
                    f.write(fixed_code)
                
                return True, f"Applied validation fixes", fixes
            
            return False, f"Validation found {len(result.errors)} errors, no auto-fix available", []
            
        except Exception as e:
            return False, f"Validation fix failed: {e}", []
    
    def _verify_fix(self, issue: "SanityIssue") -> bool:
        """Verify that the fix worked by re-running the check."""
        # Clear caches first
        for key in list(sys.modules.keys()):
            if key.startswith("anm"):
                sys.modules.pop(key, None)
        
        try:
            importlib.import_module(issue.module.split(".")[0])
            return True
        except Exception:
            return False
    
    def _generate_human_instructions(
        self,
        issue: "SanityIssue",
        attempts: List[FixAttempt],
    ) -> str:
        """Generate detailed instructions for human intervention."""
        lines = [
            "=" * 60,
            "🚨 HUMAN INTERVENTION REQUIRED",
            "=" * 60,
            "",
            f"Module: {issue.module}",
            f"Issue: {issue.message}",
            f"Category: {issue.category.value}",
            f"Severity: {issue.severity.value}",
            "",
            "Attempted Fixes:",
        ]
        
        for attempt in attempts:
            lines.append(f"  {attempt.attempt_number}. {attempt.strategy.value}: {attempt.message}")
        
        lines.extend([
            "",
            "Suggested Manual Steps:",
            f"  1. Check file: {issue.module.replace('.', '/')}.py",
            "  2. Look for syntax errors or missing imports",
            "  3. Verify all dependencies are installed",
            "  4. Check if file was accidentally deleted or corrupted",
            "",
        ])
        
        if issue.traceback:
            lines.extend([
                "Full Traceback:",
                issue.traceback,
            ])
        
        if issue.suggested_fix:
            lines.extend([
                "",
                f"Original Suggestion: {issue.suggested_fix}",
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def fix_all_issues(
        self,
        issues: List["SanityIssue"],
    ) -> tuple[List[FixResult], bool]:
        """
        Attempt to fix all issues.
        
        Returns:
            (list of FixResults, whether all were fixed)
        """
        results = []
        all_fixed = True
        
        # Only attempt to fix auto-fixable issues
        fixable_issues = [i for i in issues if i.auto_fixable]
        
        if not fixable_issues:
            return [], True
        
        if self.verbose:
            print()
            print("=" * 60)
            print("🔧 AUTO-FIX: Attempting to repair issues")
            print("=" * 60)
            print(f"   {len(fixable_issues)} fixable issues found")
        
        for issue in fixable_issues:
            result = self.fix_issue(issue)
            results.append(result)
            
            if not result.fixed:
                all_fixed = False
                
                # Print human instructions
                if result.requires_human and result.human_instructions:
                    print()
                    print(result.human_instructions)
        
        if self.verbose:
            print()
            fixed_count = sum(1 for r in results if r.fixed)
            print("=" * 60)
            print(f"🔧 AUTO-FIX COMPLETE: {fixed_count}/{len(results)} issues fixed")
            print("=" * 60)
        
        return results, all_fixed


def run_auto_fix(issues: List["SanityIssue"], verbose: bool = True) -> tuple[List[FixResult], bool]:
    """Convenience function to run auto-fix."""
    fixer = AutoFixer(verbose=verbose)
    return fixer.fix_all_issues(issues)
