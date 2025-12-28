# ============================================================
# ANM V0-OpenSource — LFM MODULE (Learning From Everything) V0-OpenSource
#  LawBook v1.2 • Verifier V0-OpenSource • Router V0-OpenSource
#  TrueWoT V0-OpenSource • PointGame V0-OpenSource • VFLLoop V0-OpenSource
#  Meta-Cognition • Meta-Efficiency • Auto-Mode • Prompt Optimization
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional, List
from collections import defaultdict
import statistics


class LFMModule:
    """
    LFM-V0-OpenSource MAX - COMPREHENSIVE LEARNING FROM EVERYTHING:
      - Learns from failures + successes + near-failures.
      - Learns from specialist confidence scores and meta-cognition.
      - Learns from efficiency metrics (tokens, time, efficiency scores).
      - Learns from auto-mode decisions (quick vs normal effectiveness).
      - Learns from prompt optimization results.
      - Learns from memory context usage patterns.
      - Learns from refiner quality and token usage.
      - Learns from WoT routing decisions and outcomes.
      - Learns from adaptive verifier analysis (question, reasoning, answer analysis).
      - Learns from specialist collaboration patterns.
      - Learns from failure contexts and prevention strategies.
      - Learns from near-failure risk factors and improvement strategies.
      - Adjusts routing (entry domain, domain weights).
      - Adjusts max WoT steps dynamically (difficulty + performance).
      - Penalizes unstable / hallucinating domains, rewards stable ones.
      - Tracks per-domain error heatmaps (including structural failures).
      - Computes WoT stability metrics with Verifier V0-OpenSource + VFLLoop hints.
      - Optionally emits a LawBook-safe Cloud Diary learning entry.
      - Crash-safe: never raises into Router / VFL / PG.
    """

    # ------------------------------------------------------------
    # Persistent scoring (in-memory; MemoryLLM may log snapshots)
    # ------------------------------------------------------------
    DOMAIN_SCORES: Dict[str, int] = {
        "general": 0,
        "math": 0,
        "physics": 0,
        "code": 0,
        "chemistry": 0,
        "biology": 0,
        "memory": 0,
        "research": 0,
        "facts": 0,
        "simulation": 0,
        "image": 0,
        "sound": 0,
        "internet": 0,
    }

    # Per-domain, per-mistake-type heatmap
    ERROR_STATS: Dict[str, Dict[str, int]] = {
        d: {} for d in DOMAIN_SCORES.keys()
    }

    def __init__(self, memory_core: Optional[Any] = None, enable_diary: bool = True) -> None:
        """
        memory_core:
          Optional handle to MemoryLLM / Diary-like object (NOT used directly).
          Instead, we expose 'diary_learning_entry' so caller can decide how to store.

        enable_diary:
          If False, diary_learning_entry will always be "".
        """
        self.memory = memory_core
        self.enable_diary = enable_diary
        self.last_analysis: Optional[Dict[str, Any]] = None
        
        # NEW: Comprehensive learning data structures
        # Confidence pattern learning
        self.CONFIDENCE_PATTERNS: Dict[str, List[float]] = defaultdict(list)  # domain -> [confidence_scores]
        self.CONFIDENCE_EFFECTIVENESS: Dict[str, Dict[str, int]] = defaultdict(lambda: {"high_success": 0, "high_fail": 0, "low_success": 0, "low_fail": 0})
        
        # Efficiency pattern learning
        self.EFFICIENCY_PATTERNS: Dict[str, List[float]] = defaultdict(list)  # domain -> [efficiency_scores]
        self.TOKEN_USAGE: Dict[str, List[int]] = defaultdict(list)  # domain -> [total_tokens]
        self.PROCESSING_TIME: Dict[str, List[float]] = defaultdict(list)  # domain -> [time_ms]
        self.TOKENS_PER_MS: Dict[str, List[float]] = defaultdict(list)  # domain -> [tokens_per_ms]
        
        # Auto-mode learning
        self.AUTO_MODE_DECISIONS: Dict[str, Dict[str, int]] = defaultdict(lambda: {"quick_success": 0, "quick_fail": 0, "normal_success": 0, "normal_fail": 0})
        
        # Prompt optimization learning
        self.PROMPT_OPTIMIZATION: Dict[str, Dict[str, int]] = defaultdict(lambda: {"optimized_success": 0, "optimized_fail": 0, "raw_success": 0, "raw_fail": 0})
        
        # Memory context learning
        self.MEMORY_USAGE: Dict[str, Dict[str, int]] = defaultdict(lambda: {"with_memory_success": 0, "with_memory_fail": 0, "no_memory_success": 0, "no_memory_fail": 0})
        
        # Refiner quality learning
        self.REFINER_QUALITY: List[Dict[str, Any]] = []  # Store refiner quality metrics
        
        # WoT routing learning
        self.WOT_ROUTING_PATTERNS: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "fail": 0})  # routing_pattern -> counts
        
        # Specialist collaboration learning
        self.COLLABORATION_PATTERNS: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "fail": 0})  # domain_combo -> counts
        
        # NEW: Failure and near-failure learning
        self.FAILURE_CONTEXTS: List[Dict[str, Any]] = []  # Detailed failure contexts
        self.NEAR_FAILURE_CONTEXTS: List[Dict[str, Any]] = []  # Near-failure contexts (approved but risky)
        self.FAILURE_PATTERNS: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "contexts": [],
            "common_causes": defaultdict(int),
            "prevention_strategies": [],
        })  # failure_type -> pattern data
        self.NEAR_FAILURE_PATTERNS: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "contexts": [],
            "risk_factors": defaultdict(int),
            "improvement_strategies": [],
        })  # near_failure_type -> pattern data

    # ============================================================
    #  MAIN ENTRY — learns from EVERYTHING possible
    # ============================================================
    def analyze(
        self,
        *,
        user_query: str,
        domain_cots: Dict[str, str],
        router_plan: Dict[str, Any],
        verification: Dict[str, Any],
        consistency: Optional[Dict[str, Any]] = None,
        vfl_meta: Optional[Dict[str, Any]] = None,
        pointgame_rfs: Optional[Dict[str, Any]] = None,
        # NEW: Comprehensive data sources
        specialist_outputs: Optional[Dict[str, Dict[str, Any]]] = None,
        refiner_metrics: Optional[Dict[str, Any]] = None,
        auto_mode_decision: Optional[bool] = None,  # True = quick mode, False = normal mode
        prompt_optimized: Optional[bool] = None,
        memory_used: Optional[bool] = None,
        processing_metrics: Optional[Dict[str, Any]] = None,
        wot_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        COMPREHENSIVE learner - learns from everything possible.

        Inputs:
          - user_query: original user question
          - domain_cots: {domain_name: cot_text} (raw internal CoTs)
          - router_plan: Router strategy dict (entry_specialist, max_steps, risk_score, etc.)
          - verification: Verifier v13 decision dict (status, notes, score, issues)
          - consistency: optional ConsistencyChecker output (rerun flag, loop notes, etc.)
          - vfl_meta: optional VFLLoop metadata (total_attempts, approved, reason)
          - pointgame_rfs: optional Router Feedback Signal from PointGame v3.0
          - specialist_outputs: {domain: {confidence, efficiency, tokens, time, etc.}}
          - refiner_metrics: {quality_score, tokens, time, etc.}
          - auto_mode_decision: True if quick mode was used, False if normal mode
          - prompt_optimized: True if prompt was optimized
          - memory_used: True if memory context was used
          - processing_metrics: {total_tokens, total_time_ms, etc.}
          - wot_steps: List of WoT routing steps with outcomes

        Returns:
          {
            "mistake_type": str,
            "lesson": str,
            "fix_recommendation": str,
            "diary_learning_entry": str,
            "domain_scores": {...},
            "error_stats": {...},
            "wot_stability": {...},
            "difficulty": "easy|medium|hard|insane|unknown",
            "meta": {
                "pointgame_rfs": {...} or None,
                "confidence_patterns": {...},
                "efficiency_patterns": {...},
                "auto_mode_effectiveness": {...},
                "prompt_optimization_effectiveness": {...},
                "memory_effectiveness": {...},
            }
          }
        """

        consistency = consistency or {}
        status = (verification.get("status") or "").lower()
        notes = (verification.get("notes") or "").lower()
        issues = [str(x).lower() for x in verification.get("issues", [])]
        verifier_score = verification.get("score", 1.0)  # 0.0-1.0
        is_success = status == "approved"
        is_near_failure = is_success and (verifier_score < 0.7 or len(issues) > 0 or "warning" in notes.lower())

        # 1) Detect mistake type (Verifer v13 + fallback)
        mistake_type = self._detect_mistake_type(status, notes, issues)
        
        # NEW: Learn from failures and near-failures
        if not is_success:
            self._learn_from_failure(
                mistake_type=mistake_type,
                verification=verification,
                router_plan=router_plan,
                specialist_outputs=specialist_outputs,
                user_query=user_query,
            )
        elif is_near_failure:
            self._learn_from_near_failure(
                verification=verification,
                router_plan=router_plan,
                specialist_outputs=specialist_outputs,
                user_query=user_query,
            )

        # 2) Update domain scores + heatmaps (existing)
        self._update_domain_scores(mistake_type, router_plan)
        self._update_error_stats(mistake_type, router_plan)

        # 3) NEW: Learn from specialist outputs (confidence, efficiency, tokens, time)
        if specialist_outputs:
            self._learn_from_specialist_outputs(specialist_outputs, is_success, router_plan)

        # 4) NEW: Learn from efficiency metrics
        if processing_metrics:
            self._learn_from_efficiency_metrics(processing_metrics, is_success, router_plan)

        # 5) NEW: Learn from auto-mode decisions
        if auto_mode_decision is not None:
            self._learn_from_auto_mode(auto_mode_decision, is_success, router_plan)

        # 6) NEW: Learn from prompt optimization
        if prompt_optimized is not None:
            self._learn_from_prompt_optimization(prompt_optimized, is_success)

        # 7) NEW: Learn from memory usage
        if memory_used is not None:
            self._learn_from_memory_usage(memory_used, is_success)

        # 8) NEW: Learn from refiner quality
        if refiner_metrics:
            self._learn_from_refiner(refiner_metrics, is_success)

        # 9) NEW: Learn from WoT routing patterns
        if wot_steps:
            self._learn_from_wot_routing(wot_steps, is_success, router_plan)

        # 10) NEW: Learn from adaptive verifier analysis
        adaptive_analysis = verification.get("adaptive_analysis")
        if adaptive_analysis:
            self._learn_from_adaptive_verifier(adaptive_analysis, is_success, router_plan)

        # 10) Difficulty (Router > PG > heuristic)
        difficulty = router_plan.get("difficulty")
        if not difficulty:
            # Try risk_score if present
            if "risk_score" in router_plan:
                difficulty = self._difficulty_from_risk(float(router_plan.get("risk_score", 0.3)))
            # Try PG RFS difficulty if present
            elif pointgame_rfs and "difficulty" in pointgame_rfs:
                difficulty = str(pointgame_rfs["difficulty"])
            else:
                difficulty = self._estimate_difficulty(user_query)

        # 11) Lesson + fix text (meta-level; not user-facing)
        lesson = self._build_lesson(mistake_type, router_plan)
        fix = self._build_fix(mistake_type, router_plan)

        # 12) Diary entry (LawBook V0-OpenSource safe, PAST-ONLY)
        diary_entry = ""
        if self.enable_diary:
            diary_entry = self._build_diary_entry(
                mistake_type=mistake_type,
                user_query=user_query,
                router_plan=router_plan,
                verification=verification,
                difficulty=difficulty,
            )

        # 13) WoT stability metrics (for SelfAwarenessLLM / Router)
        wot_stability = self._compute_wot_stability(
            status=status,
            notes=notes,
            consistency=consistency,
            router_plan=router_plan,
            vfl_meta=vfl_meta,
        )

        # 14) NEW: Compile comprehensive meta-learning data
        meta_learning = {
            "pointgame_rfs": pointgame_rfs or None,
            "confidence_patterns": self._get_confidence_summary(),
            "efficiency_patterns": self._get_efficiency_summary(),
            "auto_mode_effectiveness": self._get_auto_mode_summary(),
            "prompt_optimization_effectiveness": self._get_prompt_opt_summary(),
            "memory_effectiveness": self._get_memory_summary(),
        }

        analysis = {
            "mistake_type": mistake_type,
            "lesson": lesson,
            "fix_recommendation": fix,
            "diary_learning_entry": diary_entry,
            "domain_scores": dict(self.DOMAIN_SCORES),
            "error_stats": {d: dict(stats) for d, stats in self.ERROR_STATS.items()},
            "wot_stability": wot_stability,
            "difficulty": difficulty,
            "meta": meta_learning,
            "failure_insights": self._get_failure_insights(),
            "near_failure_insights": self._get_near_failure_insights(),
        }

        self.last_analysis = analysis
        return analysis
    
    def _get_failure_insights(self) -> Dict[str, Any]:
        """Get insights from failure patterns."""
        insights = {
            "total_failures": len(self.FAILURE_CONTEXTS),
            "failure_types": {},
            "top_failure_causes": {},
            "prevention_strategies": {},
        }
        
        for mistake_type, pattern in self.FAILURE_PATTERNS.items():
            if pattern["count"] > 0:
                insights["failure_types"][mistake_type] = {
                    "count": pattern["count"],
                    "prevention_strategies": pattern.get("prevention_strategies", [])[:5],
                }
                
                # Top causes
                top_causes = sorted(
                    pattern["common_causes"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                insights["top_failure_causes"][mistake_type] = [
                    {"cause": cause, "count": count} for cause, count in top_causes
                ]
        
        return insights
    
    def _get_near_failure_insights(self) -> Dict[str, Any]:
        """Get insights from near-failure patterns."""
        insights = {
            "total_near_failures": len(self.NEAR_FAILURE_CONTEXTS),
            "near_failure_types": {},
            "top_risk_factors": {},
            "improvement_strategies": {},
        }
        
        for nf_type, pattern in self.NEAR_FAILURE_PATTERNS.items():
            if pattern["count"] > 0:
                insights["near_failure_types"][nf_type] = {
                    "count": pattern["count"],
                    "improvement_strategies": pattern.get("improvement_strategies", [])[:5],
                }
                
                # Top risk factors
                top_risks = sorted(
                    pattern["risk_factors"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                insights["top_risk_factors"][nf_type] = [
                    {"risk": risk, "count": count} for risk, count in top_risks
                ]
        
        return insights

    # ============================================================
    #  OPTIONAL: Hook for VFLLoop / Router (update_from_run)
    # ============================================================
    def update_from_run(self, run_result: Dict[str, Any]) -> None:
        """
        COMPREHENSIVE helper so VFLLoop or Router can call:

            lfm.update_from_run(router_result)

        Extracts ALL available data sources and learns from everything.
        This is entirely crash-safe and only uses fields if present.
        """

        try:
            user_query = (
                run_result.get("user_query")
                or run_result.get("router_plan", {}).get("user_query", "")
                or ""
            )
            if not user_query:
                # Can't learn much without knowing the original question
                return

            router_plan = run_result.get("router_plan", {}) or {}
            verification = run_result.get("verification", {}) or {}
            consistency = run_result.get("consistency", {}) or {}
            vfl_meta = run_result.get("vfl_meta", None)
            domain_cots = run_result.get("domain_cots", {}) or {}
            pointgame_rfs = run_result.get("pointgame_rfs")  # optional

            # NEW: Extract comprehensive data sources
            specialist_outputs = run_result.get("specialist_outputs") or run_result.get("wot_rounds", {})
            refiner_metrics = run_result.get("refiner_metrics") or {}
            auto_mode_decision = run_result.get("auto_mode_decision") or run_result.get("quick_mode")
            prompt_optimized = run_result.get("prompt_optimized") or run_result.get("optimized_query") is not None
            memory_used = run_result.get("memory_used") or run_result.get("memory_context") is not None
            processing_metrics = run_result.get("processing_metrics") or {}
            wot_steps = run_result.get("wot_steps") or run_result.get("wot_rounds_list", [])

            # Extract specialist metrics from WoT rounds if available
            if not specialist_outputs and "wot_rounds" in run_result:
                specialist_outputs = {}
                for round_data in run_result.get("wot_rounds", {}).values():
                    if isinstance(round_data, dict):
                        for domain, output in round_data.items():
                            if isinstance(output, str):
                                # Try to parse meta blocks from output
                                metrics = self._extract_metrics_from_output(output)
                                if metrics:
                                    specialist_outputs[domain] = metrics

            self.analyze(
                user_query=user_query,
                domain_cots=domain_cots,
                router_plan=router_plan,
                verification=verification,
                consistency=consistency,
                vfl_meta=vfl_meta,
                pointgame_rfs=pointgame_rfs,
                specialist_outputs=specialist_outputs,
                refiner_metrics=refiner_metrics,
                auto_mode_decision=auto_mode_decision,
                prompt_optimized=prompt_optimized,
                memory_used=memory_used,
                processing_metrics=processing_metrics,
                wot_steps=wot_steps,
            )
        except Exception:
            # LFM must NEVER crash the VFL loop / Router
            return
    
    def _extract_metrics_from_output(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract metrics from specialist output text (parses meta blocks)."""
        if not output:
            return None
        
        metrics = {}
        
        # Extract confidence
        import re
        conf_match = re.search(r'confidence:\s*(HIGH|MEDIUM|LOW)', output, re.IGNORECASE)
        if conf_match:
            metrics["confidence"] = conf_match.group(1).upper()
        
        # Extract confidence score
        conf_score_match = re.search(r'confidence_score:\s*([0-9.]+)', output, re.IGNORECASE)
        if conf_score_match:
            metrics["confidence_score"] = float(conf_score_match.group(1))
        
        # Extract efficiency
        eff_match = re.search(r'efficiency:\s*(EFFICIENT|INEFFICIENT)', output, re.IGNORECASE)
        if eff_match:
            metrics["efficiency"] = eff_match.group(1).upper()
        
        # Extract efficiency score
        eff_score_match = re.search(r'efficiency_score:\s*([0-9.]+)', output, re.IGNORECASE)
        if eff_score_match:
            metrics["efficiency_score"] = float(eff_score_match.group(1))
        
        # Extract token metrics
        tokens_match = re.search(r'total_tokens:\s*(\d+)', output, re.IGNORECASE)
        if tokens_match:
            metrics["total_tokens"] = int(tokens_match.group(1))
        
        # Extract processing time
        time_match = re.search(r'processing_time_ms:\s*([0-9.]+)', output, re.IGNORECASE)
        if time_match:
            metrics["processing_time_ms"] = float(time_match.group(1))
        
        # Extract tokens per ms
        tpm_match = re.search(r'tokens_per_ms:\s*([0-9.]+)', output, re.IGNORECASE)
        if tpm_match:
            metrics["tokens_per_ms"] = float(tpm_match.group(1))
        
        return metrics if metrics else None

    # ============================================================
    #  ROUTER PLAN ADJUSTMENT (consumed by Router v12)
    # ============================================================
    def adjust_plan(
        self,
        *,
        user_query: str,
        base_plan: Dict[str, Any],
        memory_snapshot: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        V0-OpenSource MAX — Real learning applied here.

        Router v12 uses this to tweak strategy BEFORE WoT begins.

        Inputs:
          - user_query: original query
          - base_plan: initial Router plan from PlannerLLM
          - memory_snapshot: optional list of Memory blocks (unused here,
                             but kept for forward compatibility)

        Returns:
          - plan: adjusted plan dict (entry_specialist, max_steps, strategy_tags, etc.)
        """

        plan = dict(base_plan)  # shallow copy for safety

        # ---------- 1) Improve entry specialist using DOMAIN_SCORES + confidence patterns ----------
        scored = sorted(self.DOMAIN_SCORES.items(), key=lambda x: x[1], reverse=True)
        best_domain, best_score = scored[0]

        # NEW: Also consider confidence patterns
        confidence_adjusted_scores = {}
        for domain, score in self.DOMAIN_SCORES.items():
            # Boost domains with high average confidence
            if domain in self.CONFIDENCE_PATTERNS and self.CONFIDENCE_PATTERNS[domain]:
                avg_conf = statistics.mean(self.CONFIDENCE_PATTERNS[domain])
                if avg_conf > 0.7:  # High confidence
                    score += 5
                elif avg_conf < 0.4:  # Low confidence
                    score -= 3
            confidence_adjusted_scores[domain] = score
        
        # Re-sort with confidence adjustments
        scored = sorted(confidence_adjusted_scores.items(), key=lambda x: x[1], reverse=True)
        best_domain, best_score = scored[0]

        # Only override if best domain is strongly positive AND is allowed in this plan
        active = plan.get("active_domains")
        if best_score >= 10:
            if not active or (isinstance(active, list) and best_domain in active):
                plan["entry_specialist"] = best_domain
            # if active_domains exists and best_domain not there, we don't force it

        # ---------- 2) Difficulty-aware WoT steps ----------
        # Prefer plan["difficulty"] if already set, else estimate
        difficulty = plan.get(
            "difficulty",
            self._estimate_difficulty(user_query),
        )
        plan["difficulty"] = difficulty

        max_steps = int(plan.get("max_steps", 16) or 16)
        score_sum = sum(self.DOMAIN_SCORES.values())

        # Global performance adjustment
        if score_sum < -20:
            # We are struggling overall → allow more thinking (but capped)
            max_steps = min(28, max_steps + 4)
        elif score_sum > 20:
            # We are performing well → compress reasoning a bit
            max_steps = max(8, max_steps - 4)

        # Difficulty-based tuning (final clamp)
        if difficulty == "easy":
            max_steps = min(max_steps, 12)
        elif difficulty == "medium":
            max_steps = max(10, min(max_steps, 18))
        elif difficulty == "hard":
            max_steps = max(14, min(max_steps, 24))
        elif difficulty == "insane":
            max_steps = max(18, min(max_steps, 28))

        if max_steps <= 0:
            max_steps = 12

        plan["max_steps"] = max_steps

        # ---------- 3) Strategy tags based on error heatmap + learned patterns ----------
        strategy_tags = set(plan.get("strategy_tags", []) or [])

        # Frequent hallucinations → stronger facts/research
        hallucination_count = sum(
            self.ERROR_STATS[d].get("hallucination", 0)
            for d in self.ERROR_STATS
        )
        if hallucination_count >= 3:
            strategy_tags.add("strong_facts")
            strategy_tags.add("strong_research")

        # Frequent incomplete reasoning → deeper WoT
        incomplete_count = sum(
            self.ERROR_STATS[d].get("incomplete_reasoning", 0)
            for d in self.ERROR_STATS
        )
        if incomplete_count >= 3:
            strategy_tags.add("deep_wot")

        # Structural failures → stricter verifier + stable routing
        structural_count = sum(
            self.ERROR_STATS[d].get("structural_failure", 0)
            for d in self.ERROR_STATS
        )
        if structural_count >= 1:
            strategy_tags.add("strict_verifier")
            strategy_tags.add("structural_sanity")

        # NEW: Use auto-mode effectiveness
        quick_success_rate = 0.0
        normal_success_rate = 0.0
        if "quick" in self.AUTO_MODE_DECISIONS:
            quick_stats = self.AUTO_MODE_DECISIONS["quick"]
            quick_total = quick_stats.get("quick_success", 0) + quick_stats.get("quick_fail", 0)
            if quick_total > 0:
                quick_success_rate = quick_stats.get("quick_success", 0) / quick_total
        
        if "normal" in self.AUTO_MODE_DECISIONS:
            normal_stats = self.AUTO_MODE_DECISIONS["normal"]
            normal_total = normal_stats.get("normal_success", 0) + normal_stats.get("normal_fail", 0)
            if normal_total > 0:
                normal_success_rate = normal_stats.get("normal_success", 0) / normal_total
        
        # If quick mode is significantly better, suggest it
        if quick_success_rate > normal_success_rate + 0.1 and quick_success_rate > 0.7:
            strategy_tags.add("prefer_quick_mode")
        elif normal_success_rate > quick_success_rate + 0.1 and normal_success_rate > 0.7:
            strategy_tags.add("prefer_normal_mode")

        # NEW: Use memory effectiveness
        if "with_memory" in self.MEMORY_USAGE:
            mem_stats = self.MEMORY_USAGE["with_memory"]
            mem_total = mem_stats.get("with_memory_success", 0) + mem_stats.get("with_memory_fail", 0)
            if mem_total > 5:
                mem_success_rate = mem_stats.get("with_memory_success", 0) / mem_total
                if mem_success_rate > 0.8:
                    strategy_tags.add("prefer_memory")
                elif mem_success_rate < 0.5:
                    strategy_tags.add("avoid_memory")

        # NEW: Use prompt optimization effectiveness
        if "optimized" in self.PROMPT_OPTIMIZATION:
            opt_stats = self.PROMPT_OPTIMIZATION["optimized"]
            opt_total = opt_stats.get("optimized_success", 0) + opt_stats.get("optimized_fail", 0)
            if opt_total > 5:
                opt_success_rate = opt_stats.get("optimized_success", 0) / opt_total
                if opt_success_rate > 0.8:
                    strategy_tags.add("prefer_optimization")
                elif opt_success_rate < 0.5:
                    strategy_tags.add("skip_optimization")

        # NEW: Apply failure prevention strategies
        failure_prevention_tags = self._get_failure_prevention_tags(user_query, plan)
        strategy_tags.update(failure_prevention_tags)
        
        # NEW: Apply near-failure improvement strategies
        near_failure_tags = self._get_near_failure_improvement_tags(user_query, plan)
        strategy_tags.update(near_failure_tags)

        if strategy_tags:
            plan["strategy_tags"] = sorted(strategy_tags)

        return plan
    
    def _get_failure_prevention_tags(self, user_query: str, router_plan: Dict[str, Any]) -> set:
        """Get strategy tags to prevent known failure patterns."""
        tags = set()
        query_keywords = self._extract_keywords(user_query)
        entry_domain = router_plan.get("entry_specialist", "unknown").lower()
        
        # Check recent failures for similar patterns
        for failure in self.FAILURE_CONTEXTS[-20:]:  # Check recent 20 failures
            # Check if similar query keywords
            failure_keywords = failure.get("query_keywords", [])
            keyword_overlap = len(set(query_keywords) & set(failure_keywords))
            
            if keyword_overlap >= 2:  # Similar query
                mistake_type = failure.get("mistake_type", "")
                pattern = self.FAILURE_PATTERNS.get(mistake_type, {})
                
                # Check if same entry domain failed
                if failure.get("entry_specialist", "").lower() == entry_domain:
                    # Apply prevention strategies
                    if mistake_type == "hallucination":
                        tags.add("strong_facts")
                        tags.add("strong_research")
                    elif mistake_type == "incomplete_reasoning":
                        tags.add("deep_wot")
                        tags.add("extra_validation")
                    elif mistake_type == "domain_misuse":
                        tags.add("strict_domain_check")
                    elif mistake_type == "low_confidence":
                        tags.add("boost_confidence")
                        tags.add("additional_validation")
        
        return tags
    
    def _get_near_failure_improvement_tags(self, user_query: str, router_plan: Dict[str, Any]) -> set:
        """Get strategy tags to improve near-failure cases."""
        tags = set()
        query_keywords = self._extract_keywords(user_query)
        entry_domain = router_plan.get("entry_specialist", "unknown").lower()
        
        # Check recent near-failures for similar patterns
        for near_failure in self.NEAR_FAILURE_CONTEXTS[-20:]:  # Check recent 20
            # Check if similar query keywords
            nf_keywords = near_failure.get("query_keywords", [])
            keyword_overlap = len(set(query_keywords) & set(nf_keywords))
            
            if keyword_overlap >= 2:  # Similar query
                near_failure_type = near_failure.get("near_failure_type", "")
                pattern = self.NEAR_FAILURE_PATTERNS.get(near_failure_type, {})
                
                # Check if same entry domain had issues
                if near_failure.get("entry_specialist", "").lower() == entry_domain:
                    # Apply improvement strategies
                    if near_failure_type == "low_score":
                        tags.add("extra_validation")
                        tags.add("strict_verifier")
                    elif near_failure_type == "multiple_issues":
                        tags.add("pre_verification")
                        tags.add("strict_checks")
                    elif near_failure_type == "incomplete":
                        tags.add("comprehensive_coverage")
                        tags.add("check_all_aspects")
                    elif near_failure_type == "uncertainty":
                        tags.add("boost_confidence")
                        tags.add("additional_research")
        
        return tags

    # ============================================================
    #  NEW: COMPREHENSIVE LEARNING METHODS
    # ============================================================
    
    def _learn_from_specialist_outputs(
        self,
        specialist_outputs: Dict[str, Dict[str, Any]],
        is_success: bool,
        router_plan: Dict[str, Any],
    ) -> None:
        """Learn from specialist confidence, efficiency, and performance metrics."""
        entry_domain = router_plan.get("entry_specialist", "general").lower()
        
        for domain, metrics in specialist_outputs.items():
            domain = domain.lower()
            
            # Learn from confidence scores
            confidence = metrics.get("confidence", "unknown")
            confidence_score = metrics.get("confidence_score", 0.5)
            
            if confidence_score > 0:
                self.CONFIDENCE_PATTERNS[domain].append(confidence_score)
                # Keep only recent 100 scores
                if len(self.CONFIDENCE_PATTERNS[domain]) > 100:
                    self.CONFIDENCE_PATTERNS[domain] = self.CONFIDENCE_PATTERNS[domain][-100:]
            
            # Track confidence effectiveness
            if confidence.upper() == "HIGH":
                if is_success:
                    self.CONFIDENCE_EFFECTIVENESS[domain]["high_success"] += 1
                else:
                    self.CONFIDENCE_EFFECTIVENESS[domain]["high_fail"] += 1
            elif confidence.upper() == "LOW":
                if is_success:
                    self.CONFIDENCE_EFFECTIVENESS[domain]["low_success"] += 1
                else:
                    self.CONFIDENCE_EFFECTIVENESS[domain]["low_fail"] += 1
            
            # Learn from efficiency metrics
            efficiency_score = metrics.get("efficiency_score", 0.5)
            if efficiency_score > 0:
                self.EFFICIENCY_PATTERNS[domain].append(efficiency_score)
                if len(self.EFFICIENCY_PATTERNS[domain]) > 100:
                    self.EFFICIENCY_PATTERNS[domain] = self.EFFICIENCY_PATTERNS[domain][-100:]
            
            # Learn from token usage
            total_tokens = metrics.get("total_tokens", 0)
            if total_tokens > 0:
                self.TOKEN_USAGE[domain].append(total_tokens)
                if len(self.TOKEN_USAGE[domain]) > 100:
                    self.TOKEN_USAGE[domain] = self.TOKEN_USAGE[domain][-100:]
            
            # Learn from processing time
            processing_time = metrics.get("processing_time_ms", 0.0)
            if processing_time > 0:
                self.PROCESSING_TIME[domain].append(processing_time)
                if len(self.PROCESSING_TIME[domain]) > 100:
                    self.PROCESSING_TIME[domain] = self.PROCESSING_TIME[domain][-100:]
            
            # Learn from tokens per ms
            tokens_per_ms = metrics.get("tokens_per_ms", 0.0)
            if tokens_per_ms > 0:
                self.TOKENS_PER_MS[domain].append(tokens_per_ms)
                if len(self.TOKENS_PER_MS[domain]) > 100:
                    self.TOKENS_PER_MS[domain] = self.TOKENS_PER_MS[domain][-100:]
    
    def _learn_from_efficiency_metrics(
        self,
        processing_metrics: Dict[str, Any],
        is_success: bool,
        router_plan: Dict[str, Any],
    ) -> None:
        """Learn from overall processing efficiency."""
        # Track total token usage and processing time patterns
        total_tokens = processing_metrics.get("total_tokens", 0)
        total_time_ms = processing_metrics.get("total_time_ms", 0.0)
        
        # Learn optimal token/time ratios for success
        if total_tokens > 0 and total_time_ms > 0:
            efficiency_ratio = total_tokens / total_time_ms
            # Store for pattern analysis (can be used to optimize future queries)
            pass  # Can add more sophisticated learning here
    
    def _learn_from_auto_mode(
        self,
        used_quick_mode: bool,
        is_success: bool,
        router_plan: Dict[str, Any],
    ) -> None:
        """Learn from auto-mode decisions (quick vs normal mode effectiveness)."""
        mode_key = "quick" if used_quick_mode else "normal"
        
        if is_success:
            self.AUTO_MODE_DECISIONS[mode_key]["quick_success" if used_quick_mode else "normal_success"] += 1
        else:
            self.AUTO_MODE_DECISIONS[mode_key]["quick_fail" if used_quick_mode else "normal_fail"] += 1
    
    def _learn_from_prompt_optimization(
        self,
        was_optimized: bool,
        is_success: bool,
    ) -> None:
        """Learn from prompt optimization effectiveness."""
        opt_key = "optimized" if was_optimized else "raw"
        
        if is_success:
            self.PROMPT_OPTIMIZATION[opt_key]["optimized_success" if was_optimized else "raw_success"] += 1
        else:
            self.PROMPT_OPTIMIZATION[opt_key]["optimized_fail" if was_optimized else "raw_fail"] += 1
    
    def _learn_from_memory_usage(
        self,
        memory_used: bool,
        is_success: bool,
    ) -> None:
        """Learn from memory context usage effectiveness."""
        if is_success:
            if memory_used:
                self.MEMORY_USAGE["with_memory"]["with_memory_success"] += 1
            else:
                self.MEMORY_USAGE["no_memory"]["no_memory_success"] += 1
        else:
            if memory_used:
                self.MEMORY_USAGE["with_memory"]["with_memory_fail"] += 1
            else:
                self.MEMORY_USAGE["no_memory"]["no_memory_fail"] += 1
    
    def _learn_from_refiner(
        self,
        refiner_metrics: Dict[str, Any],
        is_success: bool,
    ) -> None:
        """Learn from refiner quality metrics."""
        self.REFINER_QUALITY.append({
            "success": is_success,
            "metrics": refiner_metrics,
        })
        # Keep only recent 100 entries
        if len(self.REFINER_QUALITY) > 100:
            self.REFINER_QUALITY = self.REFINER_QUALITY[-100:]
    
    def _learn_from_wot_routing(
        self,
        wot_steps: List[Dict[str, Any]],
        is_success: bool,
        router_plan: Dict[str, Any],
    ) -> None:
        """Learn from WoT routing patterns and specialist collaborations."""
        # Extract routing pattern (sequence of domains)
        routing_sequence = []
        for step in wot_steps:
            domain = step.get("domain") or step.get("specialist", "unknown")
            routing_sequence.append(domain.lower())
        
        if routing_sequence:
            # Create pattern key
            pattern_key = "->".join(routing_sequence)
            
            if is_success:
                self.WOT_ROUTING_PATTERNS[pattern_key]["success"] += 1
            else:
                self.WOT_ROUTING_PATTERNS[pattern_key]["fail"] += 1
            
            # Learn collaboration patterns (domain combinations)
            if len(routing_sequence) > 1:
                # Track all pairs
                for i in range(len(routing_sequence) - 1):
                    combo = f"{routing_sequence[i]}+{routing_sequence[i+1]}"
                    if is_success:
                        self.COLLABORATION_PATTERNS[combo]["success"] += 1
                    else:
                        self.COLLABORATION_PATTERNS[combo]["fail"] += 1
    
    def _get_confidence_summary(self) -> Dict[str, Any]:
        """Get summary of confidence pattern learning."""
        summary = {}
        for domain, scores in self.CONFIDENCE_PATTERNS.items():
            if scores:
                summary[domain] = {
                    "avg_confidence": statistics.mean(scores),
                    "count": len(scores),
                }
        return summary
    
    def _get_efficiency_summary(self) -> Dict[str, Any]:
        """Get summary of efficiency pattern learning."""
        summary = {}
        for domain, scores in self.EFFICIENCY_PATTERNS.items():
            if scores:
                summary[domain] = {
                    "avg_efficiency": statistics.mean(scores),
                    "count": len(scores),
                }
        return summary
    
    def _get_auto_mode_summary(self) -> Dict[str, Any]:
        """Get summary of auto-mode effectiveness."""
        summary = {}
        for mode, stats in self.AUTO_MODE_DECISIONS.items():
            total = sum(stats.values())
            if total > 0:
                success_key = f"{mode}_success"
                fail_key = f"{mode}_fail"
                success_count = stats.get(success_key, 0)
                fail_count = stats.get(fail_key, 0)
                summary[mode] = {
                    "success_rate": success_count / total if total > 0 else 0.0,
                    "total": total,
                }
        return summary
    
    def _get_prompt_opt_summary(self) -> Dict[str, Any]:
        """Get summary of prompt optimization effectiveness."""
        summary = {}
        for opt_type, stats in self.PROMPT_OPTIMIZATION.items():
            total = sum(stats.values())
            if total > 0:
                success_key = f"{opt_type}_success"
                fail_key = f"{opt_type}_fail"
                success_count = stats.get(success_key, 0)
                summary[opt_type] = {
                    "success_rate": success_count / total if total > 0 else 0.0,
                    "total": total,
                }
        return summary
    
    def _get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of memory usage effectiveness."""
        summary = {}
        for mem_type, stats in self.MEMORY_USAGE.items():
            total = sum(stats.values())
            if total > 0:
                success_key = f"{mem_type}_success"
                success_count = stats.get(success_key, 0)
                summary[mem_type] = {
                    "success_rate": success_count / total if total > 0 else 0.0,
                    "total": total,
                }
        return summary
    
    def _learn_from_adaptive_verifier(
        self,
        adaptive_analysis: Dict[str, Any],
        is_success: bool,
        router_plan: Dict[str, Any],
    ) -> None:
        """Learn from adaptive verifier's question, reasoning, and answer analysis."""
        question_analysis = adaptive_analysis.get("question_analysis", {})
        reasoning_analysis = adaptive_analysis.get("reasoning_analysis", {})
        answer_analysis = adaptive_analysis.get("answer_analysis", {})
        
        # Learn query type effectiveness
        query_type = question_analysis.get("query_type", "unknown")
        complexity = question_analysis.get("complexity", "medium")
        
        # Track query type + complexity patterns
        type_complexity_key = f"{query_type}_{complexity}"
        if type_complexity_key not in self.WOT_ROUTING_PATTERNS:
            self.WOT_ROUTING_PATTERNS[type_complexity_key] = {"success": 0, "fail": 0}
        
        if is_success:
            self.WOT_ROUTING_PATTERNS[type_complexity_key]["success"] += 1
        else:
            self.WOT_ROUTING_PATTERNS[type_complexity_key]["fail"] += 1
        
        # Learn reasoning quality patterns
        reasoning_quality = reasoning_analysis.get("reasoning_quality", "unknown")
        if reasoning_quality != "unknown":
            quality_key = f"reasoning_{reasoning_quality}"
            if quality_key not in self.WOT_ROUTING_PATTERNS:
                self.WOT_ROUTING_PATTERNS[quality_key] = {"success": 0, "fail": 0}
            
            if is_success:
                self.WOT_ROUTING_PATTERNS[quality_key]["success"] += 1
            else:
                self.WOT_ROUTING_PATTERNS[quality_key]["fail"] += 1
        
        # Learn answer completeness patterns
        completeness = answer_analysis.get("completeness", "unknown")
        if completeness != "unknown":
            completeness_key = f"answer_{completeness}"
            if completeness_key not in self.WOT_ROUTING_PATTERNS:
                self.WOT_ROUTING_PATTERNS[completeness_key] = {"success": 0, "fail": 0}
            
            if is_success:
                self.WOT_ROUTING_PATTERNS[completeness_key]["success"] += 1
            else:
                self.WOT_ROUTING_PATTERNS[completeness_key]["fail"] += 1
        
        # Learn format matching effectiveness
        has_expected_format = answer_analysis.get("has_expected_format", False)
        if has_expected_format:
            format_key = "format_matched"
        else:
            format_key = "format_mismatched"
        
        if format_key not in self.WOT_ROUTING_PATTERNS:
            self.WOT_ROUTING_PATTERNS[format_key] = {"success": 0, "fail": 0}
        
        if is_success:
            self.WOT_ROUTING_PATTERNS[format_key]["success"] += 1
        else:
            self.WOT_ROUTING_PATTERNS[format_key]["fail"] += 1
    
    def _learn_from_failure(
        self,
        mistake_type: str,
        verification: Dict[str, Any],
        router_plan: Dict[str, Any],
        specialist_outputs: Optional[Dict[str, Dict[str, Any]]],
        user_query: str,
    ) -> None:
        """Learn from complete failures - what went wrong and why."""
        failure_context = {
            "mistake_type": mistake_type,
            "verifier_status": verification.get("status", ""),
            "verifier_score": verification.get("score", 0.0),
            "verifier_notes": verification.get("notes", ""),
            "verifier_issues": verification.get("issues", []),
            "entry_specialist": router_plan.get("entry_specialist", "unknown"),
            "active_domains": router_plan.get("active_domains", []),
            "max_steps": router_plan.get("max_steps", 0),
            "difficulty": router_plan.get("difficulty", "unknown"),
            "query_length": len(user_query),
            "query_keywords": self._extract_keywords(user_query),
            "specialist_confidences": {},
            "specialist_efficiencies": {},
            "timestamp": None,  # Can be set by caller if needed
        }
        
        # Extract specialist data if available
        if specialist_outputs:
            for domain, metrics in specialist_outputs.items():
                failure_context["specialist_confidences"][domain] = metrics.get("confidence_score", 0.0)
                failure_context["specialist_efficiencies"][domain] = metrics.get("efficiency_score", 0.0)
        
        # Store failure context
        self.FAILURE_CONTEXTS.append(failure_context)
        if len(self.FAILURE_CONTEXTS) > 200:  # Keep recent 200 failures
            self.FAILURE_CONTEXTS = self.FAILURE_CONTEXTS[-200:]
        
        # Update failure pattern
        pattern = self.FAILURE_PATTERNS[mistake_type]
        pattern["count"] += 1
        pattern["contexts"].append(failure_context)
        if len(pattern["contexts"]) > 50:  # Keep recent 50 per type
            pattern["contexts"] = pattern["contexts"][-50:]
        
        # Identify common causes
        entry_domain = router_plan.get("entry_specialist", "unknown").lower()
        pattern["common_causes"][f"entry_domain_{entry_domain}"] += 1
        
        if verification.get("issues"):
            for issue in verification.get("issues", []):
                pattern["common_causes"][f"issue_{str(issue).lower()}"] += 1
        
        # Identify low confidence specialists
        if specialist_outputs:
            for domain, metrics in specialist_outputs.items():
                conf = metrics.get("confidence_score", 0.5)
                if conf < 0.4:
                    pattern["common_causes"][f"low_confidence_{domain}"] += 1
        
        # Generate prevention strategies
        self._update_failure_prevention_strategies(mistake_type, failure_context)
    
    def _learn_from_near_failure(
        self,
        verification: Dict[str, Any],
        router_plan: Dict[str, Any],
        specialist_outputs: Optional[Dict[str, Dict[str, Any]]],
        user_query: str,
    ) -> None:
        """Learn from near-failures - approved but risky cases."""
        near_failure_type = self._classify_near_failure(verification)
        
        near_failure_context = {
            "near_failure_type": near_failure_type,
            "verifier_score": verification.get("score", 1.0),
            "verifier_notes": verification.get("notes", ""),
            "verifier_issues": verification.get("issues", []),
            "entry_specialist": router_plan.get("entry_specialist", "unknown"),
            "active_domains": router_plan.get("active_domains", []),
            "max_steps": router_plan.get("max_steps", 0),
            "difficulty": router_plan.get("difficulty", "unknown"),
            "query_length": len(user_query),
            "query_keywords": self._extract_keywords(user_query),
            "specialist_confidences": {},
            "specialist_efficiencies": {},
        }
        
        # Extract specialist data if available
        if specialist_outputs:
            for domain, metrics in specialist_outputs.items():
                near_failure_context["specialist_confidences"][domain] = metrics.get("confidence_score", 0.0)
                near_failure_context["specialist_efficiencies"][domain] = metrics.get("efficiency_score", 0.0)
        
        # Store near-failure context
        self.NEAR_FAILURE_CONTEXTS.append(near_failure_context)
        if len(self.NEAR_FAILURE_CONTEXTS) > 200:  # Keep recent 200
            self.NEAR_FAILURE_CONTEXTS = self.NEAR_FAILURE_CONTEXTS[-200:]
        
        # Update near-failure pattern
        pattern = self.NEAR_FAILURE_PATTERNS[near_failure_type]
        pattern["count"] += 1
        pattern["contexts"].append(near_failure_context)
        if len(pattern["contexts"]) > 50:  # Keep recent 50 per type
            pattern["contexts"] = pattern["contexts"][-50:]
        
        # Identify risk factors
        entry_domain = router_plan.get("entry_specialist", "unknown").lower()
        pattern["risk_factors"][f"entry_domain_{entry_domain}"] += 1
        
        if verification.get("issues"):
            for issue in verification.get("issues", []):
                pattern["risk_factors"][f"issue_{str(issue).lower()}"] += 1
        
        # Identify borderline confidence specialists
        if specialist_outputs:
            for domain, metrics in specialist_outputs.items():
                conf = metrics.get("confidence_score", 0.5)
                if 0.4 <= conf < 0.6:  # Medium confidence
                    pattern["risk_factors"][f"medium_confidence_{domain}"] += 1
        
        # Generate improvement strategies
        self._update_near_failure_improvement_strategies(near_failure_type, near_failure_context)
    
    def _classify_near_failure(self, verification: Dict[str, Any]) -> str:
        """Classify the type of near-failure."""
        score = verification.get("score", 1.0)
        issues = verification.get("issues", [])
        notes = (verification.get("notes", "") or "").lower()
        
        if score < 0.5:
            return "low_score"
        elif len(issues) > 2:
            return "multiple_issues"
        elif "warning" in notes or "caution" in notes:
            return "warnings"
        elif "incomplete" in notes or "partial" in notes:
            return "incomplete"
        elif "uncertain" in notes or "uncertainty" in notes:
            return "uncertainty"
        else:
            return "borderline"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key terms from query for pattern matching."""
        # Simple keyword extraction (can be enhanced)
        import re
        words = re.findall(r'\b\w{4,}\b', query.lower())
        # Filter common words
        common_words = {"what", "when", "where", "why", "how", "this", "that", "with", "from", "about", "which"}
        keywords = [w for w in words if w not in common_words]
        return keywords[:10]  # Top 10 keywords
    
    def _update_failure_prevention_strategies(self, mistake_type: str, context: Dict[str, Any]) -> None:
        """Generate prevention strategies based on failure patterns."""
        pattern = self.FAILURE_PATTERNS[mistake_type]
        
        # Analyze common causes
        top_causes = sorted(
            pattern["common_causes"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        strategies = []
        
        # Generate strategies based on common causes
        for cause, count in top_causes:
            if cause.startswith("entry_domain_"):
                domain = cause.replace("entry_domain_", "")
                strategies.append(f"Avoid using {domain} as entry specialist for similar queries")
            elif cause.startswith("low_confidence_"):
                domain = cause.replace("low_confidence_", "")
                strategies.append(f"Ensure {domain} has high confidence before using for similar queries")
            elif cause.startswith("issue_"):
                issue = cause.replace("issue_", "")
                strategies.append(f"Address {issue} issues proactively")
        
        # Domain-specific strategies
        if mistake_type == "hallucination":
            strategies.append("Add FactsLLM validation step before final answer")
        elif mistake_type == "incomplete_reasoning":
            strategies.append("Increase WoT max_steps for similar complexity queries")
        elif mistake_type == "domain_misuse":
            strategies.append("Improve domain selection logic for query type")
        
        pattern["prevention_strategies"] = strategies[:10]  # Keep top 10
    
    def _update_near_failure_improvement_strategies(self, near_failure_type: str, context: Dict[str, Any]) -> None:
        """Generate improvement strategies for near-failures."""
        pattern = self.NEAR_FAILURE_PATTERNS[near_failure_type]
        
        # Analyze risk factors
        top_risks = sorted(
            pattern["risk_factors"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        strategies = []
        
        # Generate strategies based on risk factors
        for risk, count in top_risks:
            if risk.startswith("entry_domain_"):
                domain = risk.replace("entry_domain_", "")
                strategies.append(f"Consider alternative entry specialist instead of {domain} for similar queries")
            elif risk.startswith("medium_confidence_"):
                domain = risk.replace("medium_confidence_", "")
                strategies.append(f"Boost {domain} confidence through additional validation or research")
            elif risk.startswith("issue_"):
                issue = risk.replace("issue_", "")
                strategies.append(f"Address {issue} before it becomes a full failure")
        
        # Type-specific strategies
        if near_failure_type == "low_score":
            strategies.append("Increase verification threshold or add additional validation")
        elif near_failure_type == "multiple_issues":
            strategies.append("Add pre-verification checks to catch issues earlier")
        elif near_failure_type == "incomplete":
            strategies.append("Ensure all query aspects are addressed before finalizing")
        
        pattern["improvement_strategies"] = strategies[:10]  # Keep top 10

    # ============================================================
    #  MISTAKE DETECTION (Verifier v13 aware)
    # ============================================================
    def _detect_mistake_type(self, status: str, notes: str, issues: List[str]) -> str:
        """
        Map Verifier v13 decision → high-level mistake type.
        """
        if status == "approved":
            return "none"

        # Structural format failures
        structural_tags = {
            "missing_marker",
            "missing_block",
            "missing_status",
            "empty_output",
        }
        if any(tag in issues for tag in structural_tags) or "format_error" in notes:
            return "structural_failure"

        # Black-hole interior hallucinations / forbidden GR claims
        if "bh_interior_hallucination" in issues or "black hole interior" in notes:
            return "blackhole_interior"

        # Dimensional / unit sanity
        if "dimensional_error" in issues or "dimension" in notes:
            return "dimensional_error"

        # Malicious / unsafe code
        if "malicious_code" in issues or "unsafe code" in notes:
            return "unsafe_reasoning"

        # Domain-specific hints from notes/issue tags
        if "math" in notes or "math_error" in issues:
            return "math_error"
        if "physics" in notes or "physics_error" in issues:
            return "physics_error"
        if "chemistry" in notes or "chemistry_error" in issues:
            return "chemistry_error"
        if "biology" in notes or "biology_error" in issues:
            return "biology_error"

        # General hallucination / contradiction / context
        if "hallucination" in notes or "invent" in notes:
            return "hallucination"
        if "contradiction" in notes:
            return "contradiction"
        if "memory" in notes or "context" in notes:
            return "context_misuse"
        if "incomplete" in notes or "missing pieces" in notes:
            return "incomplete_reasoning"
        if "failed to use domain" in notes or "wrong domain" in notes:
            return "domain_misuse"
        if "unsafe" in notes:
            return "unsafe_reasoning"

        return "unknown_failure"

    # ============================================================
    #  DOMAIN SCORE + HEATMAP UPDATE
    # ============================================================
    def _update_domain_scores(self, mistake_type: str, router_plan: Dict[str, Any]) -> None:
        """
        Reward stable domains, penalize failing ones.
        ENHANCED: Also considers confidence and efficiency patterns.
        """
        entry = router_plan.get("entry_specialist", "general")
        entry = entry.lower()
        if entry not in self.DOMAIN_SCORES:
            self.DOMAIN_SCORES[entry] = 0

        base_score_change = 0
        if mistake_type == "none":
            # Reward successful entry domain
            base_score_change = 2
        else:
            # Penalize failing entry domain
            base_score_change = -3

        # NEW: Adjust based on confidence patterns
        confidence_bonus = 0
        if entry in self.CONFIDENCE_PATTERNS and self.CONFIDENCE_PATTERNS[entry]:
            avg_conf = statistics.mean(self.CONFIDENCE_PATTERNS[entry][-10:])  # Recent 10
            if avg_conf > 0.8:  # Very high confidence
                confidence_bonus = 1
            elif avg_conf < 0.3:  # Very low confidence
                confidence_bonus = -1

        # NEW: Adjust based on efficiency patterns
        efficiency_bonus = 0
        if entry in self.EFFICIENCY_PATTERNS and self.EFFICIENCY_PATTERNS[entry]:
            avg_eff = statistics.mean(self.EFFICIENCY_PATTERNS[entry][-10:])  # Recent 10
            if avg_eff > 0.8:  # Very efficient
                efficiency_bonus = 1
            elif avg_eff < 0.3:  # Very inefficient
                efficiency_bonus = -1

        # NEW: Adjust based on failure patterns
        failure_penalty = 0
        recent_failures = [f for f in self.FAILURE_CONTEXTS[-50:] if f.get("entry_specialist", "").lower() == entry]
        if len(recent_failures) > 5:  # More than 5 recent failures
            failure_penalty = -2
        elif len(recent_failures) > 2:  # 3-5 recent failures
            failure_penalty = -1
        
        # NEW: Adjust based on near-failure patterns
        near_failure_penalty = 0
        recent_near_failures = [nf for nf in self.NEAR_FAILURE_CONTEXTS[-50:] if nf.get("entry_specialist", "").lower() == entry]
        if len(recent_near_failures) > 10:  # More than 10 recent near-failures
            near_failure_penalty = -1

        # Apply all adjustments
        total_change = base_score_change + confidence_bonus + efficiency_bonus + failure_penalty + near_failure_penalty
        self.DOMAIN_SCORES[entry] += total_change

        # Clamp scores into safe range
        for k in self.DOMAIN_SCORES:
            if self.DOMAIN_SCORES[k] > 50:
                self.DOMAIN_SCORES[k] = 50
            elif self.DOMAIN_SCORES[k] < -50:
                self.DOMAIN_SCORES[k] = -50

    def _update_error_stats(self, mistake_type: str, router_plan: Dict[str, Any]) -> None:
        """
        Maintain a per-domain heatmap of error types.
        """
        if mistake_type == "none":
            return

        entry = router_plan.get("entry_specialist", "general")
        entry = entry.lower()
        if entry not in self.ERROR_STATS:
            self.ERROR_STATS[entry] = {}

        bucket = self.ERROR_STATS[entry]
        bucket[mistake_type] = bucket.get(mistake_type, 0) + 1

    # ============================================================
    #  DIFFICULTY DERIVATION (from risk_score)
    # ============================================================
    def _difficulty_from_risk(self, risk: float) -> str:
        if risk < 0.25:
            return "easy"
        if risk < 0.5:
            return "medium"
        if risk < 0.75:
            return "hard"
        return "insane"

    # ============================================================
    #  LOCAL DIFFICULTY HEURISTIC (backup)
    # ============================================================
    def _estimate_difficulty(self, query: str) -> str:
        """
        Quick heuristic for task difficulty, used if Router didn't provide one.
        """
        q = query.lower()
        score = 0

        if any(w in q for w in ["tensor", "lagrangian", "manifold"]):
            score += 3
        if any(w in q for w in ["derive", "proof", "prove", "formal"]):
            score += 2
        if any(w in q for w in ["black hole", "kerr", "quasar", "qft"]):
            score += 2
        if any(w in q for w in ["simulation", "numerical", "solver"]):
            score += 2
        if any(w in q for w in ["sonification", "sound design", "gravitational wave"]):
            score += 1
        if "explain" in q or "overview" in q:
            score += 1
        if len(query) > 200:
            score += 1

        if score <= 2:
            return "easy"
        if score <= 4:
            return "medium"
        if score <= 6:
            return "hard"
        return "insane"

    # ============================================================
    #  LESSON BUILDER (meta)
    # ============================================================
    def _build_lesson(
        self,
        mistake_type: str,
        router_plan: Dict[str, Any],
    ) -> str:
        lessons = {
            "none": "No mistake detected; ANM performed successfully under current routing.",
            "hallucination": "Avoid invented facts; route more strongly through FactsLLM and ResearchLLM before composing answers.",
            "contradiction": "Strengthen cross-domain consistency checks and ensure FactsLLM validates conflicting reasoning.",
            "math_error": "Delegate non-trivial derivations to the Math specialist earlier instead of mixing math into other domains.",
            "physics_error": "Physics must request Math for derivations and enforce dimensional checks and conservation laws.",
            "chemistry_error": "Complex chemistry must be routed to Chemistry with supporting Physics/Math checks for energetics.",
            "biology_error": "Biology claims must respect known physiology/evolution and avoid overreach; request Chemistry/Physics as needed.",
            "domain_misuse": "Router should choose specialists that match the query domain; DomainMasker rules should be tightened.",
            "incomplete_reasoning": "Increase WoT steps or add an extra cross-domain pass; ensure General + Facts consolidate reasoning.",
            "context_misuse": "Cloud Diary is PAST-ONLY; memory must not override current query, research, or facts.",
            "unsafe_reasoning": "Avoid unsafe suggestions or malicious code; Verifier must be extra-strict on safety-sensitive tasks.",
            "blackhole_interior": "Black-hole interiors must be treated as unknown/active-research; never present interior structure as settled fact.",
            "dimensional_error": "All formulas must be dimensionally consistent; Math and Physics must jointly validate units.",
            "structural_failure": "Refiner must always emit [VERIFIER_READY] and Verifier blocks must be well-formed.",
            "unknown_failure": "General inconsistency detected; favor conservative reasoning and additional FactsLLM passes.",
        }
        return lessons.get(mistake_type, "Unclassified error; apply general robustness improvements and stricter validation.")

    # ============================================================
    #  FIX RECOMMENDATION (meta)
    # ============================================================
    def _build_fix(self, mistake_type: str, router_plan: Dict[str, Any]) -> str:
        fixes = {
            "none": "No fix required; current routing and WoT depth are acceptable.",
            "hallucination": "Increase FactsLLM + ResearchLLM priority and reduce speculative extrapolation in high-risk domains.",
            "contradiction": "Add stronger early cross-domain validation and multiple FactsLLM passes before final refinement.",
            "math_error": "Trigger Math specialist earlier and prevent other domains from executing multi-step derivations alone.",
            "physics_error": "Route GR/astrophysics tasks to Physics+Math jointly with strict unit checks and LawBook GR constraints.",
            "chemistry_error": "Require Chemistry + Physics collaboration for energetic feasibility and plausible mechanisms.",
            "biology_error": "Require Biology to check plausibility and call Chemistry/Physics/Math when mechanisms get quantitative.",
            "domain_misuse": "Enforce DomainMasker + PlannerLLM to align domain selection with the query semantics.",
            "incomplete_reasoning": "Increase WoT max_steps and allow a second consolidation pass via General + Facts.",
            "context_misuse": "Add explicit 'PAST-ONLY' warnings and cap how heavily memory can influence conclusions.",
            "unsafe_reasoning": "Add safety filters and require Verifier to be extra-strict for code/engineering/real-world instructions.",
            "blackhole_interior": "Treat detailed black-hole interior claims as speculative and label them clearly as such or avoid them.",
            "dimensional_error": "Require explicit unit checks and dimensional analysis in Physics/Math for all key formulas.",
            "structural_failure": "Ensure Refiner always emits [VERIFIER_READY] and Verifier responses respect required format.",
            "unknown_failure": "Enable stricter second-pass WoT and demand FactsLLM validation before approval.",
        }
        return fixes.get(mistake_type, "General robustness improvements recommended across routing and validation.")

    # ============================================================
    #  DIARY LOG ENTRY (LawBook V0-OpenSource safe)
    # ============================================================
    def _build_diary_entry(
        self,
        *,
        mistake_type: str,
        user_query: str,
        router_plan: Dict[str, Any],
        verification: Dict[str, Any],
        difficulty: str,
    ) -> str:
        """
        Generates a LawBook-compliant text block that the caller can store into Cloud Diary.

        Rules:
          - PAST-ONLY phrasing.
          - No raw full CoTs or sensitive data.
          - No invented facts about the user.
        """
        if mistake_type == "none":
            # Optional: could still log successes, but we keep it minimal.
            return ""

        # Minimal snapshots (no raw CoTs)
        vp = {
            "status": verification.get("status", ""),
            "notes": verification.get("notes", ""),
            "score": verification.get("score", None),
            "issues": verification.get("issues", []),
        }
        rp = {
            "entry_specialist": router_plan.get("entry_specialist", "general"),
            "active_domains": router_plan.get("active_domains", []),
            "max_steps": router_plan.get("max_steps", 0),
            "difficulty": difficulty,
        }

        return f"""
In the past, ANM processed the following user query:

USER_QUERY (truncated):
{user_query[:400]}

During this run, ANM encountered a mistake of type:
{mistake_type}

ROUTER_PLAN (high-level snapshot):
{rp}

VERIFIER_DECISION (high-level snapshot):
{vp}

In the past, ANM learned the following lesson:
{self._build_lesson(mistake_type, router_plan)}

This memory describes a past run only and does NOT guarantee any current truth about the user or the world.
""".strip()

    # ============================================================
    #  WOT STABILITY METRICS
    # ============================================================
    def _compute_wot_stability(
        self,
        *,
        status: str,
        notes: str,
        consistency: Dict[str, Any],
        router_plan: Dict[str, Any],
        vfl_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute a coarse stability metric, 0–100, where higher = more stable.
        Uses:
          - Verifier status
          - ConsistencyChecker rerun flag
          - VFL attempts
          - Router max_steps
        """
        stability = 50  # base

        # Verifier status
        if status == "approved":
            stability += 20
        else:
            stability -= 10

        # Rerun hint from ConsistencyChecker
        rerun = bool(consistency.get("rerun", False))
        if rerun:
            stability -= 15

        # Attempts from VFL
        total_attempts = 1
        if vfl_meta and isinstance(vfl_meta.get("total_attempts"), int):
            total_attempts = max(1, vfl_meta["total_attempts"])

        if total_attempts > 1:
            stability -= 5 * (total_attempts - 1)

        # Max steps: very large = maybe unstable / over-thinking
        max_steps = int(router_plan.get("max_steps", 16) or 16)
        if max_steps > 24:
            stability -= 5
        elif max_steps < 10:
            stability += 3  # more confident / compressed

        # Clamp 0–100
        if stability < 0:
            stability = 0
        elif stability > 100:
            stability = 100

        return {
            "rerun_suggested": rerun,
            "verifier_status": status,
            "verifier_notes": notes,
            "total_attempts": total_attempts,
            "max_steps": max_steps,
            "stability_score": stability,
        }