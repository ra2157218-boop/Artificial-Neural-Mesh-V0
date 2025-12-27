# ============================================================
#  ANM V0-OpenSource — Code Specialist
#  Programming & Software Engineering
# ============================================================

"""
ANM Code Specialist - Programming and software engineering.

Capabilities:
- Code generation and review
- Algorithm design
- Debugging assistance
- Multiple language support
- Best practices guidance
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import re

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
)

try:
    from anm.utils.prompts import CODE_PROMPT
except ImportError:
    CODE_PROMPT = ""

# Import domain-specific inference
from anm.system.inference import run_model

__all__ = ["CodeLLM"]


class CodeLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Code Specialist.
    
    Handles programming tasks including:
    - Code generation
    - Code review and debugging
    - Algorithm design
    - Architecture planning
    - Best practices
    
    Supported languages:
    - Python, JavaScript, TypeScript
    - C, C++, Rust, Go
    - Java, Kotlin, Swift
    - SQL, Shell/Bash
    - And more...
    
    Safety:
    - No malicious code generation
    - No destructive operations
    - Security-aware suggestions
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.CODE
    
    def _get_system_prompt(self) -> str:
        # Use CODE_PROMPT from prompts.py (single source of truth)
        # CODE_PROMPT already includes META-COGNITION, META-EFFICIENCY, and OUTPUT format
        return CODE_PROMPT if CODE_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with code-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Code-specific analysis
        languages = self._detect_languages(text)
        code_blocks = self._extract_code_blocks(text)
        security = self._check_security(text)
        
        # Calculate total lines (must be outside f-string due to backslash restriction)
        newline = '\n'
        total_lines = sum(len(b.split(newline)) for b in code_blocks)
        
        code_meta = [
            "",
            "[CODE_ANALYSIS]",
            f"languages: {', '.join(languages) if languages else 'none'}",
            f"code_blocks: {len(code_blocks)}",
            f"total_lines: {total_lines}",
            f"security_check: {security}",
            f"has_tests: {self._has_tests(text)}",
            f"has_docs: {self._has_documentation(text)}",
        ]
        
        return base_meta + "\n".join(code_meta)
    
    def _detect_languages(self, text: str) -> List[str]:
        """Detect programming languages in text."""
        languages = []
        
        # Check code block headers
        for match in re.finditer(r'```(\w+)', text):
            lang = match.group(1).lower()
            if lang not in languages:
                languages.append(lang)
        
        # Check for language-specific patterns
        patterns = {
            "python": [r'\bdef \w+\(', r'\bimport \w+', r'\bclass \w+:'],
            "javascript": [r'\bfunction \w+\(', r'\bconst \w+ =', r'\blet \w+ ='],
            "typescript": [r': \w+\[\]', r'interface \w+', r': Promise<'],
            "rust": [r'\bfn \w+\(', r'\blet mut \w+', r'\bimpl \w+'],
            "go": [r'\bfunc \w+\(', r'\bpackage \w+', r'\bvar \w+ \w+'],
            "java": [r'\bpublic class', r'\bprivate \w+ \w+', r'\bSystem\.out'],
            "cpp": [r'#include <', r'\bstd::', r'\bint main\('],
            "sql": [r'\bSELECT .+ FROM', r'\bINSERT INTO', r'\bCREATE TABLE'],
        }
        
        for lang, pats in patterns.items():
            if lang not in languages:
                if any(re.search(p, text, re.IGNORECASE) for p in pats):
                    languages.append(lang)
        
        return languages
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from text."""
        blocks = []
        
        # Fenced code blocks
        for match in re.finditer(r'```[\w]*\n?(.*?)```', text, re.DOTALL):
            blocks.append(match.group(1).strip())
        
        return blocks
    
    def _check_security(self, text: str) -> str:
        """Check for security issues."""
        lower = text.lower()
        
        # Critical issues
        critical = [
            "rm -rf /",
            "drop database",
            "drop table",
            "eval(input",
            "exec(input",
            "__import__",
            "os.system(input",
        ]
        
        # Warnings
        warnings = [
            "password =",
            "api_key =",
            "secret =",
            "eval(",
            "exec(",
            "pickle.loads",
        ]
        
        if any(c in lower for c in critical):
            return "CRITICAL_ISSUES"
        if any(w in lower for w in warnings):
            return "WARNINGS"
        return "CLEAN"
    
    def _has_tests(self, text: str) -> bool:
        """Check if code includes tests."""
        lower = text.lower()
        test_markers = [
            "def test_",
            "unittest",
            "pytest",
            "@test",
            "describe(",
            "it(",
            "expect(",
            "assert",
        ]
        return any(m in lower for m in test_markers)
    
    def _has_documentation(self, text: str) -> bool:
        """Check if code includes documentation."""
        # Docstrings
        if '"""' in text or "'''" in text:
            return True
        
        # JSDoc
        if "/**" in text and "*/" in text:
            return True
        
        # Significant comments
        comment_lines = len(re.findall(r'^\s*[#//]', text, re.MULTILINE))
        total_lines = len(text.split('\n'))
        
        return comment_lines / max(total_lines, 1) > 0.1
    
    def run(self, wot_packet: str) -> str:
        """
        Override run method to use Stable-Code-3B instead of default model.
        
        CodeLLM uses Stable-Code-3B, a specialized code generation model,
        instead of the default DeepSeek-R1-1.5B model used by other specialists.
        
        Args:
            wot_packet: The WoT packet containing query and context
            
        Returns:
            Processed output with WOT_REQUEST
        """
        import time
        start_time = time.perf_counter()
        
        # Build prompt
        prompt = self._build_prompt(wot_packet)
        prompt_length = len(prompt)
        
        # Run LLM using domain-specific model (Stable-Code-3B for code domain)
        # This uses a separate inference engine instance specifically for code tasks
        raw_output = run_model(prompt, max_tokens=self.config.max_tokens, domain="code")
        
        # Clean output
        cleaned = self._clean_output(raw_output)
        
        # Ensure WOT_REQUEST
        cleaned = self._ensure_wot_request(cleaned)
        
        # Calculate processing time
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(
            cleaned, prompt_length, processing_time
        )
        
        # Store efficiency metrics for meta block
        self._last_efficiency_metrics = efficiency_metrics
        
        # Build meta block (now includes efficiency)
        meta_text = self._build_meta_block(cleaned)
        
        # Combine
        final = self._attach_meta(cleaned, meta_text)
        
        # Log to memory
        self._log_to_memory(final, processing_time)
        
        return final
