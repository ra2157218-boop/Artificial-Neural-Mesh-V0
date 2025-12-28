# ============================================================
# ANM V0-OpenSource — Metacognitive Execution Strategy
#  Full metacognition integration (MAXIMUM LEVEL)
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional
import time

from anm.wot.strategies.base import WoTExecutionStrategy
# WoTResult is only used in type annotations (strings with __future__ annotations)


class MetacognitiveStrategy(WoTExecutionStrategy):
    """
    Full metacognitive execution:
    1. Pre-assess query
    2. Adaptive execution with quality gates
    3. Self-correction when needed
    4. Post-reflection
    """
    
    def execute(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
    ) -> WoTResult:
        """Execute metacognitive strategy."""
        start_time = time.time()
        
        # 1. Pre-assessment
        assessment = self.engine._metacog_pre_assess(query, entry_domain)
        
        # Adjust max steps based on complexity
        if self.config.adaptive_max_steps:
            complexity = assessment.get("cognitive_load", 0.5)
            adjusted_steps = int(self.config.max_steps * (1 + complexity * self.config.complexity_step_multiplier))
            self.config.max_steps = min(adjusted_steps, 64)
        
        # 2. Check if we should proceed
        if assessment.get("should_defer", False):
            # Return with acknowledgment
            self.cots[entry_domain] = f"[DEFERRED] This query is outside my expertise in {entry_domain}."
            return self._build_result(entry_domain, time.time() - start_time, assessment=assessment)
        
        # 3. Execute with quality gates
        current = entry_domain
        prev_domain: Optional[str] = None
        
        # Initial call
        packet = self._build_wot_packet(query)
        out = specialists[current].run(packet)
        self._record(current, out)
        
        steps = 0
        while not self.engine.global_stable and steps < self.config.max_steps:
            steps += 1
            self.engine.total_steps = steps
            
            # Reset updated flags
            for d in self.engine.domains:
                self.engine.updated[d] = False
            
            # Analyze output
            analysis = self._analyze_output(current, out)
            wot_request = self._extract_wot_request(out)
            
            # Quality gate check
            step_conf = self._estimate_step_confidence(out)
            step_qual = self._estimate_step_quality(out, analysis)
            self.engine.step_quality.append({"confidence": step_conf, "quality": step_qual})
            
            # Self-correction if quality is low
            if self.config.enable_self_correction and step_qual < self.config.min_reasoning_quality:
                if self.engine._correction_count < self.config.max_corrections:
                    corrected_out = self.engine._attempt_self_correction(current, out, query, specialists)
                    if corrected_out != out:
                        out = corrected_out
                        self._record(current, out)
                        self.engine._correction_count += 1
                        continue
            
            # Backtracking if stuck
            if self.config.enable_backtracking:
                if analysis["needs_help"] and step_conf < 0.3:
                    if self.engine._attempt_backtrack():
                        current = self.engine._backtrack_stack[-1]["domain"]
                        out = self.engine._backtrack_stack[-1]["output"]
                        continue
            
            # Chain verification
            if self.config.enable_chain_verification:
                verified, issue = self.engine._verify_step(current, out, query)
                if not verified and self.config.enable_self_correction:
                    corrected_out = self.engine._correct_issue(current, out, issue, query, specialists)
                    if corrected_out != out:
                        out = corrected_out
                        self._record(current, out)
                        self.engine._correction_count += 1
                        continue
            
            # Standard routing
            if wot_request == "NONE":
                if analysis["needs_help"]:
                    helper = self._choose_helper_domain(current, specialists, prev_domain)
                    if helper and helper != current:
                        wot_request = helper
                    else:
                        self.engine.global_stable = True
                        break
                else:
                    self.engine.global_stable = True
                    break
            
            if wot_request == current or wot_request not in specialists:
                self.engine.global_stable = True
                break
            
            # Ping-pong detection
            if prev_domain and wot_request == prev_domain:
                if self.domain_stats[current]["calls"] > 0 and self.domain_stats[prev_domain]["calls"] > 0:
                    self.engine.global_stable = True
                    break
            
            # Save for backtracking
            if self.config.enable_backtracking:
                self.engine._save_backtrack_point(current, out)
            
            # Route to next domain
            prev_domain = current
            current = wot_request
            packet = self._build_full_context_packet(query)
            out = specialists[current].run(packet)
            self._record(current, out)
            
            # Loop detection
            self._update_loop_window(current, self._extract_wot_request(out))
            if self._loop_pattern_detected():
                self.engine.global_stable = True
                break
            
            # Stability
            self._update_stability_flags()
            
            # Emit hooks
            if self.engine._on_step:
                self.engine._emit_step(steps, current, wot_request, analysis)
        
        # 4. Post-reflection
        reflection = self.engine._metacog_reflect(query, current, self.cots)
        
        return self._build_result(
            current, 
            time.time() - start_time,
            assessment=assessment,
            reflection=reflection,
        )

