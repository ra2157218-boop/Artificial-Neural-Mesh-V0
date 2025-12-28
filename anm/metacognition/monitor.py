# ============================================================
# ANM V0-OpenSource — METACOGNITIVE MONITOR
#  Real-time tracking of cognitive processes
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import threading


class ProcessingPhase(Enum):
    """Phases of cognitive processing."""
    IDLE = "idle"
    RECEIVING = "receiving"           # Receiving input
    PARSING = "parsing"               # Understanding the query
    ROUTING = "routing"               # Determining domains
    RETRIEVING = "retrieving"         # Memory/knowledge retrieval
    REASONING = "reasoning"           # Active reasoning
    GENERATING = "generating"         # Generating response
    VERIFYING = "verifying"           # Checking answer
    REFINING = "refining"             # Improving response
    REFLECTING = "reflecting"         # Post-hoc reflection
    COMPLETE = "complete"


@dataclass
class CognitiveState:
    """Current state of cognitive processing."""
    phase: ProcessingPhase = ProcessingPhase.IDLE
    current_domain: Optional[str] = None
    active_specialists: List[str] = field(default_factory=list)
    
    # Processing metrics
    steps_taken: int = 0
    time_in_phase_ms: float = 0
    total_time_ms: float = 0
    
    # Cognitive indicators
    attention_focus: str = ""          # What ANM is focusing on
    working_memory_load: float = 0.0   # 0-1, how full is working memory
    reasoning_depth: int = 0           # How deep in reasoning chain
    
    # Quality indicators
    coherence_score: float = 1.0       # 0-1, how coherent is current state
    confidence_trend: str = "stable"   # rising, stable, falling
    uncertainty_flags: List[str] = field(default_factory=list)
    
    # Alerts
    alerts: List[str] = field(default_factory=list)


class MetaCognitiveMonitor:
    """
    Real-time monitor of ANM's cognitive processes.
    
    Tracks:
    - Current processing phase
    - Active specialists and domains
    - Cognitive load and attention
    - Coherence and confidence trends
    - Processing anomalies
    
    Usage:
        monitor = MetaCognitiveMonitor()
        
        monitor.start_session(query)
        monitor.enter_phase(ProcessingPhase.REASONING)
        monitor.log_step({"domain": "physics", "action": "applying Newton's laws"})
        state = monitor.get_state()
        monitor.end_session()
    """
    
    def __init__(self):
        self._state = CognitiveState()
        self._history: List[Dict[str, Any]] = []
        self._phase_start_time: float = 0
        self._session_start_time: float = 0
        self._step_log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        # Thresholds for alerts
        self._max_steps_per_phase = 50
        self._max_reasoning_depth = 10
        self._coherence_warning_threshold = 0.5
        self._load_warning_threshold = 0.8
    
    def start_session(self, query: str) -> None:
        """Start a new cognitive session."""
        with self._lock:
            self._session_start_time = time.time()
            self._phase_start_time = self._session_start_time
            self._state = CognitiveState(
                phase=ProcessingPhase.RECEIVING,
                attention_focus=query[:100],
            )
            self._step_log = []
            self._history.append({
                "event": "session_start",
                "timestamp": datetime.now().isoformat(),
                "query_preview": query[:50],
            })
    
    def enter_phase(self, phase: ProcessingPhase, context: Optional[Dict] = None) -> None:
        """Transition to a new processing phase."""
        with self._lock:
            now = time.time()
            
            # Log time in previous phase
            if self._phase_start_time:
                self._state.time_in_phase_ms = (now - self._phase_start_time) * 1000
            
            # Check for phase anomalies
            if self._state.steps_taken > self._max_steps_per_phase:
                self._state.alerts.append(
                    f"High step count in {self._state.phase.value}: {self._state.steps_taken}"
                )
            
            # Update state
            old_phase = self._state.phase
            self._state.phase = phase
            self._state.steps_taken = 0
            self._phase_start_time = now
            self._state.total_time_ms = (now - self._session_start_time) * 1000
            
            if context:
                if "domain" in context:
                    self._state.current_domain = context["domain"]
                if "focus" in context:
                    self._state.attention_focus = context["focus"]
            
            # Log transition
            self._history.append({
                "event": "phase_transition",
                "from": old_phase.value,
                "to": phase.value,
                "timestamp": datetime.now().isoformat(),
                "context": context,
            })
    
    def log_step(self, step_info: Dict[str, Any]) -> None:
        """Log a processing step."""
        with self._lock:
            self._state.steps_taken += 1
            
            step_record = {
                "step": self._state.steps_taken,
                "phase": self._state.phase.value,
                "timestamp": time.time(),
                **step_info,
            }
            self._step_log.append(step_record)
            
            # Update attention focus
            if "focus" in step_info:
                self._state.attention_focus = step_info["focus"]
            
            # Update domain
            if "domain" in step_info:
                self._state.current_domain = step_info["domain"]
                if step_info["domain"] not in self._state.active_specialists:
                    self._state.active_specialists.append(step_info["domain"])
            
            # Update reasoning depth
            if "depth" in step_info:
                self._state.reasoning_depth = step_info["depth"]
            
            # Check for warnings
            if self._state.reasoning_depth > self._max_reasoning_depth:
                self._state.alerts.append(
                    f"Deep reasoning chain: depth={self._state.reasoning_depth}"
                )
    
    def update_load(self, load: float) -> None:
        """Update working memory load estimate."""
        with self._lock:
            self._state.working_memory_load = max(0, min(1, load))
            
            if load > self._load_warning_threshold:
                self._state.alerts.append(
                    f"High cognitive load: {load:.2f}"
                )
    
    def update_coherence(self, coherence: float) -> None:
        """Update coherence score."""
        with self._lock:
            old_coherence = self._state.coherence_score
            self._state.coherence_score = max(0, min(1, coherence))
            
            if coherence < self._coherence_warning_threshold:
                self._state.alerts.append(
                    f"Low coherence detected: {coherence:.2f}"
                )
            
            # Update trend
            if coherence > old_coherence + 0.1:
                self._state.confidence_trend = "rising"
            elif coherence < old_coherence - 0.1:
                self._state.confidence_trend = "falling"
            else:
                self._state.confidence_trend = "stable"
    
    def flag_uncertainty(self, reason: str) -> None:
        """Flag an uncertainty source."""
        with self._lock:
            if reason not in self._state.uncertainty_flags:
                self._state.uncertainty_flags.append(reason)
    
    def get_state(self) -> CognitiveState:
        """Get current cognitive state."""
        with self._lock:
            # Update time
            now = time.time()
            self._state.time_in_phase_ms = (now - self._phase_start_time) * 1000
            self._state.total_time_ms = (now - self._session_start_time) * 1000
            return self._state
    
    def get_step_log(self) -> List[Dict[str, Any]]:
        """Get all logged steps."""
        with self._lock:
            return self._step_log.copy()
    
    def get_alerts(self) -> List[str]:
        """Get current alerts."""
        with self._lock:
            return self._state.alerts.copy()
    
    def clear_alerts(self) -> None:
        """Clear all alerts."""
        with self._lock:
            self._state.alerts = []
    
    def end_session(self) -> Dict[str, Any]:
        """End cognitive session and return summary."""
        with self._lock:
            now = time.time()
            
            summary = {
                "total_time_ms": (now - self._session_start_time) * 1000,
                "phases_visited": list(set(h["to"] for h in self._history if h.get("event") == "phase_transition")),
                "total_steps": sum(s.get("step", 0) for s in self._step_log),
                "specialists_used": self._state.active_specialists,
                "final_coherence": self._state.coherence_score,
                "alerts_generated": len(self._state.alerts),
                "uncertainty_flags": self._state.uncertainty_flags,
                "max_reasoning_depth": self._state.reasoning_depth,
            }
            
            self._state = CognitiveState(phase=ProcessingPhase.COMPLETE)
            
            return summary
    
    def get_processing_trace(self) -> str:
        """Get human-readable processing trace."""
        with self._lock:
            lines = ["=== COGNITIVE PROCESSING TRACE ==="]
            
            for event in self._history[-20:]:  # Last 20 events
                if event.get("event") == "phase_transition":
                    lines.append(
                        f"  {event['from']} → {event['to']}"
                    )
            
            lines.append(f"\nCurrent: {self._state.phase.value}")
            lines.append(f"Domain: {self._state.current_domain}")
            lines.append(f"Focus: {self._state.attention_focus[:50]}...")
            lines.append(f"Load: {self._state.working_memory_load:.2f}")
            lines.append(f"Coherence: {self._state.coherence_score:.2f}")
            
            if self._state.alerts:
                lines.append("\nALERTS:")
                for alert in self._state.alerts:
                    lines.append(f"  ⚠ {alert}")
            
            return "\n".join(lines)
