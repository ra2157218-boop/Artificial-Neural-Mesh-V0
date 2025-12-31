# ============================================================
#  ANM V0-OpenSource — Internet Specialist
#  Real-Time Web Search & Information Retrieval
# ============================================================

"""
ANM Internet Specialist - Web Search & Information Retrieval

Capabilities:
- Real-time web search via multiple backends
- Content extraction from URLs
- Search result aggregation
- Source credibility assessment
- Fact verification support

Backends:
- DuckDuckGo (default, no API key needed)
- SerpAPI (optional, for Google results)
- Brave Search (optional)
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import hashlib
import time
from urllib.parse import urlparse, quote_plus

# Import base
from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
    run_model,
)

# Import prompt
try:
    from anm.utils.prompts import INTERNET_PROMPT
except ImportError:
    INTERNET_PROMPT = ""

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

__all__ = [
    "InternetLLM",
    "SearchResult",
    "SearchBackend",
    "WebSearcher",
]


class SearchBackend(Enum):
    """Available search backends."""
    DUCKDUCKGO = "duckduckgo"
    SERPAPI = "serpapi"
    BRAVE = "brave"


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    snippet: str
    url: str
    source: str
    rank: int = 0
    credibility: float = 0.5
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_text(self) -> str:
        """Convert to text for LLM."""
        return f"[{self.rank}] {self.title}\n    URL: {self.url}\n    {self.snippet}"


@dataclass
class SearchResponse:
    """Complete search response."""
    query: str
    results: List[SearchResult]
    total_found: int
    search_time_ms: float
    backend: str
    success: bool
    error: Optional[str] = None


class WebSearcher:
    """
    Multi-backend web search engine.
    
    Supports:
    - DuckDuckGo (default, no API key)
    - SerpAPI (needs API key for Google results)
    - Brave Search (needs API key)
    """
    
    def __init__(
        self,
        default_backend: SearchBackend = SearchBackend.DUCKDUCKGO,
        serpapi_key: Optional[str] = None,
        brave_key: Optional[str] = None,
        timeout: int = 10,
        max_results: int = 10,
    ):
        self.default_backend = default_backend
        self.serpapi_key = serpapi_key
        self.brave_key = brave_key
        self.timeout = timeout
        self.max_results = max_results
        
        # Result cache
        self._cache: Dict[str, SearchResponse] = {}
        self._cache_ttl = 300  # 5 minutes
    
    def search(
        self,
        query: str,
        backend: Optional[SearchBackend] = None,
        max_results: Optional[int] = None,
    ) -> SearchResponse:
        """
        Execute web search.
        
        Args:
            query: Search query
            backend: Which backend to use
            max_results: Max results to return
            
        Returns:
            SearchResponse with results
        """
        if not REQUESTS_AVAILABLE:
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                search_time_ms=0,
                backend="none",
                success=False,
                error="requests library not available",
            )
        
        backend = backend or self.default_backend
        max_results = max_results or self.max_results
        
        # Check cache
        cache_key = self._cache_key(query, backend)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Check if still valid
            if hasattr(cached, '_cache_time'):
                if time.time() - cached._cache_time < self._cache_ttl:
                    return cached
        
        start = time.perf_counter()
        
        try:
            if backend == SearchBackend.DUCKDUCKGO:
                response = self._search_duckduckgo(query, max_results)
            elif backend == SearchBackend.SERPAPI and self.serpapi_key:
                response = self._search_serpapi(query, max_results)
            elif backend == SearchBackend.BRAVE and self.brave_key:
                response = self._search_brave(query, max_results)
            else:
                # Fallback to DuckDuckGo
                response = self._search_duckduckgo(query, max_results)
            
            response.search_time_ms = (time.perf_counter() - start) * 1000
            
            # Cache result
            response._cache_time = time.time()
            self._cache[cache_key] = response
            
            return response
            
        except Exception as e:
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                search_time_ms=(time.perf_counter() - start) * 1000,
                backend=backend.value,
                success=False,
                error=str(e),
            )
    
    def _cache_key(self, query: str, backend: SearchBackend) -> str:
        """Generate cache key."""
        return hashlib.md5(f"{backend.value}:{query.lower()}".encode()).hexdigest()
    
    def _search_duckduckgo(self, query: str, max_results: int) -> SearchResponse:
        """Search using DuckDuckGo - try duckduckgo-search library first, fallback to Instant Answer API."""
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "Starting DuckDuckGo web search", "data": {"query": query, "max_results": max_results}, "timestamp": int(time.time() * 1000)}) + "\n")
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
                    results_list = list(ddg_results)
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "duckduckgo-search library available, using web search", "data": {"results_count": len(results_list)}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            results: List[SearchResult] = []
            rank = 1
            for result in ddg_results:
                if len(results) >= max_results:
                    break
                results.append(SearchResult(
                    title=result.get("title", "")[:200],
                    snippet=result.get("body", "")[:500],
                    url=result.get("href", ""),
                    source="duckduckgo_web",
                    rank=rank,
                    credibility=0.8,
                ))
                rank += 1
            
            if results:
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        import json
                        import time
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "duckduckgo-search returned results", "data": {"results_count": len(results), "first_title": results[0].title[:100] if results else "none"}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                return SearchResponse(
                    query=query,
                    results=results,
                    total_found=len(results),
                    search_time_ms=0,
                    backend="duckduckgo",
                    success=True,
                )
        except ImportError:
            # duckduckgo-search not installed, fall back to Instant Answer API
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "duckduckgo-search not available, falling back to Instant Answer API", "data": {}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "duckduckgo-search failed, falling back to Instant Answer API", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
        
        # Fallback: Use Instant Answer API (limited, but better than nothing)
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "no_redirect": "1",
        }
        
        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            data = r.json()

            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "Instant Answer API response", "data": {"has_abstract": bool(data.get("Abstract")), "related_topics_count": len(data.get("RelatedTopics", [])), "data_keys": list(data.keys())}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "Instant Answer API request failed", "data": {"error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                search_time_ms=0,
                backend="duckduckgo",
                success=False,
                error=str(e),
            )
        
        results: List[SearchResult] = []
        rank = 1
        
        # Abstract (main answer)
        if data.get("Abstract"):
            results.append(SearchResult(
                title=data.get("Heading", "DuckDuckGo Answer"),
                snippet=data["Abstract"][:500],
                url=data.get("AbstractURL", ""),
                source="duckduckgo_abstract",
                rank=rank,
                credibility=0.7,
            ))
            rank += 1
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if "Topics" in topic:
                # Nested topics
                for sub in topic.get("Topics", [])[:3]:
                    if len(results) >= max_results:
                        break
                    text = sub.get("Text", "")
                    if text:
                        results.append(SearchResult(
                            title=text[:100],
                            snippet=text[:300],
                            url=sub.get("FirstURL", ""),
                            source="duckduckgo_related",
                            rank=rank,
                            credibility=0.6,
                        ))
                        rank += 1
            elif "Text" in topic:
                if len(results) >= max_results:
                    break
                text = topic.get("Text", "")
                results.append(SearchResult(
                    title=text[:100],
                    snippet=text[:300],
                    url=topic.get("FirstURL", ""),
                    source="duckduckgo_related",
                    rank=rank,
                    credibility=0.6,
                ))
                rank += 1
        
        # Infobox results
        if data.get("Infobox"):
            for content in data["Infobox"].get("content", [])[:3]:
                if len(results) >= max_results:
                    break
                label = content.get("label", "")
                value = content.get("value", "")
                if label and value:
                    results.append(SearchResult(
                        title=f"{label}: {value}",
                        snippet=f"{label} is {value}",
                        url=data.get("AbstractURL", ""),
                        source="duckduckgo_infobox",
                        rank=rank,
                        credibility=0.8,
                    ))
                    rank += 1
        
        if not results:
            # #region agent log
            try:
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    import json
                    import time
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "No results from DuckDuckGo Instant Answer API", "data": {"query": query, "has_abstract": bool(data.get("Abstract")), "topics_count": len(data.get("RelatedTopics", []))}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                search_time_ms=0,
                backend="duckduckgo",
                success=False,
                error="No results found. DuckDuckGo Instant Answer API only works for very specific queries. Install 'duckduckgo-search' for proper web search: pip install duckduckgo-search",
            )
        
        # #region agent log
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                import json
                import time
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "DUCKDUCKGO_WEB", "location": "internet_llm.py:_search_duckduckgo", "message": "DuckDuckGo search completed", "data": {"results_count": len(results), "sources": [r.source for r in results]}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        
        return SearchResponse(
            query=query,
            results=results,
            total_found=len(results),
            search_time_ms=0,
            backend="duckduckgo",
            success=True,
        )
    
    def _search_serpapi(self, query: str, max_results: int) -> SearchResponse:
        """Search using SerpAPI (Google results)."""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "engine": "google",
            "num": max_results,
        }
        
        r = requests.get(url, params=params, timeout=self.timeout)
        data = r.json()
        
        results: List[SearchResult] = []
        rank = 1
        
        # Organic results
        for item in data.get("organic_results", [])[:max_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                source="google",
                rank=rank,
                credibility=self._assess_credibility(item.get("link", "")),
            ))
            rank += 1
        
        # Answer box
        if data.get("answer_box"):
            box = data["answer_box"]
            results.insert(0, SearchResult(
                title=box.get("title", "Google Answer"),
                snippet=box.get("answer", box.get("snippet", "")),
                url=box.get("link", ""),
                source="google_answer_box",
                rank=0,
                credibility=0.9,
            ))
        
        return SearchResponse(
            query=query,
            results=results,
            total_found=data.get("search_information", {}).get("total_results", len(results)),
            search_time_ms=0,
            backend="serpapi",
            success=True,
        )
    
    def _search_brave(self, query: str, max_results: int) -> SearchResponse:
        """Search using Brave Search API."""
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": self.brave_key,
        }
        params = {
            "q": query,
            "count": max_results,
        }
        
        r = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        data = r.json()
        
        results: List[SearchResult] = []
        rank = 1
        
        for item in data.get("web", {}).get("results", [])[:max_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                snippet=item.get("description", ""),
                url=item.get("url", ""),
                source="brave",
                rank=rank,
                credibility=self._assess_credibility(item.get("url", "")),
            ))
            rank += 1
        
        return SearchResponse(
            query=query,
            results=results,
            total_found=len(results),
            search_time_ms=0,
            backend="brave",
            success=True,
        )
    
    def _assess_credibility(self, url: str) -> float:
        """Assess URL credibility."""
        if not url:
            return 0.3
        
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            return 0.3
        
        # High credibility domains
        high_cred = [
            "wikipedia.org", "britannica.com", "nature.com",
            "science.org", "sciencedirect.com", "ncbi.nlm.nih.gov",
            "pubmed.gov", "arxiv.org", "gov", "edu",
        ]
        
        for hc in high_cred:
            if hc in domain:
                return 0.9
        
        # Medium credibility
        medium_cred = [
            "medium.com", "stackoverflow.com", "github.com",
            "bbc.com", "nytimes.com", "theguardian.com",
        ]
        
        for mc in medium_cred:
            if mc in domain:
                return 0.7
        
        return 0.5


class InternetLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Internet Specialist.
    
    Responsibilities:
    - Execute web searches based on query
    - Aggregate and analyze search results
    - Extract relevant information
    - Assess source credibility
    - Provide structured findings
    
    Does NOT:
    - Fabricate URLs or citations
    - Claim certainty about unverified info
    - Make up sources that don't exist
    """
    
    def __init__(
        self,
        config: Optional[SpecialistConfig] = None,
        searcher: Optional[WebSearcher] = None,
        serpapi_key: Optional[str] = None,
        brave_key: Optional[str] = None,
        **kwargs,
    ):
        # Initialize searcher
        self.searcher = searcher or WebSearcher(
            serpapi_key=serpapi_key,
            brave_key=brave_key,
        )
        
        super().__init__(config=config, **kwargs)
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.INTERNET
    
    def _get_system_prompt(self) -> str:
        # Use INTERNET_PROMPT from prompts.py (single source of truth)
        return INTERNET_PROMPT if INTERNET_PROMPT else ""
    
    def run(self, wot_packet: str) -> str:
        """
        Process query with web search.
        """
        start_time = time.perf_counter()
        
        # Extract search query
        search_query = self._extract_search_query(wot_packet)
        
        # Perform search
        search_response = self.searcher.search(search_query, max_results=8)
        
        # Format results for LLM
        results_text = self._format_results(search_response)
        
        # Build prompt
        prompt = self._build_analysis_prompt(wot_packet, search_query, results_text)
        
        # Run LLM analysis
        raw_output = run_model(prompt, max_tokens=self.config.max_tokens)
        
        # Clean and format
        cleaned = self._clean_output(raw_output)
        cleaned = self._ensure_wot_request(cleaned)
        
        # Add search metadata
        meta = self._build_search_meta(search_response)
        
        # Combine
        final = self._attach_meta(cleaned, meta)
        
        # Log
        processing_time = (time.perf_counter() - start_time) * 1000
        self._log_to_memory(final, processing_time)
        
        return final
    
    def _extract_search_query(self, wot_packet: str) -> str:
        """Extract search query from WoT packet."""
        # Look for USER_QUERY
        for line in wot_packet.split("\n"):
            if "USER_QUERY:" in line:
                query = line.split("USER_QUERY:", 1)[1].strip()
                if query:
                    return query
        
        # Look for SEARCH_QUERY
        for line in wot_packet.split("\n"):
            if "SEARCH_QUERY:" in line:
                query = line.split("SEARCH_QUERY:", 1)[1].strip()
                if query:
                    return query
        
        # Use first meaningful content
        lines = [l.strip() for l in wot_packet.split("\n") if l.strip()]
        for line in lines:
            if len(line) > 10 and not line.startswith("[") and not line.startswith("==="):
                return line[:200]
        
        return wot_packet[:200]
    
    def _format_results(self, response: SearchResponse) -> str:
        """Format search results for LLM."""
        if not response.success:
            return f"[SEARCH ERROR: {response.error}]"
        
        if not response.results:
            return "[NO RESULTS FOUND]"
        
        lines = [
            f"Search Query: {response.query}",
            f"Backend: {response.backend}",
            f"Results Found: {len(response.results)}",
            f"Search Time: {response.search_time_ms:.0f}ms",
            "",
            "=== SEARCH RESULTS ===",
        ]
        
        for result in response.results:
            lines.append(f"\n[{result.rank}] {result.title}")
            lines.append(f"    URL: {result.url}")
            lines.append(f"    Source: {result.source}")
            lines.append(f"    Credibility: {result.credibility:.1f}")
            lines.append(f"    Snippet: {result.snippet}")
        
        return "\n".join(lines)
    
    def _build_analysis_prompt(
        self,
        wot_packet: str,
        search_query: str,
        results_text: str,
    ) -> str:
        """Build the analysis prompt."""
        return f"""
{self._system_prompt}

--- ORIGINAL REQUEST ---
{wot_packet[:1500]}

--- SEARCH QUERY ---
{search_query}

--- SEARCH RESULTS ---
{results_text}

--- YOUR TASK ---
Analyze these search results and provide:
1. KEY FINDINGS: What did we learn? (cite sources)
2. CONSENSUS: What do sources agree on?
3. DISAGREEMENTS: Any conflicting information?
4. CREDIBILITY: How reliable are these sources?
5. GAPS: What's still unknown?

Then decide if more research is needed or route to appropriate specialist.

End with: WOT_REQUEST: <DOMAIN or NONE>
"""
    
    def _build_search_meta(self, response: SearchResponse) -> str:
        """Build search metadata block."""
        lines = [
            "[INTERNET_SEARCH]",
            f"query: {response.query}",
            f"backend: {response.backend}",
            f"results_found: {len(response.results)}",
            f"search_time_ms: {response.search_time_ms:.0f}",
            f"success: {response.success}",
        ]
        
        if response.error:
            lines.append(f"error: {response.error}")
        
        # Credibility summary
        if response.results:
            avg_cred = sum(r.credibility for r in response.results) / len(response.results)
            lines.append(f"avg_credibility: {avg_cred:.2f}")
        
        lines.append("")
        lines.append("[DOMAIN_HEALTH]")
        lines.append("domain: internet")
        lines.append(f"version: {self.VERSION}")
        
        return "\n".join(lines)
    
    def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """
        Direct search without LLM analysis.
        Useful for other specialists needing quick lookup.
        """
        return self.searcher.search(query, max_results=max_results)
