# ============================================================
# ANM V0-OpenSource — TRUE WEB-OF-THOUGHT ENGINE V0-OpenSource-MESH
#  SUPERVISED POLYMATH + SIMULATION + IMAGE + SOUND + REALTIME HOOKS
#
#  Domains:
#    - general
#    - math
#    - physics
#    - code
#    - chemistry
#    - biology
#    - memory       (MemoryLLM adapter, optional direct MemoryLLM)
#    - research     (ResearchLLM)
#    - facts        (FactsLLM)
#    - simulation   (SimulationLLM / sim-core controller)
#    - image        (ImageLLM / perception adapter)
#    - sound        (Sound / Sonification specialist)
#
#  V0-OpenSource UPGRADES vs v13:
#    - Added SOUND domain wiring (helper graph + stats)
#    - Missing-WOT detection at WoT-level (per-domain stats)
#    - Stronger stability tracking (no-change + loop-window)
#    - Enriched analysis dict (missing_wot_request flag)
#    - Intent & branch trace preserved + capped (32 records)
#    - Safer hooks (KG / sim_stream / micro_verifier) — never crash WoT
#    - Fully backward compatible .run(...) API for Router
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable, Tuple
import time

from anm.utils.prompts import WOT_PACKET_TEMPLATES  # kept for future use / compatibility

__all__ = ["TrueWoT"]


class TrueWoT:
    """
    Dynamic multi-domain Web-of-Thought reasoning engine (V0-OpenSource-MESH).

    Communication protocol (per specialist output):
        WOT_REQUEST: <DOMAIN | MEMORY | NONE>
        MEMORY_QUERY: <subquery>          (optional, when requesting MEMORY)
        INTENT: <short label>             (optional, for intent tracing)
        BRANCH: <token>                   (optional, for multi-branch tagging)

    Domains (up to 12):
        general, math, physics, code, chemistry, biology,
        memory, research, facts, simulation, image, sound

    Memory behavior:
        - If memory_llm is provided to TrueWoT, it will:
            * Load diary context once at the start
            * Optionally refresh on WOT_REQUEST: MEMORY
        - If you only use a "memory" specialist (MemorySpecialistAdapter),
          TrueWoT still works — it will just show "No diary memory loaded."

    Hooks:
        - on_step(step, current_domain, wot_request, analysis, cots_snapshot,
                  domain_stats, call_graph)

        - sim_stream_hook(step, current_domain="simulation", simulation_cot,
                          cots_snapshot, domain_stats)

        - kg_hook(step, current_domain, domain_cot, cots_snapshot)

        - micro_verifier(step, current_domain, domain_cot, analysis,
                         cots_snapshot, domain_stats)
              -> { "override_wot_request": Optional[str], "force_stop": bool }

    Stability & safety:
        - Stops when:
            * WOT_REQUEST: NONE (and no auto-help is needed)
            * OR max_steps reached
            * OR repeated self-request (non-MEMORY) is detected
            * OR outputs stop changing for several steps
            * OR per-domain call cap is hit
            * OR ping-pong between two domains is detected
            * OR loop-window pattern (ABAB / collapse) is detected
            * OR micro-verifier requests force_stop
    """

    # --------------------------------------------------------
    #  CONSTRUCTOR
    # --------------------------------------------------------

    def __init__(
        self,
        domain_names: List[str],
        memory_llm: Optional[Any] = None,
    ) -> None:

        # Known domains in this run (keys of specialists dict)
        # (Router controls what actually gets passed in `specialists`)
        self.domains = list(domain_names)

        # Optional direct MemoryLLM (separate from "memory" specialist)
        self.memory_llm = memory_llm
        self.memory_context: Optional[Dict[str, Any]] = None

        # Domain → latest CoT text
        self.cots: Dict[str, str] = {d: "" for d in self.domains}

        # Domain → list of all CoT snapshots (history)
        # Most recent entries at the end; truncated per domain
        self.cot_history: Dict[str, List[str]] = {d: [] for d in self.domains}
        self.max_history_per_domain: int = 8

        # Domain call graph (for debugging / analysis)
        # Example: physics → [math, simulation]
        self.call_graph: Dict[str, List[str]] = {d: [] for d in self.domains}

        # Domain updated flags (per loop)
        self.updated: Dict[str, bool] = {d: False for d in self.domains}

        # Global stability flags
        self.global_stable: bool = False
        self.no_change_steps: int = 0      # how many loops with no change

        # Per-domain stats (reset per run in run())
        self.domain_stats: Dict[str, Dict[str, int]] = {
            d: {
                "calls": 0,
                "uncertain_outputs": 0,
                "missing_wot": 0,
            }
            for d in self.domains
        }

        # Simple per-run metadata
        self.total_steps: int = 0

        # Hard safety caps
        self.max_domain_calls: int = 4  # per-domain max calls per run

        # Weighted helper graph (can be overridden per-run)
        self.helper_weights: Dict[str, Dict[str, float]] = {}

        # State-machine default chain (used when mode="state_machine")
        self.state_machine_chain: List[str] = [
            "general",
            "physics",
            "math",
            "simulation",
            "image",
            "sound",
            "general",   # loop back for consolidation
        ]

        # Domain → helper domains priority graph
        # Only helpers that exist in this run (in specialists dict) are used.
        self.helper_graph: Dict[str, List[str]] = {
            "physics": [
                "math", "simulation", "image", "sound", "research", "facts", "memory", "general"
            ],
            "math": [
                "physics", "simulation", "image", "sound", "research", "facts", "memory", "general"
            ],
            "code": [
                "simulation", "math", "general", "facts", "research", "memory", "image", "sound"
            ],
            "chemistry": [
                "physics", "math", "research", "facts", "memory", "general"
            ],
            "biology": [
                "chemistry", "physics", "research", "facts", "memory", "general"
            ],
            "general": [
                "research", "facts", "memory", "math", "physics", "simulation", "image", "sound"
            ],
            "research": [
                "facts", "general", "math", "memory", "physics"
            ],
            "facts": [
                "research", "math", "physics", "memory", "general"
            ],
            "memory": [
                "general", "research"
            ],
            "simulation": [
                "physics", "math", "code", "image", "sound", "research", "facts", "memory", "general"
            ],
            # image domain cooperates with physics/math/code/simulation
            "image": [
                "physics", "math", "simulation", "code", "sound", "research", "facts", "memory", "general"
            ],
            # sound domain cooperates with physics/math/simulation/image
            "sound": [
                "physics", "math", "simulation", "image", "research", "facts", "memory", "general"
            ],
        }

        # Hooks (set per-run in `run(...)`)
        self._kg_hook: Optional[
            Callable[[int, str, str, Dict[str, str]], None]
        ] = None
        self._sim_stream_hook: Optional[
            Callable[[int, str, str, Dict[str, str], Dict[str, Dict[str, int]]], None]
        ] = None
        self._micro_verifier: Optional[
            Callable[
                [int, str, str, Dict[str, Any], Dict[str, str], Dict[str, Dict[str, int]]],
                Dict[str, Any],
            ]
        ] = None
        self._micro_verifier_enabled: bool = False

        # Intent + branch tracing
        self.intent_trace: List[Dict[str, Any]] = []
        self.branch_tags: Dict[str, str] = {d: "core" for d in self.domains}

        # Loop window (for extra loop pattern detection)
        self.loop_window: List[Tuple[str, str]] = []  # list of (domain, wot_request)
        self.loop_window_size: int = 6

    # ========================================================
    #  MAIN EXECUTION LOOP
    # ========================================================

    def run(
        self,
        entry_domain: str,
        query: str,
        specialists: Dict[str, Any],
        max_steps: int = 32,
        *,
        mode: str = "adaptive",  # "adaptive" (old behaviour) | "state_machine"
        helper_weights: Optional[Dict[str, Dict[str, float]]] = None,
        enable_micro_verifier: bool = False,
        micro_verifier: Optional[
            Callable[
                [int, str, str, Dict[str, Any], Dict[str, str], Dict[str, Dict[str, int]]],
                Dict[str, Any],
            ]
        ] = None,
        kg_hook: Optional[
            Callable[[int, str, str, Dict[str, str]], None]
        ] = None,
        sim_stream_hook: Optional[
            Callable[[int, str, str, Dict[str, str], Dict[str, Dict[str, int]]], None]
        ] = None,
        on_step: Optional[
            Callable[
                [int, str, str, Dict[str, Any], Dict[str, Dict[str, Any]], Dict[str, Dict[str, int]], Dict[str, List[str]]],
                None,
            ]
        ] = None,
    ) -> Dict[str, str]:
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "J", "location": "wot_engine.py:run", "message": "WoT.run entry", "data": {"entry_domain": entry_domain, "max_steps": max_steps, "mode": mode, "specialists_count": len(specialists)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        """
        Execute polymath Web-of-Thought until stable.

        Args:
            entry_domain: starting domain (e.g. "general")
            query: original user query (string) — already includes Cloud Diary brief if Router wants
            specialists: {domain_name: specialist_instance}
            max_steps: hard safety cap on reasoning steps

            mode:
                - "adaptive": standard WoT behaviour (use WOT_REQUEST + helper_graph)
                - "state_machine": deterministic sequence of domains

            helper_weights:
                Optional fine-grained weights for helper selection:
                    {
                      "physics": {"math": 1.5, "simulation": 2.0, ...},
                      ...
                    }

            enable_micro_verifier / micro_verifier:
                Optional micro-verifier hook called each step for safety/sanity.

            kg_hook:
                Optional knowledge-graph hook called after each domain update.

            sim_stream_hook:
                Optional hook called whenever the `simulation` domain runs.

            on_step:
                Optional callback invoked after every WoT step:
                    on_step(
                        step_index: int,
                        current_domain: str,
                        wot_request: str,
                        analysis: dict,
                        cots_snapshot: dict,
                        domain_stats: dict,
                        call_graph: dict,
                    )

        Returns:
            dict: {domain_name: latest_cot_text}
        """

        # ---------------------------------------------
        # Attach per-run config
        # ---------------------------------------------
        self.helper_weights = helper_weights or {}
        self._kg_hook = kg_hook
        self._sim_stream_hook = sim_stream_hook
        self._micro_verifier = micro_verifier
        self._micro_verifier_enabled = bool(enable_micro_verifier and callable(micro_verifier))

        # Reset global flags + stats for this run
        self.global_stable = False
        self.no_change_steps = 0
        self.total_steps = 0
        self.loop_window = []
        self.intent_trace = []

        for d in self.domains:
            self.updated[d] = False
            # per-run stats reset
            self.domain_stats[d]["calls"] = 0
            self.domain_stats[d]["uncertain_outputs"] = 0
            self.domain_stats[d]["missing_wot"] = 0

        # ----------------------------------------------------
        # LOAD MEMORY ONCE AT START (if direct MemoryLLM provided)
        # ----------------------------------------------------
        if self.memory_llm is not None:
            try:
                self.memory_context = self.memory_llm.query(
                    user_query=query,
                    limit_blocks=6,
                )
            except Exception as e:
                self.memory_context = {
                    "query": query,
                    "raw_blocks": [],
                    "memory_summary": f"[MemoryLLM error: {e}]",
                    "highlights": [],
                }

        # Normalize entry domain
        if entry_domain not in specialists:
            # fallback: if invalid, use general if available, else any
            entry_domain = "general" if "general" in specialists else list(specialists.keys())[0]

        current = entry_domain
        prev_domain: Optional[str] = None  # for ping-pong detection

        # Initial packet for the entry domain
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "J", "location": "wot_engine.py:run", "message": "Before initial specialist call", "data": {"current": current, "has_specialist": current in specialists}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        init_packet = self._build_wot_packet(query)
        out = specialists[current].run(init_packet)
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "J", "location": "wot_engine.py:run", "message": "After initial specialist call", "data": {"current": current, "output_length": len(out) if out else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        self._record(current, out)
        self._register_intent_from_output(step_index=0, domain=current, output=out)

        # Hooks after first record
        self._maybe_emit_kg_facts(step_index=0, current_domain=current, output=out)
        self._maybe_emit_sim_stream(step_index=0, current_domain=current, output=out)

        # Optional realtime callback for step 0 (initial)
        analysis0 = self._analyze_output(current, out)
        w0 = self._extract_wot_request(out)
        if on_step is not None:
            on_step(
                0,
                current,
                w0,
                analysis0,
                dict(self.cots),
                dict(self.domain_stats),
                dict(self.call_graph),
            )

        # Seed loop window
        self._update_loop_window(current_domain=current, wot_request=w0)

        # ----------------------------------------------------
        # TRUE POLYMATH LOOP
        # ----------------------------------------------------
        steps = 0

        while not self.global_stable and steps < max_steps:
            steps += 1
            self.total_steps = steps

            # Reset "updated" flags for this loop
            for d in self.domains:
                self.updated[d] = False

            analysis = self._analyze_output(current, out)
            wot_request = self._extract_wot_request(out)
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "WOT_STABILITY", "location": "wot_engine.py:run", "message": "WoT step", "data": {"step": steps, "current_domain": current, "wot_request": wot_request, "global_stable": self.global_stable, "no_change_steps": self.no_change_steps, "max_steps": max_steps}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

            # ----------------------------------------
            # Micro-verifier (pre-routing override / stop)
            # ----------------------------------------
            wot_request, forced_stop = self._apply_micro_verifier(
                step_index=steps,
                current_domain=current,
                output=out,
                analysis=analysis,
                wot_request=wot_request,
            )
            if forced_stop:
                # Already stable; final on_step + break
                if on_step is not None:
                    on_step(
                        steps,
                        current,
                        "NONE",
                        analysis,
                        dict(self.cots),
                        dict(self.domain_stats),
                        dict(self.call_graph),
                    )
                break

            # ----------------------------------------
            # State-machine mode: ignore WOT_REQUEST, follow chain
            # ----------------------------------------
            if mode == "state_machine":
                next_domain = self._next_state_machine_domain(current, specialists)
                if next_domain is None or next_domain == current:
                    self.global_stable = True
                    if on_step is not None:
                        on_step(
                            steps,
                            current,
                            "NONE",
                            analysis,
                            dict(self.cots),
                            dict(self.domain_stats),
                            dict(self.call_graph),
                        )
                    break

                prev_domain = current
                current = next_domain
                packet = self._build_full_context_packet(query)
                out = specialists[current].run(packet)
                self._record(current, out)
                self._register_intent_from_output(step_index=steps, domain=current, output=out)

                self._update_stability_flags()
                self._maybe_emit_kg_facts(step_index=steps, current_domain=current, output=out)
                self._maybe_emit_sim_stream(step_index=steps, current_domain=current, output=out)

                if on_step is not None:
                    analysis_next = self._analyze_output(current, out)
                    w_next = self._extract_wot_request(out)
                    on_step(
                        steps,
                        current,
                        w_next,
                        analysis_next,
                        dict(self.cots),
                        dict(self.domain_stats),
                        dict(self.call_graph),
                    )

                self._update_loop_window(current_domain=current, wot_request=w_next)
                if self._loop_pattern_detected():
                    self.global_stable = True
                    break

                continue  # next loop iteration

            # ----------------------------------------
            # ADAPTIVE MODE (legacy behaviour, enhanced)
            # ----------------------------------------

            # Per-domain call cap check
            if self.domain_stats[current]["calls"] >= self.max_domain_calls:
                # This domain is saturated; force help if possible
                helper = self._choose_helper_domain(current, specialists, prev_domain)
                if helper is None or helper == current:
                    # No helper left → treat as stable stop
                    self.global_stable = True
                    # Realtime callback before break
                    if on_step is not None:
                        on_step(
                            steps,
                            current,
                            "NONE",
                            analysis,
                            dict(self.cots),
                            dict(self.domain_stats),
                            dict(self.call_graph),
                        )
                    break
                wot_request = helper

            # Handle explicit MEMORY request (direct MemoryLLM path)
            if wot_request == "MEMORY" and self.memory_llm is not None:
                mem_query = self._extract_memory_query(out, default=query)
                try:
                    self.memory_context = self.memory_llm.query(
                        user_query=mem_query,
                        limit_blocks=10,
                    )
                except Exception as e:
                    # Preserve previous context but annotate error
                    self.memory_context = {
                        "query": mem_query,
                        "raw_blocks": [],
                        "memory_summary": f"[MemoryLLM error on refresh: {e}]",
                        "highlights": [],
                    }

                packet = self._build_full_context_packet(query)
                out = specialists[current].run(packet)
                self._record(current, out)
                self._register_intent_from_output(step_index=steps, domain=current, output=out)

                # After refresh, go to next loop
                self._update_stability_flags()
                self._maybe_emit_kg_facts(step_index=steps, current_domain=current, output=out)
                self._maybe_emit_sim_stream(step_index=steps, current_domain=current, output=out)

                if on_step is not None:
                    analysis_mem = self._analyze_output(current, out)
                    w_mem = self._extract_wot_request(out)
                    on_step(
                        steps,
                        current,
                        w_mem,
                        analysis_mem,
                        dict(self.cots),
                        dict(self.domain_stats),
                        dict(self.call_graph),
                    )

                self._update_loop_window(current_domain=current, wot_request=w_mem)
                if self._loop_pattern_detected():
                    self.global_stable = True
                    break

                continue

            # If WOT_REQUEST: NONE but output is uncertain → AUTO-HELP
            if wot_request == "NONE" and analysis["needs_help"]:
                helper = self._choose_helper_domain(current, specialists, prev_domain)
                if helper is not None and helper != current:
                    wot_request = helper

            # If STILL NONE → stable stop
            if wot_request == "NONE":
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "WOT_STABILITY", "location": "wot_engine.py:run", "message": "WoT stable: WOT_REQUEST NONE", "data": {"step": steps, "current_domain": current}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                self.global_stable = True
                if on_step is not None:
                    on_step(
                        steps,
                        current,
                        "NONE",
                        analysis,
                        dict(self.cots),
                        dict(self.domain_stats),
                        dict(self.call_graph),
                    )
                break

            # Invalid or unknown domain request → stable stop
            if (wot_request not in ("NONE", "MEMORY")) and (wot_request not in specialists):
                self.global_stable = True
                if on_step is not None:
                    on_step(
                        steps,
                        current,
                        "NONE",
                        analysis,
                        dict(self.cots),
                        dict(self.domain_stats),
                        dict(self.call_graph),
                    )
                break

            # Self-loop request (non-MEMORY) → stop to avoid infinite cycles
            if wot_request == current:
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "WOT_STABILITY", "location": "wot_engine.py:run", "message": "WoT stable: self-loop detected", "data": {"step": steps, "current_domain": current, "wot_request": wot_request}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                self.global_stable = True
                if on_step is not None:
                    on_step(
                        steps,
                        current,
                        wot_request,
                        analysis,
                        dict(self.cots),
                        dict(self.domain_stats),
                        dict(self.call_graph),
                    )
                break

            # MEMORY was already handled above; if still present here without direct MemoryLLM,
            # and there is a "memory" specialist, we fall back to that.
            if wot_request == "MEMORY" and self.memory_llm is None:
                if "memory" in specialists:
                    next_domain = "memory"
                else:
                    # No memory specialist → treat as NONE
                    self.global_stable = True
                    if on_step is not None:
                        on_step(
                            steps,
                            current,
                            "NONE",
                            analysis,
                            dict(self.cots),
                            dict(self.domain_stats),
                            dict(self.call_graph),
                        )
                    break
            else:
                # Normal domain routing
                next_domain = wot_request

            # Ping-pong protection: if we are about to bounce back to previous domain,
            # and both domains have already been called at least once, treat as stable stop.
            if prev_domain is not None and next_domain == prev_domain:
                if (
                    self.domain_stats.get(current, {}).get("calls", 0) > 0
                    and self.domain_stats.get(prev_domain, {}).get("calls", 0) > 0
                ):
                    # #region agent log
                    try:
                        with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                            import json
                            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "WOT_STABILITY", "location": "wot_engine.py:run", "message": "WoT stable: ping-pong detected", "data": {"step": steps, "current_domain": current, "prev_domain": prev_domain, "next_domain": next_domain}, "timestamp": int(time.time() * 1000)}) + "\n")
                    except Exception:
                        pass
                    # #endregion
                    self.global_stable = True
                    if on_step is not None:
                        on_step(
                            steps,
                            current,
                            next_domain,
                            analysis,
                            dict(self.cots),
                            dict(self.domain_stats),
                            dict(self.call_graph),
                        )
                    break

            # Register dependency edge (current → requested)
            if next_domain in specialists:
                self.call_graph.setdefault(current, []).append(next_domain)

            # Build cross-domain CoT packet
            packet = self._build_full_context_packet(query)

            prev_domain = current
            current = next_domain
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H", "location": "wot_engine.py:run", "message": "Before specialist.run call", "data": {"domain": current, "step": steps, "packet_length": len(packet) if packet else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            out = specialists[current].run(packet)
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H", "location": "wot_engine.py:run", "message": "After specialist.run call", "data": {"domain": current, "step": steps, "output_length": len(out) if out else 0, "is_empty": not out or not out.strip()}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # CRITICAL: Ensure no empty output - if empty, log error and provide fallback
            if not out or not out.strip() or out.strip() in ["", "None", "N/A"]:
                import logging
                logging.error(f"WoT: {current} specialist returned empty output at step {steps}")
                # Provide a fallback response to prevent pipeline failure
                out = f"[{current.upper()} specialist encountered an issue]\nThe {current} domain was called but produced no output. This may indicate a processing error.\nWOT_REQUEST: NONE"
            
            self._record(current, out)
            self._register_intent_from_output(step_index=steps, domain=current, output=out)

            # Stability tracking (no-change detection)
            self._update_stability_flags()

            # Hooks after this step
            self._maybe_emit_kg_facts(step_index=steps, current_domain=current, output=out)
            self._maybe_emit_sim_stream(step_index=steps, current_domain=current, output=out)

            # Realtime callback after this step
            if on_step is not None:
                analysis_next = self._analyze_output(current, out)
                w_next = self._extract_wot_request(out)
                on_step(
                    steps,
                    current,
                    w_next,
                    analysis_next,
                    dict(self.cots),
                    dict(self.domain_stats),
                    dict(self.call_graph),
                )

            # Loop-window update & pattern detection
            w_for_loop = self._extract_wot_request(out)
            self._update_loop_window(current_domain=current, wot_request=w_for_loop)
            if self._loop_pattern_detected():
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "WOT_STABILITY", "location": "wot_engine.py:run", "message": "WoT stable: loop pattern detected", "data": {"step": steps, "current_domain": current, "loop_window": self.loop_window[-6:] if len(self.loop_window) >= 6 else self.loop_window}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                self.global_stable = True
                break

        # End of loop — return final CoTs per domain
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "WOT_STABILITY", "location": "wot_engine.py:run", "message": "WoT completed", "data": {"total_steps": self.total_steps, "global_stable": self.global_stable, "no_change_steps": self.no_change_steps, "domains_used": list(self.cots.keys()), "domain_stats": {d: self.domain_stats[d]["calls"] for d in self.domains}}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        return self.cots

    # ========================================================
    #  MICRO-VERIFIER + HOOK HELPERS
    # ========================================================

    def _apply_micro_verifier(
        self,
        step_index: int,
        current_domain: str,
        output: str,
        analysis: Dict[str, Any],
        wot_request: str,
    ) -> Tuple[str, bool]:
        """
        If micro-verifier is enabled, let it:
          - override WOT_REQUEST, and/or
          - force stop the run.

        Returns:
            (new_wot_request, force_stop_flag)
        """
        if not self._micro_verifier_enabled or self._micro_verifier is None:
            return wot_request, False

        try:
            decision = self._micro_verifier(
                step_index,
                current_domain,
                output,
                analysis,
                dict(self.cots),
                dict(self.domain_stats),
            ) or {}
        except Exception as e:
            # Micro-verifier must never crash WoT
            # Blueprint compliance: Log failure for transparency
            logging.warning(f"Micro-verifier failed at step {step_index} for {current_domain}: {e}")
            return wot_request, False

        force_stop = bool(decision.get("force_stop", False))

        override = decision.get("override_wot_request")
        if isinstance(override, str) and override.strip():
            tok = override.strip()
            up = tok.upper()
            if up in ("NONE", "MEMORY"):
                wot_request = up
            else:
                wot_request = tok.lower()

        if force_stop:
            self.global_stable = True
            wot_request = "NONE"

        return wot_request, force_stop

    def _maybe_emit_kg_facts(
        self,
        step_index: int,
        current_domain: str,
        output: str,
    ) -> None:
        """
        Call external KG hook with the domain CoT so it can extract triples.
        """
        if self._kg_hook is None:
            return
        try:
            self._kg_hook(
                step_index,
                current_domain,
                output,
                dict(self.cots),
            )
        except Exception as e:
            # KG failures must never crash WoT
            # Blueprint compliance: Log failure for transparency
            logging.debug(f"Knowledge graph hook failed at step {step_index}: {e}")
            return

    def _maybe_emit_sim_stream(
        self,
        step_index: int,
        current_domain: str,
        output: str,
    ) -> None:
        """
        If current_domain == 'simulation' and a sim_stream_hook is provided,
        call it so the visual engine can inspect simulation metadata inside
        the CoT (e.g., paths, frame indices).
        """
        if self._sim_stream_hook is None:
            return
        if current_domain != "simulation":
            return
        try:
            self._sim_stream_hook(
                step_index,
                current_domain,
                output,
                dict(self.cots),
                dict(self.domain_stats),
            )
        except Exception as e:
            # Streaming hook must not crash WoT
            # Blueprint compliance: Log failure for transparency
            logging.debug(f"Simulation stream hook failed at step {step_index}: {e}")
            return

    # ========================================================
    #  STATE-MACHINE MODE
    # ========================================================

    def _next_state_machine_domain(
        self,
        current_domain: str,
        specialists: Dict[str, Any],
    ) -> Optional[str]:
        """
        Deterministic domain sequence:
            general → physics → math → simulation → image → sound → general → ...

        Only domains that actually exist in `specialists` are used.
        """
        chain = [d for d in self.state_machine_chain if d in specialists]
        if not chain:
            return None

        if current_domain not in chain:
            # Start from the beginning of the chain
            return chain[0]

        idx = chain.index(current_domain)
        # Loop around to allow multiple passes; safety still via max_steps
        next_idx = (idx + 1) % len(chain)
        return chain[next_idx]

    # ========================================================
    #  UPDATE STORAGE & STABILITY FLAGS
    # ========================================================

    def _record(self, domain: str, output: str) -> None:
        """
        Store latest CoT for a domain and mark whether it changed.

        - Only marks updated[domain] = True if the content actually changed
          (ignoring whitespace).
        - Updates per-domain stats.
        - Appends to per-domain history (bounded).
        """
        if output is None:
            output = ""

        old = self.cots.get(domain, "")
        changed = (old.strip() != output.strip())

        self.cots[domain] = output
        self.updated[domain] = changed

        # History
        history = self.cot_history.setdefault(domain, [])
        history.append(output)
        if len(history) > self.max_history_per_domain:
            # Keep only the most recent N entries
            self.cot_history[domain] = history[-self.max_history_per_domain :]

        # Update stats
        if domain in self.domain_stats:
            self.domain_stats[domain]["calls"] += 1

            # crude heuristic for uncertainty tracking added in _analyze_output
            if self._is_uncertain_text(output):
                self.domain_stats[domain]["uncertain_outputs"] += 1

            # Missing-WOT detection (for structural diagnostics)
            if "WOT_REQUEST:" not in output:
                self.domain_stats[domain]["missing_wot"] += 1

    def _update_stability_flags(self) -> None:
        """
        Check if any domain changed in this step.
        - If none changed → increment no_change_steps
        - If at least one changed → reset no_change_steps
        - If no_change_steps >= 2 → treat as stable and stop
        """
        if any(self.updated.values()):
            self.no_change_steps = 0
        else:
            self.no_change_steps += 1

        if self.no_change_steps >= 2:
            self.global_stable = True

    # ========================================================
    #  OUTPUT ANALYSIS (CONFUSION / UNCERTAINTY)
    # ========================================================

    def _analyze_output(self, domain: str, text: str) -> Dict[str, Any]:
        """
        Light-weight heuristic analysis of a specialist output to decide
        whether it seems confident or confused.

        Returns:
            {
              "needs_help": bool,
              "uncertain_phrases": int,
              "has_cannot_do": bool,
              "missing_wot_request": bool
            }
        """
        if not text:
            return {
                "needs_help": True,
                "uncertain_phrases": 0,
                "has_cannot_do": True,
                "missing_wot_request": True,
            }

        lower = text.lower()

        uncertain_markers = [
            "i think", "i guess", "maybe", "might be",
            "i'm not sure", "i am not sure",
            "not entirely sure", "not completely sure",
            "probably", "perhaps", "it seems like",
            "i'm uncertain", "i am uncertain",
        ]
        cannot_do_markers = [
            "i cannot", "i can't", "i can’t",
            "i don't know", "i do not know",
            "no idea", "beyond my capability",
            "out of scope", "not able to derive",
        ]

        uncertain_count = sum(1 for m in uncertain_markers if m in lower)
        cannot_flag = any(m in lower for m in cannot_do_markers)

        needs_help = False

        # Strong triggers
        if cannot_flag:
            needs_help = True
        # Multiple uncertainty markers also trigger help
        elif uncertain_count >= 3:
            needs_help = True
        # For high-risk domains (physics / math / code / simulation / image / sound)
        # two markers is enough
        elif domain in ("physics", "math", "code", "simulation", "image", "sound") and uncertain_count >= 2:
            needs_help = True

        missing_wot = "wot_request:" not in lower

        return {
            "needs_help": needs_help,
            "uncertain_phrases": uncertain_count,
            "has_cannot_do": cannot_flag,
            "missing_wot_request": missing_wot,
        }

    def _is_uncertain_text(self, text: str) -> bool:
        """
        Helper used only for stats; looser than _analyze_output.
        """
        if not text:
            return True
        lower = text.lower()
        markers = ["i think", "maybe", "i guess", "not sure", "probably", "perhaps"]
        return any(m in lower for m in markers)

    # ========================================================
    #  AUTO-HELP ROUTING (WEIGHTED)
    # ========================================================

    def _choose_helper_domain(
        self,
        current_domain: str,
        specialists: Dict[str, Any],
        prev_domain: Optional[str],
    ) -> Optional[str]:
        """
        Choose the best helper domain for `current_domain` based on
        a static helper graph and current availability + optional weights.

        Skips:
        - Domains not in `specialists`
        - Domains that already hit max_domain_calls
        - The immediate previous domain (to reduce ping-pong)
        """
        helpers = self.helper_graph.get(current_domain, [])
        if not helpers:
            helpers = []

        # Filter by availability & caps & avoid direct bounce to prev_domain
        candidates: List[str] = []
        for h in helpers:
            if h == prev_domain:
                continue
            if h in specialists and self.domain_stats.get(h, {}).get("calls", 0) < self.max_domain_calls:
                candidates.append(h)

        # Fallback: try some generic helpers if nothing selected
        if not candidates:
            for h in ["research", "facts", "memory", "general", "simulation", "image", "sound"]:
                if h == prev_domain:
                    continue
                if h in specialists and self.domain_stats.get(h, {}).get("calls", 0) < self.max_domain_calls:
                    candidates.append(h)

        if not candidates:
            return None

        # If no weights for this domain, keep original priority order
        weights_for_domain = self.helper_weights.get(current_domain)
        if not weights_for_domain:
            return candidates[0]

        # Otherwise pick candidate with max weight (default weight = 1.0)
        best_helper = None
        best_score = float("-inf")
        for h in candidates:
            score = float(weights_for_domain.get(h, 1.0))
            if score > best_score:
                best_score = score
                best_helper = h

        return best_helper or candidates[0]

    # ========================================================
    #  WOT REQUEST / INTENT / BRANCH PARSERS
    # ========================================================

    def _extract_wot_request(self, text: str) -> str:
        """
        Parse "WOT_REQUEST: <TOKEN>" from specialist output.

        Normalization rules:
          - If token is NONE   → returns "NONE"
          - If token is MEMORY → returns "MEMORY"
          - Otherwise returns the *lowercase* domain name
            (so "MATH" / "Math" → "math"), compatible with Router keys.

        If absent, default to "NONE".
        """
        if not text or "WOT_REQUEST:" not in text:
            return "NONE"

        raw_line = text.split("WOT_REQUEST:", 1)[1]
        # Only take the first line after the marker
        raw = raw_line.split("\n", 1)[0].strip()
        if not raw:
            return "NONE"

        tok_upper = raw.upper()
        if tok_upper == "NONE":
            return "NONE"
        if tok_upper == "MEMORY":
            return "MEMORY"

        # Domain names: normalize to lower-case for compatibility
        return raw.strip().lower()

    def _extract_memory_query(self, text: str, default: str) -> str:
        """
        Parse "MEMORY_QUERY: <...>" if present; fallback to original query.
        """
        if not text or "MEMORY_QUERY:" not in text:
            return default
        line = text.split("MEMORY_QUERY:", 1)[1].split("\n", 1)[0].strip()
        return line or default

    def _extract_intent(self, text: str) -> Optional[str]:
        """
        Parse "INTENT: <...>" if present; return label or None.
        """
        if not text or "INTENT:" not in text:
            return None
        line = text.split("INTENT:", 1)[1].split("\n", 1)[0].strip()
        return line or None

    def _extract_branch(self, text: str) -> Optional[str]:
        """
        Parse "BRANCH: <...>" if present; return token or None.
        """
        if not text or "BRANCH:" not in text:
            return None
        line = text.split("BRANCH:", 1)[1].split("\n", 1)[0].strip()
        return line or None

    # ========================================================
    #  PACKET BUILDERS
    # ========================================================

    def _build_wot_packet(self, query: str) -> str:
        """
        First packet sent to the entry domain.
        Contains:
            - USER QUERY
            - MEMORY CONTEXT (if any)
            - Note that no previous specialists have spoken yet.
        """
        mem_section = self._format_memory_section()

        return f"""
USER QUERY:
{query}

MEMORY CONTEXT (PAST DIARY — NOT GUARANTEED TRUE):
{mem_section}

CROSS-DOMAIN CONTEXT:
None yet — this is the first domain.

COT HISTORY:
No history yet (first step).

INTENT CONTEXT:
No explicit intents yet.

INSTRUCTIONS:
Provide your domain-specific reasoning.
Be honest about limitations; if the task exceeds your capability
or you feel uncertain, explicitly say so.
If needed, request another domain using:
  WOT_REQUEST: <domain>

To refresh diary (if supported):
  WOT_REQUEST: MEMORY
(optional)
  MEMORY_QUERY: <query>

(Optional metadata you may output for WoT:
  INTENT: <short label of what you're trying to do>
  BRANCH: <core|sim|image|sound|... if you want to tag this reasoning stream>
)
"""

    def _build_full_context_packet(self, query: str) -> str:
        """
        Full packet sent to any domain after the first step.
        Contains:
            - USER QUERY
            - MEMORY CONTEXT
            - ALL domain CoTs so far (latest snapshot)
            - Compact CoT history per domain
            - Intent trace summary (last few steps)
        """
        mem_section = self._format_memory_section()

        # Latest CoTs
        domain_dump = "\n\n".join(
            f"== {d.upper()} (LATEST) ==\n{self.cots[d]}"
            for d in self.domains
            if self.cots[d].strip()
        )
        if not domain_dump.strip():
            domain_dump = "[No previous domain reasoning yet.]"

        # CoT history (last few per domain)
        history_dump_parts: List[str] = []
        for d in self.domains:
            hist = self.cot_history.get(d) or []
            if not hist:
                continue
            # show last up to 3 entries
            recent = hist[-3:]
            history_dump_parts.append(f"== {d.upper()} HISTORY (most recent first) ==")
            for idx, txt in enumerate(reversed(recent), start=1):
                history_dump_parts.append(f"[{idx}] ---")
                history_dump_parts.append(txt)
        history_dump = "\n".join(history_dump_parts) if history_dump_parts else "[No CoT history yet.]"

        # Intent trace (short, last few steps)
        intent_dump_parts: List[str] = []
        if self.intent_trace:
            intent_dump_parts.append("INTENT TRACE (recent steps):")
            for rec in self.intent_trace[-6:]:
                step = rec.get("step")
                dom = rec.get("domain")
                intent = rec.get("intent") or "none"
                wot = rec.get("wot_request") or "NONE"
                branch = rec.get("branch") or "core"
                intent_dump_parts.append(
                    f"- step={step}, domain={dom}, branch={branch}, intent={intent}, wot_request={wot}"
                )
        intent_dump = "\n".join(intent_dump_parts) if intent_dump_parts else "No explicit intents yet."

        return f"""
USER QUERY:
{query}

MEMORY CONTEXT (PAST DIARY — NOT GUARANTEED TRUE):
{mem_section}

CROSS-DOMAIN CONTEXT (LATEST SNAPSHOTS):
{domain_dump}

COT HISTORY (PER DOMAIN, TRUNCATED):
{history_dump}

INTENT CONTEXT (LAST FEW STEPS):
{intent_dump}

INSTRUCTIONS:
- Read ALL domain reasoning + diary context.
- Fix inconsistencies ONLY inside YOUR domain.
- Be honest about your own limitations; do not fake precision.
- Treat diary text strictly as past experiences, not guaranteed truth.
- If you need another domain → WOT_REQUEST: <domain>
- If you need deeper diary → WOT_REQUEST: MEMORY
  (optionally)
    MEMORY_QUERY: <query>

(Optional metadata you may output for WoT:
  INTENT: <short label of what you're trying to do>
  BRANCH: <core|sim|image|sound|... if you want to tag this reasoning stream>
)
"""

    # ========================================================
    #  MEMORY FORMATTER (SAFE + TRUNCATED)
    # ========================================================

    def _format_memory_section(self) -> str:
        """
        Render memory_context into a compact, bounded section.

        Includes:
            - query used
            - up to 12 highlights
            - truncated summary
            - up to 2 diary blocks (truncated)

        Supports both:
            - "raw_blocks" (from MemoryLLM v12+)
            - "blocks"     (older layout)
        """

        if not self.memory_context:
            return "No diary memory loaded.\n"

        mc = self.memory_context
        lines: List[str] = []

        # Query
        q = mc.get("query") or ""
        if q:
            lines.append(f"- Diary query used: {q}")

        # Highlights
        highlights = mc.get("highlights") or []
        if highlights:
            lines.append("HIGHLIGHTS (past patterns):")
            for h in highlights[:12]:
                lines.append(f"  - {h}")
            if len(highlights) > 12:
                lines.append(f"  ... (+{len(highlights) - 12} more)")

        # Summary (truncated)
        summary = (mc.get("memory_summary") or "").strip()
        if summary:
            if len(summary) > 800:
                summary = summary[:800].rstrip() + " ... [truncated]"
            lines.append("")
            lines.append("SUMMARY (past-focused):")
            for line in summary.splitlines():
                lines.append("  " + line.strip())

        # Optional diary blocks (truncated)
        blocks = mc.get("blocks") or mc.get("raw_blocks") or []
        if isinstance(blocks, list) and blocks:
            max_blocks = 2
            lines.append("")
            lines.append(f"BLOCKS (showing up to {max_blocks}):")
            for idx, b in enumerate(blocks[:max_blocks], start=1):
                # robust if legacy dicts miss some keys
                if isinstance(b, dict):
                    title = b.get("title") or "Untitled"
                    ts = b.get("timestamp") or "unknown"
                    kind = b.get("kind") or "unknown"
                    raw = (b.get("raw") or "").strip()
                else:
                    title = "Legacy Block"
                    ts = "unknown"
                    kind = "unknown"
                    raw = str(b).strip()

                if len(raw) > 600:
                    raw = raw[:600].rstrip() + " ... [truncated]"

                lines.append(f"  [BLOCK {idx}] {title} (ts={ts}, kind={kind})")
                for line in raw.splitlines():
                    lines.append("    " + line.strip())

        return "\n".join(lines) or "Diary context present but empty."

    # ========================================================
    #  INTENT + LOOP WINDOW UTILITIES
    # ========================================================

    def _register_intent_from_output(self, step_index: int, domain: str, output: str) -> None:
        """
        Inspect a domain output for INTENT: / BRANCH: and log to intent_trace.
        """
        intent = self._extract_intent(output) or None
        branch = self._extract_branch(output) or self.branch_tags.get(domain, "core")

        # Update branch tag for this domain (so later we know its "track")
        self.branch_tags[domain] = branch or "core"

        rec = {
            "step": step_index,
            "domain": domain,
            "intent": intent,
            "branch": branch,
            "wot_request": self._extract_wot_request(output),
        }
        self.intent_trace.append(rec)
        # keep last ~32 intent records
        if len(self.intent_trace) > 32:
            self.intent_trace = self.intent_trace[-32:]

    def _update_loop_window(self, current_domain: str, wot_request: str) -> None:
        """
        Maintain a sliding window of recent (domain, wot_request) pairs
        to detect oscillation / collapsed reasoning loops.
        """
        pair = (current_domain, wot_request)
        self.loop_window.append(pair)
        if len(self.loop_window) > self.loop_window_size:
            self.loop_window = self.loop_window[-self.loop_window_size :]

    def _loop_pattern_detected(self) -> bool:
        """
        Detect simple loop/oscillation patterns like:
          - ABAB
          - AAAAA...
        or very low diversity in recent steps.
        """
        win = self.loop_window
        if len(win) < 4:
            return False

        # Very low diversity with enough length → likely collapsed loop
        if len(set(win)) <= 2 and len(win) >= 4:
            return True

        # ABAB pattern: last 4 pairs alternate between two states
        last4 = win[-4:]
        if len(set(last4)) == 2 and last4[0] == last4[2] and last4[1] == last4[3]:
            return True

        return False
