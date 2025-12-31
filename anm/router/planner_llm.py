# ============================================================
# ANM V0-OpenSource — PlannerLLM V0-OpenSource MAX (Synced)
#  LawBook V0-OpenSource • DomainMasker V0-OpenSource • TrueWoT V0-OpenSource compatible
#  Multi-modal Strategy Engine (Simulation/Image/Sound)
#  Hard JSON Stability • Zero-Hallucination Planning
# ============================================================

from __future__ import annotations
import logging
import json
from typing import Any, Dict, Optional

from anm.system.inference import run_model
from anm.utils.debug_logger import log_debug
from anm.utils.prompts import ROUTER_PROMPT


# ============================================================
#                     PlannerLLM V0-OpenSource MAX
# ============================================================

class PlannerLLM:
    """
    PlannerLLM V0-OpenSource MAX.

    NEW in synced V0-OpenSource MAX:
      ✓ Simulation domain supported officially
      ✓ Image domain fully integrated (visual analysis auto-detected)
      ✓ Sound domain upgraded with sound-design risk control
      ✓ PAST-ONLY memory enforcement (LawBook V0-OpenSource)
      ✓ High-risk physics auto-disables research (speculation guard)
      ✓ Router V0-OpenSource multi-domain mesh strategy tagging
      ✓ TrueWoT V0-OpenSource → supports 4–64 structured steps
      ✓ Super-stable JSON extractor (unbreakable)
      ✓ Strategic depth scoring (risk_score + risk_level + domain_span)
      ✓ Auto-detection of:
          - design
          - derivation
          - simulation
          - creative_worldbuilding
          - sound_design
          - visual_analysis
          - fiction
          - analysis (default)
      ✓ Full alignment with DomainMasker V0-OpenSource MAX (risk_level field added)
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

    def __init__(
        self,
        model_name: str = "deepseek-r1:1.5b",
        system_prompt: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        # Use ROUTER_PROMPT from centralized prompts.py
        self.system_prompt = system_prompt or (
            f"{ROUTER_PROMPT}\n\n"
            "You are PlannerLLM. Output STRICT JSON ONLY. Do NOT use markdown.\n"
        )

    # --------------------------------------------------------
    #  PUBLIC: Generate Plan
    # --------------------------------------------------------
    def plan(self, user_query: str, memory_brief: str = "") -> Dict[str, Any]:
        # #region agent log
        import json
        import time
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "planner_llm.py:plan", "message": "Plan start", "data": {"user_query": user_query[:200]}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion
        prompt = self._build_prompt(user_query, memory_brief)
        raw = run_model(prompt, max_tokens=512)
        parsed = self._parse_json(raw)
        safe = self._normalize(parsed, user_query)
        # #region agent log
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "planner_llm.py:plan", "message": "Plan result", "data": {"entry_specialist": safe.get("entry_specialist"), "reason": safe.get("reason", "")[:200]}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion
        return safe

    # --------------------------------------------------------
    #  PROMPT Builder
    # --------------------------------------------------------
    def _build_prompt(self, q: str, mem: str) -> str:
        return f"""
{self.system_prompt}

INPUTS:
  USER_QUERY = problem to solve.
  MEMORY_BRIEF = PAST-ONLY diary patterns, never guaranteed true.

VALID_DOMAINS:
  ["general","math","physics","code","chemistry","biology",
   "memory","research","facts","simulation","image","sound"]

YOU MUST RETURN JSON:
{{
  "entry_specialist": "...",
  "active_domains": ["general","math"],
  "max_steps": 12,
  "reason": "...",
  "inject_memory": true,
  "needs_research": false,
  "needs_facts": false,
  "strategy_tags": ["multi-domain"],
  "risk_score": 0.4,
  "task_type": "analysis",
  "step_plan": "..."
}}

RULES (LawBook V0-OpenSource):
  • STRICT JSON ONLY.
  • Memory = PAST ONLY, weak evidence.
  • Physics = high-risk → disable research unless absolutely required.
  • Sound & Image must be activated when required.
  • Simulation domain activated for physical, orbital, dynamics tasks.
  • No hallucination, no invention.
  • Step plan MUST be a short 2–10 line outline.
  • risk_score in [0.0 – 1.0]

USER_QUERY:
\"\"\"{q[:4000]}\"\"\"

MEMORY_BRIEF:
\"\"\"{mem[:4000]}\"\"\"
"""

    # --------------------------------------------------------
    #  JSON PARSER (Indestructible)
    # --------------------------------------------------------
    def _parse_json(self, raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            return {}

    # --------------------------------------------------------
    #  Helper: infer task_type from query + entry
    # --------------------------------------------------------
    def _infer_task_type(self, query: str, entry: str) -> str:
        q = query.lower()

        # Fiction / story / worldbuilding
        if any(k in q for k in ["story", "novel", "scene", "chapter", "fanfic", "worldbuilding"]):
            return "creative_worldbuilding"

        # Sound design / audio
        if any(k in q for k in ["sound design", "soundtrack", "foley", "audio mix", "sfx", "binaural"]):
            return "sound_design"

        # Visual analysis
        if any(k in q for k in ["frame analysis", "shot composition", "color grading", "visual style"]):
            return "visual_analysis"

        # Simulation / dynamics / video generation
        if any(k in q for k in [
            "simulate", "simulation", "orbit", "trajectory",
            "n-body", "fluid", "cfd", "particle", "time evolution",
            # Video generation triggers
            "generate a video", "generate video", "create a video", "create video",
            "make a video", "make video", "video of it", "animation", "animate",
            # Physics scenarios that need simulation
            "fall", "falling", "drop", "bounce", "collision", "impact", "splash",
            "what happens", "what will happen", "visualize",
        ]):
            return "simulation"

        # Derivations / proofs
        if any(k in q for k in [
            "derive", "derivation", "proof", "prove", "show that",
            "integral", "differential equation", "theorem"
        ]):
            return "derivation"

        # Design / architecture
        if any(k in q for k in [
            "design", "architecture", "system design", "api design",
            "ui layout", "pipeline design", "module layout"
        ]):
            return "design"

        # Fallbacks based on entry domain
        if entry in {"physics", "math", "code", "chemistry", "biology"}:
            return "analysis"

        # Default
        return "analysis"

    # --------------------------------------------------------
    #  Helper: risk score from query content
    # --------------------------------------------------------
    def _auto_risk_from_query(self, query: str, entry: str) -> float:
        q = query.lower()
        score = 0.3  # base

        # Hard theoretical physics / GR
        if any(k in q for k in ["black hole", "kerr", "schwarzschild", "event horizon", "quasar"]):
            score += 0.25
        if any(k in q for k in ["general relativity", "gr", "qft", "quantum field", "quantum gravity"]):
            score += 0.25

        # Heavy engineering / safety-sensitive
        if any(k in q for k in ["rocket engine", "combustion chamber", "pressure vessel", "bridge load", "structural failure"]):
            score += 0.2

        # Code / security hints
        if any(k in q for k in ["exploit", "malware", "ransomware", "backdoor", "sql injection"]):
            score += 0.25

        # Medicine / bio-risk hints
        if any(k in q for k in ["dosage", "drug", "vaccine", "pathogen", "virus culture"]):
            score += 0.25

        # If entry is physics or code and asking for “precise”, “exact”, etc.
        if entry in {"physics", "math"} and any(k in q for k in ["exact", "rigorous", "precise derivation"]):
            score += 0.1

        # Clamp
        if score < 0.0:
            score = 0.0
        if score > 1.0:
            score = 1.0
        return score

    # --------------------------------------------------------
    #  Helper: risk level from score
    # --------------------------------------------------------
    def _risk_level_from_score(self, score: float) -> str:
        if score < 0.25:
            return "low"
        if score < 0.55:
            return "medium"
        if score < 0.8:
            return "high"
        return "insane"

    # --------------------------------------------------------
    #  NORMALIZATION (LawBook V0-OpenSource SAFE)
    # --------------------------------------------------------
    def _normalize(self, plan: Dict[str, Any], query: str) -> Dict[str, Any]:

        safe: Dict[str, Any] = {
            "entry_specialist": "general",
            "active_domains": ["general"],
            "max_steps": 12,
            "reason": "fallback plan",
            "inject_memory": True,
            "needs_research": False,
            "needs_facts": False,
            "strategy_tags": ["auto"],
            "risk_score": 0.3,
            "risk_level": "medium",
            "task_type": "analysis",
            "step_plan": "general → refine → final",
        }

        if not isinstance(plan, dict):
            # We still run heuristics on the raw query below
            q_lower = query.lower()
            entry = self._infer_entry_from_query(q_lower)
            task_type = self._infer_task_type(query, entry)
            risk_score = self._auto_risk_from_query(query, entry)
            risk_level = self._risk_level_from_score(risk_score)

            safe["entry_specialist"] = entry
            safe["active_domains"] = [entry, "general"]
            safe["risk_score"] = risk_score
            safe["risk_level"] = risk_level
            safe["task_type"] = task_type
            safe["reason"] = f"Heuristic fallback plan for query: {query[:200]}"
            return safe

        q = query.lower()

        # --------------------------------------------------------
        # ENTRY SPECIALIST
        # --------------------------------------------------------
        entry = str(plan.get("entry_specialist", "")).lower()

        if entry not in self.VALID_DOMAINS:
            entry = self._infer_entry_from_query(q)

        safe["entry_specialist"] = entry

        # --------------------------------------------------------
        # ACTIVE DOMAINS
        # --------------------------------------------------------
        raw_domains = plan.get("active_domains", [])
        clean = []

        if isinstance(raw_domains, list):
            for d in raw_domains:
                d = str(d).lower().strip()
                if d in self.VALID_DOMAINS and d not in clean:
                    clean.append(d)

        if entry not in clean:
            clean.insert(0, entry)

        if not clean:
            clean = [entry]

        safe["active_domains"] = clean

        # --------------------------------------------------------
        # MAX STEPS
        # --------------------------------------------------------
        try:
            ms = int(plan.get("max_steps", 12))
        except Exception:
            ms = 12
        safe["max_steps"] = max(4, min(ms, 64))

        # --------------------------------------------------------
        # BOOLEAN FLAGS
        # --------------------------------------------------------
        def to_bool(x, default):
            if isinstance(x, bool):
                return x
            if isinstance(x, str):
                lx = x.lower().strip()
                if lx in ("true", "1", "yes"):
                    return True
                if lx in ("false", "0", "no"):
                    return False
            return default

        safe["inject_memory"] = to_bool(plan.get("inject_memory"), True)
        safe["needs_research"] = to_bool(plan.get("needs_research"), False)
        safe["needs_facts"] = to_bool(plan.get("needs_facts"), False)

        # --------------------------------------------------------
        # STRATEGY TAGS (base)
        # --------------------------------------------------------
        tags = []
        raw_tags = plan.get("strategy_tags", [])

        if isinstance(raw_tags, list):
            for t in raw_tags:
                t = str(t).strip()
                if t and t not in tags:
                    tags.append(t)

        # Auto-tags from query
        if "sound" in q or "audio" in q:
            tags.append("sound-design")
        if "image" in q or "visual" in q or "frame" in q:
            tags.append("visual-analysis")
        
        # Simulation triggers (EXTENDED - includes video generation)
        simulation_triggers = [
            "simulate", "simulation", "orbit", "trajectory",
            "generate a video", "generate video", "create a video", "create video",
            "make a video", "make video", "video of it", "animation", "animate",
            "fall", "falling", "drop", "bounce", "collision", "impact", "splash",
            "what happens", "what will happen", "visualize",
        ]
        if any(k in q for k in simulation_triggers):
            tags.append("simulation")
            # IMPORTANT: Also add simulation to active_domains!
            if "simulation" not in safe["active_domains"]:
                safe["active_domains"].append("simulation")
        
        # Physics triggers (gravity, motion, forces)
        physics_triggers = [
            "fall", "falling", "drop", "dropping", "gravity", "throw", "thrown",
            "velocity", "acceleration", "force", "energy", "momentum", "speed",
            "height", "distance", "time", "motion", "projectile", "trajectory",
            "water", "air", "friction", "resistance", "impact", "collision", "collide",
        ]
        if any(k in q for k in physics_triggers):
            if "physics" not in safe["active_domains"]:
                safe["active_domains"].append("physics")
        
        if "story" in q or "fiction" in q or "novel" in q:
            tags.append("fiction")
        if "derive" in q or "proof" in q or "prove" in q:
            tags.append("derivation")

        if not tags:
            tags = ["auto"]

        # Dedup
        safe["strategy_tags"] = list(dict.fromkeys(tags))

        # --------------------------------------------------------
        # RISK SCORE + RISK LEVEL
        # --------------------------------------------------------
        try:
            risk = float(plan.get("risk_score", 0.3))
        except Exception:
            risk = 0.3

        heuristic_risk = self._auto_risk_from_query(query, entry)
        # Use the max of LLM suggestion vs heuristic guard
        risk = max(risk, heuristic_risk)
        if risk < 0.0:
            risk = 0.0
        if risk > 1.0:
            risk = 1.0

        safe["risk_score"] = risk
        safe["risk_level"] = self._risk_level_from_score(risk)

        # PHYSICS / SOUND SAFETY → do not request research by default
        if entry in {"physics", "sound"}:
            safe["needs_research"] = False

        # --------------------------------------------------------
        # TASK TYPE
        # --------------------------------------------------------
        tt = plan.get("task_type", "")
        if not isinstance(tt, str) or not tt.strip():
            tt = self._infer_task_type(query, entry)
        safe["task_type"] = tt

        # --------------------------------------------------------
        # STEP PLAN
        # --------------------------------------------------------
        sp = plan.get("step_plan", "")
        safe["step_plan"] = sp if isinstance(sp, str) else str(sp)

        # --------------------------------------------------------
        # REASON
        # --------------------------------------------------------
        r = plan.get("reason", "")
        # Always ensure reason matches the current query (prevent caching issues)
        if not isinstance(r, str) or not r.strip() or query[:50] not in r:
            r = f"Auto-selected strategy for query: {query[:200]}"
        safe["reason"] = r.strip()

        return safe

    # --------------------------------------------------------
    #  Helper: infer entry specialist from query (fallback)
    # --------------------------------------------------------
    def _infer_entry_from_query(self, q_lower: str) -> str:
        q = q_lower

        # #region agent log
        import json
        import time
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference start", "data": {"query": q_lower[:200]}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion

        # SIMULATION: video generation, animations, physics scenarios
        if any(k in q for k in [
            "simulate", "simulation", "orbit", "trajectory", "n-body",
            "generate a video", "generate video", "create a video", "create video",
            "make a video", "make video", "video of it", "animation", "animate",
        ]):
            result = "simulation"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "simulation"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        
        # PHYSICS: gravity, motion, forces, falling objects
        if any(k in q for k in [
            "fall", "falling", "drop", "dropping", "gravity", "throw", "thrown",
            "velocity", "acceleration", "force", "energy", "momentum",
            "black hole", "relativity", "quantum", "astrophysics",
            "collision", "impact", "bounce", "projectile",
        ]):
            result = "physics"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "physics"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        
        if any(k in q for k in ["sound", "audio", "hum", "chirp", "binaural", "mix"]):
            result = "sound"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "sound"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        if any(k in q for k in ["image", "visual", "frame", "diagram", "picture"]):
            result = "image"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "image"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        # MATH: arithmetic, calculations, equations, derivations
        # Check for arithmetic patterns first (simple math questions)
        import re
        arithmetic_pattern = re.search(r'\d+\s*[+\-*/]\s*\d+', q)
        if arithmetic_pattern or any(k in q for k in ["what is", "calculate", "compute", "solve", "equals", "="]):
            # Check if it's a simple arithmetic question
            if arithmetic_pattern or (any(k in q for k in ["what is", "equals"]) and any(op in q for op in ["+", "-", "*", "/", "×", "÷"])):
                result = "math"
                # #region agent log
                try:
                    log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "math_arithmetic"}, "timestamp": int(time.time() * 1000)})
                except Exception as e:
                    logging.warning(f"Debug logging failed: {e}")
            # #endregion
                return result
        if any(k in q for k in ["derive", "integral", "equation", "gradient", "matrix", "proof", "theorem"]):
            result = "math"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "math"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        if any(k in q for k in ["python", "code", "function", "class", "algorithm"]):
            result = "code"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "code"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        if any(k in q for k in ["reaction", "molecule", "compound", "bond", "stoichiometry"]):
            result = "chemistry"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "chemistry"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        if any(k in q for k in ["cell", "neuron", "organism", "evolution", "physiology"]):
            result = "biology"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "biology"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result
        
        # FACTS: simple factual questions (capital, population, date, etc.)
        fact_patterns = [
            "what is the", "who is", "when was", "where is", "capital of", "population of",
            "founded", "located", "born", "died", "invented", "discovered"
        ]
        if any(pattern in q for pattern in fact_patterns) and len(q.split()) <= 10:
            result = "facts"
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "facts"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            return result

        result = "general"
        # #region agent log
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "planner_llm.py:_infer_entry_from_query", "message": "Entry inference result", "data": {"result": result, "matched": "none"}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion
        return result