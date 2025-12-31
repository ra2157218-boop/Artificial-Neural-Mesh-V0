# anm/specialists/research_llm.py
# ======================================================================
# ANM V0-OpenSource — RESEARCH SPECIALIST V0-OpenSource (V0-OpenSource)
#  Strict • Zero-Fallback • GRE V0-OpenSource • Self-Awareness • Diagnostics v3
#  DuckDuckGo (default backend) • Evidence-Only Aggregator
#  INTERNAL USE ONLY • No final user-facing answers
#  Always ends with single: WOT_REQUEST: <DOMAIN or NONE>
# ======================================================================

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from anm.rules.global_rule_engine import GlobalRulesEngine
from anm.specialists.selfawareness_llm import SelfAwarenessLLM
from anm.memory.working_memory import WorkingMemory
from anm.memory.meta_memory import MetaMemory
from anm.system.inference import run_model
from anm.utils.output_utils import clean_output, normalize_text

try:
    from anm.utils.prompts import RESEARCH_PROMPT
except ImportError:
    RESEARCH_PROMPT = ""


# ======================================================================
#  HIT DATA STRUCTURE
# ======================================================================

@dataclass
class ResearchHit:
    """
    Single search hit from any research backend.
    Pure data — no interpretation.
    """

    id: str
    title: str
    snippet: str
    url: Optional[str] = None
    score: float = 1.0
    source: str = "duckduckgo"


# ======================================================================
#  BACKEND BASE CLASS
# ======================================================================

class BaseResearchBackend(ABC):
    """
    Abstract interface for research backends.
    Implementations:
      - DuckDuckGoBackend (default)
      - (Future) LocalCorpusBackend, BingBackend, etc.
    """

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[ResearchHit]:
        """Search for research hits. Must be implemented by subclasses."""
        pass


# ======================================================================
#  DUCKDUCKGO BACKEND (DEFAULT)
# ======================================================================

class DuckDuckGoBackend(BaseResearchBackend):
    """
    Thin wrapper over DuckDuckGo's instant answer API.

    NOTE:
      - No guarantee of completeness or recency.
      - Used ONLY as a rough evidence fetcher for ResearchLLM.
    """

    API_URL = "https://api.duckduckgo.com/"

    def search(self, query: str, max_results: int = 5) -> List[ResearchHit]:
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "Starting DuckDuckGo search", "data": {"query": query, "max_results": max_results}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        # Try duckduckgo-search library first (proper web search)
        try:
            import duckduckgo_search
            ddg_results = duckduckgo_search.DDGS().text(query, max_results=max_results)
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "duckduckgo-search library available, using web search", "data": {"results_count": len(list(ddg_results)) if ddg_results else 0}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            hits: List[ResearchHit] = []
            for result in ddg_results:
                if len(hits) >= max_results:
                    break
                hits.append(
                    ResearchHit(
                        id=str(uuid.uuid4()),
                        title=result.get("title", "")[:260],
                        snippet=result.get("body", "")[:500],
                        url=result.get("href"),
                        score=1.0,
                        source="duckduckgo_web",
                    )
                )
            
            if hits:
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        import time
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "duckduckgo-search returned results", "data": {"hits_count": len(hits), "first_title": hits[0].title[:100] if hits else "none"}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                return hits
        except ImportError:
            # duckduckgo-search not installed, fall back to Instant Answer API
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "duckduckgo-search not available, falling back to Instant Answer API", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "duckduckgo-search failed, falling back to Instant Answer API", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
        
        # Fallback: Use Instant Answer API (limited, but better than nothing)
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "no_redirect": "1",
        }

        try:
            r = requests.get(self.API_URL, params=params, timeout=6)
            data = r.json()
            
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "Instant Answer API response", "data": {"has_abstract": bool(data.get("Abstract")), "related_topics_count": len(data.get("RelatedTopics", [])), "data_keys": list(data.keys())}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "Instant Answer API request failed", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            return [
                ResearchHit(
                    id=str(uuid.uuid4()),
                    title="DuckDuckGo Error",
                    snippet=f"Search failed: {str(e)}",
                    url=None,
                    score=0.0,
                    source="duckduckgo",
                )
            ]

        hits: List[ResearchHit] = []
        
        # Check for Abstract (instant answer)
        if data.get("Abstract"):
            hits.append(
                ResearchHit(
                    id=str(uuid.uuid4()),
                    title=data.get("Heading", "DuckDuckGo Answer")[:260],
                    snippet=data["Abstract"][:500],
                    url=data.get("AbstractURL"),
                    score=0.9,
                    source="duckduckgo_instant",
                )
            )
        
        topics = data.get("RelatedTopics", []) or []

        for t in topics:
            # Nested topics
            if "Topics" in t:
                for sub in t.get("Topics", []):
                    txt = sub.get("Text", "") or ""
                    url = sub.get("FirstURL")
                    if not txt:
                        continue
                    hits.append(
                        ResearchHit(
                            id=str(uuid.uuid4()),
                            title=txt[:260],
                            snippet=txt[:500],
                            url=url,
                            source="duckduckgo",
                        )
                    )
                    if len(hits) >= max_results:
                        return hits

            # Flat topic
            elif "Text" in t:
                txt = t.get("Text", "") or ""
                url = t.get("FirstURL")
                if not txt:
                    continue
                hits.append(
                    ResearchHit(
                        id=str(uuid.uuid4()),
                        title=txt[:260],
                        snippet=txt[:500],
                        url=url,
                        source="duckduckgo",
                    )
                )
                if len(hits) >= max_results:
                    return hits

        if not hits:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "No results from DuckDuckGo", "data": {"query": query, "has_abstract": bool(data.get("Abstract")), "topics_count": len(topics)}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            hits.append(
                ResearchHit(
                    id=str(uuid.uuid4()),
                    title="No Results",
                    snippet=f"DuckDuckGo returned no results for: {query}. The Instant Answer API only works for very specific queries. Consider installing 'duckduckgo-search' library for proper web search: pip install duckduckgo-search",
                    url=None,
                    score=0.0,
                    source="duckduckgo",
                )
            )
        else:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_SEARCH", "location": "research_llm.py:DuckDuckGoBackend.search", "message": "DuckDuckGo search completed", "data": {"hits_count": len(hits), "sources": [h.source for h in hits]}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion

        return hits


# ======================================================================
#  RESEARCH SPECIALIST V0-OpenSource (V0-OpenSource)
# ======================================================================

class ResearchLLM:
    """
    Research Specialist for ANM V0-OpenSource True Web-of-Thought (V0-OpenSource).

    RESPONSIBILITIES:
      - Run external search (DuckDuckGo or other backend).
      - Aggregate hits into structured evidence (themes, consensus, conflict).
      - Detect contradictions, uncertainty, and speculation.
      - NEVER invent data, URLs, or citations.
      - NEVER output final user-facing answers.
      - ALWAYS end with a single WOT_REQUEST line.

    META:
      - Uses GlobalRulesEngine (if wired).
      - Uses SelfAwarenessLLM (if wired).
      - Logs to WorkingMemory + MetaMemory (if wired).
      - Emits RESEARCH_DIAGNOSTICS + DOMAIN_HEALTH + GLOBAL_RULES + POINTGAME_FEEDBACK.
    """

    def __init__(
        self,
        backend: Optional[BaseResearchBackend] = None,
        model_name: str = "deepseek-r1:1.5b",
        gre: Optional[GlobalRulesEngine] = None,
        self_awareness_llm: Optional[SelfAwarenessLLM] = None,
        working_memory: Optional[WorkingMemory] = None,
        meta_memory: Optional[MetaMemory] = None,
        research_kb=None,
    ) -> None:

        self.backend = backend or DuckDuckGoBackend()
        self.model = model_name

        # STRICT meta modules (no silent fallbacks)
        self.gre = gre
        self.selfaware = self_awareness_llm
        self.working_memory = working_memory
        self.meta_memory = meta_memory

        # Research Knowledge Base (optional)
        self.research_kb = research_kb

        self.system_prefix = self._system_prefix()

    # ==================================================================
    #  SYSTEM PREFIX
    # ==================================================================

    def _system_prefix(self) -> str:
        # Use RESEARCH_PROMPT from prompts.py (single source of truth)
        # RESEARCH_PROMPT already includes META-COGNITION, META-EFFICIENCY, and OUTPUT format
        return RESEARCH_PROMPT if RESEARCH_PROMPT else ""

    # ==================================================================
    #  MAIN EXECUTION (TrueWoT entry)
    # ==================================================================

    def run(self, wot_packet: str) -> str:
        """
        Main entry point called by Router / TrueWoT.

        INPUT:
          - wot_packet: full WoT packet (user query + context).

        PROCESS:
          - Extract a search query.
          - Check research KB for related past research (RAG).
          - Fetch hits via backend (evidence only).
          - Provide hits + context + past research to DeepSeek for analysis.
          - Build META block (GRE + Self-Awareness + Diagnostics).
          - Attach META + final WOT_REQUEST line.

        OUTPUT:
          - Internal reasoning text + META + single WOT_REQUEST line.
        """
        query = self._extract_query_from_wot_packet(wot_packet)

        # Check for related past research (RAG)
        past_research_context = ""
        if self.research_kb and self.research_kb.is_available():
            try:
                past_research_summary = self.research_kb.get_research_summary(
                    query=query,
                    limit=3,
                )
                if past_research_summary:
                    past_research_context = (
                        "\n\n--- RELATED PAST RESEARCH (KNOWLEDGE BASE) ---\n"
                        + past_research_summary
                        + "\n[Use this to avoid repeating research and build on past findings]\n"
                    )
            except Exception as e:
                # Non-critical, continue without past research
                pass

        # Research Mode: Fetch 50-200 results for comprehensive research (per user requirement)
        # Use 100 as default for balanced coverage (min 50, max 200)
        # Adjust based on query complexity
        query_length = len(query)
        if query_length > 200:  # Complex queries get more results
            max_results = min(200, max(50, query_length // 2))
        else:
            max_results = 100  # Default for standard queries
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "RESEARCH_RESULTS", "location": "research_llm.py:run", "message": "Fetching comprehensive research results", "data": {"max_results": max_results, "query_length": query_length}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        try:
            hits = self.backend.search(query, max_results=max_results)
        except Exception as e:
            hits = [
                ResearchHit(
                    id=str(uuid.uuid4()),
                    title="Backend Error",
                    snippet=str(e),
                    url=None,
                    score=0.0,
                    source="backend",
                )
            ]

        search_dump = self._format_hits(hits)

        prompt = (
            self.system_prefix
            + "\n\n--- WoT PACKET (RESEARCH VIEW) ---\n"
            + wot_packet
            + "\n\n--- SEARCH QUERY (DERIVED) ---\n"
            + query[:500]
            + past_research_context
            + "\n\n--- SEARCH RESULTS (RAW EVIDENCE) ---\n"
            + search_dump
            + "\n\nRespond ONLY with research reasoning + final WOT_REQUEST.\n"
              "Do NOT fabricate any additional sources, citations, or URLs."
        )

        raw = run_model(prompt, max_tokens=2048)
        cleaned = self._clean_output(raw)

        meta_text, gre_snapshot, awareness_snapshot = self._build_meta(
            cleaned, hits=hits, query=query
        )
        final = self._attach_meta(cleaned, meta_text)

        # Memory hooks (non-fatal)
        self._log_to_working_memory(cleaned, gre_snapshot, awareness_snapshot, query)
        self._log_to_meta_memory(cleaned, gre_snapshot, awareness_snapshot, query)

        return final

    # ==================================================================
    #  QUERY EXTRACTOR (WoT-safe)
    # ==================================================================

    def _extract_query_from_wot_packet(self, wot_packet: str) -> str:
        """
        Tries to locate a USER_QUERY: line inside the WoT packet.
        If not found, falls back to the full packet (truncated).
        """
        lines = wot_packet.splitlines()
        for ln in lines:
            if "USER_QUERY:" in ln:
                after = ln.split("USER_QUERY:", 1)[1].strip()
                if after:
                    return after
        return wot_packet.strip()[:800] or "general research query"

    # ==================================================================
    #  HIT FORMATTER
    # ==================================================================

    def _format_hits(self, hits: List[ResearchHit]) -> str:
        """
        Build a plain-text dump of results, safe for LLM.
        """
        parts: List[str] = []

        for h in hits:
            parts.append(f"- ID: {h.id}")
            parts.append(f"  SOURCE: {h.source}")
            parts.append(f"  TITLE: {h.title}")
            parts.append(f"  SNIPPET: {h.snippet}")
            parts.append(f"  URL: {h.url if h.url else 'None'}")
            parts.append("")

        return "\n".join(parts).strip()

    # ==================================================================
    #  META BLOCK (Self-Awareness + GRE + Diagnostics v3)
    # ==================================================================

    def _build_meta(
        self,
        text: str,
        hits: List[ResearchHit],
        query: str,
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:

        # ----- Self-Awareness -----
        awareness: Dict[str, Any] = {
            "confidence": "unknown",
            "uncertainty": "unknown",
            "notes": "",
            "source": "SelfAwarenessLLM" if self.selfaware is not None else "unavailable",
        }

        if self.selfaware is not None:
            try:
                sa = self.selfaware.analyze("research", text)
                if isinstance(sa, dict):
                    for k in ("confidence", "uncertainty", "notes"):
                        if k in sa:
                            awareness[k] = sa[k]
            except Exception as e:
                awareness["notes"] = f"Self-awareness error: {e}"

        # ----- GRE -----
        if self.gre is not None:
            try:
                gre = self.gre.analyze(text, module_name="ResearchLLM")
            except Exception as e:
                gre = {
                    "passed": False,
                    "risk_level": "medium",
                    "violations": ["gre_internal_error"],
                    "penalty": 1,
                    "self_reflection": f"GRE crashed: {e}",
                }
        else:
            gre = {
                "passed": True,
                "risk_level": "unknown",
                "violations": ["gre_unavailable"],
                "penalty": 0,
                "self_reflection": "GRE unavailable for ResearchLLM",
            }

        diagn = self._diagnostics(text, hits, query)

        viol = ", ".join(gre.get("violations", []) or []) or "none"
        success = "yes" if gre.get("passed") else "no"

        lines: List[str] = []
        lines.append("[DOMAIN_HEALTH]")
        lines.append(f"confidence: {awareness['confidence']}")
        lines.append(f"uncertainty: {awareness['uncertainty']}")
        if awareness["notes"]:
            lines.append(f"notes: {awareness['notes']}")
        lines.append(f"source: {awareness['source']}")
        lines.append("")
        lines.append("[GLOBAL_RULES]")
        lines.append(f"passed: {gre.get('passed')}")
        lines.append(f"risk_level: {gre.get('risk_level')}")
        lines.append(f"violations: {viol}")
        lines.append(f"penalty: {gre.get('penalty')}")
        lines.append(f"self_reflection: {gre.get('self_reflection')}")
        lines.append("")
        lines.append("[RESEARCH_DIAGNOSTICS]")
        for k, v in diagn.items():
            lines.append(f"{k}: {v}")
        lines.append("")
        lines.append("[POINTGAME_FEEDBACK]")
        lines.append(f"success_signal: {success}")
        lines.append(f"reason: {gre.get('self_reflection')}")

        meta_text = "\n".join(lines).strip()
        return meta_text, gre, awareness

    # ==================================================================
    #  RESEARCH DIAGNOSTICS v3
    # ==================================================================

    def _diagnostics(
        self,
        text: str,
        hits: List[ResearchHit],
        query: str,
    ) -> Dict[str, str]:
        lower = text.lower()

        evidence_count = len(hits)
        error_hits = [h for h in hits if "error" in (h.title or "").lower()]
        no_result_hits = [h for h in hits if "no results" in (h.title or "").lower()]

        return {
            "evidence_count": str(evidence_count),
            "error_hits": str(len(error_hits)),
            "no_result_hits": str(len(no_result_hits)),
            "evidence_strength": (
                "weak"
                if evidence_count <= 1 or "no evidence" in lower
                else "ok"
            ),
            "contradiction_detected": (
                "yes" if any(x in lower for x in ["contradiction", "conflicting"]) else "no"
            ),
            "speculation_risk": (
                "high"
                if any(x in lower for x in ["uncertain", "disputed", "speculative"])
                else "low"
            ),
            "noise_level": (
                "high" if "irrelevant" in lower or "noise" in lower else "normal"
            ),
            "url_quality": (
                "low"
                if any((h.url is None or h.url == "None") for h in hits)
                else "ok"
            ),
            "query_ambiguity": (
                "high"
                if len(query.split()) <= 2 or "general research query" in query.lower()
                else "normal"
            ),
        }

    # ==================================================================
    #  CLEAN OUTPUT
    # ==================================================================

    def _clean_output(self, text: str) -> str:
        """
        Clean output using centralized utilities.
        Ensure at least one WOT_REQUEST line exists.
        """
        if not text:
            return "WOT_REQUEST: NONE"

        # Use centralized cleaning utility
        t = clean_output(
            text,
            domain_name="research",
            clean_thinking=True,
            remove_role_prefixes=True,
        )

        if "</think>" in t:
            t = t.split("</think>", 1)[-1].strip()

        # Compress triple blank lines
        while "\n\n\n" in t:
            t = t.replace("\n\n\n", "\n\n")

        lines = [ln for ln in t.splitlines() if ln.strip()]

        # Ensure at least one WOT_REQUEST
        if not any(ln.startswith("WOT_REQUEST:") for ln in lines):
            lines.append("WOT_REQUEST: NONE")

        return "\n".join(lines).strip()

    # ==================================================================
    #  META ATTACHER
    # ==================================================================

    def _attach_meta(self, cleaned: str, meta: str) -> str:
        """
        Attach META block just before a single final WOT_REQUEST line.
        """
        lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
        body: List[str] = []
        final_wot: Optional[str] = None

        for ln in lines:
            if ln.startswith("WOT_REQUEST:"):
                final_wot = ln
            else:
                body.append(ln)

        if final_wot is None:
            final_wot = "WOT_REQUEST: NONE"

        body_text = "\n".join(body)
        final = body_text + "\n\n" + meta + "\n\n" + final_wot
        return final.strip()

    # ==================================================================
    #  WORKING MEMORY LOGGING (non-fatal)
    # ==================================================================

    def _log_to_working_memory(
        self,
        cleaned: str,
        gre_res: Dict[str, Any],
        awareness: Dict[str, Any],
        query: str,
    ) -> None:
        if not self.working_memory:
            return

        try:
            self.working_memory.add(
                domain="research",
                note="ResearchLLM V0-OpenSource processed research packet.",
                meta={
                    "passed_gre": gre_res.get("passed"),
                    "risk_level": gre_res.get("risk_level"),
                    "violations": gre_res.get("violations", []),
                    "confidence": awareness.get("confidence"),
                    "uncertainty": awareness.get("uncertainty"),
                    "query": query,
                },
            )
        except Exception:
            return

    # ==================================================================
    #  META MEMORY LOGGING (non-fatal)
    # ==================================================================

    def _log_to_meta_memory(
        self,
        cleaned: str,
        gre_res: Dict[str, Any],
        awareness: Dict[str, Any],
        query: str,
    ) -> None:
        if not self.meta_memory:
            return

        try:
            risk = str(gre_res.get("risk_level", "unknown"))
            self.meta_memory.store_pattern(
                module="ResearchLLM",
                pattern=(
                    f"ResearchLLM V0-OpenSource run: passed={gre_res.get('passed')}, "
                    f"risk={risk}, violations={gre_res.get('violations', [])}, "
                    f"query='{query[:80]}'"
                ),
                risk_level=risk,
                tags=["research", "evidence", "domain_health"],
                extra={
                    "confidence": awareness.get("confidence"),
                    "uncertainty": awareness.get("uncertainty"),
                },
            )
        except Exception:
            return