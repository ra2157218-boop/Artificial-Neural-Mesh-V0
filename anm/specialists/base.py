# ============================================================
#  ANM V0-OpenSource — Base Specialist
#  Unified Interface for All Domain Specialists
# ============================================================

"""
ANM Base Specialist - Common interface for all specialists.

All specialists inherit from BaseSpecialist which provides:
- Unified run() interface
- Common output cleaning
- WOT_REQUEST handling
- Meta block generation
- Memory logging
- Quality tracking
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import re

# Import the new inference engine
from anm.system.inference import run_model

# Import common utilities
from anm.utils.wot_utils import extract_wot_request, ensure_wot_request
from anm.utils.output_utils import clean_output, estimate_confidence

__all__ = [
    "BaseSpecialist",
    "SpecialistConfig",
    "SpecialistResult",
    "SpecialistDomain",
    "run_model",
]


class SpecialistDomain(Enum):
    """All specialist domains."""
    GENERAL = "general"
    MATH = "math"
    PHYSICS = "physics"
    CODE = "code"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    MEMORY = "memory"
    RESEARCH = "research"
    FACTS = "facts"
    SIMULATION = "simulation"
    IMAGE = "image"
    SOUND = "sound"
    INTERNET = "internet"


@dataclass
class SpecialistConfig:
    """Configuration for specialists."""
    max_tokens: int = 2048  # Reasonable limit - model context is 4096, leave room for prompt
    max_output_length: int = 100000
    clean_thinking_tags: bool = True
    require_wot_request: bool = True


@dataclass
class SpecialistResult:
    """Result from specialist processing."""
    output: str
    domain: SpecialistDomain
    wot_request: str
    confidence: float
    processing_time_ms: float
    success: bool
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# run_model is imported from anm.system.inference
# It provides direct model loading via llama-cpp-python
# with GPU acceleration (Metal/CUDA) and automatic model downloading


class BaseSpecialist(ABC):
    """
    Base class for all ANM specialists.
    
    Provides unified interface for:
    - Query processing
    - Output cleaning
    - WOT_REQUEST handling
    - Meta block generation
    - Memory logging
    
    Subclasses must implement:
    - domain: The specialist's domain
    - _get_system_prompt(): Domain-specific system prompt
    - _process(): Optional custom processing
    """
    
    # Version for all specialists
    VERSION = "0.1.0-opensource"
    
    def __init__(
        self,
        config: Optional[SpecialistConfig] = None,
        gre: Optional[Any] = None,
        selfaware: Optional[Any] = None,
        working_memory: Optional[Any] = None,
        meta_memory: Optional[Any] = None,
    ) -> None:
        self.config = config or SpecialistConfig()
        
        # Meta modules (optional)
        self.gre = gre
        self.selfaware = selfaware
        self.working_memory = working_memory
        self.meta_memory = meta_memory
        
        # Efficiency tracking
        self._last_efficiency_metrics: Optional[Dict[str, Any]] = None
        
        # Build system prompt
        self._system_prompt = self._build_system_prompt()
    
    @property
    @abstractmethod
    def domain(self) -> SpecialistDomain:
        """Return the specialist's domain."""
        ...
    
    @property
    def domain_name(self) -> str:
        """Return domain name as string."""
        return self.domain.value
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return domain-specific system prompt."""
        ...
    
    def _build_system_prompt(self) -> str:
        """Build complete system prompt with common elements."""
        base = self._get_system_prompt()
        
        common = f"""

=== ANM V0-OpenSource {self.domain_name.upper()} SPECIALIST ===

COMMON RULES:
1. Process the WoT packet and provide domain-specific reasoning
2. Be honest about limitations and uncertainties
3. DO NOT fabricate data, citations, or facts
4. End with exactly one: WOT_REQUEST: <DOMAIN or NONE>

WOT ROUTING:
- Need math/derivations → WOT_REQUEST: MATH
- Need physics analysis → WOT_REQUEST: PHYSICS  
- Need code/algorithms → WOT_REQUEST: CODE
- Need chemistry → WOT_REQUEST: CHEMISTRY
- Need biology → WOT_REQUEST: BIOLOGY
- Need web search → WOT_REQUEST: INTERNET
- Need fact checking → WOT_REQUEST: FACTS
- Need memory/diary → WOT_REQUEST: MEMORY
- Need simulation → WOT_REQUEST: SIMULATION
- Satisfied/done → WOT_REQUEST: NONE
"""
        return base + common
    
    def run(self, wot_packet: str) -> str:
        """
        Main entry point for processing.
        
        Args:
            wot_packet: The WoT packet containing query and context
            
        Returns:
            Processed output with WOT_REQUEST
        """
        start_time = time.perf_counter()
        
        # Build prompt
        prompt = self._build_prompt(wot_packet)
        prompt_length = len(prompt)
        
        # #region agent log
        import json
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "base.py:run", "message": "Prompt built", "data": {"domain": self.domain_name, "prompt_length": prompt_length, "prompt_preview": prompt[:300] if prompt else "EMPTY", "wot_packet_length": len(wot_packet) if wot_packet else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        # Run LLM using direct model loading
        raw_output = run_model(prompt, max_tokens=self.config.max_tokens)
        
        # #region agent log
        import json
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "base.py:run", "message": "Raw output from model", "data": {"domain": self.domain_name, "raw_output_length": len(raw_output) if raw_output else 0, "raw_output_preview": raw_output[:100] if raw_output else "EMPTY", "is_empty": not raw_output or not raw_output.strip()}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        # Clean output
        cleaned = self._clean_output(raw_output)
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "base.py:run", "message": "Cleaned output", "data": {"domain": self.domain_name, "cleaned_length": len(cleaned) if cleaned else 0, "cleaned_preview": cleaned[:100] if cleaned else "EMPTY", "has_no_output_marker": "[produced no output]" in cleaned if cleaned else False}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
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
    
    def run_full(self, wot_packet: str) -> SpecialistResult:
        """
        Run with full result metadata.
        """
        start_time = time.perf_counter()
        
        output = self.run(wot_packet)
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Extract WOT_REQUEST
        wot_request = self._extract_wot_request(output)
        
        # Estimate confidence
        confidence = self._estimate_confidence(output)
        
        # Check for errors
        errors = []
        if "[ERROR" in output:
            errors.append("LLM error detected")
        
        return SpecialistResult(
            output=output,
            domain=self.domain,
            wot_request=wot_request,
            confidence=confidence,
            processing_time_ms=processing_time,
            success=len(errors) == 0,
            errors=errors,
        )
    
    def _build_prompt(self, wot_packet: str) -> str:
        """Build the full prompt."""
        return (
            self._system_prompt
            + f"\n\n--- WoT PACKET ({self.domain_name.upper()} VIEW) ---\n"
            + wot_packet
            + f"\n\nProvide your {self.domain_name} reasoning and end with WOT_REQUEST."
        )
    
    def _clean_output(self, text: str) -> str:
        """Clean LLM output using common utilities."""
        if not text:
            return f"[{self.domain_name.upper()} produced no output]\nWOT_REQUEST: NONE"
        
        # Use centralized cleaning utility
        cleaned = clean_output(
            text,
            domain_name=self.domain_name,
            clean_thinking=self.config.clean_thinking_tags,
            remove_role_prefixes=True,
        )
        
        return cleaned
    
    def _ensure_wot_request(self, text: str) -> str:
        """Ensure output has WOT_REQUEST using common utility."""
        default = "NONE"
        return ensure_wot_request(text, default=default, require=self.config.require_wot_request)
    
    def _extract_wot_request(self, text: str) -> str:
        """Extract WOT_REQUEST value using common utility."""
        return extract_wot_request(text)
    
    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence from output using common utility."""
        return estimate_confidence(text)
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta information block."""
        lines = []
        
        # Domain health
        awareness = self._get_self_awareness(text)
        
        # Extract confidence from output if present
        confidence_from_output = self._extract_confidence_from_output(text)
        if confidence_from_output:
            awareness['confidence'] = confidence_from_output
        
        # Extract efficiency from output if present
        efficiency_from_output = self._extract_efficiency_from_output(text)
        
        lines.append("[DOMAIN_HEALTH]")
        lines.append(f"domain: {self.domain_name}")
        lines.append(f"confidence: {awareness.get('confidence', 'unknown')}")
        lines.append(f"uncertainty: {awareness.get('uncertainty', 'unknown')}")
        lines.append(f"confidence_score: {self._estimate_confidence(text):.2f}")
        lines.append(f"version: {self.VERSION}")
        
        # Efficiency metrics
        if hasattr(self, '_last_efficiency_metrics') and self._last_efficiency_metrics:
            eff = self._last_efficiency_metrics
            lines.append("")
            lines.append("[EFFICIENCY_METRICS]")
            lines.append(f"efficiency_score: {eff.get('efficiency_score', 0.5):.2f}")
            lines.append(f"efficiency_self_assessment: {efficiency_from_output or 'not_provided'}")
            lines.append(f"tokens_per_ms: {eff.get('tokens_per_ms', 0.0):.2f}")
            lines.append(f"output_tokens: {eff.get('output_tokens', 0)}")
            lines.append(f"prompt_tokens: {eff.get('prompt_tokens', 0)}")
            lines.append(f"total_tokens: {eff.get('total_tokens', 0)}")
            lines.append(f"processing_time_ms: {eff.get('processing_time_ms', 0.0):.1f}")
        
        # GRE check
        gre_result = self._check_gre(text)
        lines.append("")
        lines.append("[GLOBAL_RULES]")
        lines.append(f"passed: {gre_result.get('passed', True)}")
        lines.append(f"risk_level: {gre_result.get('risk_level', 'low')}")
        violations = gre_result.get('violations', [])
        lines.append(f"violations: {', '.join(violations) if violations else 'none'}")
        
        return "\n".join(lines)
    
    def _extract_confidence_from_output(self, text: str) -> Optional[str]:
        """Extract CONFIDENCE value from output if present."""
        if not text:
            return None
        
        # Look for CONFIDENCE: HIGH|MEDIUM|LOW pattern
        match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def _extract_efficiency_from_output(self, text: str) -> Optional[str]:
        """Extract EFFICIENCY value from output if present."""
        if not text:
            return None
        
        # Look for EFFICIENCY: EFFICIENT|INEFFICIENT pattern
        match = re.search(r'EFFICIENCY:\s*(EFFICIENT|INEFFICIENT)', text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def _calculate_efficiency_metrics(
        self, 
        text: str, 
        prompt_length: int, 
        processing_time_ms: float
    ) -> Dict[str, Any]:
        """Calculate efficiency metrics."""
        if not text or processing_time_ms <= 0:
            return {
                "efficiency_score": 0.5,
                "tokens_per_ms": 0.0,
                "output_length": 0,
                "prompt_length": prompt_length,
                "processing_time_ms": processing_time_ms,
            }
        
        # Estimate tokens (rough: ~3.5 chars per token)
        output_tokens = int(len(text) / 3.5)
        prompt_tokens = int(prompt_length / 3.5)
        total_tokens = output_tokens + prompt_tokens
        
        # Calculate tokens per millisecond
        tokens_per_ms = total_tokens / processing_time_ms if processing_time_ms > 0 else 0.0
        
        # Efficiency score (0.0-1.0)
        # Higher score = more efficient (concise output, fast processing)
        # Penalize: very long outputs, very slow processing, redundant content
        
        efficiency_score = 0.7  # Base score
        
        # Check for efficiency markers in output
        efficiency_from_output = self._extract_efficiency_from_output(text)
        if efficiency_from_output == "EFFICIENT":
            efficiency_score += 0.2
        elif efficiency_from_output == "INEFFICIENT":
            efficiency_score -= 0.3
        
        # Penalize very long outputs (relative to prompt)
        if output_tokens > prompt_tokens * 3:
            efficiency_score -= 0.2
        
        # Penalize very slow processing
        if processing_time_ms > 5000:  # > 5 seconds
            efficiency_score -= 0.1
        
        # Check for redundancy indicators
        lower = text.lower()
        redundancy_markers = ["as mentioned", "as stated", "as previously", "again", "repeated"]
        redundancy_count = sum(1 for m in redundancy_markers if m in lower)
        if redundancy_count >= 3:
            efficiency_score -= 0.15
        
        # Reward concise outputs for simple queries
        if len(text) < 200 and processing_time_ms < 2000:
            efficiency_score += 0.1
        
        return {
            "efficiency_score": max(0.0, min(1.0, efficiency_score)),
            "tokens_per_ms": tokens_per_ms,
            "output_tokens": output_tokens,
            "prompt_tokens": prompt_tokens,
            "total_tokens": total_tokens,
            "output_length": len(text),
            "prompt_length": prompt_length,
            "processing_time_ms": processing_time_ms,
        }
    
    def _get_self_awareness(self, text: str) -> Dict[str, Any]:
        """Get self-awareness analysis."""
        if self.selfaware:
            try:
                result = self.selfaware.analyze(self.domain_name, text)
                if isinstance(result, dict):
                    return result
            except Exception:
                pass
        
        # Fallback: simple heuristic
        lower = text.lower()
        
        confidence = "high"
        if any(w in lower for w in ["uncertain", "not sure", "maybe"]):
            confidence = "medium"
        if any(w in lower for w in ["don't know", "cannot determine"]):
            confidence = "low"
        
        uncertainty = "low"
        if any(w in lower for w in ["possibly", "might", "could be"]):
            uncertainty = "medium"
        if any(w in lower for w in ["unknown", "unclear", "ambiguous"]):
            uncertainty = "high"
        
        return {"confidence": confidence, "uncertainty": uncertainty}
    
    def _check_gre(self, text: str) -> Dict[str, Any]:
        """Check global rules."""
        if self.gre:
            try:
                return self.gre.analyze(text, module_name=f"{self.domain_name.title()}LLM")
            except Exception:
                pass
        
        # Default: passed
        return {"passed": True, "risk_level": "low", "violations": []}
    
    def _attach_meta(self, cleaned: str, meta: str) -> str:
        """Attach meta block before WOT_REQUEST."""
        lines = cleaned.split("\n")
        body = []
        wot_line = None
        
        for ln in lines:
            if ln.strip().startswith("WOT_REQUEST:"):
                wot_line = ln
            else:
                body.append(ln)
        
        if wot_line is None:
            wot_line = "WOT_REQUEST: NONE"
        
        return "\n".join(body) + "\n\n" + meta + "\n\n" + wot_line
    
    def _log_to_memory(self, output: str, processing_time: float) -> None:
        """Log to working memory."""
        if self.working_memory:
            try:
                self.working_memory.add(
                    domain=self.domain_name,
                    note=f"{self.domain_name.title()}LLM processed packet",
                    meta={
                        "processing_time_ms": processing_time,
                        "output_length": len(output),
                    },
                )
            except Exception:
                pass
