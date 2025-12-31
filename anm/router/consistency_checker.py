# ============================================================
# ANM V0-OpenSource — Consistency Checker V0-OpenSource (V0-OpenSource)
#  Fully synced with Verifier V0-OpenSource + Refiner V0-OpenSource
#  LawBook V0-OpenSource • Multi-modal • Zero-loop guarantee
# ============================================================

from __future__ import annotations
from typing import Dict, Any


class ConsistencyChecker:
    """
    ConsistencyChecker V0-OpenSource
    ----------------------------
    Runs AFTER Verifier V0-OpenSource but BEFORE VFL rerun logic.

    Upgrades from V0-OpenSource MAX:
      • Supports new Verifier V0-OpenSource issue tags
      • New multi-modal hallucination detectors (image/sound/sim)
      • Detects LawBook chain-priority violations
      • Detects Refiner synthesis weakness (cross-domain merging)
      • Detects MemoryLLM override attempts
      • Detects TrueWoT infinite-loop markers
      • Still guarantees: at most ONE rerun
    """

    def __init__(self):
        # TODO: Initialize consistency checker state if needed
        # Currently stateless - no initialization required
        pass

    # ------------------------------------------------------------
    def analyze(
        self,
        user_query: str,
        merged_reasoning: str,
        verification: Dict[str, Any],
    ) -> Dict[str, Any]:

        status = (verification or {}).get("status", "approved")
        notes  = (verification or {}).get("notes", "").lower()
        issues = (verification or {}).get("issues", []) or []

        # ========================================================
        #  1. APPROVED → No rerun
        # ========================================================
        if status == "approved":
            return {
                "rerun": False,
                "reason": "Verifier approved — output stable.",
                "verifier_notes": notes,
            }

        # ========================================================
        #  2. HARD FAILURES (no rerun possible)
        # ========================================================

        HARD_FAIL = [

            # ------------- Structural / Format -------------
            "missing_marker", "missing_block", "missing_status",
            "format_error", "invalid_structure",

            # ------------- LawBook Violations --------------
            "lawbook_violation", "breaks_lawbook", "illegal_evidence_order",

            # ------------- Chain Priority Violation --------
            # Research > Facts > Physics/Math > Chem/Bio > Code > Sim > Image > Sound
            "priority_violation", "evidence_chain_broken",

            # ------------- Memory Violations ---------------
            "memory_invention", "invented_past", "fabricated_memory",
            "memory_override", "treated_memory_as_truth",

            # ------------- Physics Fatal -------------------
            "bh_interior", "black_hole_interior", "kerr_interior",
            "qg_claim", "spacetime_inside_horizon",
            "violates_conservation", "dimensional_error",
            "dimensionally_inconsistent",

            # ------------- Code Safety ---------------------
            "unsafe_code", "exploit", "malicious_behavior",

            # ------------- Image Hard Violations ----------
            "hallucinated_image", "invented_visual",
            "identity_guess", "race_guess", "emotion_guess",
            "biometric_inference",

            # ------------- Sound Hard Violations ----------
            "invented_frequency", "hz_claim", "decibel_claim",
            "hallucinated_sound", "fabricated_audio",

            # ------------- Simulation Hard Violations -----
            "simulation_as_real", "simulated_measurement",
            "invented_simulation_values",

            # ------------- Internal Safety -----------------
            "self_flagged", "internal_error",

            # ------------- Router / WoT Infinite Loop -----
            "infinite_loop", "loop_detected", "wot_loop",
        ]

        # Check notes + issues for hard fail matches
        for hp in HARD_FAIL:
            if hp in notes:
                return {
                    "rerun": False,
                    "reason": f"Hard failure (‘{hp}’) — rerun cannot fix.",
                    "verifier_notes": notes,
                }

        for issue in issues:
            low = issue.lower()
            if any(hp in low for hp in HARD_FAIL):
                return {
                    "rerun": False,
                    "reason": f"Hard issue from verifier: {issue}",
                    "verifier_notes": notes,
                }

        # ========================================================
        #  3. FICTION MODE — No rerun allowed
        # ========================================================
        if "fiction_mode" in notes or "creative_only" in notes:
            return {
                "rerun": False,
                "reason": "Fiction-mode output — no rerun allowed.",
                "verifier_notes": notes,
            }

        # ========================================================
        #  4. SOFT FAILURES (One rerun allowed)
        # ========================================================

        SOFT = [
            "contradiction",
            "incomplete", "missing steps",
            "weak explanation", "weak reasoning",
            "uncertain", "low confidence",
            "underused facts", "underused research",
            "context mismatch", "misaligned",
            "shallow", "superficial",
            "unstable", "needs more detail",
            "hallucination",  # soft hallucination
        ]

        for sp in SOFT:
            if sp in notes:
                return {
                    "rerun": True,
                    "reason": f"Soft failure (‘{sp}’) — one rerun may help.",
                    "verifier_notes": notes,
                }

        # -------- Simulation soft --------
        SIM_SOFT = [
            "weak simulation", "missing simulation detail",
            "simulation mismatch", "simulation_uncertain",
        ]
        for s in SIM_SOFT:
            if s in notes:
                return {
                    "rerun": True,
                    "reason": f"Simulation-soft (‘{s}’) — rerun allowed.",
                    "verifier_notes": notes,
                }

        # -------- Image soft --------
        IMG_SOFT = [
            "weak visual", "visual_uncertain", "missing visual detail",
            "incomplete image reasoning",
        ]
        for i in IMG_SOFT:
            if i in notes:
                return {
                    "rerun": True,
                    "reason": f"Image-soft (‘{i}’) — rerun allowed.",
                    "verifier_notes": notes,
                }

        # -------- Sound soft --------
        SND_SOFT = [
            "weak audio reasoning", "sound_uncertain",
            "poor sound mapping", "missing_sound_detail",
        ]
        for snd in SND_SOFT:
            if snd in notes:
                return {
                    "rerun": True,
                    "reason": f"Sound-soft (‘{snd}’) — rerun allowed.",
                    "verifier_notes": notes,
                }

        # -------- Refiner Ultra soft patterns --------
        ULTRA_SOFT = [
            "refiner_incomplete_synthesis",
            "cross_domain_merge_weak",
            "integration_shallow",
        ]
        for us in ULTRA_SOFT:
            if us in notes:
                return {
                    "rerun": True,
                    "reason": f"Refiner-soft (‘{us}’) — rerun may improve.",
                    "verifier_notes": notes,
                }

        # ========================================================
        #  5. UNKNOWN soft rejection → conservative rerun
        # ========================================================
        return {
            "rerun": True,
            "reason": "Unknown rejection — conservative one-time rerun.",
            "verifier_notes": notes,
        }