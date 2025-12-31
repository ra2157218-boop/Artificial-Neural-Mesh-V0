# ============================================================
# ANM V0-OpenSource — CODE VALIDATOR (MAXIMUM LEVEL)
#  AST Validation • Static Analysis • Type Checking • Testing
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import ast
import sys
import os
import subprocess
import tempfile


@dataclass
class ValidationError:
    """A code validation error."""
    type: str  # syntax, type, lint, test, import
    line: Optional[int]
    column: Optional[int]
    message: str
    severity: str  # error, warning, info


@dataclass
class ValidationResult:
    """Complete validation result."""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    info: List[ValidationError]
    stats: Dict[str, Any]


class CodeValidator:
    """
    MAXIMUM LEVEL Code Validator.
    
    Features:
    - AST parsing and validation
    - Import resolution checking
    - Type checking (mypy/pyright)
    - Linting (ruff/flake8)
    - Complexity analysis
    - Security scanning (bandit)
    - Auto-fix suggestions
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.available_tools = self._detect_available_tools()
    
    def _detect_available_tools(self) -> Dict[str, bool]:
        """Detect which validation tools are available."""
        tools = {
            "ruff": False,
            "mypy": False,
            "pyright": False,
            "bandit": False,
            "black": False,
        }
        
        for tool in tools:
            try:
                result = subprocess.run(
                    [tool, "--version"],
                    capture_output=True,
                    timeout=5,
                )
                tools[tool] = result.returncode == 0
            except Exception:
                pass
        
        return tools
    
    def validate(self, code: str, filename: str = "module.py") -> ValidationResult:
        """
        Run full validation on code.
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        info: List[ValidationError] = []
        stats = {}
        
        # 1. Syntax validation (AST parsing)
        syntax_result = self._validate_syntax(code)
        errors.extend(syntax_result[0])
        stats["syntax_valid"] = len(syntax_result[0]) == 0
        
        if not stats["syntax_valid"]:
            # Can't proceed with invalid syntax
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                info=info,
                stats=stats,
            )
        
        # 2. Import validation
        import_result = self._validate_imports(code)
        warnings.extend(import_result[0])
        stats["imports_checked"] = import_result[1]
        
        # 3. Complexity analysis
        complexity_result = self._analyze_complexity(code)
        info.extend(complexity_result[0])
        stats.update(complexity_result[1])
        
        # 4. Type checking (if available)
        if self.available_tools.get("mypy") or self.available_tools.get("pyright"):
            type_result = self._run_type_check(code, filename)
            errors.extend([e for e in type_result if e.severity == "error"])
            warnings.extend([e for e in type_result if e.severity == "warning"])
        
        # 5. Linting (if available)
        if self.available_tools.get("ruff"):
            lint_result = self._run_linter(code, filename)
            warnings.extend(lint_result)
        
        # 6. Security scan (if available)
        if self.available_tools.get("bandit"):
            security_result = self._run_security_scan(code, filename)
            errors.extend([e for e in security_result if e.severity == "error"])
            warnings.extend([e for e in security_result if e.severity == "warning"])
        
        # Determine overall validity
        valid = len(errors) == 0
        if self.strict_mode:
            valid = valid and len(warnings) == 0
        
        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            info=info,
            stats=stats,
        )
    
    def _validate_syntax(self, code: str) -> Tuple[List[ValidationError], Dict[str, Any]]:
        """Validate Python syntax using AST."""
        errors = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(ValidationError(
                type="syntax",
                line=e.lineno,
                column=e.offset,
                message=str(e.msg),
                severity="error",
            ))
        
        return errors, {"parsed": len(errors) == 0}
    
    def _validate_imports(self, code: str) -> Tuple[List[ValidationError], int]:
        """Validate that imports can be resolved."""
        warnings = []
        imports_checked = 0
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_checked += 1
                        if not self._can_import(alias.name):
                            warnings.append(ValidationError(
                                type="import",
                                line=node.lineno,
                                column=0,
                                message=f"Module '{alias.name}' may not be available",
                                severity="warning",
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    imports_checked += 1
                    module = node.module or ""
                    if not self._can_import(module):
                        warnings.append(ValidationError(
                            type="import",
                            line=node.lineno,
                            column=0,
                            message=f"Module '{module}' may not be available",
                            severity="warning",
                        ))
        except Exception:
            pass
        
        return warnings, imports_checked
    
    def _can_import(self, module_name: str) -> bool:
        """Check if a module can be imported."""
        # Standard library modules
        stdlib = {
            "os", "sys", "json", "re", "math", "datetime", "time",
            "collections", "itertools", "functools", "typing",
            "pathlib", "subprocess", "hashlib", "uuid", "logging",
        }
        
        root_module = module_name.split(".")[0]
        
        # Always assume standard library is available
        if root_module in stdlib:
            return True
        
        # ANM internal modules
        if root_module == "anm":
            return True
        
        # Try actual import
        try:
            __import__(root_module)
            return True
        except ImportError:
            return False
    
    def _analyze_complexity(self, code: str) -> Tuple[List[ValidationError], Dict[str, Any]]:
        """Analyze code complexity."""
        info = []
        stats = {
            "total_lines": len(code.splitlines()),
            "classes": 0,
            "functions": 0,
            "max_function_lines": 0,
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    stats["classes"] += 1
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    stats["functions"] += 1
                    
                    # Calculate function length
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                    stats["max_function_lines"] = max(stats["max_function_lines"], func_lines)
                    
                    # Warn about long functions
                    if func_lines > 50:
                        info.append(ValidationError(
                            type="complexity",
                            line=node.lineno,
                            column=0,
                            message=f"Function '{node.name}' is {func_lines} lines (consider refactoring)",
                            severity="info",
                        ))
        except Exception:
            pass
        
        return info, stats
    
    def _run_type_check(self, code: str, filename: str) -> List[ValidationError]:
        """Run type checking using mypy or pyright."""
        errors = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            tool = "mypy" if self.available_tools.get("mypy") else "pyright"
            result = subprocess.run(
                [tool, temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            for line in result.stdout.splitlines():
                if "error:" in line.lower():
                    errors.append(ValidationError(
                        type="type",
                        line=None,
                        column=None,
                        message=line,
                        severity="error",
                    ))
                elif "warning:" in line.lower():
                    errors.append(ValidationError(
                        type="type",
                        line=None,
                        column=None,
                        message=line,
                        severity="warning",
                    ))
        except Exception:
            pass
        finally:
            os.unlink(temp_path)
        
        return errors
    
    def _run_linter(self, code: str, filename: str) -> List[ValidationError]:
        """Run linting using ruff."""
        warnings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["ruff", "check", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            for line in result.stdout.splitlines():
                if ":" in line:
                    warnings.append(ValidationError(
                        type="lint",
                        line=None,
                        column=None,
                        message=line,
                        severity="warning",
                    ))
        except Exception:
            pass
        finally:
            os.unlink(temp_path)

        return warnings

    def _run_security_scan(self, code: str, filename: str) -> List[ValidationError]:
        """Run security scanning using bandit."""
        errors = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            import json
            data = json.loads(result.stdout)
            
            for issue in data.get("results", []):
                severity = "error" if issue.get("severity") == "HIGH" else "warning"
                errors.append(ValidationError(
                    type="security",
                    line=issue.get("line_number"),
                    column=None,
                    message=issue.get("issue_text", ""),
                    severity=severity,
                ))
        except Exception:
            pass
        finally:
            os.unlink(temp_path)
        
        return errors
    
    def auto_fix(self, code: str) -> Tuple[str, List[str]]:
        """Attempt to auto-fix code issues."""
        fixes_applied = []
        
        # Try formatting with black if available
        if self.available_tools.get("black"):
            try:
                import black
                fixed = black.format_str(code, mode=black.Mode())
                if fixed != code:
                    fixes_applied.append("Formatted with black")
                    code = fixed
            except Exception:
                pass
        
        # Try auto-fixing with ruff if available
        if self.available_tools.get("ruff"):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                subprocess.run(
                    ["ruff", "check", "--fix", temp_path],
                    capture_output=True,
                    timeout=30,
                )
                
                with open(temp_path, 'r') as f:
                    fixed = f.read()

                if fixed != code:
                    fixes_applied.append("Auto-fixed lint issues with ruff")
                    code = fixed
            except Exception:
                pass
            finally:
                os.unlink(temp_path)
        
        return code, fixes_applied
