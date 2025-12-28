# ============================================================
# ANM V0-OpenSource — TASK COMPILER V0-OpenSource ULTRA (FINAL BUILD)
#  Fully-Synced With All Specialists (Physics, Sim, Sound, Memory)
#  Router-Ready • Planner-Safe • Stable DAG • Zero-Hallucination
# ============================================================

from __future__ import annotations
from typing import List, Dict, Any, Optional, Set, Tuple
import re


class TaskCompiler:
    """
    TASK COMPILER V0-OpenSource ULTRA (ANM V0-OpenSource)

    ‣ Multi-domain extraction (math, physics, code, memory, research, sound, sim, image)
    ‣ Auto pipeline selection (simulation_dominant, research_dominant, mixed, default)
    ‣ Entry-specialist chosen via SelfAwarenessLLM → ROUTING_SUGGESTION
    ‣ Fully synced with:
         - SelfAwarenessLLM V0-OpenSource
         - SimulationLLM V0-OpenSourceA (3D raymarch)
         - SoundLLM V0-OpenSource
         - ResearchLLM V0-OpenSource
         - MemoryLLM V0-OpenSource
    ‣ DAG-checked + auto-repair cycle breaker
    """

    # ------------------------------------------------------------
    # DOMAIN KEYWORD MAP (UPDATED)
    # ------------------------------------------------------------
    DOMAIN_MAP: Dict[str, List[str]] = {
        "math": [
            "solve","derive","integral","equation","tensor","limit","matrix",
            "algebra","proof","calculate","gradient","differential","probability",
            "statistics","eigenvalue","compute","symbolic"
        ],
        "physics": [
            "energy","force","gravity","orbit","black hole","kerr","schwarzschild",
            "relativity","velocity","acceleration","quantum","field","accretion",
            "radiation","astrophysics","trajectory","momentum","angular momentum",
            "neutron star","collapse","simulation physics","bh","ns","spin"
        ],
        "code": [
            "script","python","algorithm","function","bug","fix","pseudocode","api",
            "module","code","class","compile","debug","refactor","tests","unit test",
            "runtime","exception","stacktrace"
        ],
        "chemistry": [
            "reaction","bond","molecule","electron","ion","acid","base","atomic",
            "stoichiometry","chemical","oxidation","reduction","ph","orbitals",
            "covalent","ionic"
        ],
        "biology": [
            "cell","dna","organism","protein","immune","biological","gene","genetic",
            "evolution","metabolism","neuron","brain tissue"
        ],
        "research": [
            "latest","current","study","paper","search","research","real data","dataset",
            "internet","sources","citation","recent","external"
        ],
        "facts": [
            "verify","true","fact","check validity","correct?","is it real","fact check",
            "valid?","accurate?","wrong?"
        ],
        "simulation": [
            "simulate","simulation","render","frames","engine","orbit animation",
            "motion animation","bh simulation","accretion simulation","particle system",
            "fluid sim","physics engine","n-body","3d sim","raymarch","3d","camera path"
        ],
        "image": [
            "image","photo","picture","vision","analyze image","what do you see",
            "frame","object detection","screenshot","look at this image"
        ],
        "sound": [
            "sound","audio","sonification","sound blueprint","audio mapping","pulse",
            "music","cinematic score","envelope","sound design"
        ],
        "general": [
            "explain","overview","understand","concept","meaning","why","how",
            "idea","structure","intuition","high level","summary"
        ],
    }

    _SIM_EXTRA_TRIGGERS = ["animate","animation","trajectory","3d orbit","ray-trace","particle","gpu simulation"]
    _IMG_EXTRA = ["see in this", "see in the image", "see in photo"]
    _SOUND_EXTRA = ["sound", "blueprint", "sonify", "sonification", "cinematic audio"]

    # ------------------------------------------------------------
    # MAIN COMPILE
    # ------------------------------------------------------------
    def compile(self, user_query: str, memory_brief: str, planner_plan: Dict[str, Any]) -> Dict[str, Any]:
        q = (user_query or "").strip()
        ql = q.lower()

        sa = planner_plan.get("self_awareness", {}) or {}

        # ENTRY SPECIALIST
        entry = planner_plan.get("entry_specialist") or self._pick_entry(sa, ql)

        # DETECT DOMAINS
        detected = self._detect_domains(ql, sa)

        # DIFFICULTY
        difficulty = self._difficulty(ql, detected, sa, memory_brief)

        # TEMPLATE PIPELINE
        template = self._pick_template(detected, difficulty, entry)

        # BUILD TASK GRAPH
        tasks = self._build_tasks(
            detected_domains=detected,
            entry_domain=entry,
            difficulty=difficulty,
            pipeline_template=template,
            memory_brief=memory_brief,
            sa=sa,
        )

        graph_ok, warnings = self._verify_graph(tasks)

        return {
            "tasks": tasks,
            "metadata": {
                "detected_domains": detected,
                "difficulty": difficulty,
                "entry_specialist": entry,
                "domain_count": len(detected),
                "pipeline_template": template,
                "graph_ok": graph_ok,
                "graph_warnings": warnings,
            }
        }

    # ------------------------------------------------------------
    # DOMAIN DETECTION (UPGRADED)
    # ------------------------------------------------------------
    def _detect_domains(self, q: str, sa: Dict[str, Any]) -> List[str]:
        out: Set[str] = set()

        for dom, kws in self.DOMAIN_MAP.items():
            if any(k in q for k in kws):
                out.add(dom)

        if any(w in q for w in self._SIM_EXTRA_TRIGGERS):
            out.add("simulation")
        if any(w in q for w in self._IMG_EXTRA):
            out.add("image")
        if any(w in q for w in self._SOUND_EXTRA):
            out.add("sound")

        # Always include general
        out.add("general")

        # SelfAwareness route recommendations
        sa_route = sa.get("ROUTING_SUGGESTION", {}) or {}
        if isinstance(sa_route, dict):
            rec = sa_route.get("recommended_domains")
            if isinstance(rec, str):
                rec = [x.strip() for x in rec.split(",") if x.strip()]
            if isinstance(rec, list):
                for r in rec:
                    out.add(r.lower())

            pref = sa_route.get("preferred_entry_domain")
            if isinstance(pref, str):
                out.add(pref.lower())

        return sorted(out)

    # ------------------------------------------------------------
    # DIFFICULTY ESTIMATION
    # ------------------------------------------------------------
    def _difficulty(self, q: str, doms: List[str], sa: Dict[str, Any], memory_brief: str) -> str:
        score = 0
        if len(doms) >= 4: score += 2
        if "math" in doms and "physics" in doms: score += 1
        if "simulation" in doms: score += 2
        if "sound" in doms: score += 1
        if "research" in doms: score += 1
        if len(q) > 250: score += 1
        if memory_brief and len(memory_brief) > 300: score += 1

        sa_task = sa.get("TASK_OVERVIEW", {}) or {}
        diff = str(sa_task.get("difficulty", "")).lower()
        score += {"low":0, "medium":1, "high":2, "extreme":3}.get(diff, 0)

        if score <= 1: return "easy"
        if score <= 3: return "medium"
        if score <= 5: return "hard"
        return "insane"

    # ------------------------------------------------------------
    # ENTRY SPECIALIST PICKER
    # ------------------------------------------------------------
    def _pick_entry(self, sa: Dict[str, Any], q: str) -> str:
        route = sa.get("ROUTING_SUGGESTION") or {}
        if isinstance(route, dict):
            pref = route.get("preferred_entry_domain")
            if isinstance(pref, str): return pref.lower()

        if "simulate" in q or "ray" in q: return "simulation"
        if "sound" in q: return "sound"
        if "python" in q or "code" in q: return "code"
        if "search" in q or "latest" in q: return "research"
        return "general"

    # ------------------------------------------------------------
    # PIPELINE TEMPLATE SELECTOR (UPGRADED)
    # ------------------------------------------------------------
    def _pick_template(self, doms: List[str], difficulty: str, entry: str) -> str:
        d = set(doms)

        if "simulation" in d and ("physics" in d or "math" in d):
            return "simulation_dominant"
        if "sound" in d and "simulation" in d:
            return "cine_audio_pipeline"
        if "research" in d:
            return "research_dominant"
        if difficulty in ("hard","insane"):
            return "multi_domain_heavy"
        return "default"

    # ------------------------------------------------------------
    # BUILD TASKS
    # ------------------------------------------------------------
    def _build_tasks(self, detected_domains, entry_domain, difficulty, pipeline_template, memory_brief, sa):
        tasks = []
        next_id = 1
        domain_ids = {}

        def add(dom, desc, pri, deps=None, tags=None):
            nonlocal next_id, tasks
            tid = next_id; next_id += 1
            t = {
                "id": tid,
                "domain": dom,
                "description": desc,
                "priority": pri,
                "depends_on": deps or [],
            }
            if tags: t["tags"] = tags
            tasks.append(t)
            domain_ids.setdefault(dom, []).append(tid)
            return tid

        # META
        meta_id = add("meta","SelfAwarenessLLM meta-analysis.",1,[],["self_awareness"])

        # GENERAL
        gen_id = add("general","Interpret query and break into sub-intents.",1,[meta_id])

        # MEMORY
        mem_id = add("memory","Retrieve episodic/semantic/sim/sound memory.",2,[meta_id, gen_id])

        # CORE DOMAINS
        for dom in ["math","physics","code","chemistry","biology"]:
            if dom in detected_domains:
                pri = 2 + (1 if difficulty in ("hard","insane") else 0)
                add(dom,f"{dom.upper()} reasoning.",pri,[meta_id, gen_id, mem_id],["core"])

        # SIMULATION
        if "simulation" in detected_domains:
            deps = [meta_id, gen_id, mem_id]
            deps += domain_ids.get("physics",[])
            deps += domain_ids.get("math",[]) if pipeline_template!="default" else []
            add("simulation","SimulationLLM (3D raymarch) run.",3,sorted(set(deps)),["sim"])

        # IMAGE
        if "image" in detected_domains:
            deps = [meta_id, gen_id, mem_id] + domain_ids.get("simulation",[])
            add("image","ImageLLM visual reasoning.",2,sorted(set(deps)),["vision"])

        # SOUND (NEW MODULE)
        if "sound" in detected_domains:
            deps = [meta_id, gen_id, mem_id]
            deps += domain_ids.get("simulation",[])  # allow sim → sound
            add("sound","SoundLLM V0-OpenSource blueprint generation.",3,sorted(set(deps)),["cine_audio"])

        # RESEARCH
        if "research" in detected_domains:
            deps = [meta_id, gen_id, mem_id]
            add("research","External evidence retrieval.",3,sorted(set(deps)),["evidence"])

        # FACTS VALIDATOR
        if "facts" in detected_domains:
            deps = [t["id"] for t in tasks]
            add("facts","Multi-domain fact consistency check.",4,sorted(deps),["validator"])

        # FINAL SYNTHESIS (entry specialist)
        all_ids = [t["id"] for t in tasks]
        add(entry_domain,
            "Synthesize all domain outputs into unified answer.",
            5,
            sorted(all_ids),
            ["synthesis"])

        return tasks

    # ------------------------------------------------------------
    # DAG CHECKER + AUTO-FIX
    # ------------------------------------------------------------
    def _verify_graph(self, tasks):
        warnings = []
        valid_ids = {t["id"] for t in tasks}

        # Fix invalid deps
        for t in tasks:
            t["depends_on"] = [d for d in t.get("depends_on",[]) if d in valid_ids and d!=t["id"]]

        # Build adjacency
        adj = {tid: [] for tid in valid_ids}
        for t in tasks:
            for d in t["depends_on"]:
                adj[d].append(t["id"])

        # Cycle detection
        visited = set()
        stack = set()
        has_cycle = False

        def dfs(u):
            nonlocal has_cycle
            visited.add(u)
            stack.add(u)
            for v in adj.get(u,[]):
                if v not in visited:
                    dfs(v)
                elif v in stack:
                    has_cycle = True
                    return
            stack.remove(u)

        for n in valid_ids:
            if n not in visited:
                dfs(n)
            if has_cycle:
                break

        # Auto-fix
        if has_cycle:
            warnings.append("Cycle detected → Reset to linear chain.")
            tasks_sorted = sorted(tasks, key=lambda x: x["id"])
            prev = None
            for t in tasks_sorted:
                t["depends_on"] = [] if prev is None else [prev]
                prev = t["id"]
            return False, warnings

        return True, warnings