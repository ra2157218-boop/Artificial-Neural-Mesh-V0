# ============================================================
# ANM V0-OpenSource — SANITY CHECKER
#  Comprehensive Pre-Startup Validation System
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
import os
import time
import traceback
import importlib


class IssueSeverity(Enum):
    """Severity levels for sanity issues."""
    CRITICAL = "critical"  # System cannot start
    ERROR = "error"        # Major functionality broken
    WARNING = "warning"    # Degraded functionality
    INFO = "info"          # Minor issue, system works


class IssueCategory(Enum):
    """Categories of sanity issues."""
    IMPORT = "import"           # Module import failure
    INSTANTIATION = "instantiation"  # Component creation failure
    INTEGRATION = "integration"  # Components don't work together
    CONFIG = "config"           # Configuration issues
    DEPENDENCY = "dependency"   # Missing external dependency
    SYNC = "sync"               # Components out of sync


@dataclass
class SanityIssue:
    """Represents a single sanity check issue."""
    category: IssueCategory
    severity: IssueSeverity
    module: str
    message: str
    exception: Optional[str] = None
    traceback: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    fix_code: Optional[str] = None


@dataclass
class SanityResult:
    """Result of a complete sanity check run."""
    passed: bool
    issues: List[SanityIssue] = field(default_factory=list)
    checks_run: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    duration_ms: float = 0.0
    timestamp: str = ""
    
    @property
    def critical_issues(self) -> List[SanityIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]
    
    @property
    def errors(self) -> List[SanityIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.ERROR]
    
    @property
    def warnings(self) -> List[SanityIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]
    
    @property
    def auto_fixable_issues(self) -> List[SanityIssue]:
        return [i for i in self.issues if i.auto_fixable]


class SanityChecker:
    """
    Comprehensive ANM Sanity Check System.
    
    Runs pre-startup validation to ensure:
    - All modules can be imported
    - All components can be instantiated
    - Components integrate properly
    - Configuration is valid
    - Dependencies are available
    """
    
    # Core modules that MUST work
    CORE_MODULES = [
        "anm.router.router",
        "anm.router.planner_llm",
        "anm.router.domain_masker",
        "anm.wot.wot_engine",
        "anm.refiner.refiner",
        "anm.verifier.verifier",
        "anm.utils.logger",
        "anm.config.settings",
    ]
    
    # Specialist modules
    SPECIALIST_MODULES = [
        "anm.specialists.general_llm",
        "anm.specialists.math_llm",
        "anm.specialists.physics_llm",
        "anm.specialists.code_llm",
        "anm.specialists.chemistry_llm",
        "anm.specialists.biology_llm",
        "anm.specialists.memory_llm",
        "anm.specialists.research_llm",
        "anm.specialists.facts_llm",
        "anm.specialists.sound_llm",
    ]
    
    # Optional modules (warnings only)
    OPTIONAL_MODULES = [
        "anm.specialists.simulation_llm",
        "anm.specialists.image_llm",
        "anm.sim.engine_2d",
        "anm.sim.renderer_2d",
    ]
    
    # Expansion modules
    EXPANSION_MODULES = [
        "anm.expansion.expansion_engine_v2",
        "anm.expansion.core.novelty_detector",
        "anm.expansion.core.voting_system",
        "anm.expansion.core.metrics",
        "anm.expansion.discovery.multi_source",
        "anm.expansion.code.writer_v2",
        "anm.expansion.code.validator",
        "anm.expansion.training.trainer",
    ]
    
    # Memory modules
    MEMORY_MODULES = [
        "anm.memory.diary_memory",
        "anm.memory.working_memory",
        "anm.memory.episodic_memory",
        "anm.memory.semantic_memory",
        "anm.memory.meta_memory",
    ]
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.issues: List[SanityIssue] = []
        self.checks_run = 0
        self.checks_passed = 0
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            prefix = {
                "INFO": "ℹ️ ",
                "OK": "✅",
                "WARN": "⚠️ ",
                "ERROR": "❌",
                "CRITICAL": "🚨",
            }.get(level, "  ")
            print(f"{prefix} {message}")
    
    def run_full_check(self) -> SanityResult:
        """
        Run all sanity checks.
        
        Returns:
            SanityResult with all issues found
        """
        start_time = time.time()
        self.issues = []
        self.checks_run = 0
        self.checks_passed = 0
        
        if self.verbose:
            print()
            print("=" * 60)
            print("🔍 ANM SANITY CHECK")
            print("=" * 60)
            print()
        
        # Phase 1: Import Checks
        self.log("Phase 1: Import Checks", "INFO")
        self._check_imports()
        
        # Phase 2: Component Instantiation
        self.log("Phase 2: Component Instantiation", "INFO")
        self._check_components()
        
        # Phase 3: Integration Tests
        self.log("Phase 3: Integration Tests", "INFO")
        self._check_integration()
        
        # Phase 4: Config Validation
        self.log("Phase 4: Configuration Validation", "INFO")
        self._check_config()
        
        # Phase 5: Dependency Checks
        self.log("Phase 5: Dependency Checks", "INFO")
        self._check_dependencies()
        
        # Phase 6: Sync Validation
        self.log("Phase 6: Sync Validation", "INFO")
        self._check_sync()
        
        # Build result
        duration_ms = (time.time() - start_time) * 1000
        
        # Determine if passed (no critical/error issues)
        critical_or_errors = [
            i for i in self.issues 
            if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.ERROR)
        ]
        passed = len(critical_or_errors) == 0
        
        result = SanityResult(
            passed=passed,
            issues=self.issues,
            checks_run=self.checks_run,
            checks_passed=self.checks_passed,
            checks_failed=self.checks_run - self.checks_passed,
            duration_ms=duration_ms,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        
        # Print summary
        if self.verbose:
            print()
            print("=" * 60)
            print("📊 SANITY CHECK SUMMARY")
            print("=" * 60)
            print(f"   Checks Run: {result.checks_run}")
            print(f"   Passed: {result.checks_passed}")
            print(f"   Failed: {result.checks_failed}")
            print(f"   Duration: {result.duration_ms:.1f}ms")
            print()
            
            if result.passed:
                print("✅ SANITY CHECK PASSED - ANM is ready!")
            else:
                print(f"❌ SANITY CHECK FAILED - {len(critical_or_errors)} critical/error issues")
                for issue in critical_or_errors:
                    print(f"   • [{issue.category.value}] {issue.message}")
            
            if result.warnings:
                print(f"\n⚠️  {len(result.warnings)} warnings:")
                for issue in result.warnings:
                    print(f"   • {issue.message}")
            
            print("=" * 60)
            print()
        
        return result
    
    def _add_issue(
        self,
        category: IssueCategory,
        severity: IssueSeverity,
        module: str,
        message: str,
        exception: Optional[Exception] = None,
        suggested_fix: Optional[str] = None,
        auto_fixable: bool = False,
        fix_code: Optional[str] = None,
    ) -> None:
        """Add an issue to the list."""
        issue = SanityIssue(
            category=category,
            severity=severity,
            module=module,
            message=message,
            exception=str(exception) if exception else None,
            traceback=traceback.format_exc() if exception else None,
            suggested_fix=suggested_fix,
            auto_fixable=auto_fixable,
            fix_code=fix_code,
        )
        self.issues.append(issue)
        
        level = {
            IssueSeverity.CRITICAL: "CRITICAL",
            IssueSeverity.ERROR: "ERROR",
            IssueSeverity.WARNING: "WARN",
            IssueSeverity.INFO: "INFO",
        }.get(severity, "INFO")
        self.log(f"[{module}] {message}", level)
    
    def _check_import(
        self,
        module_name: str,
        severity: IssueSeverity = IssueSeverity.ERROR,
    ) -> bool:
        """Check if a module can be imported."""
        self.checks_run += 1
        try:
            importlib.import_module(module_name)
            self.checks_passed += 1
            return True
        except Exception as e:
            self._add_issue(
                category=IssueCategory.IMPORT,
                severity=severity,
                module=module_name,
                message=f"Failed to import: {e}",
                exception=e,
                suggested_fix=f"Check if {module_name} exists and has no syntax errors",
                auto_fixable=True,
            )
            return False
    
    def _check_imports(self) -> None:
        """Check all module imports."""
        # Core modules (CRITICAL)
        for module in self.CORE_MODULES:
            self._check_import(module, IssueSeverity.CRITICAL)
        
        # Specialist modules (ERROR)
        for module in self.SPECIALIST_MODULES:
            self._check_import(module, IssueSeverity.ERROR)
        
        # Optional modules (WARNING)
        for module in self.OPTIONAL_MODULES:
            self._check_import(module, IssueSeverity.WARNING)
        
        # Expansion modules (ERROR)
        for module in self.EXPANSION_MODULES:
            self._check_import(module, IssueSeverity.ERROR)
        
        # Memory modules (ERROR)
        for module in self.MEMORY_MODULES:
            self._check_import(module, IssueSeverity.ERROR)
    
    def _check_components(self) -> None:
        """Check if core components can be instantiated."""
        components_to_check = [
            ("anm.expansion.core.novelty_detector", "NoveltyDetectorV2", {}),
            ("anm.expansion.core.voting_system", "VotingSystemV2", {}),
            ("anm.expansion.core.metrics", "ExpansionMetrics", {}),
            ("anm.expansion.discovery.multi_source", "MultiSourceDiscovery", {}),
            ("anm.expansion.code.validator", "CodeValidator", {}),
            ("anm.expansion.training.trainer", "LoRATrainer", {}),
        ]
        
        for module_name, class_name, kwargs in components_to_check:
            self.checks_run += 1
            try:
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                instance = cls(**kwargs)
                self.checks_passed += 1
            except Exception as e:
                self._add_issue(
                    category=IssueCategory.INSTANTIATION,
                    severity=IssueSeverity.ERROR,
                    module=f"{module_name}.{class_name}",
                    message=f"Failed to instantiate: {e}",
                    exception=e,
                    suggested_fix=f"Check {class_name} constructor in {module_name}",
                    auto_fixable=True,
                )
    
    def _check_integration(self) -> None:
        """Check if components integrate properly."""
        # Test Router can be created with all specialists
        self.checks_run += 1
        try:
            from anm.router.router import Router
            router = Router({})
            
            # Check router has required methods and handlers
            required_methods = [
                "handle",
            ]
            
            for method in required_methods:
                if not hasattr(router, method):
                    raise AttributeError(f"Router missing method: {method}")
            
            # Check for handler objects (refactored from methods)
            required_handlers = [
                "novelty_handler",
                "voting_handler", 
                "expansion_handler",
            ]
            
            for handler in required_handlers:
                if not hasattr(router, handler):
                    raise AttributeError(f"Router missing handler: {handler}")
            
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.INTEGRATION,
                severity=IssueSeverity.CRITICAL,
                module="anm.router.router.Router",
                message=f"Router integration failed: {e}",
                exception=e,
                suggested_fix="Check Router class and its dependencies",
                auto_fixable=True,
            )
        
        # Test Expansion Engine can be created
        self.checks_run += 1
        try:
            from anm.expansion import ExpansionEngineV2, ExpansionConfig
            engine = ExpansionEngineV2(ExpansionConfig())
            
            # Check engine has required components
            required_attrs = [
                "novelty_detector",
                "voting_system",
                "metrics",
                "discovery",
                "code_writer",
            ]
            
            for attr in required_attrs:
                if not hasattr(engine, attr):
                    raise AttributeError(f"ExpansionEngineV2 missing: {attr}")
            
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.INTEGRATION,
                severity=IssueSeverity.ERROR,
                module="anm.expansion.ExpansionEngineV2",
                message=f"Expansion Engine integration failed: {e}",
                exception=e,
                suggested_fix="Check ExpansionEngineV2 and its dependencies",
                auto_fixable=True,
            )
        
        # Test NoveltyDetector actually works
        self.checks_run += 1
        try:
            from anm.expansion import NoveltyDetectorV2
            detector = NoveltyDetectorV2()
            result = detector.detect("Test query for sanity check")
            
            if not hasattr(result, "requires_new_domain"):
                raise AttributeError("NoveltyResult missing requires_new_domain")
            if not hasattr(result, "confidence"):
                raise AttributeError("NoveltyResult missing confidence")
            
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.INTEGRATION,
                severity=IssueSeverity.ERROR,
                module="anm.expansion.NoveltyDetectorV2",
                message=f"Novelty detection failed: {e}",
                exception=e,
                suggested_fix="Check NoveltyDetectorV2.detect() method",
                auto_fixable=True,
            )
    
    def _check_config(self) -> None:
        """Check configuration is valid."""
        self.checks_run += 1
        try:
            from anm.config.settings import get_config
            config = get_config()
            
            # Config should be a dict
            if not isinstance(config, dict):
                raise TypeError(f"Config should be dict, got {type(config)}")
            
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.CONFIG,
                severity=IssueSeverity.ERROR,
                module="anm.config.settings",
                message=f"Config validation failed: {e}",
                exception=e,
                suggested_fix="Check settings.py get_config() function",
                auto_fixable=False,
            )
    
    def _check_dependencies(self) -> None:
        """Check external dependencies."""
        optional_deps = [
            ("huggingface_hub", "HuggingFace dataset downloading"),
            ("sentence_transformers", "Semantic embeddings for novelty detection"),
            ("torch", "LoRA/QLoRA training"),
            ("transformers", "Model fine-tuning"),
        ]
        
        for dep_name, purpose in optional_deps:
            self.checks_run += 1
            try:
                importlib.import_module(dep_name)
                self.checks_passed += 1
            except Exception as e:
                # Catch all exceptions (ImportError, slow imports, etc.)
                # These are optional dependencies, so any failure is just informational
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else error_type
                
                # For ImportError, use the original message format
                if isinstance(e, ImportError):
                    message = f"Optional dependency not installed: {dep_name} ({purpose})"
                else:
                    # For other exceptions (slow imports, etc.), include error details
                    message = f"Optional dependency not available: {dep_name} ({purpose}) - {error_type}: {error_msg[:100]}"
                
                self._add_issue(
                    category=IssueCategory.DEPENDENCY,
                    severity=IssueSeverity.INFO,
                    module=dep_name,
                    message=message,
                    suggested_fix=f"pip install {dep_name}",
                    auto_fixable=False,
                )
                self.checks_passed += 1  # Optional, so still counts as pass
    
    def _check_sync(self) -> None:
        """Check if all components are in sync."""
        # Check ANM main interface exports everything
        self.checks_run += 1
        try:
            from anm import (
                ANM,
                Router,
                GeneralLLM,
                MathLLM,
                PhysicsLLM,
                ExpansionEngineV2,
                NoveltyDetectorV2,
            )
            
            # Check ANM class (skip sanity check to avoid recursion)
            anm = ANM(skip_sanity_check=True)
            if not hasattr(anm, "query"):
                raise AttributeError("ANM missing query() method")
            if not hasattr(anm, "expand"):
                raise AttributeError("ANM missing expand() method")
            
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.SYNC,
                severity=IssueSeverity.ERROR,
                module="anm",
                message=f"Main ANM interface out of sync: {e}",
                exception=e,
                suggested_fix="Check anm/__init__.py exports",
                auto_fixable=True,
            )
        
        # Check specialists module exports
        self.checks_run += 1
        try:
            from anm.specialists import (
                GeneralLLM,
                MathLLM,
                PhysicsLLM,
                CodeLLM,
                ChemistryLLM,
                BiologyLLM,
            )
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.SYNC,
                severity=IssueSeverity.ERROR,
                module="anm.specialists",
                message=f"Specialists module out of sync: {e}",
                exception=e,
                suggested_fix="Check anm/specialists/__init__.py exports",
                auto_fixable=True,
            )
        
        # Check expansion module exports
        self.checks_run += 1
        try:
            from anm.expansion import (
                ExpansionEngineV2,
                ExpansionConfig,
                NoveltyDetectorV2,
                VotingSystemV2,
                MultiSourceDiscovery,
                CodeWriterV2,
                LoRATrainer,
                HuggingFaceDatasetDownloader,
            )
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.SYNC,
                severity=IssueSeverity.ERROR,
                module="anm.expansion",
                message=f"Expansion module out of sync: {e}",
                exception=e,
                suggested_fix="Check anm/expansion/__init__.py exports",
                auto_fixable=True,
            )
        
        # Check memory module exports
        self.checks_run += 1
        try:
            from anm.memory import (
                DiaryMemory,
                WorkingMemory,
                EpisodicMemory,
            )
            self.checks_passed += 1
        except Exception as e:
            self._add_issue(
                category=IssueCategory.SYNC,
                severity=IssueSeverity.ERROR,
                module="anm.memory",
                message=f"Memory module out of sync: {e}",
                exception=e,
                suggested_fix="Check anm/memory/__init__.py exports",
                auto_fixable=True,
            )


def run_sanity_check(verbose: bool = True) -> SanityResult:
    """Convenience function to run sanity check."""
    checker = SanityChecker(verbose=verbose)
    return checker.run_full_check()


if __name__ == "__main__":
    # Allow running directly for testing
    result = run_sanity_check()
    sys.exit(0 if result.passed else 1)
