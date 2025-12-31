# ============================================================
# ANM V0-OpenSource — Adaptive Execution Strategy
#  Classic WoT with auto-help (legacy behavior, enhanced)
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional
import time

from anm.wot.strategies.base import WoTExecutionStrategy
# WoTResult is only used in type annotations (strings with __future__ annotations)


class AdaptiveStrategy(WoTExecutionStrategy):
    """
    Enhanced adaptive mode from V0-OpenSource.
    
    Classic WoT behavior with automatic helper domain selection.
    """
    
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Execute adaptive strategy."""
        start_time = time.time()
        
        current = entry_domain
        prev_domain: Optional[str] = None
        
        packet = self._build_wot_packet(query)
        out = self._run_specialist(current, packet, specialists)
        self._record(current, out)
        
        steps = 0
        while not self.engine.global_stable and steps < self.config.max_steps:
            steps += 1
            self.engine.total_steps = steps
            
            for d in self.engine.domains:
                self.engine.updated[d] = False
            
            analysis = self._analyze_output(current, out)
            wot_request = self._extract_wot_request(out)
            
            # Per-domain cap
            if self.domain_stats[current]["calls"] >= self.engine.max_domain_calls:
                helper = self._choose_helper_domain(current, specialists, prev_domain)
                if helper and helper != current:
                    wot_request = helper
                else:
                    self.engine.global_stable = True
                    break
            
            # MEMORY handling
            if wot_request == "MEMORY" and self.engine.memory_llm:
                self.engine._refresh_memory(query, out)
                packet = self._build_full_context_packet(query)
                out = self._run_specialist(current, packet, specialists)
                self._record(current, out)
                continue
            
            # Auto-help
            if wot_request == "NONE" and analysis["needs_help"]:
                helper = self._choose_helper_domain(current, specialists, prev_domain)
                if helper and helper != current:
                    wot_request = helper
            
            if wot_request == "NONE":
                self.engine.global_stable = True
                break
            
            if wot_request == current or wot_request not in specialists:
                self.engine.global_stable = True
                break
            
            # Ping-pong
            if prev_domain and wot_request == prev_domain:
                if self.domain_stats[current]["calls"] > 0 and self.domain_stats[prev_domain]["calls"] > 0:
                    self.engine.global_stable = True
                    break
            
            prev_domain = current
            current = wot_request
            packet = self._build_full_context_packet(query)
            out = self._run_specialist(current, packet, specialists)
            self._record(current, out)
            
            self._update_stability_flags()
            self._update_loop_window(current, self._extract_wot_request(out))
            if self._loop_pattern_detected():
                self.engine.global_stable = True
                break
        
        return self._build_result(current, time.time() - start_time)

