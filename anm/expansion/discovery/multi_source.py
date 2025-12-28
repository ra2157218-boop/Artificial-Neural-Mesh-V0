# ============================================================
# ANM V0-OpenSource — MULTI-SOURCE DISCOVERY (MAXIMUM LEVEL)
#  Parallel Multi-Source Search • Quality Scoring • Ranking
#  Caching • Rate Limiting • Retry Logic
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import os
import hashlib


@dataclass
class DiscoveredDataset:
    """Rich dataset information."""
    name: str
    source: str  # huggingface, kaggle, github, arxiv, etc.
    url: Optional[str]
    description: str
    size_mb: Optional[float]
    license: Optional[str]
    quality_score: float
    relevance_score: float
    download_url: Optional[str]
    format: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def combined_score(self) -> float:
        return (self.quality_score * 0.4 + self.relevance_score * 0.6)


@dataclass
class DiscoveryResult:
    """Complete discovery result."""
    success: bool
    domain: str
    total_found: int
    datasets: List[DiscoveredDataset]
    sources_searched: List[str]
    errors: List[str]
    search_time_ms: float
    cached: bool = False


class DataSourceBase:
    """Base class for data sources."""
    name: str = "base"
    
    def search(self, query: str, domain: str, max_results: int = 10) -> List[DiscoveredDataset]:
        raise NotImplementedError


class MultiSourceDiscovery:
    """
    MAXIMUM LEVEL Multi-Source Dataset Discovery.
    
    Features:
    - Parallel search across multiple sources
    - Intelligent relevance scoring
    - Quality assessment
    - Result caching
    - Rate limiting
    - Automatic retry
    - Source priority weighting
    """
    
    def __init__(
        self,
        sources: Optional[List[DataSourceBase]] = None,
        cache_dir: str = ".anm_cache/discovery",
        max_workers: int = 4,
        cache_ttl_hours: int = 24,
    ):
        self.sources = sources or self._get_default_sources()
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl_hours * 3600
        
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_default_sources(self) -> List[DataSourceBase]:
        """Get default data sources."""
        from anm.expansion.discovery.sources import (
            HuggingFaceSource,
            KaggleSource,
            GitHubSource,
            ArxivSource,
        )
        return [
            HuggingFaceSource(),
            KaggleSource(),
            GitHubSource(),
            ArxivSource(),
        ]
    
    def discover(
        self,
        domain: str,
        user_query: str,
        max_results_per_source: int = 10,
        min_quality_score: float = 0.3,
    ) -> DiscoveryResult:
        """
        Discover datasets from all sources in parallel.
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(domain, user_query)
        cached_result = self._load_cache(cache_key)
        if cached_result:
            cached_result.cached = True
            return cached_result
        
        # Search all sources in parallel
        all_datasets: List[DiscoveredDataset] = []
        errors: List[str] = []
        sources_searched: List[str] = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for source in self.sources:
                future = executor.submit(
                    self._search_source,
                    source,
                    domain,
                    user_query,
                    max_results_per_source,
                )
                futures[future] = source.name
            
            for future in as_completed(futures, timeout=60.0):
                source_name = futures[future]
                sources_searched.append(source_name)
                
                try:
                    datasets = future.result(timeout=10.0)
                    all_datasets.extend(datasets)
                except Exception as e:
                    errors.append(f"{source_name}: {str(e)}")
        
        # Filter by quality
        filtered = [d for d in all_datasets if d.quality_score >= min_quality_score]
        
        # Sort by combined score
        filtered.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Calculate relevance scores
        for dataset in filtered:
            dataset.relevance_score = self._calculate_relevance(dataset, domain, user_query)
        
        # Re-sort with updated relevance
        filtered.sort(key=lambda x: x.combined_score, reverse=True)
        
        search_time = (time.time() - start_time) * 1000
        
        result = DiscoveryResult(
            success=len(filtered) > 0,
            domain=domain,
            total_found=len(filtered),
            datasets=filtered,
            sources_searched=sources_searched,
            errors=errors,
            search_time_ms=search_time,
        )
        
        # Cache result
        self._save_cache(cache_key, result)
        
        return result
    
    def _search_source(
        self,
        source: DataSourceBase,
        domain: str,
        user_query: str,
        max_results: int,
    ) -> List[DiscoveredDataset]:
        """Search a single source with retry logic."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                return source.search(user_query, domain, max_results)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        return []
    
    def _calculate_relevance(
        self,
        dataset: DiscoveredDataset,
        domain: str,
        user_query: str,
    ) -> float:
        """Calculate relevance score for a dataset."""
        score = 0.5
        
        # Domain match in name
        if domain.lower() in dataset.name.lower():
            score += 0.3
        
        # Domain match in description
        if domain.lower() in dataset.description.lower():
            score += 0.2
        
        # Query keywords match
        query_words = user_query.lower().split()
        desc_lower = dataset.description.lower()
        matches = sum(1 for word in query_words if word in desc_lower)
        score += min(matches * 0.05, 0.2)
        
        # Prefer certain licenses
        if dataset.license:
            license_lower = dataset.license.lower()
            if any(lic in license_lower for lic in ["mit", "apache", "cc0", "public"]):
                score += 0.1
        
        return min(1.0, score)
    
    def _get_cache_key(self, domain: str, query: str) -> str:
        content = f"{domain}|{query}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_cache(self, cache_key: str) -> Optional[DiscoveryResult]:
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_path):
            return None
        
        # Check TTL
        if time.time() - os.path.getmtime(cache_path) > self.cache_ttl:
            return None
        
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            
            datasets = [
                DiscoveredDataset(**d) for d in data.get("datasets", [])
            ]
            
            return DiscoveryResult(
                success=data["success"],
                domain=data["domain"],
                total_found=data["total_found"],
                datasets=datasets,
                sources_searched=data["sources_searched"],
                errors=data.get("errors", []),
                search_time_ms=data.get("search_time_ms", 0),
            )
        except:
            return None
    
    def _save_cache(self, cache_key: str, result: DiscoveryResult) -> None:
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        data = {
            "success": result.success,
            "domain": result.domain,
            "total_found": result.total_found,
            "sources_searched": result.sources_searched,
            "errors": result.errors,
            "search_time_ms": result.search_time_ms,
            "datasets": [
                {
                    "name": d.name,
                    "source": d.source,
                    "url": d.url,
                    "description": d.description[:500],
                    "size_mb": d.size_mb,
                    "license": d.license,
                    "quality_score": d.quality_score,
                    "relevance_score": d.relevance_score,
                    "download_url": d.download_url,
                    "format": d.format,
                }
                for d in result.datasets
            ],
        }
        
        with open(cache_path, "w") as f:
            json.dump(data, f)
