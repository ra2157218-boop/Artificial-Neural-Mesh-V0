# ============================================================
# ANM V0-OpenSource — WoT Execution Strategy Base Class
# ============================================================

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from anm.wot.wot_engine_v15 import TrueWoTMax, WoTResult
# Runtime import deferred to avoid circular dependency
# WoTResult is only used in type annotations (which are strings)


class WoTExecutionStrategy(ABC):
    """
    Base class for WoT execution strategies.
    
    Each strategy implements a different execution mode:
    - Adaptive: Classic WoT with auto-help
    - Parallel: Parallel domain execution
    - Beam Search: Explore multiple paths
    - Consensus: Multi-domain agreement
    - Metacognitive: Full metacognition integration
    - State Machine: Deterministic sequence
    """
    
    def __init__(self, engine: Any):
        """
        Initialize strategy with engine reference.
        
        Args:
            engine: The TrueWoTMax engine instance (provides state and helpers)
        """
        self.engine = engine
    
    @abstractmethod
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> "WoTResult":
        """
        Execute the strategy.
        
        Args:
            entry_domain: Starting domain
            query: User query
            specialists: Dict of domain specialists
            
        Returns:
            WoTResult with execution results
        """
        # TODO: Implement in concrete strategy classes (Sequential, Parallel, Adaptive)
        # This is an abstract method that must be overridden
        raise NotImplementedError("Subclasses must implement execute()")
    
    # ========================================================
    #  CONVENIENCE ACCESSORS (delegate to engine)
    # ========================================================
    
    @property
    def config(self):
        """Access engine config."""
        return self.engine.config
    
    @property
    def cots(self) -> Dict[str, str]:
        """Access current CoTs."""
        return self.engine.cots
    
    @property
    def domain_stats(self) -> Dict[str, Dict[str, Any]]:
        """Access domain statistics."""
        return self.engine.domain_stats
    
    @property
    def helper_graph(self) -> Dict[str, list]:
        """Access helper graph."""
        return self.engine.helper_graph
    
    @property
    def helper_weights(self) -> Dict[str, Dict[str, float]]:
        """Access helper weights."""
        return self.engine.helper_weights
    
    def _record(self, domain: str, output: str) -> None:
        """Record domain output."""
        self.engine._record(domain, output)
    
    def _analyze_output(self, domain: str, text: str) -> Dict[str, Any]:
        """Analyze output for uncertainty/help needs."""
        return self.engine._analyze_output(domain, text)
    
    def _extract_wot_request(self, text: str) -> str:
        """Extract WOT_REQUEST from output."""
        return self.engine._extract_wot_request(text)
    
    def _build_wot_packet(self, query: str) -> str:
        """Build initial WoT packet."""
        return self.engine._build_wot_packet(query)
    
    def _build_full_context_packet(self, query: str) -> str:
        """Build full context packet with all domain CoTs."""
        return self.engine._build_full_context_packet(query)
    
    def _choose_helper_domain(
        self,
        current: str,
        specialists: Dict[str, Any],
        prev: str = None,
    ) -> str | None:
        """Choose best helper domain."""
        return self.engine._choose_helper_domain(current, specialists, prev)
    
    def _update_stability_flags(self) -> None:
        """Update stability tracking."""
        self.engine._update_stability_flags()
    
    def _update_loop_window(self, domain: str, wot_request: str) -> None:
        """Update loop detection window."""
        self.engine._update_loop_window(domain, wot_request)
    
    def _loop_pattern_detected(self) -> bool:
        """Detect loop patterns."""
        return self.engine._loop_pattern_detected()
    
    def _estimate_step_confidence(self, output: str) -> float:
        """Estimate confidence from output text."""
        return self.engine._estimate_step_confidence(output)
    
    def _estimate_step_quality(self, output: str, analysis: Dict[str, Any]) -> float:
        """Estimate reasoning quality."""
        return self.engine._estimate_step_quality(output, analysis)
    
    def _build_result(
        self,
        final_domain: str,
        execution_time: float,
        assessment: Dict[str, Any] | None = None,
        reflection: Dict[str, Any] | None = None,
    ) -> "WoTResult":
        """Build WoT result."""
        return self.engine._build_result(final_domain, execution_time, assessment, reflection)
    
    def _get_parallel_candidates(self, entry: str, specialists: Dict[str, Any]) -> list:
        """Get independent domains for parallel execution."""
        return self.engine._get_parallel_candidates(entry, specialists)

    def _select_best_domain(self, domains: list) -> str:
        """Select best domain based on output quality."""
        return self.engine._select_best_domain(domains)

    def _run_specialist(
        self,
        domain: str,
        packet: str,
        specialists: Dict[str, Any],
    ) -> str:
        """Run specialist with caching optimization."""
        return self.engine._run_specialist_cached(domain, packet, specialists)

