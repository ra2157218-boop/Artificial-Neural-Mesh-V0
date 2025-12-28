# ============================================================
# ANM V0-OpenSource — VFL LOOP V0-OpenSource
#  Verifier V0-OpenSource → Feedback → Learning Orchestrator
#  Router V0-OpenSource • Refiner V0-OpenSource • Verifier V0-OpenSource
# ============================================================

from __future__ import annotations
from typing import Any, Dict, List, Optional


class VFLLoop:
    """
    VFLLoop V0-OpenSource — safety governor for ANM V0-OpenSource.

    Features:
    ---------
    ✓ Verifier V0-OpenSource support (status / notes / score / issues)
    ✓ Structural tags: missing_verifier_ready, missing_merged_reasoning
    ✓ Treats VERIFIER format errors as structural → no rerun
    ✓ Still allows semantic conflicts to be rerun if consistency.rerun == True
    ✓ PointGame / LFM scoreboard hooks (success + penalty)
    ✓ Router exceptions never crash the VFL loop
    """

    def __init__(
        self,
        router: Any,
        lfm_scoreboard: Optional[Any] = None,
        max_attempts: int = 2,
    ) -> None:
        self.router = router
        self.lfm = lfm_scoreboard
        self.max_attempts = max(1, max_attempts)

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------
    def run(self, user_query: str) -> Dict[str, Any]:
        attempts: List[Dict[str, Any]] = []
        final_result: Optional[Dict[str, Any]] = None
        approved = False
        reason = "not_run"

        for run_idx in range(1, self.max_attempts + 1):

            # --------------------------------------------
            # 1. EXECUTE ROUTER (single full ANM run)
            # --------------------------------------------
            try:
                result = self.router.handle(user_query)
            except Exception as e:
                attempts.append({
                    "run_index": run_idx,
                    "status": "router_error",
                    "error": str(e),
                })
                reason = f"router_error: {e}"
                break

            # --------------------------------------------
            # 2. COLLECT VERIFICATION AND CONSISTENCY
            # --------------------------------------------
            verification: Dict[str, Any] = result.get("verification", {}) or {}
            consistency: Dict[str, Any] = result.get("consistency", {}) or {}

            status = verification.get("status", "unknown")
            notes = verification.get("notes", "")
            score = verification.get("score", None)
            issues = verification.get("issues", []) or []

            attempts.append({
                "run_index": run_idx,
                "status": status,
                "verification": verification,
                "consistency": consistency,
                "log_path": result.get("log_path"),
                "run_id": result.get("run_id"),
                "verifier_score": score,
                "verifier_issues": issues,
            })

            # Notify point engine (if present)
            self._notify_lfm(result)

            # --------------------------------------------
            # 3. APPROVED — STOP
            # --------------------------------------------
            if status == "approved":
                final_result = result
                approved = True
                reason = "approved"
                break

            # --------------------------------------------
            # 4. STRUCTURAL FAILURES → NO RERUN
            # --------------------------------------------
            if self._is_structural_failure(verification):
                final_result = result
                approved = False
                reason = f"rejected_structural ({notes})"
                break

            # --------------------------------------------
            # 5. RERUN LOGIC (ConsistencyChecker-driven)
            # --------------------------------------------
            rerun_flag = bool(consistency.get("rerun", False))

            if not rerun_flag:
                final_result = result
                approved = False
                reason = f"rejected_no_rerun ({notes})"
                break

            # If final attempt reached, stop
            if run_idx >= self.max_attempts:
                final_result = result
                approved = False
                reason = f"rejected_max_attempts ({notes})"
                break

            # Otherwise: retry with SAME user query
            # (Router + internal modules can adapt using past attempt info)

        # --------------------------------------------
        # 6. SAFETY FALLBACK (router returned nothing)
        # --------------------------------------------
        if final_result is None:
            final_result = {
                "status": "failed",
                "result": "[VFL] Router produced no valid result.",
                "verification": {},
                "router_plan": {},
                "consistency": {},
                "log_path": None,
            }

        # --------------------------------------------
        # 7. FINAL WRAP
        # --------------------------------------------
        vfl_meta = {
            "total_attempts": len(attempts),
            "approved": approved,
            "reason": reason,
        }

        return {
            "final": final_result,
            "attempts": attempts,
            "vfl_meta": vfl_meta,
        }

    # --------------------------------------------------------
    # INTERNAL: LFM / PointGame Integration
    # --------------------------------------------------------
    def _notify_lfm(self, router_result: Dict[str, Any]) -> None:
        """
        Safe hook into Learning Feedback Module / PointGame.
        Never allowed to crash the VFL loop.
        """
        if not self.lfm:
            return
        try:
            if hasattr(self.lfm, "update_from_run"):
                self.lfm.update_from_run(router_result)
        except Exception:
            # NEVER crash the VFL loop
            return

    # --------------------------------------------------------
    # INTERNAL: Structural failure detector (V0-OpenSource)
    # --------------------------------------------------------
    def _is_structural_failure(self, verification: Dict[str, Any]) -> bool:
        """
        Structural failures = the pipeline is broken, not just "answer is wrong".

        Verifier V0-OpenSource can emit:
          - notes: starting with "FORMAT_ERROR: ..."
          - issues: [
                "missing_verifier_ready",
                "missing_merged_reasoning",
                "missing_block",
                "missing_status",
                "empty_output",
                "missing_marker",
                ...
            ]

        We treat these as hard structural failures (no rerun),
        because retrying the same pipeline won't fix formatting.
        """

        if not verification:
            return True

        notes = str(verification.get("notes", "")).lower()
        issues = [str(i).lower() for i in (verification.get("issues") or [])]

        # Direct format / structure tags from v13 + V0-OpenSource
        format_tags = {
            "missing_marker",
            "missing_block",
            "missing_status",
            "empty_output",
            "missing_verifier_ready",
            "missing_merged_reasoning",
        }

        # 1) Notes-based checks
        if (
            "format_error" in notes
            or "missing [verifier_ready]" in notes
            or "missing decision block" in notes
            or "missing_verifier_ready" in notes
            or "missing_merged_reasoning" in notes
            or "verifier_packet missing merged_reasoning" in notes
        ):
            return True

        # 2) Issues-based checks
        if any(tag in issues for tag in format_tags):
            return True

        # Status "unknown" with no score and no issues is also suspicious
        status = verification.get("status")
        score = verification.get("score", None)
        if (status is None or status == "unknown") and not issues and score in (None, 0):
            return True

        return False