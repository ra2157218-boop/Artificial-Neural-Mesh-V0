# ============================================================
# ANM V0-OpenSource — ROUTER V0-OpenSource
#  SUPERVISED POLYMATH + LFM V0-OpenSource MAX + PointGame v3.0
#  HyperMemory V0-OpenSource (MemoryBridge V0-OpenSource MAX)
#  META-AWARE • SOUND / IMAGE / SIMULATION DOMAIN • PARALLEL R1 ENSEMBLE
#  WoT V15 MAX • METACOGNITIVE • SELF-CORRECTING
#  LawBook V0-OpenSource aligned
# ============================================================

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from anm.utils.prompts import ROUTER_PROMPT, WOT_PACKET_TEMPLATES
from anm.utils.debug_logger import log_debug

# Specialists
from anm.specialists.math_llm import MathLLM
from anm.specialists.physics_llm import PhysicsLLM
from anm.specialists.general_llm import GeneralLLM
from anm.specialists.code_llm import CodeLLM
from anm.specialists.chemistry_llm import ChemistryLLM
from anm.specialists.biology_llm import BiologyLLM
from anm.specialists.facts_llm import FactsLLM
from anm.specialists.memory_llm import MemoryLLM

# For Research Mode: Direct specialist instantiation (no ParallelSpecialistAdapter)

# Research specialist (optional - requires requests)
try:
    from anm.specialists.research_llm import ResearchLLM
    RESEARCH_LLM_AVAILABLE = True
except ImportError:
    ResearchLLM = None
    RESEARCH_LLM_AVAILABLE = False
from anm.specialists.sound_llm import SoundLLM  # SOUND domain

# Optional multi-modal specialists (graceful if missing)
try:
    from anm.specialists.simulation_llm import SimulationLLM  # type: ignore
except Exception:  # pragma: no cover - optional
    SimulationLLM = None  # type: ignore

try:
    from anm.specialists.image_llm import ImageLLM  # type: ignore
except Exception:  # pragma: no cover - optional
    ImageLLM = None  # type: ignore

# Executive modules
from anm.utils.logger import ANMLogger
from anm.refiner.refiner import Refiner
from anm.verifier.verifier import Verifier

# WoT V15 MAX (with fallback to V14)
try:
    from anm.wot import TrueWoTMax as TrueWoT, WoTConfig, WoTMode
    WOT_V15_AVAILABLE = True
except ImportError:
    from anm.wot.wot_engine import TrueWoT
    WOT_V15_AVAILABLE = False
    WoTConfig = None
    WoTMode = None

from anm.memory_bridges.memory_bridge import build_memory_brief
from anm.router.planner_llm import PlannerLLM
from anm.router.domain_masker import DomainMasker
from anm.router.consistency_checker import ConsistencyChecker
from anm.router.novelty_handler import NoveltyHandler
from anm.router.voting_handler import VotingHandler
from anm.router.expansion_handler import ExpansionHandler

# Learning & scoring
from anm.lfm.lfm_module import LFMModule          # LFM V0-OpenSource MAX
from anm.learning.point_game import PointGame     # PointGame v3.0


# ------------------------------------------------------------
#  PARALLEL SPECIALIST ADAPTER (4× R1 ENSEMBLE)
# ------------------------------------------------------------

class ParallelSpecialistAdapter:
    """
    Wraps a specialist class (e.g., PhysicsLLM) into an ensemble of N workers.

    WoT expects:   run(wot_packet: str) -> str
    Worker class:  run(wot_packet: str) -> str

    Behaviour:
      • Spawns N workers (default = 4).
      • For each .run(packet):
          - Calls all workers in parallel.
          - Picks a primary candidate (longest CoT that also has a valid WOT_REQUEST).
          - Strips all internal WOT_REQUEST lines from that primary.
          - Appends a single consensus WOT_REQUEST line at the end.
      • This keeps TrueWoT happy (ONLY one WOT_REQUEST: line visible).

    OPTIMIZATION (V0-OpenSource):
      • adaptive_workers: Use fewer workers in ADAPTIVE mode (1 by default)
      • set_adaptive_mode(bool): Toggle between full ensemble and single worker
    """

    def __init__(
        self,
        worker_cls,
        n_workers: int = 4,
        name: str = "",
        worker_kwargs: Optional[Dict[str, Any]] = None,  # NEW: Pass kwargs to workers
        adaptive_workers: int = 1,  # Workers for adaptive mode (optimization)
    ) -> None:
        self.worker_cls = worker_cls
        self.n_workers = max(1, int(n_workers or 1))
        self.adaptive_workers = max(1, int(adaptive_workers or 1))
        self._adaptive_mode = False  # Start in full ensemble mode
        self.name = name or getattr(worker_cls, "__name__", "specialist")
        kwargs = worker_kwargs or {}
        self.workers = [worker_cls(**kwargs) for _ in range(self.n_workers)]

    def set_adaptive_mode(self, enabled: bool) -> None:
        """Enable/disable adaptive mode (uses fewer workers for speed)."""
        self._adaptive_mode = enabled

    @property
    def active_workers(self) -> int:
        """Get current active worker count based on mode."""
        return self.adaptive_workers if self._adaptive_mode else self.n_workers

    # ------------- internal helpers -------------

    @staticmethod
    def _extract_wot_request(text: str) -> str:
        """
        Parse WOT_REQUEST: <TOKEN> from the text.

        Uses centralized utility for consistency.
        """
        from anm.utils.wot_utils import extract_wot_request
        return extract_wot_request(text)

    @staticmethod
    def _strip_all_wot_requests(text: str) -> str:
        """
        Remove ALL lines that start with 'WOT_REQUEST:' (case-insensitive).
        
        Uses centralized utility for consistency.
        """
        from anm.utils.wot_utils import strip_all_wot_requests
        return strip_all_wot_requests(text)

    # ------------- public API -------------

    def run(self, wot_packet: str) -> str:
        # Get active worker count (respects adaptive mode)
        num_active = self.active_workers

        # Single worker case → just delegate (optimized path)
        if num_active <= 1 or len(self.workers) <= 1:
            return self.workers[0].run(wot_packet)

        # Multi-worker ensemble (use only active_workers count)
        results: List[str] = []
        active_workers_list = self.workers[:num_active]

        def _safe_run(worker):
            try:
                out = worker.run(wot_packet)
                return str(out) if out is not None else ""
            except Exception as e:
                return f"[{self.name} worker error: {e}]"

        with ThreadPoolExecutor(max_workers=num_active) as ex:
            futs = [ex.submit(_safe_run, w) for w in active_workers_list]
            for fut in as_completed(futs):
                try:
                    results.append(fut.result())
                except Exception as e:
                    results.append(f"[{self.name} worker crashed: {e}]")

        if not results:
            # Extreme edge case
            return (
                f"[{self.name} ParallelSpecialistAdapter] "
                "All workers failed.\n\nWOT_REQUEST: NONE"
            )

        # Choose primary candidate:
        #   1) must have a non-NONE WOT_REQUEST if possible
        #   2) then longest length
        best_idx = 0
        best_score = -1
        best_req = "NONE"

        for idx, txt in enumerate(results):
            t = txt or ""
            req = self._extract_wot_request(t)
            length_score = len(t)

            # preference: valid WOT_REQUEST + length
            score = length_score
            if req not in ("NONE", "", "none"):
                score += 5000  # strong preference for having a domain request

            if score > best_score:
                best_score = score
                best_idx = idx
                best_req = req if req else "NONE"

        primary = results[best_idx]

        # Strip all WOT_REQUEST lines from primary, append single consensus line
        body = self._strip_all_wot_requests(primary).rstrip()
        final_req = best_req if best_req else "NONE"

        if not body:
            body = f"[{self.name} ensemble] empty reasoning."

        return f"{body}\n\nWOT_REQUEST: {final_req}"


# ------------------------------------------------------------
# MEMORY SPECIALIST ADAPTER (WoT-facing)
# ------------------------------------------------------------

class MemorySpecialistAdapter:
    """
    Thin adapter so that MemoryLLM can be used as a WoT "specialist".

    WoT expects:   run(wot_packet: str) -> str
    MemoryLLM:     query(user_query: str, ...) -> dict
    """

    def __init__(self, memory_llm: Optional[MemoryLLM] = None) -> None:
        self.memory_llm = memory_llm or MemoryLLM()

    def run(self, wot_packet: str) -> str:
        user_query = self._extract_user_query(wot_packet)
        result = self.memory_llm.query(
            user_query=user_query,
            limit_blocks=5,
            use_recent_fallback=True,
        )

        highlights = result.get("highlights", []) or []
        summary = result.get("memory_summary", "").strip() or "No summary."

        lines: List[str] = []
        lines.append("MEMORY HIGHLIGHTS (PAST CONTEXT):")
        if not highlights:
            lines.append("- No specific matching memories found.")
        else:
            for h in highlights:
                lines.append(f"- {h}")

        lines.append("")
        lines.append("MEMORY SUMMARY (PAST EXPERIENCES, NOT GUARANTEED CURRENT):")
        lines.append(summary)
        lines.append("")
        lines.append("WOT_REQUEST: NONE")

        return "\n".join(lines).strip()

    @staticmethod
    def _extract_user_query(packet: str) -> str:
        """
        Extract a rough USER QUERY from a WoT packet.
        Fallback: first ~400 chars.
        """
        if "USER QUERY:" not in packet:
            return packet.strip()[:400]

        after = packet.split("USER QUERY:", 1)[1]
        lines = after.splitlines()

        collected: List[str] = []
        started = False

        for ln in lines[1:]:
            if not started and not ln.strip():
                continue
            if not ln.strip():
                break
            started = True
            collected.append(ln.rstrip())

        text = "\n".join(collected).strip()
        return text or packet.strip()[:400]


# ------------------------------------------------------------
# ROUTER V0-OpenSource MAX
# ------------------------------------------------------------

class Router:
    """
    ANM V0-OpenSource Router V0-OpenSource MAX — SUPERVISED POLYMATH MODE + SOUND/IMAGE/SIMULATION + 4×R1.

    LawBook V0-OpenSource alignment:
      - All user queries pass through this Router.
      - Memory is PAST-ONLY and never treated as current truth.
      - Physics / Math treated with extra caution.
      - Sound / Image / Simulation domains are additive; never override hard evidence.
      - Learning modules (LFM + PointGame) cannot override hard safety.

    Domains:
      - general     (ParallelSpecialistAdapter[GeneralLLM])
      - math        (ParallelSpecialistAdapter[MathLLM])
      - physics     (ParallelSpecialistAdapter[PhysicsLLM])
      - code        (ParallelSpecialistAdapter[CodeLLM])
      - chemistry   (ParallelSpecialistAdapter[ChemistryLLM])
      - biology     (ParallelSpecialistAdapter[BiologyLLM])
      - memory      (MemoryLLM + MemorySpecialistAdapter — single core)
      - research    (ParallelSpecialistAdapter[ResearchLLM])
      - facts       (ParallelSpecialistAdapter[FactsLLM])
      - sound       (ParallelSpecialistAdapter[SoundLLM])
      - simulation  (ParallelSpecialistAdapter[SimulationLLM])  [optional]
      - image       (ParallelSpecialistAdapter[ImageLLM])       [optional]
    """

    VALID_DOMAINS = {
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
    }

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Router with configuration."""
        self._logger = logging.getLogger(__name__)
        self.config = config or {}

        self.default_max_steps: int = self.config.get("wot_max_steps", 16)
        self.router_model: str = self.config.get("model_router", "deepseek-r1:1.5b")
        self.system_prompt: str = ROUTER_PROMPT

        # NORMAL MODE: N workers per specialist for ensemble voting (default: 4)
        # RESEARCH MODE: Bypasses this entirely - uses _build_research_specialists()
        #                which creates 1 worker per specialist with authority models
        self.parallel_workers: int = int(self.config.get("parallel_r1_workers", 4) or 4)

        # Logger
        self.logger = ANMLogger()

        # Memory core (single) + adapter (single specialist)
        self._memory_core = MemoryLLM()
        self.memory_adapter = MemorySpecialistAdapter(self._memory_core)

        # Specialists (WRAPPED in ParallelSpecialistAdapter, except memory)
        self.general = ParallelSpecialistAdapter(
            GeneralLLM,
            n_workers=self.parallel_workers,
            name="general",
        )
        self.math = ParallelSpecialistAdapter(
            MathLLM,
            n_workers=self.parallel_workers,
            name="math",
        )
        self.physics = ParallelSpecialistAdapter(
            PhysicsLLM,
            n_workers=self.parallel_workers,
            name="physics",
        )
        self.code = ParallelSpecialistAdapter(
            CodeLLM,
            n_workers=self.parallel_workers,
            name="code",
        )
        self.chemistry = ParallelSpecialistAdapter(
            ChemistryLLM,
            n_workers=self.parallel_workers,
            name="chemistry",
        )
        self.biology = ParallelSpecialistAdapter(
            BiologyLLM,
            n_workers=self.parallel_workers,
            name="biology",
        )
        
        # Research specialist (optional - requires requests)
        # NOTE: ResearchLLM initialization moved after research_kb setup (line 455+)
        # Placeholder for now - will be initialized after research_kb
        self.research = None
        
        self.facts = ParallelSpecialistAdapter(
            FactsLLM,
            n_workers=self.parallel_workers,
            name="facts",
        )
        self.sound = ParallelSpecialistAdapter(
            SoundLLM,
            n_workers=self.parallel_workers,
            name="sound",
        )

        # Optional multi-modal specialists (created only if class exists)
        # SimulationLLM now uses Nebula Engine directly (no config needed)
        if SimulationLLM is not None:
            self.simulation = ParallelSpecialistAdapter(
                SimulationLLM,
                n_workers=self.parallel_workers,
                name="simulation",
            )
        else:
            self.simulation = None

        if ImageLLM is not None:
            self.image = ParallelSpecialistAdapter(
                ImageLLM,
                n_workers=self.parallel_workers,
                name="image",
            )
        else:
            self.image = None

        # Executive modules
        self.refiner = Refiner()
        self.verifier = Verifier()
        self.planner = PlannerLLM(
            model_name=self.router_model,
            system_prompt=self.system_prompt,
        )
        self.domain_masker = DomainMasker(self.config, self.VALID_DOMAINS)
        self.consistency_checker = ConsistencyChecker()

        # Learning From Mistakes
        self.lfm = LFMModule(self._memory_core)

        # Make sure LFM knows about multi-modal domains (avoid KeyError)
        if hasattr(self.lfm, "DOMAIN_SCORES"):
            self.lfm.DOMAIN_SCORES.setdefault("sound", 0)
            self.lfm.DOMAIN_SCORES.setdefault("simulation", 0)
            self.lfm.DOMAIN_SCORES.setdefault("image", 0)
            if hasattr(self.lfm, "ERROR_STATS"):
                self.lfm.ERROR_STATS.setdefault("sound", {})
                self.lfm.ERROR_STATS.setdefault("simulation", {})
                self.lfm.ERROR_STATS.setdefault("image", {})

        # PointGame scoring engine (global performance across runs)
        self.point_game = PointGame()
        
        # Handlers for modularity
        self.novelty_handler = NoveltyHandler(self.VALID_DOMAINS, self.config)
        
        # Initialize Research Knowledge Base (RAG) - BEFORE ResearchLLM
        self.research_kb = None
        research_kb_enabled = self.config.get("research_kb_enabled", True)
        if research_kb_enabled:
            try:
                from anm.memory.research_vector_store import ResearchVectorStore
                self.research_kb = ResearchVectorStore()
                if self.research_kb.is_available():
                    self._logger.info("Research Knowledge Base enabled")
                else:
                    self._logger.warning("Research KB unavailable, RAG disabled")
                    self.research_kb = None
            except Exception as e:
                self._logger.warning(f"Failed to initialize Research KB: {e}")
                self.research_kb = None

        # Initialize ResearchLLM with research_kb (after research_kb is ready)
        if ResearchLLM is not None:
            research_kwargs = {
                "research_kb": self.research_kb,
                "model_name": self.router_model,  # Use same model as router
                # Note: gre, self_awareness_llm, working_memory, meta_memory are optional
                # Router doesn't initialize these components, so they default to None
                # ResearchLLM will work fine without them (graceful degradation)
            }
            self.research = ParallelSpecialistAdapter(
                ResearchLLM,
                n_workers=self.parallel_workers,
                name="research",
                worker_kwargs=research_kwargs,
            )

        # Build specialists dict for handlers (needed for voting and expansion)
        self._handler_specialists = {
            "general": self.general,
            "math": self.math,
            "physics": self.physics,
            "code": self.code,
            "chemistry": self.chemistry,
            "biology": self.biology,
            "facts": self.facts,
        }
        if self.research is not None:
            self._handler_specialists["research"] = self.research

        self.voting_handler = VotingHandler(self._handler_specialists, self.config)
        self.expansion_handler = ExpansionHandler(self._handler_specialists, self.config)

        # Research mode configuration
        self.research_mode_config = self.config.get("research_mode_configs", {})
        self.research_mode_active = False

    # ========================================================
    #  MAIN ENTRY
    # ========================================================

    def handle(self, user_query: str, quick_mode: bool = False, research_mode: bool = False, progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Main entry point for processing a user query.

        Args:
            user_query: The user's query
            quick_mode: Whether to use quick mode (simplified pipeline)
            research_mode: Whether to use research mode (maximum quality, deterministic routing)

        Returns:
            Dict containing result, verification, metadata, and metrics
        """
        # Input validation
        if not user_query or not isinstance(user_query, str):
            self._logger.error(f"Invalid query type: {type(user_query)}")
            return {
                "status": "error",
                "result": "Invalid query: must be a non-empty string",
                "error": "Invalid input",
            }
        
        user_query = user_query.strip()
        if not user_query:
            self._logger.warning("Empty query received")
            return {
                "status": "error",
                "result": "Invalid query: query cannot be empty",
                "error": "Empty input",
            }
        
        import time
        handle_start_time = time.time()
        self._logger.debug(f"Processing query (quick_mode={quick_mode}, research_mode={research_mode}): {user_query[:100]}...")

        # Call progress callback for initial stage
        if progress_callback:
            progress_callback("Initializing", 0.0)

        # Research mode: deterministic routing
        self.research_mode_active = research_mode
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_CHECK", "location": "router.py:handle", "message": "Research mode check", "data": {"research_mode": research_mode, "will_use_research_mode": research_mode}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        if research_mode:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_CHECK", "location": "router.py:handle", "message": "Calling _handle_research_mode", "data": {"user_query_preview": user_query[:100]}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            return self._handle_research_mode(user_query, progress_callback=progress_callback)

        # Quick mode: simplified path
        if quick_mode:
            return self._handle_quick_mode(user_query)

        # Normal mode: full pipeline

        # 0) Snapshot PointGame state BEFORE this run (PAST-ONLY for Refiner)
        pg_stats_before = self.point_game.stats()

        # 1) Start log run
        self.logger.new_run(user_query)

        # 2) Load memory brief at start (global context, PAST-ONLY)
        memory_info = build_memory_brief(self._memory_core, user_query)
        memory_brief = memory_info["brief_text"]
        self.logger.log_memory(memory_brief)

        # 3) AI-powered domain classification (using R1 model)
        # This intelligently analyzes the query to determine the best specialist
        coarse_entry = self._ai_domain_classifier(user_query)

        # 3.5) Novelty Detection - Check if query requires a new domain
        novelty_result = self.novelty_handler.detect(user_query, memory_brief)
        if novelty_result.get("requires_new_domain", False):
            # Trigger specialists voting system with graceful timeout handling
            try:
                voting_result = self.voting_handler.vote(
                    user_query=user_query,
                    detected_domain=novelty_result.get("detected_domain"),
                    novelty_reasoning=novelty_result.get("reasoning", ""),
                    memory_brief=memory_brief,
                )
            except (TimeoutError, Exception) as voting_error:
                # Gracefully handle voting timeout - continue without expansion
                self._logger.warning(f"Voting system timeout/error: {voting_error}. Skipping expansion.")
                voting_result = {
                    "majority_yes": False,
                    "skipped": True,
                    "error": str(voting_error),
                    "votes": {},
                }
            if voting_result.get("majority_yes", False):
                # Trigger expansion engine
                expansion_result = self.expansion_handler.trigger(
                    user_query=user_query,
                    detected_domain=novelty_result.get("detected_domain"),
                    novelty_reasoning=novelty_result.get("reasoning", ""),
                    voting_result=voting_result,
                    memory_brief=memory_brief,
                )
                # If expansion was triggered, return early with expansion status
                if expansion_result.get("expansion_triggered", False):
                    return {
                        "status": "expansion_triggered",
                        "novelty": novelty_result,
                        "voting": voting_result,
                        "expansion": expansion_result,
                        "run_id": self.logger.run_id,
                    }

        # 4) PlannerLLM decides strategy (soft brain)
        base_plan = self.planner.plan(user_query, memory_brief) or {}
        base_plan.setdefault("run_id", self.logger.run_id)
        base_plan["user_query"] = user_query  # DomainMasker uses this

        # Ensure entry_specialist exists (fallback to coarse or general)
        entry_specialist = str(base_plan.get("entry_specialist", "") or "").lower()
        if entry_specialist not in self.VALID_DOMAINS:
            entry_specialist = coarse_entry or "general"
        base_plan["entry_specialist"] = entry_specialist

        # Ensure max_steps is sane
        max_steps = base_plan.get("max_steps", self.default_max_steps)
        if not isinstance(max_steps, int) or max_steps <= 0:
            max_steps = self.default_max_steps
        base_plan["max_steps"] = max_steps

        # 5) LFM Module — adjust plan using past failures
        # #region agent log
        try:
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "router.py:handle", "message": "Before LFM adjust_plan", "data": {"has_base_plan": bool(base_plan), "user_query": user_query[:100]}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        try:
            adjusted_plan = self.lfm.adjust_plan(
                user_query=user_query,
                base_plan=base_plan,
                memory_snapshot=memory_info.get("raw_memory"),
            )
        except Exception as e:
            # #region agent log
            try:
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "router.py:handle", "message": "LFM adjust_plan exception", "data": {"error_type": type(e).__name__, "error_msg": str(e)[:200]}, "timestamp": int(time.time() * 1000)})
            except Exception as ex:
                logging.warning(f"Debug logging failed: {ex}")
            # #endregion
            self._logger.error(f"LFM adjust_plan failed: {type(e).__name__}: {e}", exc_info=True)
            # Fallback to base_plan if LFM fails
            adjusted_plan = base_plan.copy() if base_plan else {
                "entry_specialist": entry_specialist if 'entry_specialist' in locals() else "general",
                "active_domains": active_domains if 'active_domains' in locals() else ["general"],
                "max_steps": max_steps if 'max_steps' in locals() else self.default_max_steps,
            }
        # #region agent log
        try:
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "router.py:handle", "message": "After LFM adjust_plan", "data": {"has_adjusted_plan": bool(adjusted_plan), "entry_specialist": adjusted_plan.get("entry_specialist") if adjusted_plan else None}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        
        # CRITICAL: Ensure adjusted_plan is always a valid dict
        if not adjusted_plan or not isinstance(adjusted_plan, dict):
            adjusted_plan = {
                "entry_specialist": entry_specialist if 'entry_specialist' in locals() else "general",
                "active_domains": active_domains if 'active_domains' in locals() else ["general"],
                "max_steps": max_steps if 'max_steps' in locals() else self.default_max_steps,
            }

        # Normalize again after LFM
        entry_specialist = str(adjusted_plan.get("entry_specialist", entry_specialist)).lower()
        if entry_specialist not in self.VALID_DOMAINS:
            entry_specialist = coarse_entry or "general"
        adjusted_plan["entry_specialist"] = entry_specialist

        max_steps = adjusted_plan.get("max_steps", max_steps)
        if not isinstance(max_steps, int) or max_steps <= 0:
            max_steps = self.default_max_steps
        adjusted_plan["max_steps"] = max_steps
        adjusted_plan["user_query"] = user_query

        # 6) Merge research/facts flags into active_domains BEFORE masking
        active_domains_plan = adjusted_plan.get("active_domains")
        if not isinstance(active_domains_plan, list):
            active_domains_plan = []

        # ensure entry is present
        active_domains_lower = [str(d).lower() for d in active_domains_plan]
        if entry_specialist not in active_domains_lower:
            active_domains_plan.append(entry_specialist)

        # planner signals
        if bool(adjusted_plan.get("needs_research", False)):
            active_domains_plan.append("research")
        if bool(adjusted_plan.get("needs_facts", False)):
            active_domains_plan.append("facts")

        adjusted_plan["active_domains"] = active_domains_plan

        # 7) Domain masking — final active domains (config-aware gating)
        active_domains = self.domain_masker.apply(adjusted_plan)

        # Ensure entry specialist is included after masking
        if entry_specialist not in active_domains:
            if entry_specialist in self.VALID_DOMAINS:
                active_domains.append(entry_specialist)
            else:
                entry_specialist = "general"
                if "general" not in active_domains:
                    active_domains.insert(0, "general")

        # 8) Log router plan + domains (+ coarse + adjusted)
        self.logger.log_router_decision(
            {
                "coarse_entry": coarse_entry,
                "planner_plan": base_plan,
                "lfm_adjusted_plan": adjusted_plan,
                "entry_specialist": entry_specialist,
                "max_steps": max_steps,
                "active_domains": active_domains,
            }
        )

        # 9) Build specialists dict for TrueWoT (only active ones)
        all_specialists: Dict[str, Any] = {
            "general": self.general,
            "math": self.math,
            "physics": self.physics,
            "code": self.code,
            "chemistry": self.chemistry,
            "biology": self.biology,
            "memory": self.memory_adapter,  # single-core
            "facts": self.facts,
            "sound": self.sound,
        }

        # optional ones only if instantiated
        if self.research is not None:
            all_specialists["research"] = self.research
        if self.simulation is not None:
            all_specialists["simulation"] = self.simulation
        if self.image is not None:
            all_specialists["image"] = self.image

        specialists: Dict[str, Any] = {
            name: all_specialists[name]
            for name in active_domains
            if name in all_specialists and all_specialists[name] is not None
        }

        # Safety: if for some reason we ended up with zero specialists
        if not specialists:
            specialists = {"general": self.general}
            entry_specialist = "general"
            active_domains = ["general"]

        # 10) Build full_query that includes memory brief (PAST-ONLY)
        full_query = (
            f"{user_query.strip()}\n\n"
            f"{memory_brief}\n\n"
            "Use the Cloud Diary brief ONLY as past context; "
            "it is NOT guaranteed to be true now.\n"
        )

        # 11) Run TrueWoT polymath engine
        import time
        wot_start_time = time.time()
        # #region agent log
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "router.py:handle", "message": "Before WoT execution", "data": {"has_adjusted_plan": bool(adjusted_plan), "entry_specialist": entry_specialist, "active_domains": active_domains}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "I", "location": "router.py:handle", "message": "Before WoT try block", "data": {"entry_specialist": entry_specialist, "specialists_count": len(specialists)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        try:
            # Determine WoT mode from config/plan
            wot_mode = adjusted_plan.get("wot_mode", "metacognitive").lower()
            use_adaptive_mode = wot_mode == "adaptive"

            # OPTIMIZATION: Set adaptive mode on specialists (uses 1 worker instead of 4)
            if use_adaptive_mode:
                for spec in specialists.values():
                    if hasattr(spec, 'set_adaptive_mode'):
                        spec.set_adaptive_mode(True)

            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "I", "location": "router.py:handle", "message": "Before TrueWoT instantiation", "data": {"wot_mode": wot_mode, "use_adaptive_mode": use_adaptive_mode}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

            wot = TrueWoT(
                domain_names=list(specialists.keys()),
                memory_llm=self._memory_core,  # direct MemoryLLM path
            )
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "I", "location": "router.py:handle", "message": "After TrueWoT instantiation, before wot.run", "data": {"entry_domain": entry_specialist, "max_steps": max_steps}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            domain_cots: Dict[str, str] = wot.run(
                entry_domain=entry_specialist,
                query=full_query,
                specialists=specialists,
                max_steps=max_steps,
                mode=wot_mode if wot_mode in ("adaptive", "parallel", "beam_search", "consensus", "metacognitive", "state_machine") else None,
            )
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "I", "location": "router.py:handle", "message": "After wot.run call", "data": {"domain_cots_count": len(domain_cots) if domain_cots else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            wot_end_time = time.time()
            wot_processing_time_ms = (wot_end_time - wot_start_time) * 1000
            wot_steps = getattr(wot, 'total_steps', 0)
        except Exception as e:
            # If WoT fails, return error with router_plan defined
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "router.py:handle", "message": "WoT exception caught", "data": {"error_type": type(e).__name__, "error_msg": str(e)[:200], "has_adjusted_plan": 'adjusted_plan' in locals(), "adjusted_plan_type": type(adjusted_plan).__name__ if 'adjusted_plan' in locals() else "N/A"}, "timestamp": int(time.time() * 1000)})
            except Exception as ex:
                logging.warning(f"Debug logging failed: {ex}")
            # #endregion
            self._logger.error(f"WoT execution failed: {type(e).__name__}: {e}", exc_info=True)
            wot_end_time = time.time()
            wot_processing_time_ms = (wot_end_time - wot_start_time) * 1000
            wot_steps = 0
            domain_cots = {}
            
            # Return error result with router_plan properly set
            return {
                "status": "error",
                "result": f"WoT execution failed: {str(e)}",
                "error": f"{type(e).__name__}: {str(e)}",
                "log_path": self.logger.save() if hasattr(self.logger, 'save') else None,
                "router_plan": adjusted_plan if 'adjusted_plan' in locals() else {"entry_specialist": "general", "active_domains": ["general"], "mode": "normal"},  # Ensure router_plan is always defined
                "processing_time_ms": (time.time() - handle_start_time) * 1000,
                "wot_steps": 0,
            }

        # For now, we log a single round aggregate
        self.logger.log_round(1, domain_cots)

        # 12) Refiner (build enriched packet with task_meta + anm_stats)
        # Store adjusted_plan in a variable that persists through exception handling
        # CRITICAL: Define router_plan_for_refiner BEFORE try block to ensure it's always available
        # Ensure adjusted_plan exists before copying
        if 'adjusted_plan' not in locals() or not adjusted_plan:
            # Fallback: create default adjusted_plan
            adjusted_plan = {
                "entry_specialist": entry_specialist if 'entry_specialist' in locals() else "general",
                "active_domains": active_domains if 'active_domains' in locals() else ["general"],
                "max_steps": max_steps if 'max_steps' in locals() else self.default_max_steps,
            }
        router_plan_for_refiner = adjusted_plan.copy() if adjusted_plan else {}
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H6", "location": "router.py:handle", "message": "router_plan_for_refiner defined", "data": {"has_router_plan": bool(router_plan_for_refiner), "entry_specialist": router_plan_for_refiner.get("entry_specialist") if router_plan_for_refiner else None}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        try:
            refiner_packet = self._build_refiner_packet(
                user_query=user_query,
                domain_cots=domain_cots,
                entry_specialist=entry_specialist,
                router_plan=router_plan_for_refiner,  # Use captured copy
                pg_stats_before=pg_stats_before,
            )
            self.logger.log_refiner_packet(refiner_packet)

            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "router.py:handle", "message": "Before refiner.refine call", "data": {"refiner_packet_length": len(refiner_packet) if refiner_packet else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

            refined_output = self.refiner.refine(refiner_packet)
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "router.py:handle", "message": "After refiner.refine call", "data": {"refined_output_length": len(refined_output) if refined_output else 0, "is_empty": not refined_output or not refined_output.strip()}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # CRITICAL: Block empty output from refiner
            if not refined_output or not refined_output.strip() or refined_output.strip() in ["", "None", "N/A", "[VERIFIER_READY]"]:
                logging.error("Router: Refiner returned empty output - using emergency fallback")
                # Try to extract content from domain outputs
                fallback_parts = []
                for domain, cot in domain_cots.items():
                    if cot and cot.strip() and "[produced no output]" not in cot.lower():
                        # Extract first meaningful sentence
                        sentences = re.split(r'[.!?]\s+', cot)
                        for sent in sentences:
                            if len(sent.strip()) > 20:
                                fallback_parts.append(f"**{domain.title()}**: {sent.strip()}")
                                break
                        if len(fallback_parts) >= 2:
                            break
                
                if fallback_parts:
                    # Blueprint compliance: Mark output as fallback (transparent reporting)
                    refined_output = "\n\n".join(fallback_parts) + "\n\n[FALLBACK OUTPUT - Refiner unavailable. Content extracted from domain outputs.]\n[VERIFIER_READY]"
                else:
                    refined_output = f"I apologize, but I encountered an issue while processing your query: '{user_query}'. The system was unable to generate a proper response. Please try rephrasing your question.\n\n[FALLBACK OUTPUT - Refiner and domain outputs unavailable.]\n[VERIFIER_READY]"
            
            self.logger.log_refiner(refined_output)

            # 13) Verifier
            verifier_packet = self._build_verifier_packet(
                user_query=user_query,
                merged_reasoning=refined_output,
                entry_specialist=entry_specialist,
                router_reason=router_plan_for_refiner.get("reason", ""),
            )
            self.logger.log_verifier_packet(verifier_packet)

            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "router.py:handle", "message": "Before verifier.run call", "data": {"verifier_packet_length": len(verifier_packet) if verifier_packet else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

            verification = self.verifier.run(verifier_packet)
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "router.py:handle", "message": "After verifier.run call", "data": {"verification_status": verification.get("status") if verification else "NONE"}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            self.logger.log_verifier(verification)

            status = verification.get("status", "approved")
        except Exception as e:
            # If refiner/verifier fails, return error with router_plan defined
            # router_plan_for_refiner should already be defined before try block
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H6", "location": "router.py:handle", "message": "Refiner/Verifier exception caught", "data": {"error_type": type(e).__name__, "error_msg": str(e)[:200], "has_router_plan_for_refiner": 'router_plan_for_refiner' in locals()}, "timestamp": int(time.time() * 1000)})
            except Exception as ex:
                logging.warning(f"Debug logging failed: {ex}")
            # #endregion
            self._logger.error(f"Refiner/Verifier execution failed: {type(e).__name__}: {e}", exc_info=True)
            refined_output = f"[Error during refinement/verification: {str(e)}]"
            verification = {
                "status": "error",
                "notes": f"Refiner/Verifier failed: {str(e)}",
                "score": 0,
                "issues": ["processing_error"],
            }
            status = "error"
            # Ensure router_plan_for_refiner is available even if exception occurred before definition
            if 'router_plan_for_refiner' not in locals():
                router_plan_for_refiner = adjusted_plan.copy() if 'adjusted_plan' in locals() and adjusted_plan else {}

        # 14) Consistency Checker (hook for future rerun)
        consistency_decision = self.consistency_checker.analyze(
            user_query=user_query,
            merged_reasoning=refined_output,
            verification=verification,
        )
        self.logger.log_wot_analysis(consistency_decision)

        # 15) PointGame — update scores and get Router Feedback Signal (RFS)
        # Use router_plan_for_refiner if available, otherwise fall back to adjusted_plan
        # #region agent log
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H5", "location": "router.py:handle", "message": "Before PointGame router_plan check", "data": {}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        try:
            router_plan_for_pg = router_plan_for_refiner
        except NameError:
            try:
                router_plan_for_pg = adjusted_plan
            except NameError:
                router_plan_for_pg = {}
        run_result_for_pg: Dict[str, Any] = {
            "status": status,
            "verification": verification,
            "router_plan": router_plan_for_pg,
            "router_entry": entry_specialist,
            "domain_cots": domain_cots,
        }
        try:
            rfs = self.point_game.update_from_run(run_result_for_pg)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            # Specific exceptions for point game update failures
            self.logger.log_error("point_game_update", f"{type(e).__name__}: {str(e)}")
            rfs = {
                "difficulty": "unknown",
                "reward": 0,
                "boost": False,
                "penalty": False,
                "suggest_stricter_verifier": False,
                "suggest_more_domains": False,
                "suggest_reduce_domains": False,
            }

        pg_stats_after = self.point_game.stats()

        # 16) LFMModule — analyze this run (COMPREHENSIVE learning with all data sources)
        lfm_report: Optional[Dict[str, Any]] = None
        try:
            # Extract specialist outputs with metrics from domain_cots
            specialist_outputs = self._extract_specialist_metrics(domain_cots, specialists)
            
            # Extract refiner metrics
            refiner_metrics = self._extract_refiner_metrics(refined_output)
            
            # Extract WoT steps (if available from TrueWoT)
            wot_steps = self._extract_wot_steps(wot, domain_cots)
            
            # Build processing metrics
            total_processing_time_ms = (time.time() - handle_start_time) * 1000
            processing_metrics = {
                "total_tokens": 0,  # Can be enhanced if token tracking is available
                "total_time_ms": total_processing_time_ms,
                "wot_time_ms": wot_processing_time_ms,
                "wot_steps": wot_steps,
            }
            
            # Determine auto mode decision (from router plan or config)
            auto_mode_decision = adjusted_plan.get("mode") == "quick" or quick_mode
            
            # Determine if prompt was optimized (check if query was modified)
            prompt_optimized = adjusted_plan.get("prompt_optimized", False)
            
            # Determine if memory was used
            memory_used = bool(memory_brief and memory_brief.strip() and memory_brief != "No relevant past context found.")
            
            # Use router_plan_for_refiner if available, otherwise fall back to adjusted_plan
            # #region agent log
            import json
            import time
            try:
                router_plan_in_locals = 'router_plan_for_refiner' in locals()
                adjusted_plan_in_locals = 'adjusted_plan' in locals()
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "router.py:handle", "message": "Checking router_plan availability", "data": {"router_plan_in_locals": router_plan_in_locals, "adjusted_plan_in_locals": adjusted_plan_in_locals, "has_router_plan_for_refiner": 'router_plan_for_refiner' in globals() if 'router_plan_for_refiner' in globals() else False}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                try:
                    log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "router.py:handle", "message": "Error checking router_plan", "data": {"error": str(e)}, "timestamp": int(time.time() * 1000)})
                except Exception as ex:
                    logging.warning(f"Debug logging failed: {ex}")
            # #endregion
            # Try to access router_plan_for_refiner directly (it should be in outer scope)
            try:
                router_plan_for_lfm = router_plan_for_refiner
            except NameError:
                # If not available, try adjusted_plan
                try:
                    router_plan_for_lfm = adjusted_plan
                except NameError:
                    # Last resort: create default
                    router_plan_for_lfm = {}
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "router.py:handle", "message": "router_plan_for_lfm determined", "data": {"has_router_plan": bool(router_plan_for_lfm), "entry_specialist": router_plan_for_lfm.get("entry_specialist") if router_plan_for_lfm else None}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            lfm_report = self.lfm.analyze(
                user_query=user_query,
                domain_cots=domain_cots,
                router_plan=router_plan_for_lfm,
                verification=verification,
                consistency=consistency_decision,
                vfl_meta=None,
                pointgame_rfs=rfs,
                # NEW: Comprehensive data sources
                specialist_outputs=specialist_outputs,
                refiner_metrics=refiner_metrics,
                auto_mode_decision=auto_mode_decision,
                prompt_optimized=prompt_optimized,
                memory_used=memory_used,
                processing_metrics=processing_metrics,
                wot_steps=wot_steps,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            # Specific exceptions for LFM analysis failures - never crash router
            self.logger.log_error("lfm_analyze", f"{type(e).__name__}: {str(e)}")
            lfm_report = None

        # Optional logger hook for PointGame (if implemented)
        try:
            self.logger.log_point_game(
                {
                    "rfs": rfs,
                    "stats_before": pg_stats_before,
                    "stats_after": pg_stats_after,
                }
            )
        except (AttributeError, TypeError):
            # Fine if logger doesn't have this method - expected for some logger implementations
            pass

        # 17) MemoryLLM — log this session into Cloud Diary
        # Use router_plan_for_refiner if available, otherwise fall back to adjusted_plan
        # #region agent log
        try:
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M2", "location": "router.py:handle", "message": "Before memory log_session", "data": {"has_memory_core": self._memory_core is not None, "has_lfm_report": lfm_report is not None}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        try:
            router_plan_for_memory = router_plan_for_refiner
        except NameError:
            try:
                router_plan_for_memory = adjusted_plan
            except NameError:
                router_plan_for_memory = {}
        try:
            self._memory_core.log_session(
                user_query=user_query,
                final_answer=refined_output,
                verification=verification,
                router_plan=router_plan_for_memory,
                active_domains=active_domains,
                run_id=self.logger.run_id,
                lfm_report=lfm_report,
                point_game_stats=pg_stats_after,
            )
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M2", "location": "router.py:handle", "message": "memory log_session completed", "data": {}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        except TypeError:
            # backwards compatibility if log_session has different signature
            try:
                self._memory_core.log_session(
                    user_query=user_query,
                    final_answer=refined_output,
                    verification=verification,
                    router_plan=router_plan_for_memory,
                    active_domains=active_domains,
                )
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                self.logger.log_error("memory_log_session", f"{type(e).__name__}: {str(e)}")
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            self.logger.log_error("memory_log_session", f"{type(e).__name__}: {str(e)}")

        # 18) Save full logs
        log_path = self.logger.save()
        
        # Calculate total processing time
        total_processing_time_ms = (time.time() - handle_start_time) * 1000

        # Use router_plan_for_refiner if available, otherwise fall back to adjusted_plan
        # CRITICAL: Ensure router_plan_for_return is always defined
        try:
            router_plan_for_return = router_plan_for_refiner
        except NameError:
            try:
                router_plan_for_return = adjusted_plan.copy() if adjusted_plan else {}
            except NameError:
                # Last resort: create default router_plan
                router_plan_for_return = {
                    "entry_specialist": entry_specialist if 'entry_specialist' in locals() else "general",
                    "active_domains": active_domains if 'active_domains' in locals() else ["general"],
                    "mode": "normal",
                }
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H6", "location": "router.py:handle", "message": "Final return router_plan", "data": {"has_router_plan": bool(router_plan_for_return), "entry_specialist": router_plan_for_return.get("entry_specialist") if router_plan_for_return else None}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
        # #endregion
        return {
            "status": status,
            "result": refined_output,
            "verification": verification,
            "log_path": log_path,
            "router_plan": router_plan_for_return,
            "consistency": consistency_decision,
            "memory_brief": memory_brief,
            "lfm_report": lfm_report,
            "point_game_rfs": rfs,
            "point_game_stats": pg_stats_after,
            "processing_time_ms": total_processing_time_ms,
            "wot_steps": wot_steps,
        }

    def _handle_research_mode(self, user_query: str, progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Research Mode: Correctness > Authority > Completeness > Speed

        Pipeline:
        1. Deterministic domain detection (keyword-based)
        2. Authority model assignment (locked, no override)
        3. Build specialists (1 worker each, 4-10 modules run in parallel based on query)
        4. Run WoT with minimum depth enforcement
        5. Meta-cognition audit (self-check)
        6. Generate structured PDF (with markdown fallback)
        7. Return result with explicit status
        """
        import time
        start_time = time.time()

        # 1. Start log run
        self.logger.new_run(user_query)

        # 2. Load memory brief (PAST-ONLY context)
        if progress_callback:
            progress_callback("Loading Memory", 10.0)
        # build_memory_brief is already imported at top (line 65)
        memory_info = build_memory_brief(self._memory_core, user_query)
        memory_brief = memory_info["brief_text"]
        self.logger.log_memory(memory_brief)

        # 3. Deterministic domain detection
        if progress_callback:
            progress_callback("Domain Detection", 20.0)
        detected_domains = self._deterministic_domain_detection(user_query)
        entry_domain = detected_domains[0] if detected_domains else "general"

        # 3.5. Internet Research Pipeline (per Blueprint Section 7)
        # MANDATORY in Research Mode - always run internet research
        internet_research_data = None
        if progress_callback:
            progress_callback("Internet Research", 25.0)
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "INTERNET_RESEARCH", "location": "router.py:_handle_research_mode", "message": "Internet research is MANDATORY in Research Mode", "data": {"user_query": user_query[:200]}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        internet_research_data = self._run_internet_research_pipeline(user_query, memory_brief)
        # Add internet research to detected domains if not already present
        if "internet" not in detected_domains and "research" not in detected_domains:
            detected_domains.append("research")

        # 4. Authority model assignment (LOCKED)
        authority_assignments = self._assign_authority_models(detected_domains)

        # 5. Select 4-10 modules dynamically based on query complexity
        selected_domains = self._select_parallel_modules(detected_domains, user_query)

        # 6. Build specialists (no ensemble - each runs once) with authority models
        specialists = self._build_research_specialists(selected_domains, authority_assignments)

        # 7. Log router decision
        self.logger.log_router_decision({
            "mode": "research",
            "detected_domains": detected_domains,
            "selected_domains": selected_domains,
            "entry_domain": entry_domain,
            "authority_assignments": authority_assignments,
            "parallel_modules": len(selected_domains),  # Dynamic 4-10 based on query
            "workers_per_module": 1,  # No ensemble in research mode
        })

        # 8. Run TrueWoT with minimum depth enforcement
        if progress_callback:
            progress_callback("Web-of-Thought Reasoning", 30.0)
        wot_start_time = time.time()
        max_steps = self.research_mode_config.get("wot_max_steps", 20)
        min_depth = self.research_mode_config.get("wot_min_depth", 3)

        # Include internet research data in full_query if available
        research_context = ""
        if internet_research_data and internet_research_data.get("summary"):
            research_context = f"\n\n--- INTERNET RESEARCH CONTEXT ---\n{internet_research_data['summary']}\n--- END INTERNET RESEARCH ---\n"
        
        full_query = f"{user_query}\n\n{memory_brief}{research_context}\n\n[RESEARCH MODE: Correctness required]"

        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "Before WoT try block", "data": {"entry_domain": entry_domain, "specialists_count": len(specialists), "max_steps": max_steps}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion

        try:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "Before TrueWoT instantiation", "data": {"domain_names_count": len(list(specialists.keys()))}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # TrueWoT is already imported at top (line 57)
            wot = TrueWoT(
                domain_names=list(specialists.keys()),
                memory_llm=self._memory_core,
                # min_depth parameter doesn't exist in TrueWoT constructor
                # Depth validation happens after wot.run() at line 1143
            )
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "After TrueWoT instantiation, before wot.run", "data": {"entry_domain": entry_domain, "max_steps": max_steps, "specialists_keys": list(specialists.keys()), "full_query_length": len(full_query)}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "About to call wot.run()", "data": {"wot_type": type(wot).__name__, "has_run_method": hasattr(wot, "run")}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            try:
                domain_cots = wot.run(
                entry_domain=entry_domain,
                query=full_query,
                specialists=specialists,
                max_steps=max_steps,
            )
            except Exception as wot_exc:
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "wot.run() raised exception", "data": {"error_type": type(wot_exc).__name__, "error_msg": str(wot_exc)[:200]}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                raise
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "After wot.run call", "data": {"domain_cots_count": len(domain_cots) if domain_cots else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            wot_end_time = time.time()
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "After wot_end_time calculation", "data": {"wot_processing_time_ms": (wot_end_time - wot_start_time) * 1000}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            wot_steps = getattr(wot, 'total_steps', 0)

            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "After wot_steps extraction", "data": {"wot_steps": wot_steps, "min_depth": min_depth}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

            # Validate minimum depth - ENFORCE (per Blueprint: "minimum reasoning depth enforced")
            if wot_steps < min_depth:
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_WOT", "location": "router.py:_handle_research_mode", "message": "WoT depth insufficient, forcing continuation", "data": {"wot_steps": wot_steps, "min_depth": min_depth, "will_continue": True}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                
                # Force continuation if depth insufficient (per Blueprint: "no 'good enough' termination")
                self.logger.log_error("research_wot_depth",
                    f"WoT depth {wot_steps} < minimum {min_depth}. Forcing continuation to meet minimum depth requirement.")
                
                # Continue WoT with remaining steps to reach minimum depth (per Blueprint: "minimum reasoning depth enforced")
                remaining_steps = min_depth - wot_steps
                current_domain_for_continuation = entry_domain
                
                # Build WoT packet format (same as WoT uses internally)
                full_query_with_memory = f"{user_query}\n\n{memory_brief}\n\n[RESEARCH MODE: Correctness required]"
                
                for additional_step in range(remaining_steps):
                    # Get next domain (cycle through selected domains to ensure all are used)
                    if len(selected_domains) > 1:
                        try:
                            current_idx = selected_domains.index(current_domain_for_continuation)
                            next_idx = (current_idx + 1) % len(selected_domains)
                            current_domain_for_continuation = selected_domains[next_idx]
                        except ValueError:
                            # If current_domain not in selected_domains, use first available
                            current_domain_for_continuation = selected_domains[0]
                    else:
                        # Only one domain, but we need more steps - use helper domains
                        if current_domain_for_continuation == "general":
                            current_domain_for_continuation = "facts" if "facts" in selected_domains else "memory"
                        elif current_domain_for_continuation == "facts":
                            current_domain_for_continuation = "general" if "general" in selected_domains else "memory"
                        else:
                            current_domain_for_continuation = "general"
                    
                    # Ensure domain is in specialists
                    if current_domain_for_continuation not in specialists:
                        # Fallback to first available
                        current_domain_for_continuation = list(specialists.keys())[0] if specialists else "general"
                    
                    # Build packet using WoT's full context format (includes all domain CoTs)
                    if hasattr(wot, '_build_full_context_packet'):
                        packet = wot._build_full_context_packet(full_query_with_memory)
                    elif hasattr(wot, '_build_wot_packet'):
                        packet = wot._build_wot_packet(full_query_with_memory)
                    else:
                        # Fallback: build basic packet with current domain CoTs
                        cots_text = "\n\n".join([f"{d.upper()}:\n{cots}" for d, cots in domain_cots.items() if cots])
                        packet = f"""
USER QUERY:
{full_query_with_memory}

PREVIOUS DOMAIN REASONING:
{cots_text}

[RESEARCH MODE: Additional step to meet minimum depth requirement]
"""
                    
                    # Run additional step
                    additional_output = specialists[current_domain_for_continuation].run(packet)
                    
                    # Ensure output is not empty
                    if not additional_output or not additional_output.strip():
                        additional_output = f"[{current_domain_for_continuation.upper()} specialist: Additional reasoning step for minimum depth]\nWOT_REQUEST: NONE"
                    
                    domain_cots[current_domain_for_continuation] = additional_output
                    wot_steps += 1
                    
                    # #region agent log
                    try:
                        with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                            import json
                            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_WOT", "location": "router.py:_handle_research_mode", "message": "Forced additional WoT step", "data": {"step": additional_step + 1, "current_domain": current_domain_for_continuation, "total_steps": wot_steps, "remaining": remaining_steps - additional_step - 1}, "timestamp": int(time.time() * 1000)}) + "\n")
                    except Exception:
                        pass
                    # #endregion
                
                # Update wot.total_steps
                if hasattr(wot, 'total_steps'):
                    wot.total_steps = wot_steps
                
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_WOT", "location": "router.py:_handle_research_mode", "message": "WoT depth enforcement complete", "data": {"final_wot_steps": wot_steps, "min_depth": min_depth, "meets_requirement": wot_steps >= min_depth}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "After depth validation, before except block end", "data": {"domain_cots_defined": "domain_cots" in locals(), "domain_cots_count": len(domain_cots) if "domain_cots" in locals() and domain_cots else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

        except Exception as e:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "K", "location": "router.py:_handle_research_mode", "message": "WoT try block exception caught", "data": {"error_type": type(e).__name__, "error_msg": str(e)[:200]}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            # Explicit failure reporting (per Blueprint)
            return {
                "status": "error_explicit",
                "result": f"[RESEARCH MODE ERROR] {str(e)}",
                "error": str(e),
                "uncertainty": "High - Research pipeline failed",
                "retries_exhausted": False,
                "authority_assignments": authority_assignments,
                "mode": "research",
            }

        # 9. Meta-cognition audit (self-check)
        if progress_callback:
            progress_callback("Meta-cognition Audit", 70.0)
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "L", "location": "router.py:_handle_research_mode", "message": "Before metacognition audit", "data": {"domain_cots_count": len(domain_cots) if domain_cots else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        metacognition_audit = self._run_metacognition_audit(
            user_query=user_query,
            domain_cots=domain_cots,
            entry_domain=entry_domain,
        )
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "L", "location": "router.py:_handle_research_mode", "message": "After metacognition audit", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion

        # 10. Refiner (with research mode hints)
        if progress_callback:
            progress_callback("Refining Response", 80.0)
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "L", "location": "router.py:_handle_research_mode", "message": "Before refiner.refine call", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        refiner_packet = self._build_refiner_packet(
            user_query=user_query,
            domain_cots=domain_cots,
            entry_specialist=entry_domain,
            router_plan={"mode": "research", "authority": authority_assignments},
            pg_stats_before={},
        )
        refined_output = self.refiner.refine(refiner_packet)
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "L", "location": "router.py:_handle_research_mode", "message": "After refiner.refine call", "data": {"refined_output_length": len(refined_output) if refined_output else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        # CRITICAL: Block empty output from refiner
        if not refined_output or not refined_output.strip() or refined_output.strip() in ["", "None", "N/A", "[VERIFIER_READY]"]:
            logging.error("Router (Research Mode): Refiner returned empty output - using emergency fallback")
            # Try to extract content from domain outputs
            fallback_parts = []
            for domain, cot in domain_cots.items():
                if cot and cot.strip() and "[produced no output]" not in cot.lower():
                    sentences = re.split(r'[.!?]\s+', cot)
                    for sent in sentences:
                        if len(sent.strip()) > 20:
                            fallback_parts.append(f"**{domain.title()}**: {sent.strip()}")
                            break
                    if len(fallback_parts) >= 2:
                        break
            
            if fallback_parts:
                refined_output = "\n\n".join(fallback_parts) + "\n\n[VERIFIER_READY]"
            else:
                refined_output = f"I apologize, but I encountered an issue while processing your query: '{user_query}'. The system was unable to generate a proper response. Please try rephrasing your question.\n\n[VERIFIER_READY]"
        
        self.logger.log_refiner(refined_output)

        # 11. Verifier (strict research mode verification)
        if progress_callback:
            progress_callback("Verifying Quality", 90.0)
        verifier_packet = self._build_verifier_packet(
            user_query=user_query,
            merged_reasoning=refined_output,
            entry_specialist=entry_domain,
            router_reason="Research mode: authority-driven analysis",
        )
        verification = self.verifier.run(verifier_packet)
        
        if progress_callback:
            progress_callback("Completing", 100.0)
        self.logger.log_verifier(verification)

        status = verification.get("status", "approved")

        # 12. Generate structured PDF (with markdown fallback)
        output_path = None
        output_format = "none"

        if self.research_mode_config.get("pdf_output", True):
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_PDF", "location": "router.py:_handle_research_mode", "message": "Attempting PDF generation", "data": {"pdf_output_enabled": True}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            try:
                from anm.output.research_pdf import ResearchPDFGenerator

                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_PDF", "location": "router.py:_handle_research_mode", "message": "PDF generator imported successfully", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion

                pdf_generator = ResearchPDFGenerator()

                # Extract sources before refinement strips URLs (Blueprint compliance)
                sources = self._extract_sources_from_outputs(domain_cots)

                output_path = pdf_generator.generate(
                    user_query=user_query,
                    domain_cots=domain_cots,
                    refined_output=refined_output,
                    verification=verification,
                    metacognition=metacognition_audit,
                    authority_assignments=authority_assignments,
                    wot_steps=wot_steps,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    sources=sources,  # Blueprint compliance: Sources section
                )
                output_format = "pdf"
                
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_PDF", "location": "router.py:_handle_research_mode", "message": "PDF generated successfully", "data": {"output_path": output_path, "output_format": output_format}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
            except ImportError as e:
                # reportlab not installed
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_PDF", "location": "router.py:_handle_research_mode", "message": "PDF generation failed: reportlab not installed", "data": {"error": str(e), "error_type": "ImportError"}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                
                # Fallback to markdown if PDF generation fails
                if self.research_mode_config.get("markdown_fallback", True):
                    self.logger.log_error("pdf_generation_failed",
                        f"PDF generation failed: reportlab not installed. Install with: pip install reportlab. Falling back to markdown.")
            except Exception as e:
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_PDF", "location": "router.py:_handle_research_mode", "message": "PDF generation failed with exception", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                
                # Fallback to markdown if PDF generation fails
                if self.research_mode_config.get("markdown_fallback", True):
                    self.logger.log_error("pdf_generation_failed",
                        f"PDF generation failed: {e}. Falling back to markdown.")

                    try:
                        from anm.output.research_markdown import ResearchMarkdownGenerator
                        md_generator = ResearchMarkdownGenerator()
                        output_path = md_generator.generate(
                            user_query=user_query,
                            domain_cots=domain_cots,
                            refined_output=refined_output,
                            verification=verification,
                            metacognition=metacognition_audit,
                            authority_assignments=authority_assignments,
                            wot_steps=wot_steps,
                            processing_time_ms=(time.time() - start_time) * 1000,
                        )
                        output_format = "markdown"
                    except Exception as md_e:
                        self.logger.log_error("markdown_generation_failed",
                            f"Markdown generation also failed: {md_e}.")
                        output_path = None
                        output_format = "none"
                else:
                    self.logger.log_error("pdf_generation_failed",
                        f"PDF generation failed: {e}. No fallback enabled.")
                    output_path = None
                    output_format = "none"

        # 13. Index research output in knowledge base (RAG)
        if self.research_kb and self.research_kb.is_available() and output_path:
            try:
                from datetime import datetime, timezone

                # Extract active domains for metadata
                active_domains = list(domain_cots.keys()) if domain_cots else []

                self.research_kb.add_research_output(
                    query=user_query,
                    research_content=refined_output,
                    metadata={
                        "domains": active_domains,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "format": output_format,
                        "verification_status": status,
                    },
                    output_path=output_path,
                )
                self._logger.info(f"Indexed research output in KB: {output_path}")
            except Exception as e:
                self._logger.warning(f"Failed to index research output: {e}")

        # 14. Save logs
        log_path = self.logger.save()

        # 15. Return comprehensive result
        return {
            "status": status,
            "result": refined_output,
            "verification": verification,
            "metacognition": metacognition_audit,
            "authority_assignments": authority_assignments,
            "output_path": output_path,
            "output_format": output_format,  # "pdf", "markdown", or "none"
            "log_path": log_path,
            "mode": "research",
            "wot_steps": wot_steps,
            "processing_time_ms": (time.time() - start_time) * 1000,
            "selected_domains": selected_domains,  # For UI to display all modules used
            "domain_cots": domain_cots,  # For UI to show which domains produced output
        }

    def _handle_quick_mode(self, user_query: str) -> Dict[str, Any]:
        """
        Quick Mode: Simplified path - Router -> Quick Model -> Refiner -> Verifier -> Output
        
        Skips:
        - WoT (no multi-domain reasoning)
        - Memory (no context loading)
        - Learning (no post-processing)
        - PointGame (no scoring)
        
        Includes:
        - Refiner (to ensure verifier-ready format)
        
        Path: Route to general specialist -> Run quick model -> Refine -> Verify -> Return
        """
        import time
        quick_mode_start_time = time.time()
        
        # 1) Start log run
        self.logger.new_run(user_query)
        
        # 2) Simple domain guess (just use general for quick mode)
        entry_specialist = "general"
        
        # 3) Log router decision
        self.logger.log_router_decision({
            "coarse_entry": "general",
            "planner_plan": {"entry_specialist": "general", "active_domains": ["general"]},
            "lfm_adjusted_plan": {"entry_specialist": "general", "active_domains": ["general"]},
            "entry_specialist": "general",
            "max_steps": 1,
            "active_domains": ["general"],
        })
        
        # 4) Build simple prompt (no memory, no context)
        simple_prompt = f"USER QUERY: {user_query}\n\nProvide a direct, concise answer."
        
        # 5) Run quick model directly (using general specialist with quick mode)
        # Note: Inference engine is already configured by ANM.query() based on quick_mode flag
        # We just need to ensure it's available - no need to reconfigure
        from anm.system.inference import get_inference_engine
        engine = get_inference_engine()  # Get singleton - already configured by ANM
        
        # Use general specialist to build proper prompt
        wot_packet = f"""--- WoT PACKET (GENERAL VIEW) ---

{simple_prompt}

Provide your general reasoning and end with WOT_REQUEST: NONE"""
        
        # Run through general specialist (which will use quick mode model)
        raw_output = self.general.run(wot_packet)
        
        # Extract just the answer (remove meta blocks and WOT_REQUEST)
        # Improved cleaning: handle partial lines and meta blocks better
        lines = raw_output.split("\n")
        answer_lines = []
        in_meta_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check for meta block markers
            if line_stripped.startswith("[DOMAIN_HEALTH]") or line_stripped.startswith("[GLOBAL_RULES]") or line_stripped.startswith("[ROUTER_HINTS]") or line_stripped.startswith("[EFFICIENCY_METRICS]"):
                in_meta_block = True
                break
            
            # Check for WOT_REQUEST (but allow if it's part of a sentence)
            # Only break if WOT_REQUEST: is a standalone marker, not when embedded in text
            if "WOT_REQUEST:" in line_stripped:
                # Check if it's a standalone marker
                # Standalone means: starts with WOT_REQUEST: and has 3 or fewer words total
                words = line_stripped.split()
                if line_stripped.startswith("WOT_REQUEST:") and len(words) <= 3:
                    # It's a standalone marker like "WOT_REQUEST: NONE" - break here
                    break
                # If WOT_REQUEST: appears later in the line (not at start), it's part of text - continue processing
                # Don't break, just continue to the next iteration
            
            # Skip empty lines if we're in a meta section
            if in_meta_block:
                continue
            
            # Include the line if it's not a meta marker
            if line_stripped and not line_stripped.startswith("["):
                answer_lines.append(line)
            elif line_stripped and not any(marker in line_stripped for marker in ["[DOMAIN_HEALTH]", "[GLOBAL_RULES]", "[ROUTER_HINTS]", "[EFFICIENCY_METRICS]", "WOT_REQUEST:"]):
                answer_lines.append(line)
        
        cleaned_output = "\n".join(answer_lines).strip()
        
        # Additional cleanup: remove any remaining meta markers
        cleaned_output = re.sub(r'\[DOMAIN_HEALTH\].*?\[ROUTER_HINTS\].*?WOT_REQUEST:.*', '', cleaned_output, flags=re.DOTALL)
        cleaned_output = cleaned_output.strip()
        
        # Fallback if cleaning resulted in empty output
        if not cleaned_output or len(cleaned_output) < 5:
            # Try to extract any meaningful content from raw output
            # Remove meta blocks more aggressively
            fallback = re.sub(r'\[.*?\].*?WOT_REQUEST:.*', '', raw_output, flags=re.DOTALL)
            fallback = re.sub(r'WOT_REQUEST:.*', '', fallback, flags=re.DOTALL)
            cleaned_output = fallback.strip()
        
        if not cleaned_output or len(cleaned_output) < 5:
            cleaned_output = "[No response generated]"
        
        # 6) NEW: Pass through Refiner to ensure verifier-ready format
        # Build refiner packet (simplified for quick mode)
        refiner_packet = {
            "user_query": user_query,
            "general_rounds": cleaned_output,  # Single domain output for quick mode
            "entry_specialist": entry_specialist,
            "mode": "quick",
        }
        
        # Refine the answer (this will add [VERIFIER_READY] marker)
        refined_output = self.refiner.refine(refiner_packet)
        
        # CRITICAL: Block empty output from refiner
        if not refined_output or not refined_output.strip() or refined_output.strip() in ["", "None", "N/A", "[VERIFIER_READY]"]:
            logging.error("Router (Quick Mode): Refiner returned empty output - using emergency fallback")
            # For quick mode, provide a simple fallback
            refined_output = f"I apologize, but I encountered an issue while processing your query: '{user_query}'. The system was unable to generate a proper response. Please try rephrasing your question.\n\n[VERIFIER_READY]"
        
        self.logger.log_refiner(refined_output)
        
        # 7) Verifier (uses refined output)
        verifier_packet = self._build_verifier_packet(
            user_query=user_query,
            merged_reasoning=refined_output,
            entry_specialist=entry_specialist,
            router_reason="Quick mode - refined response",
        )
        self.logger.log_verifier_packet(verifier_packet)
        
        verification = self.verifier.run(verifier_packet)
        self.logger.log_verifier(verification)
        
        status = verification.get("status", "approved")
        
        # 8) Save logs
        log_path = self.logger.save()
        
        # Calculate processing time for quick mode
        processing_time_ms = (time.time() - quick_mode_start_time) * 1000
        
        # NEW: Learn from quick mode run via LFM
        try:
            # Extract specialist metrics from general output
            general_output = raw_output  # Use raw output before cleaning
            specialist_outputs = {}
            if general_output:
                specialist_outputs["general"] = self._extract_specialist_metrics(
                    {"general": general_output},
                    {"general": self.general}
                ).get("general", {})
            
            # Extract refiner metrics
            refiner_metrics = self._extract_refiner_metrics(refined_output)
            
            # Build processing metrics
            processing_metrics = {
                "total_tokens": 0,  # Can be enhanced if token tracking is available
                "total_time_ms": processing_time_ms,
                "wot_time_ms": 0,  # No WoT in quick mode
                "wot_steps": 0,
            }
            
            # Quick mode specific data
            quick_mode_plan = {
                "entry_specialist": "general",
                "active_domains": ["general"],
                "mode": "quick",
            }
            
            # Learn from quick mode run
            self.lfm.analyze(
                user_query=user_query,
                domain_cots={"general": cleaned_output},  # Use cleaned output
                router_plan=quick_mode_plan,
                verification=verification,
                consistency={},
                vfl_meta=None,
                pointgame_rfs=None,
                specialist_outputs=specialist_outputs,
                refiner_metrics=refiner_metrics,
                auto_mode_decision=True,  # Quick mode always uses quick model
                prompt_optimized=False,  # Quick mode doesn't optimize prompts
                memory_used=False,  # Quick mode doesn't use memory
                processing_metrics=processing_metrics,
                wot_steps=[],  # No WoT steps in quick mode
            )
        except Exception as e:
            # Never crash on LFM learning
            self.logger.log_error("lfm_quick_mode", f"{type(e).__name__}: {str(e)}")
        
        return {
            "status": status,
            "result": refined_output,  # Return refined output (with [VERIFIER_READY])
            "verification": verification,
            "log_path": log_path,
            "router_plan": {
                "entry_specialist": "general",
                "active_domains": ["general"],
                "mode": "quick",
            },
            "mode": "quick",
            "processing_time_ms": processing_time_ms,
            "wot_steps": 0,  # Quick mode doesn't use WoT
        }

    # ========================================================
    #  NOVELTY DETECTION, VOTING, AND EXPANSION
    #  (Now handled by separate handler modules)
    # ========================================================
    # These methods have been extracted to:
    # - anm/router/novelty_handler.py (NoveltyHandler)
    # - anm/router/voting_handler.py (VotingHandler)
    # - anm/router/expansion_handler.py (ExpansionHandler)
    # ========================================================

    # ========================================================
    #  HELPER METHODS FOR COMPREHENSIVE LFM DATA EXTRACTION
    # ========================================================
    
    def _extract_specialist_metrics(
        self,
        domain_cots: Dict[str, str],
        specialists: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Extract metrics from specialist outputs for LFM learning."""
        import re
        specialist_outputs = {}
        
        for domain, output in domain_cots.items():
            if not output:
                continue
            
            metrics = {}
            
            # Extract confidence
            conf_match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', output, re.IGNORECASE)
            if conf_match:
                metrics["confidence"] = conf_match.group(1).upper()
            
            # Extract confidence score
            conf_score_match = re.search(r'confidence_score:\s*([0-9.]+)', output, re.IGNORECASE)
            if conf_score_match:
                metrics["confidence_score"] = float(conf_score_match.group(1))
            
            # Extract efficiency
            eff_match = re.search(r'EFFICIENCY:\s*(EFFICIENT|INEFFICIENT)', output, re.IGNORECASE)
            if eff_match:
                metrics["efficiency"] = eff_match.group(1).upper()
            
            # Extract efficiency score
            eff_score_match = re.search(r'efficiency_score:\s*([0-9.]+)', output, re.IGNORECASE)
            if eff_score_match:
                metrics["efficiency_score"] = float(eff_score_match.group(1))
            
            # Extract token metrics from [EFFICIENCY_METRICS] block
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
            
            # Try to get metrics from specialist object if available
            if domain in specialists:
                specialist = specialists[domain]
                # Check if it's a ParallelSpecialistAdapter and get underlying specialist
                if hasattr(specialist, 'workers') and specialist.workers:
                    underlying = specialist.workers[0] if specialist.workers else None
                    if underlying and hasattr(underlying, '_last_efficiency_metrics'):
                        eff_metrics = underlying._last_efficiency_metrics
                        if eff_metrics:
                            metrics.update({
                                "total_tokens": eff_metrics.get("total_tokens", metrics.get("total_tokens", 0)),
                                "processing_time_ms": eff_metrics.get("processing_time_ms", metrics.get("processing_time_ms", 0.0)),
                                "tokens_per_ms": eff_metrics.get("tokens_per_ms", metrics.get("tokens_per_ms", 0.0)),
                                "efficiency_score": eff_metrics.get("efficiency_score", metrics.get("efficiency_score", 0.5)),
                            })
            
            if metrics:
                specialist_outputs[domain] = metrics
        
        return specialist_outputs
    
    def _extract_refiner_metrics(self, refined_output: str) -> Dict[str, Any]:
        """Extract metrics from refiner output for LFM learning."""
        metrics = {}
        
        # Check if output has [VERIFIER_READY] marker (quality indicator)
        metrics["verifier_ready"] = "[VERIFIER_READY]" in refined_output
        
        # Basic quality metrics
        metrics["output_length"] = len(refined_output)
        metrics["has_code"] = "```" in refined_output
        metrics["has_math"] = "$" in refined_output or "\\[" in refined_output
        
        return metrics
    
    def _extract_wot_steps(
        self,
        wot: Any,
        domain_cots: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Extract WoT routing steps for LFM learning."""
        wot_steps = []
        
        # Try to get step history from TrueWoT if available
        if hasattr(wot, 'step_history'):
            for step in wot.step_history:
                wot_steps.append({
                    "domain": step.get("domain", "unknown"),
                    "specialist": step.get("specialist", step.get("domain", "unknown")),
                    "action": step.get("action", "process"),
                })
        else:
            # Fallback: create steps from domain_cots
            for domain, output in domain_cots.items():
                if output and output.strip():
                    wot_steps.append({
                        "domain": domain,
                        "specialist": domain,
                        "action": "process",
                    })
        
        return wot_steps

    # ========================================================
    #  AI-POWERED DOMAIN CLASSIFIER (USING R1 MODEL)
    # ========================================================

    def _ai_domain_classifier(self, query: str) -> str:
        """
        AI-powered domain classifier using DeepSeek R1 model.

        Instead of keyword matching, this uses the R1 model to intelligently
        analyze the query and determine which specialist domain should handle it.

        This is MUCH smarter than keyword matching and can handle:
        - Edge cases that keywords miss
        - Ambiguous queries that need context understanding
        - Novel query patterns not covered by keywords

        Returns:
            str: Domain name (e.g., "math", "physics", "code", "biology", etc.)
        """
        if not query or not isinstance(query, str) or not query.strip():
            return "general"

        # Build classification prompt for R1 (optimized)
        classification_prompt = f"""Classify query to specialist: math, physics, chemistry, biology, code, general, research, facts.

Query: "{query}"

Examples: "25 + 8"→math, "force calculation"→physics, "DNA"→biology, "Python function"→code, "current president"→research, "World War 2"→facts, "weather"→general.

Classification (ONE WORD):"""

        try:
            # Use the inference engine to get R1's classification
            from anm.system.inference import get_inference_engine

            engine = get_inference_engine()
            response = engine.generate(
                classification_prompt,
                max_tokens=20,  # We only need 1 word
            )

            # Extract the domain from R1's response
            # R1 might give reasoning, so extract just the domain word
            response_lower = response.lower().strip()

            # Look for valid domain names in the response
            valid_domains = {
                "math", "physics", "chemistry", "biology", "code",
                "general", "research", "facts", "sound", "simulation", "image"
            }

            # Check if response is directly a valid domain
            if response_lower in valid_domains:
                return response_lower

            # Extract domain from response (look for domain words in order of specificity)
            domain_priority = [
                "math", "physics", "chemistry", "biology", "code",
                "sound", "simulation", "image", "research", "facts", "general"
            ]

            for domain in domain_priority:
                if domain in response_lower:
                    return domain

            # Fallback: if R1 didn't return a valid domain, log and use keyword fallback
            self._logger.warning(
                f"AI classifier returned invalid response: '{response[:100]}'. "
                f"Falling back to keyword matching."
            )
            return self._coarse_domain_guess(query)

        except Exception as e:
            # If AI classification fails, fall back to keyword matching
            self._logger.error(
                f"AI domain classification failed: {type(e).__name__}: {e}. "
                f"Falling back to keyword matching."
            )
            return self._coarse_domain_guess(query)

    # ========================================================
    #  COARSE DOMAIN GUESSER (ROUTER'S HARD RULES - FALLBACK)
    # ========================================================

    def _coarse_domain_guess(self, query: str) -> str:
        """
        Very simple heuristic classifier so Router is self-aware
        of which domain should LEAD, even if PlannerLLM messes up.

        Uses word boundary matching to avoid false positives
        (e.g., "tan" in "standard" or "sin" in "using").
        """
        if not query:
            return "general"

        q = query.lower()

        # Helper function for word boundary matching
        def contains_keyword(text: str, keyword: str) -> bool:
            """Check if keyword exists as whole word or phrase in text."""
            import re
            # For multi-word keywords, check if the phrase exists
            if " " in keyword:
                return keyword in text
            # For single-word keywords, use word boundaries
            # \b matches word boundaries (start/end of word)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            return bool(re.search(pattern, text))

        def any_keyword_match(text: str, keywords: list) -> bool:
            """Check if any keyword matches in text."""
            return any(contains_keyword(text, k) for k in keywords)

        # Physics - COMPREHENSIVE (basic + advanced)
        physics_keywords = [
            # Basic physics
            "force", "mass", "acceleration", "velocity", "speed",
            "energy", "kinetic", "potential", "momentum", "friction",
            "newton", "newton's law", "inertia", "motion",
            "gravity", "gravitational", "weight", "pressure",
            "temperature", "heat", "thermodynamics", "celsius", "fahrenheit",
            "light", "wavelength", "frequency", "photon", "wave",
            "electricity", "current", "voltage", "resistance", "ohm",
            "magnet", "magnetic", "electromagnetic",
            # Advanced physics
            "black hole", "relativistic", "kerr", "newman",
            "orbit", "quasar", "quantum field", "lagrangian", "hamiltonian",
            "schwarzschild", "kerr-newman", "relativity", "quantum",
            "planck", "heisenberg", "schrodinger", "uncertainty principle",
        ]
        if any_keyword_match(q, physics_keywords):
            return "physics"

        # Math - COMPREHENSIVE (basic arithmetic + advanced math)
        math_keywords = [
            # Basic arithmetic
            "add", "sum", "subtract", "multiply", "multiplied", "divide", "divided", "times",
            "plus", "minus", "product", "quotient", "calculate",
            "square root", "sqrt", "power", "exponent", "factorial",
            "gcd", "lcm", "prime", "factor",
            # Intermediate math
            "equation", "solve for", "solve", "x =", "y =",
            "mean", "average", "median", "mode", "probability",
            "fraction", "decimal", "percent", "ratio", "proportion",
            # Advanced math
            "integral", "derive", "derivative", "limit", "theorem",
            "matrix", "vector", "proof", "differential",
            "series", "statistic", "logarithm", "trigonometry",
            "sin", "cos", "tan", "arcsin", "arccos", "arctan",
            # Math symbols/patterns
            "x^", "x²", "x³", "√", "π", "∫", "∑",
        ]
        if any_keyword_match(q, math_keywords):
            return "math"

        # Code - COMPREHENSIVE
        code_keywords = [
            # Programming languages
            "python", "javascript", "java", "c++", "golang", "rust",
            "typescript", "ruby", "php", "swift", "kotlin",
            # Code actions
            "write a function", "write a program", "write code",
            "code snippet", "script", "program",
            # Code concepts
            "function", "class ", "method", "loop", "for loop", "while loop",
            "if statement", "variable", "array", "list", "dictionary",
            "tuple", "set", "exception", "try", "except", "catch",
            "def ", "return", "import", "include",
            # Debugging
            "bug", "error", "stack trace", "traceback", "debug",
            "runtime error", "segmentation fault", "syntax error",
            "compile", "compiler", "interpreter",
        ]
        if any_keyword_match(q, code_keywords):
            return "code"

        # Chemistry - COMPREHENSIVE
        chemistry_keywords = [
            # Basic chemistry
            "atom", "atomic", "element", "compound", "mixture",
            "molecule", "molecular", "ion", "proton", "neutron", "electron",
            "periodic table", "valence", "chemical formula",
            "h2o", "co2", "o2", "h2", "nacl",
            # Chemical reactions
            "reaction", "chemical", "balance", "equation",
            "acid", "base", "ph", "neutral", "alkali",
            "oxidation", "reduction", "redox", "catalyst",
            # Advanced chemistry
            "organic", "inorganic", "biochemistry",
            "bond", "covalent", "ionic", "metallic", "hydrogen bond",
            "stoichiometry", "mole", "avogadro", "molarity",
        ]
        if any_keyword_match(q, chemistry_keywords):
            return "chemistry"

        # Biology - COMPREHENSIVE
        biology_keywords = [
            # Basic biology
            "cell", "organism", "animal", "plant", "bacteria", "virus",
            "living", "life", "biological",
            "dna", "rna", "gene", "chromosome", "chromosomes", "genetic",
            "protein", "amino acid", "nucleic acid",
            # Body systems
            "heart", "blood", "oxygen", "hemoglobin", "respiration",
            "digestion", "nervous system", "brain", "neuron",
            "immune", "antibody", "vaccine", "disease",
            # Cellular/molecular
            "mitochondria", "nucleus", "ribosome", "membrane",
            "photosynthesis", "cellular respiration", "atp", "glucose",
            "metabolism", "enzyme", "catalyst",
            # Evolution/ecology
            "evolution", "natural selection", "adaptation", "species",
            "ecosystem", "food chain", "biodiversity",
        ]
        if any_keyword_match(q, biology_keywords):
            return "biology"

        # Sound / audio domain
        sound_keywords = [
            "sound design", "audio design", "soundtrack", "binaural",
            "music", "song", "beat", "mixing", "mastering",
            "audio effect", "reverb", "echo", "sound effect",
            "foley", "audio pipeline", "audio clip", "sound clip",
        ]
        if any_keyword_match(q, sound_keywords):
            return "sound"

        # Simulation / image hints (for completeness; mainly Planner + DomainMasker)
        sim_keywords = [
            "simulate", "simulation", "trajectory", "orbit",
            "fluid", "particle", "dynamics",
        ]
        if any_keyword_match(q, sim_keywords):
            return "physics"  # lead domain; simulation domain will also activate

        image_keywords = [
            "image", "picture", "visual", "frame", "diagram", "camera",
        ]
        if any_keyword_match(q, image_keywords):
            return "general"  # image specialist supports; general leads

        # Facts / research style - ONLY trigger if no domain-specific match
        # These are generic question patterns that could apply to any domain
        # So we ONLY use them if we haven't found a more specific domain match
        # NOTE: By placing this AFTER all domain checks, we ensure domain-specific
        # queries like "What is DNA?" go to biology, not facts
        research_keywords = [
            "latest", "current", "recent", "news", "today", "update",
        ]
        facts_keywords = [
            "who is", "when was", "where is",
            "date of", "fact", "true or false",
        ]
        if any_keyword_match(q, research_keywords):
            return "research"
        if any_keyword_match(q, facts_keywords):
            return "facts"

        # Fallback
        return "general"

    # ========================================================
    #  BUILD REFINER / VERIFIER PACKETS
    # ========================================================

    def _build_refiner_packet(
        self,
        user_query: str,
        domain_cots: Dict[str, str],
        entry_specialist: str,
        router_plan: Dict[str, Any],
        pg_stats_before: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build enriched packet for Refiner V0-OpenSource MAX.

        Includes:
          - raw domain CoTs
          - router metadata
          - basic task_meta derived from plan + query
          - anm_stats: derived from PointGame stats (PAST-ONLY snapshot)
        """
        # Defensive: ensure router_plan is always a valid dict
        if not router_plan or not isinstance(router_plan, dict):
            router_plan = {
                "entry_specialist": entry_specialist or "general",
                "active_domains": list(domain_cots.keys()) or ["general"],
                "risk_score": 0.3,
            }

        def get(domain: str) -> str:
            return domain_cots.get(domain, "")

        # --- derive task_meta for Refiner adaptive style ---
        risk_score = float(router_plan.get("risk_score", 0.3) or 0.3)
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        q_low = user_query.lower()

        # crude task_type classification
        if entry_specialist in {"math", "physics"} and any(
            kw in q_low for kw in ["derive", "derivation", "integral", "differential", "equation"]
        ):
            task_type = "derivation"
        elif entry_specialist in {"code"}:
            task_type = "design"
        elif entry_specialist in {"sound"} or any(
            kw in q_low for kw in ["sound design", "soundtrack", "music", "audio"]
        ):
            task_type = "sound_design"
        elif any(kw in q_low for kw in ["story", "novel", "character", "worldbuilding", "fanfic"]):
            task_type = "creative_worldbuilding"
        else:
            task_type = "general"

        # detail level heuristic
        if len(user_query) > 800 or "multi-step" in q_low:
            detail_level = "high"
        elif len(user_query) < 200:
            detail_level = "low"
        else:
            detail_level = "medium"

        # audience heuristic
        if entry_specialist in {"math", "physics", "code"} and risk_level != "low":
            audience = "intermediate"
        else:
            audience = "beginner"

        task_meta = {
            "task_type": task_type,
            "risk_level": risk_level,
            "detail_level": detail_level,
            "audience": audience,
        }

        # anm_stats based on PointGame PAST-ONLY snapshot
        pg_recent = pg_stats_before.get("recent", []) or []
        recent_status = [snap.get("status", "unknown") for snap in pg_recent]

        anm_stats = {
            "points": pg_stats_before.get("score", 0),
            "recent_verifier_status": recent_status,
        }

        return {
            "user_query": user_query,
            "entry_specialist": entry_specialist,
            "router_reason": router_plan.get("reason", ""),
            "active_specialists": list(domain_cots.keys()),
            # domain rounds
            "general_rounds": get("general"),
            "math_rounds": get("math"),
            "physics_rounds": get("physics"),
            "code_rounds": get("code"),
            "chemistry_rounds": get("chemistry"),
            "biology_rounds": get("biology"),
            "memory_rounds": get("memory"),
            "research_rounds": get("research"),
            "facts_rounds": get("facts"),
            # multi-modal rounds
            "simulation_rounds": get("simulation"),
            "image_rounds": get("image"),
            "sound_rounds": get("sound"),
            # meta
            "task_meta": task_meta,
            "anm_stats": anm_stats,
        }

    def _build_verifier_packet(
        self,
        user_query: str,
        merged_reasoning: str,
        entry_specialist: str,
        router_reason: str,
    ) -> str:
        flags = (
            f"Router entry specialist: {entry_specialist}. "
            f"Reason: {router_reason}. "
            f"Original user query: {user_query!r}"
        )

        return WOT_PACKET_TEMPLATES["verifier_packet"].format(
            merged_reasoning=merged_reasoning,
            router_flags=flags,
            instructions="Approve only if reasoning is correct, coherent, and non-hallucinated.",
        )

    # ========================================================
    #  RESEARCH MODE HELPER METHODS
    # ========================================================

    def _deterministic_domain_detection(self, user_query: str) -> list:
        """
        Deterministic keyword-based domain detection for Research Mode.
        Returns list of detected domains in priority order.
        """
        detected_domains = []
        query_lower = user_query.lower()

        # Math patterns
        math_keywords = ["calculate", "equation", "integral", "derivative", "matrix", "algebra",
                        "geometry", "trigonometry", "calculus", "math", "formula", "solve"]
        if any(kw in query_lower for kw in math_keywords):
            detected_domains.append("math")

        # Physics patterns (expanded for astronomy/astrophysics)
        physics_keywords = ["physics", "force", "energy", "momentum", "velocity", "acceleration",
                           "gravity", "electromagnetic", "quantum", "relativity", "thermodynamics",
                           "black hole", "blackhole", "quasar", "star", "galaxy", "nebula", "supernova",
                           "neutron star", "white dwarf", "event horizon", "singularity", "accretion",
                           "astrophysics", "cosmology", "spacetime", "gravitational", "mass", "density",
                           "fusion", "fission", "radiation", "photon", "wavelength", "spectrum"]
        if any(kw in query_lower for kw in physics_keywords):
            detected_domains.append("physics")

        # Chemistry patterns
        chemistry_keywords = ["chemistry", "molecule", "atom", "reaction", "compound", "element",
                             "chemical", "bond", "periodic table", "ion", "acid", "base"]
        if any(kw in query_lower for kw in chemistry_keywords):
            detected_domains.append("chemistry")

        # Biology patterns
        biology_keywords = ["biology", "cell", "dna", "gene", "organism", "protein", "evolution",
                           "ecosystem", "species", "bacteria", "virus", "anatomy"]
        if any(kw in query_lower for kw in biology_keywords):
            detected_domains.append("biology")

        # Code patterns
        code_keywords = ["code", "program", "function", "algorithm", "python", "javascript",
                        "java", "c++", "sql", "debug", "syntax", "compile", "execute"]
        if any(kw in query_lower for kw in code_keywords):
            detected_domains.append("code")

        # Internet research patterns
        internet_keywords = ["research", "latest", "recent", "current", "news", "web", "online",
                            "internet", "search", "find information", "look up"]
        if any(kw in query_lower for kw in internet_keywords):
            detected_domains.append("internet")

        # Facts patterns
        facts_keywords = ["fact", "what is", "who is", "when did", "where is", "define",
                         "explain", "describe", "tell me about"]
        if any(kw in query_lower for kw in facts_keywords):
            detected_domains.append("facts")

        # Default to general if no specific domain detected
        if not detected_domains:
            detected_domains.append("general")

        return detected_domains

    def _select_parallel_modules(self, detected_domains: list, user_query: str) -> list:
        """
        Dynamically select 4-10 modules based on query complexity.
        Simple queries -> 4 modules minimum
        Complex queries -> up to 10 modules
        """
        min_modules = self.research_mode_config.get("min_parallel_modules", 4)
        max_modules = self.research_mode_config.get("max_parallel_modules", 10)

        # Complexity heuristics
        query_length = len(user_query)
        word_count = len(user_query.split())
        domain_count = len(detected_domains)

        # Calculate complexity score (0-100)
        complexity_score = 0

        # Length factor (0-30 points)
        if query_length > 200:
            complexity_score += 30
        elif query_length > 100:
            complexity_score += 20
        elif query_length > 50:
            complexity_score += 10

        # Word count factor (0-30 points)
        if word_count > 40:
            complexity_score += 30
        elif word_count > 20:
            complexity_score += 20
        elif word_count > 10:
            complexity_score += 10

        # Domain diversity factor (0-40 points)
        complexity_score += min(domain_count * 10, 40)
        
        # Research Mode bonus: Complex queries (multiple questions, "and", "how", "why") get bonus
        query_lower = user_query.lower()
        question_indicators = [" and ", " how ", " why ", " what ", " when ", " where ", " explain ", " describe "]
        question_count = sum(1 for indicator in question_indicators if indicator in query_lower)
        if question_count >= 2:
            complexity_score += 15  # Multi-part questions are more complex
        elif question_count >= 1:
            complexity_score += 5

        # Map complexity to module count (4-10)
        # Per Blueprint: "If 8 modules are relevant, all 8 run in parallel"
        # For Research Mode, be more aggressive with module selection
        if complexity_score >= 80:
            num_modules = max_modules  # 10 modules for very complex queries
        elif complexity_score >= 60:
            num_modules = 8  # Complex queries use 8 modules
        elif complexity_score >= 40:
            num_modules = 6  # Medium complexity uses 6 modules
        else:
            num_modules = min_modules  # 4 modules minimum (per Blueprint)

        # Select top N detected domains
        selected = detected_domains[:num_modules]

        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_MODULES", "location": "router.py:_select_parallel_modules", "message": "Module selection", "data": {"detected_domains": detected_domains, "complexity_score": complexity_score, "num_modules": num_modules, "selected_before_fill": selected}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion

        # ENFORCE minimum modules (per Blueprint: "4-10 modules run in parallel")
        # Always ensure at least min_modules, even if we need to add general/facts/memory/research
        while len(selected) < min_modules:
            if "general" not in selected:
                selected.append("general")
            elif "facts" not in selected:
                selected.append("facts")
            elif "memory" not in selected:
                selected.append("memory")
            elif "research" not in selected:
                selected.append("research")
            else:
                # If we still don't have enough, cycle through available domains
                all_available = ["general", "math", "physics", "code", "chemistry", "biology", "memory", "research", "facts"]
                for domain in all_available:
                    if domain not in selected and len(selected) < min_modules:
                        selected.append(domain)
                break

        return selected[:max_modules]  # Cap at max_modules

    def _assign_authority_models(self, detected_domains: list) -> dict:
        """
        Map domains to authority models per Blueprint specification.
        Returns dict: {"math": "nanbeige4-3b", "code": "stable-code-3b", ...}
        
        Per Blueprint:
        - Physics/Chemistry/Biology/Math -> NanBeige4-3B
        - Meta-Cognition/Self-Awareness -> DeepSeek R1-1.5B
        - Internet Research -> Qwen2.5-3B-Instruct
        - Coding -> StableCode-3B
        """
        from anm.system.model_registry import get_authority_model_for_domain
        
        assignments = {}

        # Use model_registry for correct authority model mapping (per Blueprint)
        for domain in detected_domains:
            authority_model = get_authority_model_for_domain(domain)
            if authority_model:
                assignments[domain] = authority_model
            else:
                # Fallback to DeepSeek R1 for general/metacognition (per Blueprint)
                assignments[domain] = "deepseek-r1-1.5b"
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_AUTHORITY", "location": "router.py:_assign_authority_models", "message": "Authority model assignments", "data": {"detected_domains": detected_domains, "assignments": assignments}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion

        return assignments

    def _build_research_specialists(self, selected_domains: list, authority_assignments: dict) -> dict:
        """
        Create specialists WITHOUT ParallelSpecialistAdapter ensemble.
        Research mode uses 1 worker per specialist (no voting) with authority models.
        Returns specialists dict for WoT.
        """
        specialists = {}
        
        from anm.system.model_registry import get_authority_model_for_domain

        for domain in selected_domains:
            # Get authority model for this domain
            authority_model = authority_assignments.get(domain)
            if not authority_model:
                # Fallback: use registry mapping
                authority_model = get_authority_model_for_domain(domain)
            
            # Normalize model name (handle "deepseek-r1:1.5b" -> "deepseek-r1-1.5b")
            if authority_model:
                authority_model = authority_model.replace(":", "-").lower()
            
            # Create single-worker specialist with authority model (not ParallelSpecialistAdapter)
            # Extract the base specialist class from ParallelSpecialistAdapter
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH", "location": "router.py:_build_research_specialists", "message": "Building research specialist", "data": {"domain": domain, "authority_model": authority_model}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            if domain == "general" and hasattr(self, 'general'):
                # Get base class from adapter
                base_class = GeneralLLM
                specialists["general"] = base_class(model_name=authority_model)
            elif domain == "math" and hasattr(self, 'math'):
                base_class = MathLLM
                specialists["math"] = base_class(model_name=authority_model)
            elif domain == "physics" and hasattr(self, 'physics'):
                base_class = PhysicsLLM
                specialists["physics"] = base_class(model_name=authority_model)
            elif domain == "chemistry" and hasattr(self, 'chemistry'):
                base_class = ChemistryLLM
                specialists["chemistry"] = base_class(model_name=authority_model)
            elif domain == "biology" and hasattr(self, 'biology'):
                base_class = BiologyLLM
                specialists["biology"] = base_class(model_name=authority_model)
            elif domain == "code" and hasattr(self, 'code'):
                base_class = CodeLLM
                specialists["code"] = base_class(model_name=authority_model)
            elif domain == "internet":
                # Research Mode: Create ResearchLLM with authority model (Blueprint compliance)
                from anm.specialists.research_llm import ResearchLLM
                specialists["internet"] = ResearchLLM(model_name=authority_model)
            elif domain == "facts" and hasattr(self, 'facts'):
                base_class = FactsLLM
                specialists["facts"] = base_class(model_name=authority_model)
            elif domain == "memory" and hasattr(self, 'memory_adapter'):
                # Memory adapter is already single-worker
                specialists["memory"] = self.memory_adapter

        return specialists

    def _extract_sources_from_outputs(self, domain_outputs: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Extract source URLs from domain outputs before refinement strips them.
        Blueprint compliance: Sources section requires explicit URL attribution.
        """
        import re
        sources = []
        seen_urls = set()

        # URL pattern to match http/https URLs
        url_pattern = r'https?://[^\s\)\"\'\<\>\]\[,]+'

        for domain, output in domain_outputs.items():
            if not output:
                continue

            urls = re.findall(url_pattern, str(output))
            for url in urls:
                # Clean URL (remove trailing punctuation)
                url = url.rstrip('.,;:!?')

                if url not in seen_urls and len(url) > 10:
                    seen_urls.add(url)

                    # Try to extract title from surrounding context
                    title = "Source"

                    # Look for title patterns near URL
                    title_match = re.search(rf'(?:title|Title|TITLE)[:\s]+([^\n]+)', output)
                    if title_match:
                        title = title_match.group(1)[:100]

                    sources.append({
                        "url": url,
                        "domain": domain,
                        "title": title
                    })

        return sources

    def _run_metacognition_audit(self, user_query: str, domain_cots: dict, entry_domain: str) -> dict:
        """
        Use DeepSeek R1 to self-audit reasoning quality.
        Checks: consistency, confidence, uncertainty, limitations.
        Returns dict with audit results.
        """
        try:
            from anm.system.inference import get_inference_engine
            engine = get_inference_engine()

            audit_prompt = f"""Meta-cognitive auditor for ANM Research Mode.

Query: {user_query}
Entry: {entry_domain}

Domain Outputs:
{self._format_domain_cots_for_audit(domain_cots)}

Audit (JSON): consistency, confidence, uncertainty, limitations"""

            response = engine.generate(
                audit_prompt,
                max_tokens=500,
                temperature=0.3,
            )

            # Try to parse as JSON, fallback to plain text
            try:
                import json
                audit = json.loads(response)
            except Exception:
                audit = {
                    "consistency": "Unable to parse",
                    "confidence": "Medium",
                    "uncertainty": response,
                    "limitations": "Audit parsing failed"
                }

            return audit

        except Exception as e:
            return {
                "consistency": "Audit failed",
                "confidence": "Unknown",
                "uncertainty": f"Error: {str(e)}",
                "limitations": "Meta-cognition audit unavailable"
            }

    def _format_domain_cots_for_audit(self, domain_cots: dict) -> str:
        """Format domain COTs for meta-cognition audit."""
        formatted = []
        for domain, cot in domain_cots.items():
            formatted.append(f"[{domain.upper()}]:\n{cot[:500]}...\n")  # First 500 chars
        return "\n".join(formatted)

    def _detect_math_patterns(self, query: str) -> bool:
        """Detect if query contains math-specific patterns."""
        math_indicators = ["=", "+", "-", "*", "/", "^", "∫", "∑", "√"]
        return any(ind in query for ind in math_indicators)

    def _detect_science_patterns(self, query: str) -> bool:
        """Detect if query contains science-specific patterns."""
        science_terms = ["hypothesis", "experiment", "theory", "observation", "data"]
        query_lower = query.lower()
        return any(term in query_lower for term in science_terms)

    def _detect_code_patterns(self, query: str) -> bool:
        """Detect if query contains code-specific patterns."""
        code_indicators = ["def ", "class ", "import ", "function", "return", "if ", "for ", "while "]
        return any(ind in query for ind in code_indicators)
    
    def _needs_external_knowledge(self, user_query: str, detected_domains: list) -> bool:
        """
        Determine if external knowledge (internet research) is needed.
        Per Blueprint Section 7: "When external knowledge is required"
        """
        query_lower = user_query.lower()
        
        # Keywords that suggest external knowledge is needed
        external_knowledge_indicators = [
            "latest", "recent", "current", "news", "today", "now",
            "what is", "who is", "when did", "where is", "how many",
            "find", "search", "look up", "information about",
            "research", "study", "paper", "article", "publication",
            "discover", "discovered", "found", "published",
        ]
        
        # Check if query contains indicators
        has_indicators = any(indicator in query_lower for indicator in external_knowledge_indicators)
        
        # Check if query asks about current events or recent information
        is_current_event_query = any(phrase in query_lower for phrase in [
            "what happened", "what's happening", "current state",
            "latest development", "recent news", "breaking"
        ])
        
        # Research mode should always consider internet research for complex queries
        # But only trigger if indicators are present to avoid unnecessary API calls
        return has_indicators or is_current_event_query
    
    def _run_internet_research_pipeline(self, user_query: str, memory_brief: str) -> dict:
        """
        Internet Research Pipeline per Blueprint Section 7.
        
        Pipeline:
        1. Fetch sources (ResearchLLM/InternetLLM)
        2. Read and summarize (Qwen2.5-3B-Instruct)
        3. Reason and connect (DeepSeek R1)
        4. Validate (science/math → NanBeige, code → StableCode)
        5. Final synthesis (DeepSeek R1)
        
        Returns dict with research data to be included in WoT context.
        """
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "INTERNET_RESEARCH", "location": "router.py:_run_internet_research_pipeline", "message": "Starting internet research pipeline", "data": {"user_query": user_query[:200]}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        research_data = {
            "sources": [],
            "summary": "",
            "reasoning": "",
            "validation": "",
            "synthesis": "",
        }
        
        try:
            # Step 1: Fetch sources using ResearchLLM (uses Qwen2.5-3B-Instruct per Blueprint)
            if RESEARCH_LLM_AVAILABLE and ResearchLLM:
                research_llm = ResearchLLM()
                wot_packet = f"""[RESEARCH REQUEST]
Query: {user_query}

Memory Context:
{memory_brief[:500]}

[RESEARCH MODE: Fetch external sources and summarize]
[END RESEARCH REQUEST]"""
                
                # ResearchLLM will use Qwen2.5-3B-Instruct for web reading/summarization
                research_output = research_llm.run(wot_packet)
                research_data["sources"] = research_output[:2000]  # Store first 2000 chars
                
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        import time
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "INTERNET_RESEARCH", "location": "router.py:_run_internet_research_pipeline", "message": "Step 1 complete: Sources fetched", "data": {"research_output_length": len(research_output)}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                
                # Step 2-3: Reason and connect using DeepSeek R1 (already done by ResearchLLM internally)
                # ResearchLLM uses DeepSeek R1 for reasoning, so we can use its output directly
                # Clean the output to remove internal markers and META blocks before passing to WoT
                cleaned_output = self._clean_research_output(research_output)
                research_data["summary"] = cleaned_output[:1000]
                research_data["reasoning"] = cleaned_output
                
            else:
                # Fallback: Use InternetLLM if ResearchLLM not available
                if hasattr(self, 'internet') and self.internet:
                    internet_output = self.internet.run(f"[RESEARCH REQUEST]\n{user_query}\n[END RESEARCH REQUEST]")
                    research_data["sources"] = internet_output[:2000]
                    research_data["summary"] = internet_output[:1000]
                    research_data["reasoning"] = internet_output
                else:
                    # No internet research available
                    research_data["summary"] = "Internet research not available (ResearchLLM/InternetLLM not loaded)"
            
            # Step 4: Validation happens during WoT with authority models
            # (science/math → NanBeige, code → StableCode) - handled by authority model assignment
            
            # Step 5: Final synthesis happens in refiner (uses DeepSeek R1)
            # This is handled by the refiner after WoT completes
            
        except Exception as e:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "INTERNET_RESEARCH", "location": "router.py:_run_internet_research_pipeline", "message": "Internet research pipeline failed", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            research_data["summary"] = f"Internet research failed: {str(e)}"
        
        return research_data
    
    def _clean_research_output(self, raw_output: str) -> str:
        """
        Clean ResearchLLM output to remove internal markers, META blocks, and WOT_REQUEST
        before passing to WoT as context.
        
        ResearchLLM output contains:
        - Search results dump
        - LLM reasoning
        - META blocks (GRE, Self-Awareness, Diagnostics)
        - WOT_REQUEST markers
        
        We need to extract just the meaningful research content.
        """
        if not raw_output:
            return ""
        
        import re
        text = raw_output
        
        # Remove META blocks
        text = re.sub(r'\[META.*?\].*?\[/META\]', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'--- META.*?---', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[DOMAIN_HEALTH\].*?\[POINTGAME_FEEDBACK\].*?', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[GLOBAL_RULES\].*?', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[RESEARCH_DIAGNOSTICS\].*?', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove WOT_REQUEST markers
        text = re.sub(r'WOT_REQUEST:.*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'Final WOT REQUEST:.*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove search result formatting (ID, SOURCE, TITLE, SNIPPET, URL markers)
        text = re.sub(r'- ID:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'  SOURCE:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'  TITLE:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'  SNIPPET:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'  URL:.*?\n', '', text, flags=re.MULTILINE)
        
        # Remove WoT packet markers
        text = re.sub(r'--- WoT PACKET.*?---', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'--- SEARCH QUERY.*?---', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'--- SEARCH RESULTS.*?---', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'--- RELATED PAST RESEARCH.*?---', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove instruction text
        text = re.sub(r'Respond ONLY with.*?WOT_REQUEST\.', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'Do NOT fabricate.*?URLs\.', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove thinking tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</?redacted_reasoning>', '', text, flags=re.IGNORECASE)
        
        # Extract meaningful paragraphs
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or len(stripped) < 10:
                continue
            # Skip lines that are just markers or formatting
            skip_markers = ['meta', 'wot_request', 'id:', 'source:', 'title:', 'url:', 'snippet:', 'domain_health', 'global_rules', 'research_diagnostics', 'pointgame_feedback', 'confidence:', 'uncertainty:', 'passed:', 'risk_level:', 'violations:', 'penalty:', 'self_reflection:', 'success_signal:', 'reason:', 'evidence_count:', 'error_hits:', 'no_result_hits:']
            if any(marker in stripped.lower() for marker in skip_markers):
                continue
            cleaned_lines.append(stripped)
        
        result = '\n'.join(cleaned_lines)
        
        # Remove excessive whitespace
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
        result = result.strip()
        
        return result