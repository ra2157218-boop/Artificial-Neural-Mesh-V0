# ============================================================
# ANM V0-OpenSource — Consensus Execution Strategy
#  Multi-domain agreement
# ============================================================

from __future__ import annotations
from typing import Dict, Any
import time

from anm.wot.strategies.base import WoTExecutionStrategy
# WoTResult is only used in type annotations (strings with __future__ annotations)


class ConsensusStrategy(WoTExecutionStrategy):
    """
    Get agreement from multiple domains.
    
    Runs multiple domains and checks for consensus.
    """
    
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Execute consensus strategy."""
        start_time = time.time()
        
        # Run multiple domains
        consensus_domains = self.engine._get_consensus_candidates(entry_domain, specialists)
        results: Dict[str, str] = {}
        
        packet = self._build_wot_packet(query)
        for domain in consensus_domains:
            out = specialists[domain].run(packet)
            results[domain] = out
            self._record(domain, out)
        
        # Check for consensus
        consensus_reached, agreement_score, notes = self.engine._check_consensus(results)
        
        self.engine.total_steps = len(consensus_domains)
        
        if consensus_reached:
            # Merge consistent responses
            final = self.engine._merge_consensus_responses(results)
            self.cots[entry_domain] = final
        else:
            # Use most confident response
            best_domain = self.engine._select_best_domain(list(results.keys()))
            self.cots[entry_domain] = self.cots.get(best_domain, results.get(best_domain, ""))
        
        result = self._build_result(entry_domain, time.time() - start_time)
        result.verification_notes = notes
        return result

