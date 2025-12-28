# ============================================================
# ANM V0-OpenSource — POINT GAME ENGINE v3.0 (LAWBOOK v1.2 MAX EDITION)
#  Reinforcement • Safety-Aware • Cross-Domain Performance
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
import time
import math


class PointGame:
    """
    POINT GAME (PG-Core v3.0 – MAX EDITION)

    Fully compliant with LawBook V0-OpenSource.
    Used by:
       - Router → to adjust strategies
       - SelfAwarenessLLM → to diagnose performance
       - VFL → to interpret verifier outcomes

    Features:
      ✓ LawBook V0-OpenSource compliant scoring
      ✓ Domain-weighted reinforcement (physics/sim/math > gen)
      ✓ Difficulty auto-detection from Router risk_score
      ✓ Penalty for hallucinations / invented details / unsafe notes
      ✓ Reward for cross-domain coherence (>=3 domains)
      ✓ Burnout protection + streak normalization
      ✓ Stability score (0–100)
      ✓ Full diagnostics for meta-modules
    """

    # --------------------------------------------------------
    # INIT
    # --------------------------------------------------------
    def __init__(self) -> None:
        self.score: int = 0
        self.streak: int = 0

        self.history: List[Dict[str, Any]] = []
        self.max_history: int = 300

        self.total_runs: int = 0
        self.approved_count: int = 0
        self.rejected_count: int = 0

        # difficulty lanes
        self.performance_difficulty = {
            "easy": 0,
            "medium": 0,
            "hard": 0,
            "insane": 0,
            "unknown": 0,
        }

        # domain lanes
        self.performance_domain = {
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
        }

    # ============================================================
    #  MAIN UPDATE (called by VFLLoop)
    # ============================================================
    def update_from_run(self, run_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safe. Never throws.

        run_result must contain:
          - verification (status, score, notes)
          - router_plan (entry_specialist, active_domains, risk_score)
        """

        verification = run_result.get("verification", {}) or {}
        status = verification.get("status", "unknown")
        notes = (verification.get("notes", "") or "").lower()
        vscore = int(verification.get("score", 50))

        router_plan = run_result.get("router_plan", {}) or {}
        entry = router_plan.get("entry_specialist", "general")

        # detect difficulty
        difficulty = self._difficulty_from_risk(router_plan)

        active_domains = [d.lower() for d in router_plan.get("active_domains", [])]

        # update counters
        self.total_runs += 1

        # --------------------------------------------------------
        # BASE DOMAIN WEIGHT SCORING
        # --------------------------------------------------------
        domain_weight = self._domain_weight(entry)

        if status == "approved":
            base = +1 * domain_weight
            self.approved_count += 1
            self._update_streak(win=True)
        else:
            base = -1 * domain_weight
            self.rejected_count += 1
            self._update_streak(win=False)

        # verifier confidence modulator (0.4 → 0.9)
        delta = int(base * (0.40 + vscore / 200))

        # --------------------------------------------------------
        # PENALTIES (LAWBOOK)
        # --------------------------------------------------------
        # hallucination / invented detail / unsafe / illegal / black-hole interior etc.
        violation_markers = [
            "hallucination", "invent", "unsafe", "illegal",
            "black hole interior", "bh interior",
            "lawbook", "violation", "impossible physics",
        ]
        if any(m in notes for m in violation_markers):
            delta -= 2

        # --------------------------------------------------------
        # CROSS-DOMAIN COHERENCE BONUS
        # --------------------------------------------------------
        if status == "approved" and len(active_domains) >= 3:
            delta += 1

        # --------------------------------------------------------
        # BURNOUT / STREAK DEGRADATION CONTROL
        # --------------------------------------------------------
        if self.streak <= -6:
            # stop runaway punishments
            delta = max(delta, -2)

        # clamp global score
        self.score = max(-9999, min(9999, self.score + delta))

        # update heatmaps
        self.performance_difficulty[difficulty] += delta
        self.performance_domain[entry] += delta

        # --------------------------------------------------------
        # LOG HISTORY (last 300)
        # --------------------------------------------------------
        snapshot = {
            "ts": time.time(),
            "status": status,
            "difficulty": difficulty,
            "entry_domain": entry,
            "active_domains": active_domains,
            "verifier_score": vscore,
            "notes": notes,
            "delta": delta,
            "score": self.score,
            "streak": self.streak,
        }
        self.history.append(snapshot)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # --------------------------------------------------------
        # Router Feedback Signal (RFS)
        # --------------------------------------------------------
        rfs = self._router_feedback_signal(difficulty, delta)

        return rfs

    # ============================================================
    #  DIFFICULTY AUTO-DETECTION
    # ============================================================
    def _difficulty_from_risk(self, plan: Dict[str, Any]) -> str:
        risk = float(plan.get("risk_score", 0.3))

        if risk < 0.25:  return "easy"
        if risk < 0.50:  return "medium"
        if risk < 0.75:  return "hard"
        if risk <= 1.50: return "insane"
        return "unknown"

    # ============================================================
    #  DOMAIN WEIGHTING
    # ============================================================
    def _domain_weight(self, d: str) -> int:
        """
        Higher weight = bigger reward AND bigger penalty.
        Reflects complexity & risk.
        """

        table = {
            "general": 1,
            "memory": 1,
            "research": 1,
            "facts": 1,
            "code": 2,
            "chemistry": 2,
            "biology": 2,
            "math": 3,
            "physics": 4,
            "simulation": 4,
            "image": 3,
            "sound": 3,
        }
        return table.get(d.lower(), 1)

    # ============================================================
    #  STREAK MODEL
    # ============================================================
    def _update_streak(self, win: bool) -> None:
        if win:
            self.streak = self.streak + 1 if self.streak >= 0 else 1
        else:
            self.streak = self.streak - 1 if self.streak <= 0 else -1

        # soft normalization
        if abs(self.streak) > 20:
            self.streak = int(self.streak * 0.9)

    # ============================================================
    #  ROUTER FEEDBACK SIGNAL
    # ============================================================
    def _router_feedback_signal(self, difficulty: str, delta: int) -> Dict[str, Any]:
        """
        Consumed by:
           - Router
           - PlannerLLM
           - SelfAwarenessLLM
        """

        return {
            "difficulty": difficulty,
            "reward": delta,
            "boost": delta > 0,
            "penalty": delta < 0,

            # Router tuning
            "suggest_more_domains": delta > 1,
            "suggest_reduce_domains": delta < -1,
            "suggest_stricter_verifier": delta < 0,
        }

    # ============================================================
    #  DIAGNOSTICS (for SelfAwarenessLLM / Router)
    # ============================================================
    def stats(self) -> Dict[str, Any]:
        if self.total_runs == 0:
            return {
                "score": 0,
                "streak": 0,
                "approval_rate": 0,
                "mood": "🙂 NORMAL OPERATION",
                "stability_score": 50,
                "domain_map": dict(self.performance_domain),
                "difficulty_map": dict(self.performance_difficulty),
                "recent": [],
            }

        approval_rate = self.approved_count / max(1, self.total_runs)
        stability = self._compute_stability()

        return {
            "score": self.score,
            "streak": self.streak,
            "total_runs": self.total_runs,
            "approval_rate": round(approval_rate, 3),
            "stability_score": stability,
            "mood": self._mood(stability),
            "domain_map": dict(self.performance_domain),
            "difficulty_map": dict(self.performance_difficulty),
            "recent": self.history[-10:],
        }

    # ============================================================
    #  STABILITY (0–100)
    # ============================================================
    def _compute_stability(self) -> int:
        # overall performance factors
        approval_rate = self.approved_count / max(1, self.total_runs)
        streak_factor = math.tanh(self.streak / 6)

        # quality of technical domains
        tech = (
            self.performance_domain["physics"]
            + self.performance_domain["simulation"]
            + self.performance_domain["math"]
        ) / max(1, self.total_runs)

        stability = (
            40 * approval_rate +
            30 * streak_factor +
            30 * tech
        )

        return max(0, min(100, int(stability)))

    # ============================================================
    #  MOOD ENGINE
    # ============================================================
    def _mood(self, s: int) -> str:
        if s >= 85: return "🔥 HYPER-MIND MODE"
        if s >= 65: return "⚡ STABLE & SHARP"
        if s >= 40: return "🙂 NORMAL OPERATION"
        if s >= 20: return "😕 UNDERPERFORMING"
        return "🚨 CRITICAL — needs recalibration"