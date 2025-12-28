# ============================================================
# ANM V0-OpenSource — Beam Search Execution Strategy
#  Explore multiple reasoning paths simultaneously
# ============================================================

from __future__ import annotations
from typing import Dict, Any
import time

from anm.wot.strategies.base import WoTExecutionStrategy
# WoTResult is only used in type annotations (strings with __future__ annotations), ReasoningPath


class BeamSearchStrategy(WoTExecutionStrategy):
    """
    Explore multiple reasoning paths simultaneously.
    
    Maintains multiple paths and selects best based on confidence/quality.
    """
    
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Execute beam search strategy."""
        start_time = time.time()
        
        # Initialize paths
        self.engine._paths = [
            ReasoningPath(
                path_id=f"path_{i}",
                domains_visited=[entry_domain],
                cots={d: "" for d in self.engine.domains},
                confidence=1.0,
            )
            for i in range(self.config.beam_width)
        ]
        
        # Initial step for all paths
        packet = self._build_wot_packet(query)
        for path in self.engine._paths:
            out = specialists[entry_domain].run(packet)
            path.cots[entry_domain] = out
            path.confidence = self._estimate_step_confidence(out)
        
        # Beam search loop
        for depth in range(self.config.beam_depth):
            active_paths = [p for p in self.engine._paths if not p.is_complete and not p.is_dead_end]
            if not active_paths:
                break
            
            new_paths = []
            for path in active_paths:
                current = path.domains_visited[-1]
                out = path.cots[current]
                
                wot_request = self._extract_wot_request(out)
                
                if wot_request == "NONE":
                    path.is_complete = True
                    new_paths.append(path)
                elif wot_request not in specialists:
                    path.is_dead_end = True
                    new_paths.append(path)
                else:
                    # Branch path
                    path.domains_visited.append(wot_request)
                    # Use this path's context (temporarily update engine cots)
                    temp_cots = dict(self.cots)
                    self.engine.cots.clear()
                    self.engine.cots.update(path.cots)
                    packet = self._build_full_context_packet(query)
                    new_out = specialists[wot_request].run(packet)
                    path.cots[wot_request] = new_out
                    path.confidence *= self._estimate_step_confidence(new_out)
                    new_paths.append(path)
                    # Restore original cots
                    self.engine.cots.clear()
                    self.engine.cots.update(temp_cots)
            
            # Keep top beam_width paths
            self.engine._paths = sorted(new_paths, key=lambda p: p.confidence, reverse=True)[:self.config.beam_width]
            self.engine.total_steps += 1
        
        # Select best path
        best_path = max(self.engine._paths, key=lambda p: p.confidence * (1.0 if p.is_complete else 0.5))
        self.engine.cots.clear()
        self.engine.cots.update(best_path.cots)
        
        return self._build_result(
            best_path.domains_visited[-1],
            time.time() - start_time,
        )

