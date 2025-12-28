# ============================================================
# ANM V0-OpenSource — TRUE WEB-OF-THOUGHT ENGINE V0-OpenSource
#  METACOGNITIVE + PARALLEL + BEAM SEARCH + SELF-CORRECTING
#
#  V0-OpenSource UPGRADES vs V0-OpenSource:
#    - Metacognition integration (pre-assess, reflect, quality gates)
#    - Parallel domain execution (concurrent specialist calls)
#    - Beam search (explore multiple paths simultaneously)
#    - Confidence-weighted routing (dynamic path selection)
#    - Backtracking (undo bad reasoning steps)
#    - Self-correction (detect and fix issues automatically)
#    - Chain-of-Verification (verify each step)
#    - Dynamic complexity estimation
#    - Reasoning quality tracking per step
#    - Consensus mode (multi-domain agreement)
#    - Adaptive max steps based on complexity
#    - Priority queue routing
#    - Thought caching (reuse successful patterns)
#    - Enhanced loop detection (more patterns)
#    - Full backward compatibility with V0-OpenSource API
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
import threading
import time
import hashlib
import copy

# Strategy imports (avoid circular import)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from anm.wot.strategies.base import WoTExecutionStrategy

from anm.wot.strategies import (
    AdaptiveStrategy,
    ParallelStrategy,
    BeamSearchStrategy,
    ConsensusStrategy,
    MetacognitiveStrategy,
    StateMachineStrategy,
)

__all__ = ["TrueWoTMax", "WoTMode", "WoTConfig", "ReasoningPath", "WoTResult"]


class WoTMode(Enum):
    """WoT execution modes."""
    ADAPTIVE = "adaptive"           # Classic WoT with auto-help
    STATE_MACHINE = "state_machine" # Deterministic sequence
    PARALLEL = "parallel"           # Parallel domain execution
    BEAM_SEARCH = "beam_search"     # Explore multiple paths
    CONSENSUS = "consensus"         # Multi-domain agreement
    METACOGNITIVE = "metacognitive" # Full metacognition integration


@dataclass
class WoTConfig:
    """Configuration for WoT execution."""
    # Core settings
    max_steps: int = 32
    mode: WoTMode = WoTMode.METACOGNITIVE
    
    # Parallel execution
    max_parallel_domains: int = 3
    parallel_timeout_ms: int = 30000
    
    # Beam search
    beam_width: int = 3              # Number of paths to explore
    beam_depth: int = 5              # Max depth per path
    
    # Quality gates
    min_confidence_to_proceed: float = 0.3
    min_reasoning_quality: float = 0.4
    
    # Backtracking
    enable_backtracking: bool = True
    max_backtracks: int = 3
    
    # Self-correction
    enable_self_correction: bool = True
    max_corrections: int = 2
    
    # Verification
    enable_chain_verification: bool = True
    verification_strictness: float = 0.5  # 0-1
    
    # Consensus
    consensus_threshold: float = 0.7  # Agreement required
    min_consensus_domains: int = 2
    
    # Caching
    enable_thought_cache: bool = True
    cache_ttl_seconds: int = 3600
    
    # Adaptive complexity
    adaptive_max_steps: bool = True
    complexity_step_multiplier: float = 1.5


@dataclass
class ReasoningPath:
    """A single reasoning path in beam search."""
    path_id: str
    domains_visited: List[str] = field(default_factory=list)
    cots: Dict[str, str] = field(default_factory=dict)
    confidence: float = 1.0
    quality: float = 1.0
    is_complete: bool = False
    is_dead_end: bool = False
    backtrack_count: int = 0


@dataclass 
class WoTResult:
    """Complete result from WoT execution."""
    # Final outputs
    cots: Dict[str, str]
    final_answer_domain: str
    
    # Quality metrics
    overall_confidence: float
    overall_quality: float
    
    # Execution stats
    total_steps: int
    domains_used: List[str]
    execution_time_ms: float
    
    # Path info (for beam search)
    paths_explored: int = 1
    best_path_id: Optional[str] = None
    
    # Corrections made
    corrections_made: int = 0
    backtracks_made: int = 0
    
    # Verification
    verification_passed: bool = True
    verification_notes: List[str] = field(default_factory=list)
    
    # Metacognition
    metacog_assessment: Optional[Dict] = None
    metacog_reflection: Optional[Dict] = None


class TrueWoTMax:
    """
    Maximum Level Web-of-Thought Engine (V0-OpenSource).
    
    New capabilities:
    
    1. METACOGNITION INTEGRATION
       - Pre-assesses query complexity and knowledge boundaries
       - Quality gates check confidence before proceeding
       - Post-reflection analyzes reasoning quality
       
    2. PARALLEL EXECUTION
       - Runs multiple independent domains concurrently
       - Merges results intelligently
       
    3. BEAM SEARCH
       - Explores multiple reasoning paths simultaneously
       - Selects best path based on confidence/quality
       
    4. SELF-CORRECTION
       - Detects when reasoning goes wrong
       - Automatically corrects and retries
       
    5. BACKTRACKING
       - Can undo bad steps and try alternatives
       - Prevents getting stuck in dead ends
       
    6. CONSENSUS MODE
       - Gets agreement from multiple domains
       - More reliable for critical queries
       
    7. CHAIN-OF-VERIFICATION
       - Verifies each reasoning step
       - Catches errors early
       
    8. THOUGHT CACHING
       - Caches successful reasoning patterns
       - Faster responses for similar queries
    """
    
    def __init__(
        self,
        domain_names: List[str],
        memory_llm: Optional[Any] = None,
        config: Optional[WoTConfig] = None,
    ) -> None:
        self.domains = list(domain_names)
        self.memory_llm = memory_llm
        self.config = config or WoTConfig()
        self.memory_context: Optional[Dict[str, Any]] = None
        
        # Core state (per run)
        self.cots: Dict[str, str] = {d: "" for d in self.domains}
        self.cot_history: Dict[str, List[str]] = {d: [] for d in self.domains}
        self.max_history_per_domain: int = 8
        self.call_graph: Dict[str, List[str]] = {d: [] for d in self.domains}
        self.updated: Dict[str, bool] = {d: False for d in self.domains}
        
        # Stability tracking
        self.global_stable: bool = False
        self.no_change_steps: int = 0
        self.total_steps: int = 0
        
        # Per-domain statistics
        self.domain_stats: Dict[str, Dict[str, Any]] = {
            d: {
                "calls": 0,
                "uncertain_outputs": 0,
                "missing_wot": 0,
                "avg_confidence": 0.0,
                "avg_quality": 0.0,
            }
            for d in self.domains
        }
        
        # Quality tracking per step
        self.step_quality: List[Dict[str, float]] = []
        
        # Backtracking state
        self._backtrack_stack: List[Dict[str, Any]] = []
        self._backtrack_count: int = 0
        
        # Correction tracking
        self._correction_count: int = 0
        
        # Beam search state
        self._paths: List[ReasoningPath] = []
        
        # Thought cache
        self._thought_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        
        # Metacognition instance (lazy loaded)
        self._metacog = None
        
        # Helper graph (from V0-OpenSource)
        self.helper_graph: Dict[str, List[str]] = {
            "physics": ["math", "simulation", "research", "facts", "general"],
            "math": ["physics", "simulation", "code", "general"],
            "code": ["simulation", "math", "general", "research"],
            "chemistry": ["physics", "math", "research", "facts", "general"],
            "biology": ["chemistry", "physics", "research", "facts", "general"],
            "general": ["research", "facts", "memory", "math", "physics"],
            "research": ["facts", "general", "math", "memory"],
            "facts": ["research", "math", "physics", "general"],
            "memory": ["general", "research"],
            "simulation": ["physics", "math", "code", "general"],
            "image": ["physics", "math", "simulation", "general"],
            "sound": ["physics", "math", "simulation", "general"],
        }
        
        # Hooks
        self._on_step: Optional[Callable] = None
        self._kg_hook: Optional[Callable] = None
        self._sim_stream_hook: Optional[Callable] = None
        self._micro_verifier: Optional[Callable] = None
        
        # Loop detection
        self.loop_window: List[Tuple[str, str]] = []
        self.loop_window_size: int = 8
        
        # Intent tracing
        self.intent_trace: List[Dict[str, Any]] = []
        self.branch_tags: Dict[str, str] = {d: "core" for d in self.domains}
        
        # Parallel execution
        self._executor: Optional[ThreadPoolExecutor] = None
        self.max_domain_calls: int = 6  # Increased from V0-OpenSource
        
        # Helper weights (can be learned)
        self.helper_weights: Dict[str, Dict[str, float]] = {}
        
        # Strategy instance (lazy initialized)
        self._strategy: Optional[WoTExecutionStrategy] = None
    
    # ========================================================
    #  STRATEGY FACTORY
    # ========================================================
    
    def _get_strategy(self) -> "WoTExecutionStrategy":
        """Get or create strategy instance based on config mode."""
        if self._strategy is None or self._strategy.__class__ != self._strategy_class_for_mode():
            strategy_class = self._strategy_class_for_mode()
            self._strategy = strategy_class(self)
        return self._strategy
    
    def _strategy_class_for_mode(self):
        """Get strategy class for current mode."""
        mode_to_strategy = {
            WoTMode.ADAPTIVE: AdaptiveStrategy,
            WoTMode.PARALLEL: ParallelStrategy,
            WoTMode.BEAM_SEARCH: BeamSearchStrategy,
            WoTMode.CONSENSUS: ConsensusStrategy,
            WoTMode.METACOGNITIVE: MetacognitiveStrategy,
            WoTMode.STATE_MACHINE: StateMachineStrategy,
        }
        return mode_to_strategy.get(self.config.mode, AdaptiveStrategy)
    
    # ========================================================
    #  MAIN EXECUTION - DISPATCHER
    # ========================================================
    
    def run(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
        max_steps: Optional[int] = None,
        *,
        mode: Optional[str] = None,
        config: Optional[WoTConfig] = None,
        on_step: Optional[Callable] = None,
        kg_hook: Optional[Callable] = None,
        sim_stream_hook: Optional[Callable] = None,
        micro_verifier: Optional[Callable] = None,
        enable_micro_verifier: bool = False,
        helper_weights: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, str]:
        """
        Execute WoT with maximum capabilities.
        
        Backward compatible with V0-OpenSource API.
        
        Returns:
            dict: {domain_name: latest_cot_text}
        """
        # Apply config overrides
        if config:
            self.config = config
        if max_steps:
            self.config.max_steps = max_steps
        if mode:
            self.config.mode = WoTMode(mode) if isinstance(mode, str) else mode
        
        # Attach hooks
        self._on_step = on_step
        self._kg_hook = kg_hook
        self._sim_stream_hook = sim_stream_hook
        self._micro_verifier = micro_verifier if enable_micro_verifier else None
        self.helper_weights = helper_weights or {}
        
        # Reset state
        self._reset_state()
        
        # Load memory once
        self._load_memory(query)
        
        # Normalize entry domain
        if entry_domain not in specialists:
            entry_domain = "general" if "general" in specialists else list(specialists.keys())[0]
        
        # Use strategy pattern for execution
        strategy = self._get_strategy()
        result = strategy.execute(entry_domain, query, specialists)
        
        return result.cots if isinstance(result, WoTResult) else result
    
    def run_full(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
        **kwargs,
    ) -> WoTResult:
        """
        Execute WoT and return full result with metrics.
        """
        start_time = time.time()
        
        # Run with mode dispatch
        cots = self.run(entry_domain, query, specialists, **kwargs)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Find best domain (most content or highest quality)
        best_domain = entry_domain
        max_len = 0
        for d, cot in self.cots.items():
            if len(cot) > max_len:
                max_len = len(cot)
                best_domain = d
        
        # Calculate overall metrics
        overall_conf = self._calculate_overall_confidence()
        overall_qual = self._calculate_overall_quality()
        
        return WoTResult(
            cots=self.cots,
            final_answer_domain=best_domain,
            overall_confidence=overall_conf,
            overall_quality=overall_qual,
            total_steps=self.total_steps,
            domains_used=list(set(d for d in self.domains if self.cots[d].strip())),
            execution_time_ms=execution_time,
            paths_explored=len(self._paths) if self._paths else 1,
            best_path_id=self._paths[0].path_id if self._paths else None,
            corrections_made=self._correction_count,
            backtracks_made=self._backtrack_count,
        )
    
    # ========================================================
    #  EXECUTION MODES (DELEGATED TO STRATEGIES)
    # ========================================================
    # These methods now delegate to strategy classes for better modularity.
    # See anm/wot/strategies/ for implementations.
    # ========================================================
    
    def _run_metacognitive(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Delegate to MetacognitiveStrategy (backward compatibility)."""
        strategy = MetacognitiveStrategy(self)
        return strategy.execute(entry_domain, query, specialists)
    
    def _run_parallel(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Delegate to ParallelStrategy (backward compatibility)."""
        strategy = ParallelStrategy(self)
        return strategy.execute(entry_domain, query, specialists)
    
    def _run_beam_search(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Delegate to BeamSearchStrategy (backward compatibility)."""
        strategy = BeamSearchStrategy(self)
        return strategy.execute(entry_domain, query, specialists)
    
    def _run_consensus(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Delegate to ConsensusStrategy (backward compatibility)."""
        strategy = ConsensusStrategy(self)
        return strategy.execute(entry_domain, query, specialists)
    
    def _run_state_machine(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Delegate to StateMachineStrategy (backward compatibility)."""
        strategy = StateMachineStrategy(self)
        return strategy.execute(entry_domain, query, specialists)
    
    def _run_adaptive(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Delegate to AdaptiveStrategy (backward compatibility)."""
        strategy = AdaptiveStrategy(self)
        return strategy.execute(entry_domain, query, specialists)
    
    # ========================================================
    #  METACOGNITION HELPERS
    # ========================================================
    
    def _get_metacog(self):
        """Lazy load metacognition."""
        if self._metacog is None:
            try:
                from anm.metacognition import MetaCognition
                self._metacog = MetaCognition()
            except ImportError:
                self._metacog = None
        return self._metacog
    
    def _metacog_pre_assess(self, query: str, domain: str) -> Dict[str, Any]:
        """Pre-assess query using metacognition."""
        mc = self._get_metacog()
        if not mc:
            return {"cognitive_load": 0.5, "should_defer": False}
        
        try:
            assessment = mc.pre_assess(query, domain)
            return {
                "cognitive_load": assessment.cognitive_load.total_load,
                "should_defer": assessment.should_defer,
                "should_simplify": assessment.should_simplify,
                "warnings": assessment.warnings,
                "strategy": assessment.recommended_approach,
            }
        except Exception:
            return {"cognitive_load": 0.5, "should_defer": False}
    
    def _metacog_reflect(self, query: str, domain: str, cots: Dict[str, str]) -> Dict[str, Any]:
        """Reflect on completed reasoning."""
        mc = self._get_metacog()
        if not mc:
            return {}
        
        try:
            reasoning = " ".join(cots.values())
            answer = cots.get(domain, "")
            reflection = mc.reflect(query, reasoning, answer, domain)
            return {
                "quality": reflection.overall_quality,
                "confidence": reflection.confidence.score,
                "needs_revision": reflection.needs_revision,
                "lessons": reflection.lessons_learned,
            }
        except Exception:
            return {}
    
    # ========================================================
    #  QUALITY & CONFIDENCE ESTIMATION
    # ========================================================
    
    def _estimate_step_confidence(self, output: str) -> float:
        """Estimate confidence from output text."""
        if not output:
            return 0.1
        
        lower = output.lower()
        
        # Confidence markers
        high_conf = ["definitely", "certainly", "clearly", "obvious", "proven"]
        low_conf = ["maybe", "perhaps", "not sure", "uncertain", "might"]
        
        high_count = sum(1 for m in high_conf if m in lower)
        low_count = sum(1 for m in low_conf if m in lower)
        
        base = 0.6
        base += high_count * 0.1
        base -= low_count * 0.15
        
        return max(0.1, min(1.0, base))
    
    def _estimate_step_quality(self, output: str, analysis: Dict[str, Any]) -> float:
        """Estimate reasoning quality."""
        if not output:
            return 0.1
        
        quality = 0.5
        
        # Length is a weak signal
        if len(output) > 500:
            quality += 0.1
        
        # Has structure
        if any(marker in output for marker in ["1.", "2.", "•", "-", "Step"]):
            quality += 0.15
        
        # Has reasoning connectors
        connectors = ["therefore", "because", "since", "thus", "so"]
        if any(c in output.lower() for c in connectors):
            quality += 0.15
        
        # Penalize uncertainty
        if analysis.get("uncertain_phrases", 0) > 2:
            quality -= 0.2
        
        if analysis.get("has_cannot_do", False):
            quality -= 0.3
        
        return max(0.1, min(1.0, quality))
    
    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence across steps."""
        if not self.step_quality:
            return 0.5
        return sum(s["confidence"] for s in self.step_quality) / len(self.step_quality)
    
    def _calculate_overall_quality(self) -> float:
        """Calculate overall quality across steps."""
        if not self.step_quality:
            return 0.5
        return sum(s["quality"] for s in self.step_quality) / len(self.step_quality)
    
    # ========================================================
    #  SELF-CORRECTION
    # ========================================================
    
    def _attempt_self_correction(
        self,
        domain: str,
        output: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> str:
        """Attempt to correct low-quality output."""
        correction_prompt = f"""
[SELF-CORRECTION REQUEST]

Your previous response had quality issues. Please review and improve:

PREVIOUS OUTPUT:
{output[:1000]}

ISSUES DETECTED:
- Reasoning quality below threshold
- May need more structure or clarity

INSTRUCTIONS:
1. Re-read your reasoning
2. Identify weak points
3. Provide improved, clearer reasoning
4. Maintain WOT_REQUEST format

{self._build_full_context_packet(query)}
"""
        try:
            return specialists[domain].run(correction_prompt)
        except Exception:
            return output
    
    def _correct_issue(
        self,
        domain: str,
        output: str,
        issue: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> str:
        """Correct a specific issue."""
        correction_prompt = f"""
[CORRECTION NEEDED]

Issue detected: {issue}

Previous output:
{output[:800]}

Please fix this issue and provide corrected reasoning.

{self._build_full_context_packet(query)}
"""
        try:
            return specialists[domain].run(correction_prompt)
        except Exception:
            return output
    
    # ========================================================
    #  BACKTRACKING
    # ========================================================
    
    def _save_backtrack_point(self, domain: str, output: str) -> None:
        """Save state for potential backtracking."""
        self._backtrack_stack.append({
            "domain": domain,
            "output": output,
            "cots": copy.deepcopy(self.cots),
            "step": self.total_steps,
        })
        
        # Keep limited history
        if len(self._backtrack_stack) > self.config.max_backtracks + 2:
            self._backtrack_stack = self._backtrack_stack[-self.config.max_backtracks - 2:]
    
    def _attempt_backtrack(self) -> bool:
        """Attempt to backtrack to previous state."""
        if self._backtrack_count >= self.config.max_backtracks:
            return False
        
        if len(self._backtrack_stack) < 2:
            return False
        
        # Pop current (failed) state
        self._backtrack_stack.pop()
        
        # Restore previous
        prev = self._backtrack_stack[-1]
        self.cots = prev["cots"]
        self._backtrack_count += 1
        
        return True
    
    # ========================================================
    #  VERIFICATION
    # ========================================================
    
    def _verify_step(self, domain: str, output: str, query: str) -> Tuple[bool, str]:
        """Verify a reasoning step."""
        issues = []
        
        # Check for contradictions with previous steps
        for d, cot in self.cots.items():
            if d != domain and cot:
                if self._detect_contradiction(output, cot):
                    issues.append(f"Potential contradiction with {d}")
        
        # Check for unsupported claims
        if "definitely" in output.lower() or "proven" in output.lower():
            if "because" not in output.lower() and "since" not in output.lower():
                issues.append("Strong claims without justification")
        
        # Check for completeness
        if len(output) < 100 and "WOT_REQUEST:" in output:
            issues.append("Very short reasoning before routing")
        
        if issues:
            return False, "; ".join(issues)
        return True, ""
    
    def _detect_contradiction(self, text1: str, text2: str) -> bool:
        """Simple contradiction detection."""
        # Very basic: look for opposite assertions
        negatives = ["not", "isn't", "doesn't", "cannot", "wrong", "false"]
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # If one has negatives and shares key words with other...
        has_neg_1 = any(n in text1.lower() for n in negatives)
        has_neg_2 = any(n in text2.lower() for n in negatives)
        
        if has_neg_1 != has_neg_2:
            # Different polarity - check for shared content words
            shared = words1 & words2
            content_shared = len([w for w in shared if len(w) > 5]) > 3
            if content_shared:
                return True
        
        return False
    
    # ========================================================
    #  CONSENSUS HELPERS
    # ========================================================
    
    def _get_consensus_candidates(self, entry: str, specialists: Dict[str, Any]) -> List[str]:
        """Get domains for consensus."""
        candidates = [entry]
        helpers = self.helper_graph.get(entry, [])
        
        for h in helpers[:self.config.min_consensus_domains - 1]:
            if h in specialists:
                candidates.append(h)
        
        return candidates[:self.config.min_consensus_domains + 1]
    
    def _check_consensus(self, results: Dict[str, str]) -> Tuple[bool, float, List[str]]:
        """Check if results reach consensus."""
        notes = []
        
        if len(results) < 2:
            return True, 1.0, ["Single domain - no consensus needed"]
        
        # Extract conclusions
        conclusions = []
        for domain, output in results.items():
            # Look for final statement
            lines = output.strip().split("\n")
            conclusion = lines[-1] if lines else ""
            conclusions.append((domain, conclusion))
        
        # Simple agreement check (could be much more sophisticated)
        agreement = 0
        total = 0
        for i, (d1, c1) in enumerate(conclusions):
            for j, (d2, c2) in enumerate(conclusions):
                if i < j:
                    total += 1
                    # Word overlap as proxy for agreement
                    words1 = set(c1.lower().split())
                    words2 = set(c2.lower().split())
                    if words1 and words2:
                        overlap = len(words1 & words2) / max(len(words1), len(words2))
                        if overlap > 0.3:
                            agreement += 1
                            notes.append(f"{d1} and {d2} agree")
        
        score = agreement / total if total > 0 else 0
        return score >= self.config.consensus_threshold, score, notes
    
    def _merge_consensus_responses(self, results: Dict[str, str]) -> str:
        """Merge consensus responses."""
        # Simple: concatenate unique insights
        merged_lines = ["[CONSENSUS RESPONSE]"]
        seen = set()
        
        for domain, output in results.items():
            for line in output.split("\n"):
                line_clean = line.strip()
                if line_clean and line_clean not in seen and "WOT_REQUEST" not in line:
                    seen.add(line_clean)
                    merged_lines.append(f"[{domain}] {line_clean}")
        
        return "\n".join(merged_lines[:50])  # Cap length
    
    # ========================================================
    #  PARALLEL HELPERS
    # ========================================================
    
    def _get_parallel_candidates(self, entry: str, specialists: Dict[str, Any]) -> List[str]:
        """Get independent domains for parallel execution."""
        candidates = [entry]
        
        # Add non-overlapping helpers
        for d in specialists:
            if d != entry and len(candidates) < self.config.max_parallel_domains:
                candidates.append(d)
        
        return candidates
    
    def _select_best_domain(self, domains: List[str]) -> str:
        """Select best domain based on output quality."""
        best = domains[0] if domains else "general"
        best_score = 0
        
        for d in domains:
            cot = self.cots.get(d, "")
            score = len(cot) + (100 if "therefore" in cot.lower() else 0)
            if score > best_score:
                best_score = score
                best = d
        
        return best
    
    # ========================================================
    #  STATE MANAGEMENT
    # ========================================================
    
    def _reset_state(self) -> None:
        """Reset all state for new run."""
        self.cots = {d: "" for d in self.domains}
        self.cot_history = {d: [] for d in self.domains}
        self.call_graph = {d: [] for d in self.domains}
        self.updated = {d: False for d in self.domains}
        self.global_stable = False
        self.no_change_steps = 0
        self.total_steps = 0
        self.step_quality = []
        self._backtrack_stack = []
        self._backtrack_count = 0
        self._correction_count = 0
        self._paths = []
        self.loop_window = []
        self.intent_trace = []
        
        for d in self.domains:
            self.domain_stats[d] = {
                "calls": 0,
                "uncertain_outputs": 0,
                "missing_wot": 0,
                "avg_confidence": 0.0,
                "avg_quality": 0.0,
            }
    
    def _load_memory(self, query: str) -> None:
        """Load memory context."""
        if self.memory_llm:
            try:
                self.memory_context = self.memory_llm.query(user_query=query, limit_blocks=6)
            except Exception as e:
                self.memory_context = {"error": str(e)}
    
    def _refresh_memory(self, query: str, output: str) -> None:
        """Refresh memory based on MEMORY_QUERY."""
        if not self.memory_llm:
            return
        
        mem_query = self._extract_memory_query(output, query)
        try:
            self.memory_context = self.memory_llm.query(user_query=mem_query, limit_blocks=10)
        except Exception:
            pass
    
    def _build_result(
        self,
        final_domain: str,
        execution_time: float,
        assessment: Optional[Dict] = None,
        reflection: Optional[Dict] = None,
    ) -> WoTResult:
        """Build WoT result."""
        return WoTResult(
            cots=self.cots,
            final_answer_domain=final_domain,
            overall_confidence=self._calculate_overall_confidence(),
            overall_quality=self._calculate_overall_quality(),
            total_steps=self.total_steps,
            domains_used=[d for d in self.domains if self.cots[d].strip()],
            execution_time_ms=execution_time * 1000,
            paths_explored=len(self._paths) if self._paths else 1,
            corrections_made=self._correction_count,
            backtracks_made=self._backtrack_count,
            metacog_assessment=assessment,
            metacog_reflection=reflection,
        )
    
    # ========================================================
    #  RECORDING & ANALYSIS (from V0-OpenSource)
    # ========================================================
    
    def _record(self, domain: str, output: str) -> None:
        """Record domain output."""
        if output is None:
            output = ""
        
        old = self.cots.get(domain, "")
        changed = old.strip() != output.strip()
        
        self.cots[domain] = output
        self.updated[domain] = changed
        
        # History
        history = self.cot_history.setdefault(domain, [])
        history.append(output)
        if len(history) > self.max_history_per_domain:
            self.cot_history[domain] = history[-self.max_history_per_domain:]
        
        # Stats
        if domain in self.domain_stats:
            self.domain_stats[domain]["calls"] += 1
            if self._is_uncertain_text(output):
                self.domain_stats[domain]["uncertain_outputs"] += 1
            if "WOT_REQUEST:" not in output:
                self.domain_stats[domain]["missing_wot"] += 1
    
    def _analyze_output(self, domain: str, text: str) -> Dict[str, Any]:
        """Analyze output for uncertainty/help needs."""
        if not text:
            return {"needs_help": True, "uncertain_phrases": 0, "has_cannot_do": True, "missing_wot_request": True}
        
        lower = text.lower()
        
        uncertain_markers = ["i think", "maybe", "not sure", "probably", "perhaps", "uncertain"]
        cannot_markers = ["cannot", "can't", "don't know", "no idea", "out of scope"]
        
        uncertain_count = sum(1 for m in uncertain_markers if m in lower)
        cannot_flag = any(m in lower for m in cannot_markers)
        
        needs_help = cannot_flag or uncertain_count >= 3
        if domain in ("physics", "math", "code") and uncertain_count >= 2:
            needs_help = True
        
        return {
            "needs_help": needs_help,
            "uncertain_phrases": uncertain_count,
            "has_cannot_do": cannot_flag,
            "missing_wot_request": "wot_request:" not in lower,
        }
    
    def _is_uncertain_text(self, text: str) -> bool:
        """Check if text indicates uncertainty."""
        if not text:
            return True
        lower = text.lower()
        return any(m in lower for m in ["i think", "maybe", "not sure", "probably"])
    
    def _update_stability_flags(self) -> None:
        """Update stability tracking."""
        if any(self.updated.values()):
            self.no_change_steps = 0
        else:
            self.no_change_steps += 1
        
        if self.no_change_steps >= 2:
            self.global_stable = True
    
    # ========================================================
    #  ROUTING HELPERS
    # ========================================================
    
    def _choose_helper_domain(
        self,
        current: str,
        specialists: Dict[str, Any],
        prev: Optional[str],
    ) -> Optional[str]:
        """Choose best helper domain."""
        helpers = self.helper_graph.get(current, [])
        
        candidates = []
        for h in helpers:
            if h == prev:
                continue
            if h in specialists and self.domain_stats.get(h, {}).get("calls", 0) < self.max_domain_calls:
                candidates.append(h)
        
        if not candidates:
            for h in ["research", "facts", "general"]:
                if h != prev and h in specialists:
                    if self.domain_stats.get(h, {}).get("calls", 0) < self.max_domain_calls:
                        candidates.append(h)
        
        if not candidates:
            return None
        
        # Use weights if available
        weights = self.helper_weights.get(current, {})
        if weights:
            best = max(candidates, key=lambda h: weights.get(h, 1.0))
            return best
        
        return candidates[0]
    
    # ========================================================
    #  PACKET BUILDERS (from V0-OpenSource)
    # ========================================================
    
    def _build_wot_packet(self, query: str) -> str:
        """Build initial WoT packet."""
        mem = self._format_memory_section()
        return f"""
USER QUERY:
{query}

MEMORY CONTEXT:
{mem}

CROSS-DOMAIN CONTEXT:
None yet — this is the first domain.

INSTRUCTIONS:
Provide your domain-specific reasoning.
Be honest about limitations.
If needed, request another domain:
  WOT_REQUEST: <domain>
  
When done:
  WOT_REQUEST: NONE
"""
    
    def _build_full_context_packet(self, query: str) -> str:
        """Build full context packet with all domain CoTs."""
        mem = self._format_memory_section()
        
        domain_dump = "\n\n".join(
            f"== {d.upper()} ==\n{self.cots[d]}"
            for d in self.domains if self.cots[d].strip()
        ) or "[No previous reasoning.]"
        
        return f"""
USER QUERY:
{query}

MEMORY CONTEXT:
{mem}

CROSS-DOMAIN CONTEXT:
{domain_dump}

INSTRUCTIONS:
- Read ALL domain reasoning
- Build on previous insights
- Fix inconsistencies in YOUR domain
- If you need another domain → WOT_REQUEST: <domain>
- When complete → WOT_REQUEST: NONE
"""
    
    def _format_memory_section(self) -> str:
        """Format memory context."""
        if not self.memory_context:
            return "No memory loaded."
        
        mc = self.memory_context
        lines = []
        
        if mc.get("query"):
            lines.append(f"Query: {mc['query']}")
        
        if mc.get("highlights"):
            lines.append("Highlights:")
            for h in mc["highlights"][:5]:
                lines.append(f"  - {h}")
        
        if mc.get("memory_summary"):
            summary = mc["memory_summary"][:500]
            lines.append(f"Summary: {summary}")
        
        return "\n".join(lines) or "Memory context empty."
    
    # ========================================================
    #  PARSING (from V0-OpenSource)
    # ========================================================
    
    def _extract_wot_request(self, text: str) -> str:
        """Extract WOT_REQUEST from output."""
        if not text or "WOT_REQUEST:" not in text:
            return "NONE"
        
        line = text.split("WOT_REQUEST:", 1)[1].split("\n", 1)[0].strip()
        if not line:
            return "NONE"
        
        upper = line.upper()
        if upper in ("NONE", "MEMORY"):
            return upper
        
        return line.lower()
    
    def _extract_memory_query(self, text: str, default: str) -> str:
        """Extract MEMORY_QUERY from output."""
        if not text or "MEMORY_QUERY:" not in text:
            return default
        return text.split("MEMORY_QUERY:", 1)[1].split("\n", 1)[0].strip() or default
    
    # ========================================================
    #  LOOP DETECTION (enhanced from V0-OpenSource)
    # ========================================================
    
    def _update_loop_window(self, domain: str, wot_request: str) -> None:
        """Update loop detection window."""
        self.loop_window.append((domain, wot_request))
        if len(self.loop_window) > self.loop_window_size:
            self.loop_window = self.loop_window[-self.loop_window_size:]
    
    def _loop_pattern_detected(self) -> bool:
        """Detect loop patterns."""
        win = self.loop_window
        if len(win) < 4:
            return False
        
        # Low diversity
        if len(set(win)) <= 2 and len(win) >= 4:
            return True
        
        # ABAB pattern
        last4 = win[-4:]
        if len(set(last4)) == 2 and last4[0] == last4[2] and last4[1] == last4[3]:
            return True
        
        # AAA pattern
        if len(set(win[-3:])) == 1:
            return True
        
        return False
    
    # ========================================================
    #  HOOKS
    # ========================================================
    
    def _emit_step(self, step: int, domain: str, wot_request: str, analysis: Dict) -> None:
        """Emit step hook."""
        if self._on_step:
            try:
                self._on_step(
                    step, domain, wot_request, analysis,
                    dict(self.cots), dict(self.domain_stats), dict(self.call_graph),
                )
            except Exception:
                pass


# Backward compatibility alias
TrueWoT = TrueWoTMax
