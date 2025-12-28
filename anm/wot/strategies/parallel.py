# ============================================================
# ANM V0-OpenSource — Parallel Execution Strategy
#  Execute independent domains in parallel
# ============================================================

from __future__ import annotations
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from anm.wot.strategies.base import WoTExecutionStrategy
# WoTResult is only used in type annotations (strings with __future__ annotations)


class ParallelStrategy(WoTExecutionStrategy):
    """
    Execute independent domains in parallel.
    
    Runs multiple domains concurrently and merges results.
    """
    
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Execute parallel strategy."""
        start_time = time.time()
        
        # Determine parallel domains
        parallel_domains = self.engine._get_parallel_candidates(entry_domain, specialists)
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.config.max_parallel_domains) as executor:
            futures = {}
            packet = self._build_wot_packet(query)
            
            for domain in parallel_domains:
                future = executor.submit(specialists[domain].run, packet)
                futures[future] = domain
            
            # Collect results
            for future in as_completed(futures, timeout=self.config.parallel_timeout_ms / 1000):
                domain = futures[future]
                try:
                    out = future.result()
                    self._record(domain, out)
                except Exception as e:
                    self.cots[domain] = f"[ERROR] {e}"
        
        self.engine.total_steps = len(parallel_domains)
        
        # Merge and consolidate
        final_domain = self.engine._select_best_domain(parallel_domains)
        
        return self._build_result(final_domain, time.time() - start_time)

