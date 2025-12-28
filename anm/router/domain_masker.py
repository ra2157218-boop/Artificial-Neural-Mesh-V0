# ============================================================
# ANM V0-OpenSource — Domain Masker V0-OpenSource MAX (Synced)
#  LawBook V0-OpenSource • Multi-modal • Simulation/Image/Sound aware
#  Guaranteed Safety • Deterministic Domain Activation
# ============================================================

from __future__ import annotations
from typing import Dict, List, Set, Any


class DomainMasker:
    """
    DomainMasker V0-OpenSource MAX

    Responsibilities:
      • Map Router/Planner plan → safe, minimal domain set.
      • Enforce LawBook V0-OpenSource constraints.
      • Respect multi-modal domains (simulation, image, sound).
      • Always include: general + memory + entry_specialist (if valid).
      • Integrate LFM strategy tags (strong_facts, strong_research, deep_wot).
      • Use risk_score fallback when risk_level missing.

    WHAT'S NEW (this synced version):
      • _effective_risk(...) helper (risk_level or risk_score).
      • LFM tags:
            - strong_facts     → facts domain forced (if allowed)
            - strong_research  → research domain preferred (if not high/insane physics)
            - deep_wot         → slightly higher domain cap for pruning
      • Safer research gating on high/insane physics tasks.
      • Deterministic final ordering via ORDER.
    """

    ORDER = [
        "general",
        "math",
        "physics",
        "code",
        "chemistry",
        "biology",
        "memory",
        "research",
        "facts",
        "simulation",
        "image",
        "sound",
    ]

    def __init__(self, config: Dict[str, Any], valid_domains: Set[str]) -> None:
        self.config = config or {}
        self.valid = set(valid_domains)

        # Router / System gating
        self.allow_research = bool(self.config.get("router_allow_research", True))
        self.allow_facts = bool(self.config.get("router_allow_facts", True))

        # Max active domains before soft pruning
        self.max_domains = int(self.config.get("max_active_domains", 9))

    # ========================================================
    #  Effective Risk (risk_level or risk_score fallback)
    # ========================================================
    def _effective_risk(self, plan: Dict[str, Any]) -> str:
        """
        Normalize risk into: 'low' | 'medium' | 'high' | 'insane'.

        Priority:
          1) plan['risk_level'] if present and valid
          2) plan['risk_score'] (0–1-ish float) if present
          3) default 'medium'
        """
        rl = str(plan.get("risk_level") or "").strip().lower()
        if rl in {"low", "medium", "high", "insane"}:
            return rl

        # Fallback: numeric risk_score
        rs = plan.get("risk_score", 0.5)
        try:
            r = float(rs)
        except Exception:
            r = 0.5

        if r < 0.25:
            return "low"
        if r < 0.5:
            return "medium"
        if r < 0.75:
            return "high"
        return "insane"

    # ========================================================
    #                     MAIN APPLY
    # ========================================================
    def apply(self, plan: Dict[str, Any]) -> List[str]:
        """
        Takes Router/Planner plan → returns vetted list of domains.
        """

        # ------------------ Basics ------------------
        entry = str(plan.get("entry_specialist", "general")).lower()
        active_req = [str(d).lower() for d in plan.get("active_domains", [])]

        # Start with Router suggestion but validate
        active = {d for d in active_req if d in self.valid}

        # Always include GENERAL
        active.add("general")

        # Always include ENTRY SPECIALIST (if known)
        if entry in self.valid:
            active.add(entry)

        # Metadata
        q_raw = plan.get("user_query", "")
        q = q_raw.lower() if isinstance(q_raw, str) else ""
        task_type = str(plan.get("task_type", "") or "").lower()
        risk_level = self._effective_risk(plan)
        tags = [str(t).lower() for t in (plan.get("strategy_tags") or [])]

        # Local max_domains (can be adjusted by tags like deep_wot)
        local_max_domains = self.max_domains

        # ========================================================
        # 1. MEMORY ALWAYS INCLUDED (LawBook)
        # ========================================================
        if "memory" in self.valid:
            active.add("memory")

        # ========================================================
        # 2. SOUND ACTIVATION (sound queries, audio semantics)
        # ========================================================
        if any(k in q for k in ["sound", "audio", "hum", "buzz", "ring", "binaural", "music"]):
            if "sound" in self.valid:
                active.add("sound")
        if "sound" in active_req and "sound" in self.valid:
            active.add("sound")

        # ========================================================
        # 3. IMAGE ACTIVATION (if visual reasoning needed)
        # ========================================================
        if any(k in q for k in ["image", "picture", "visual", "frame", "diagram", "camera"]):
            if "image" in self.valid:
                active.add("image")
        if "image" in active_req and "image" in self.valid:
            active.add("image")

        # ========================================================
        # 4. SIMULATION ACTIVATION (scenario / physics sim / experiments / video generation)
        # ========================================================
        simulation_triggers = [
            # Core simulation keywords
            "simulate", "simulation", "orbit", "trajectory", "render", "fluid",
            "motion", "particle", "bh", "black hole", "field lines", "dynamics",
            # Video generation triggers (IMPORTANT)
            "generate a video", "generate video", "create a video", "create video",
            "make a video", "make video", "show me a video", "video of it",
            "animation", "animate", "visualize", "visualization",
            # Physics scenarios that need simulation
            "fall", "falling", "drop", "dropping", "bounce", "bouncing",
            "collision", "collide", "impact", "splash", "throw", "projectile",
            # General physics that benefit from visualization
            "what happens", "what will happen", "what would happen",
        ]
        if any(k in q for k in simulation_triggers):
            if "simulation" in self.valid:
                active.add("simulation")
        if "simulation" in active_req and "simulation" in self.valid:
            active.add("simulation")

        # ========================================================
        # 5. RESEARCH gating (LawBook V0-OpenSource)
        # ========================================================
        # Base gating
        if not self.allow_research and "research" in active:
            active.discard("research")
        else:
            # High/insane-risk physics → disable research (avoid speculative contradictions)
            if risk_level in ["high", "insane"] and "physics" in active and "research" in active:
                active.discard("research")

        # ========================================================
        # 6. FACTS gating
        # ========================================================
        if not self.allow_facts and "facts" in active:
            active.discard("facts")

        # ========================================================
        # 7. LFM Strategy Tags (strong_facts / strong_research / deep_wot)
        # ========================================================

        # strong_facts → Facts domain MUST be active (if allowed)
        if "strong_facts" in tags and self.allow_facts and "facts" in self.valid:
            active.add("facts")

        # strong_research → prefer Research domain (except high/insane physics)
        if "strong_research" in tags and self.allow_research and "research" in self.valid:
            if not (risk_level in ["high", "insane"] and "physics" in active):
                active.add("research")

        # deep_wot → allow a slightly larger domain set before pruning
        if "deep_wot" in tags:
            local_max_domains = max(local_max_domains, self.max_domains + 2)

        # ========================================================
        # 8. FICTION MODE SAFETY (LawBook)
        # ========================================================
        if "fiction" in tags:
            # disable real-world science domains
            active.discard("physics")
            active.discard("chemistry")
            active.discard("biology")
            # sound/image/simulation are safe for fictional content

        # ========================================================
        # 9. DERIVATIONS → prune chem/bio
        # ========================================================
        if task_type == "derivation":
            active.discard("chemistry")
            active.discard("biology")

        # ========================================================
        # 10. DESIGN tasks → enable Math, Code
        # ========================================================
        if task_type == "design":
            if "math" in self.valid:
                active.add("math")
            if "code" in self.valid:
                active.add("code")

        # ========================================================
        # 11. High-risk physics → restrict non-critical multimodal
        # ========================================================
        if risk_level in ["high", "insane"] and "physics" in active:
            # Keep simulation (safe numeric scenario generator)
            # sound/image are allowed but not forced here (already handled above)
            # Remove chem/bio (usually irrelevant to GR/QFT extremes)
            active.discard("chemistry")
            active.discard("biology")

        # ========================================================
        # 12. Too many domains → soft prune (LawBook)
        # ========================================================
        if len(active) > local_max_domains:

            preferred_order = [
                "general",
                entry,
                "math",
                "physics",
                "code",
                "simulation",
                "image",
                "sound",
                "memory",
                "facts",
                "research",
            ]

            pruned: List[str] = []
            for p in preferred_order:
                if len(pruned) >= local_max_domains:
                    break
                if p in active and p not in pruned:
                    pruned.append(p)

            # Fill remaining slots with whatever is left (rare)
            for d in active:
                if len(pruned) >= local_max_domains:
                    break
                if d not in pruned:
                    pruned.append(d)

            active = set(pruned)

        # ========================================================
        # 13. Ensure ENTRY + GENERAL mandatory
        # ========================================================
        if "general" in self.valid:
            active.add("general")
        if entry in self.valid:
            active.add(entry)

        # ========================================================
        # 14. Remove any domain not in valid set
        # ========================================================
        active = {d for d in active if d in self.valid}

        # ========================================================
        # 15. Final deterministic ordering
        # ========================================================
        final = [d for d in self.ORDER if d in active]

        return final