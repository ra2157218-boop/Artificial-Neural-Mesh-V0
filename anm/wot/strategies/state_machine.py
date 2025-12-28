# ============================================================
# ANM V0-OpenSource — State Machine Execution Strategy
#  Deterministic domain sequence
# ============================================================

from __future__ import annotations
from typing import Dict, Any
import time

from anm.wot.strategies.base import WoTExecutionStrategy
# WoTResult is only used in type annotations (strings with __future__ annotations)


class StateMachineStrategy(WoTExecutionStrategy):
    """
    Deterministic domain sequence.
    
    Executes domains in a predefined chain.
    """
    
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Execute state machine strategy."""
        start_time = time.time()
        
        chain = [d for d in ["general", "physics", "math", "simulation", "general"] if d in specialists]
        if not chain:
            chain = list(specialists.keys())
        
        current = chain[0]
        packet = self._build_wot_packet(query)
        
        for i, domain in enumerate(chain):
            if i >= self.config.max_steps:
                break
            
            out = specialists[domain].run(packet)
            self._record(domain, out)
            packet = self._build_full_context_packet(query)
            self.engine.total_steps += 1
        
        return self._build_result(chain[-1] if chain else entry_domain, time.time() - start_time)

