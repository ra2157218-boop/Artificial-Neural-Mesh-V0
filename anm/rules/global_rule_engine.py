# ============================================================
# ANM V0-OpenSource — GLOBAL RULES ENGINE (GRE V0-OpenSource.2 ULTRA — SYNCED)
#  LawBook V0-OpenSource • Multi-Modal • Physics-Safe • Memory-Safe
#  Router V0-OpenSource MAX compatible • Verifier V0-OpenSource aware
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List


class GlobalRulesEngine:
    """
    GRE V0-OpenSource.2 ULTRA — Fully aligned with Router V0-OpenSource + Refiner V0-OpenSource + Verifier V0-OpenSource.
    Synced with:
      • new Verifier issue tags
      • multi-modal hallucination markers
      • sound/image/simulation rules
      • LFM V0-OpenSource + PointGame v3.0 feedback loop
    """

    # ============================================================
    #   HARD VIOLATIONS (cannot be fixed by rerun)
    # ============================================================
    HARD_RULES = [

        # ----------- Physics / GR Safety -----------
        {
            "id": "BH_INTERIOR",
            "severity": "critical",
            "patterns": [
                "inside the event horizon",
                "black hole interior is solved",
                "naked singularity is stable",
                "spacetime inside horizon",
            ],
        },
        {
            "id": "QG_FAKE",
            "severity": "critical",
            "patterns": [
                "quantum gravity is solved",
                "theory of everything is proven",
            ],
        },
        {
            "id": "DIMENSION_ERROR",
            "severity": "critical",
            "patterns": [
                "dimensionally inconsistent",
                "violates conservation",
                "mass becomes energy without mechanism",
            ],
        },

        # ----------- Simulation Safety -----------
        {
            "id": "SIMULATION_AS_REAL",
            "severity": "high",
            "patterns": [
                "simulated measurement",
                "simulation shows real",
                "treat simulation as real",
                "actual result from simulation",
            ],
        },
        {
            "id": "SIMULATION_VALUES_INVENTED",
            "severity": "high",
            "patterns": [
                "invented simulation values",
                "exact numbers from simulation",
            ],
        },

        # ----------- Code Safety -----------
        {
            "id": "UNSAFE_CODE",
            "severity": "critical",
            "patterns": [
                "rm -rf", "sudo ", "exec(", "eval(", "os.system(",
            ],
        },

        # ----------- Memory Safety -----------
        {
            "id": "MEMORY_INVENT",
            "severity": "high",
            "patterns": [
                "you previously said",
                "as you told me earlier",
                "i remember when you",
                "your personality is",
                "you always",
            ],
        },

        {
            "id": "MEMORY_OVERRIDE",
            "severity": "high",
            "patterns": [
                "memory proves",
                "memory confirms",
                "memory is current truth",
            ],
        },

        # ----------- Image hallucination -----------
        {
            "id": "IMAGE_HALLUCINATION",
            "severity": "high",
            "patterns": [
                "their race is",
                "this person is definitely",
                "their age appears to be",
                "biometric inference",
                "face recognition",
            ],
        },

        # ----------- Sound hallucination -----------
        {
            "id": "SOUND_HALLUCINATION",
            "severity": "high",
            "patterns": [
                "frequency is exactly",
                "hz claim",
                "decibel claim",
                "invented frequency",
                "clear voice can be heard",
            ],
        },
    ]

    # ============================================================
    #   SOFT VIOLATIONS (rerun may fix)
    # ============================================================
    SOFT_RULES = [
        {
            "id": "SPECULATION",
            "severity": "medium",
            "patterns": [
                "i think", "probably", "maybe", "i assume",
                "appears to be", "seems like",
            ],
        },
        {
            "id": "CONTRADICTION",
            "severity": "critical",
            "patterns": ["contradiction", "inconsistent", "does not match"],
        },
        {
            "id": "DOMAIN_OVERREACH",
            "severity": "medium",
            "patterns": [
                "as a physics model i will write code",
                "chemistry explains general relativity",
                "sound module predicts equations",
            ],
        },
        {
            "id": "LOOP_INDICATOR",
            "severity": "high",
            "patterns": ["repeating itself", "looping again"],
        },
    ]

    # ============================================================
    # META SIGNALS — not failures (LFM uses these)
    # ============================================================
    META_RULES = [
        {
            "id": "HONESTY_SIGNAL",
            "severity": "ok",
            "patterns": [
                "i cannot", "i do not know", "uncertain", "insufficient data"
            ],
        },
        {
            "id": "FICTION_CONTEXT",
            "severity": "ok",
            "patterns": ["fictional", "story", "imagine", "worldbuilding"],
        },
    ]

    # ============================================================
    #   MAIN ANALYSIS ENTRY
    # ============================================================
    def analyze(self, module_output: str, module_name: str) -> Dict[str, Any]:

        if not module_output:
            return self._empty(module_name)

        text = module_output.lower()

        violations = []
        penalty = 0

        recommended_domains = set()
        abort = False
        reroute = False

        # HARD VIOLATIONS
        for rule in self.HARD_RULES:
            if any(p in text for p in rule["patterns"]):
                violations.append(rule["id"])
                penalty -= 5 if rule["severity"] == "critical" else -3
                abort = rule["severity"] == "critical"
                reroute = True

                # suggestions by category
                if rule["id"] in ["BH_INTERIOR", "QG_FAKE", "DIMENSION_ERROR"]:
                    recommended_domains.update(["math", "physics", "facts"])

                if rule["id"] == "UNSAFE_CODE":
                    recommended_domains.add("code")

                if rule["id"] in ["IMAGE_HALLUCINATION"]:
                    recommended_domains.add("image")

                if rule["id"] == "SOUND_HALLUCINATION":
                    recommended_domains.add("sound")

                if rule["id"] in ["SIMULATION_AS_REAL", "SIMULATION_VALUES_INVENTED"]:
                    recommended_domains.update(["simulation", "physics", "facts"])

                if rule["id"] in ["MEMORY_INVENT", "MEMORY_OVERRIDE"]:
                    recommended_domains.add("facts")

        # SOFT VIOLATIONS
        for rule in self.SOFT_RULES:
            if any(p in text for p in rule["patterns"]):
                violations.append(rule["id"])
                penalty -= 2 if rule["severity"] == "medium" else -3
                reroute = True

        # META SIGNALS
        meta_signals = []
        for rule in self.META_RULES:
            if any(p in text for p in rule["patterns"]):
                meta_signals.append(rule["id"])

        # RISK CLASSIFICATION
        risk_level = (
            "critical" if penalty <= -5 else
            "high" if penalty <= -3 else
            "medium" if penalty <= -1 else
            "low"
        )

        return {
            "passed": penalty >= 0,
            "risk_level": risk_level,
            "violations": violations,
            "penalty": penalty,
            "recommended_domains": sorted(list(recommended_domains)),
            "should_abort": abort,
            "should_reroute": reroute,
            "meta_signals": meta_signals,
            "self_reflection": self._reflect(module_name, violations, risk_level),
        }

    # ============================================================
    # Empty output
    # ============================================================
    def _empty(self, module):
        return {
            "passed": False,
            "risk_level": "critical",
            "violations": ["EMPTY_OUTPUT"],
            "penalty": -5,
            "recommended_domains": ["general", "facts"],
            "should_abort": True,
            "should_reroute": True,
            "meta_signals": [],
            "self_reflection": f"{module} returned empty output — cannot continue.",
        }

    # ============================================================
    # Self-reflection for LFM
    # ============================================================
    def _reflect(self, module: str, violations: List[str], risk: str) -> str:
        if not violations:
            return f"{module} executed cleanly (risk={risk})."
        return (
            f"{module} had {len(violations)} violation(s) (risk={risk}). "
            f"Domain correction recommended."
        )