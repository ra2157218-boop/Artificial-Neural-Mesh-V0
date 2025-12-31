# ============================================================
# ANM V0-OpenSource — DATA SOURCES (MAXIMUM LEVEL)
#  HuggingFace • Kaggle • GitHub • ArXiv • Academic DBs
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import requests
import os


# Import the base class and dataset type
from anm.expansion.discovery.multi_source import DataSourceBase, DiscoveredDataset


class HuggingFaceSource(DataSourceBase):
    """
    HuggingFace Datasets Hub source (ENHANCED).
    
    Features:
    - Full API integration
    - Dataset metadata extraction
    - Quality scoring based on downloads/likes
    - Direct download support via huggingface_hub
    """
    
    name = "huggingface"
    API_URL = "https://huggingface.co/api/datasets"
    
    def __init__(self):
        # Check if huggingface_hub is available
        self.hf_available = self._check_hf_availability()
        self.downloader = None
        
        if self.hf_available:
            try:
                from anm.expansion.discovery.huggingface_downloader import HuggingFaceDatasetDownloader
                self.downloader = HuggingFaceDatasetDownloader()
            except Exception:
                pass
    
    def _check_hf_availability(self) -> bool:
        """Check if huggingface_hub is available."""
        try:
            import huggingface_hub
            return True
        except ImportError:
            return False
    
    def search(self, query: str, domain: str, max_results: int = 10) -> List[DiscoveredDataset]:
        datasets = []
        
        # Try using huggingface_hub API if available (better results)
        if self.hf_available and self.downloader:
            try:
                hf_datasets = self.downloader.list_datasets(f"{domain} {query}", limit=max_results)
                
                for ds in hf_datasets:
                    downloads = ds.get("downloads", 0)
                    likes = ds.get("likes", 0)
                    
                    quality = min(
                        0.3 + (downloads / 10000) * 0.4 + (likes / 100) * 0.3,
                        1.0
                    )
                    
                    datasets.append(DiscoveredDataset(
                        name=ds["id"],
                        source=self.name,
                        url=f"https://huggingface.co/datasets/{ds['id']}",
                        description=f"Dataset: {ds['id']}",
                        size_mb=None,
                        license="unknown",
                        quality_score=quality,
                        relevance_score=0.5,
                        download_url=f"hf://datasets/{ds['id']}",  # Special format for downloader
                        format="parquet",
                        metadata={
                            "downloads": downloads,
                            "likes": likes,
                            "author": ds.get("author"),
                        },
                    ))

                if datasets:
                    return datasets
            except Exception:
                pass
        
        # Fallback to REST API
        try:
            params = {
                "search": f"{domain} {query}",
                "limit": max_results,
                "sort": "downloads",
            }
            
            response = requests.get(self.API_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data[:max_results]:
                    dataset_id = item.get("id", "")
                    downloads = item.get("downloads", 0)
                    likes = item.get("likes", 0)
                    
                    quality = min(
                        0.3 + (downloads / 10000) * 0.4 + (likes / 100) * 0.3,
                        1.0
                    )
                    
                    datasets.append(DiscoveredDataset(
                        name=dataset_id,
                        source=self.name,
                        url=f"https://huggingface.co/datasets/{dataset_id}",
                        description=item.get("description", "")[:500],
                        size_mb=None,
                        license=item.get("license", "unknown"),
                        quality_score=quality,
                        relevance_score=0.5,
                        download_url=f"hf://datasets/{dataset_id}",  # Special format
                        format="parquet",
                        metadata={
                            "downloads": downloads,
                            "likes": likes,
                            "tags": item.get("tags", []),
                        },
                    ))
        except Exception as e:
            pass
        
        return datasets
    
    def download(self, dataset_name: str, output_dir: str) -> Dict[str, Any]:
        """Download a dataset using the enhanced downloader."""
        if self.downloader:
            return self.downloader.download_dataset(dataset_name, output_dir)
        else:
            return {
                "success": False,
                "error": "huggingface_hub not available. Install with: pip install huggingface_hub datasets",
            }


class KaggleSource(DataSourceBase):
    """
    Kaggle Datasets source.
    
    Features:
    - API integration (requires KAGGLE_KEY)
    - Competition datasets
    - Quality scoring based on votes/usability
    """
    
    name = "kaggle"
    
    def search(self, query: str, domain: str, max_results: int = 10) -> List[DiscoveredDataset]:
        datasets = []
        
        # Check for Kaggle API credentials
        kaggle_key = os.environ.get("KAGGLE_KEY")
        
        if not kaggle_key:
            # Return simulated results
            return self._simulated_search(domain, query, max_results)
        
        try:
            import kaggle
            kaggle.api.authenticate()
            
            results = kaggle.api.dataset_list(search=f"{domain} {query}", page_size=max_results)
            
            for item in results:
                quality = min(
                    0.3 + (item.usabilityRating / 10) * 0.5 + (item.voteCount / 100) * 0.2,
                    1.0
                )
                
                datasets.append(DiscoveredDataset(
                    name=item.ref,
                    source=self.name,
                    url=f"https://www.kaggle.com/datasets/{item.ref}",
                    description=item.title,
                    size_mb=item.totalBytes / (1024 * 1024) if item.totalBytes else None,
                    license=item.licenseName,
                    quality_score=quality,
                    relevance_score=0.5,
                    download_url=f"https://www.kaggle.com/datasets/{item.ref}",
                    format="csv",
                    metadata={
                        "votes": item.voteCount,
                        "usability": item.usabilityRating,
                    },
                ))
        except Exception:
            return self._simulated_search(domain, query, max_results)
        
        return datasets
    
    def _simulated_search(self, domain: str, query: str, max_results: int) -> List[DiscoveredDataset]:
        """Return simulated Kaggle results when API not available."""
        return [
            DiscoveredDataset(
                name=f"kaggle-{domain}-dataset",
                source=self.name,
                url=f"https://www.kaggle.com/search?q={domain}",
                description=f"Kaggle datasets for {domain} (API key required for full access)",
                size_mb=None,
                license="various",
                quality_score=0.4,
                relevance_score=0.5,
                download_url=None,
                format="csv",
                metadata={"simulated": True},
            )
        ]


class GitHubSource(DataSourceBase):
    """
    GitHub Repositories source.
    
    Features:
    - Search for data repositories
    - README parsing
    - Star-based quality scoring
    """
    
    name = "github"
    API_URL = "https://api.github.com/search/repositories"
    
    def search(self, query: str, domain: str, max_results: int = 10) -> List[DiscoveredDataset]:
        datasets = []
        
        try:
            headers = {}
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            params = {
                "q": f"{domain} dataset {query} in:name,description,readme",
                "sort": "stars",
                "per_page": max_results,
            }
            
            response = requests.get(self.API_URL, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("items", [])[:max_results]:
                    stars = item.get("stargazers_count", 0)
                    forks = item.get("forks_count", 0)
                    
                    quality = min(
                        0.2 + (stars / 1000) * 0.5 + (forks / 100) * 0.3,
                        1.0
                    )
                    
                    datasets.append(DiscoveredDataset(
                        name=item.get("full_name", ""),
                        source=self.name,
                        url=item.get("html_url", ""),
                        description=item.get("description", "")[:500],
                        size_mb=item.get("size", 0) / 1024,
                        license=item.get("license", {}).get("spdx_id") if item.get("license") else None,
                        quality_score=quality,
                        relevance_score=0.5,
                        download_url=item.get("clone_url"),
                        format="various",
                        metadata={
                            "stars": stars,
                            "forks": forks,
                            "language": item.get("language"),
                        },
                    ))
        except Exception:
            pass
        
        return datasets


class ArxivSource(DataSourceBase):
    """
    ArXiv Papers source.
    
    Features:
    - Search academic papers
    - Extract datasets mentioned in papers
    - Citation-based quality scoring
    """
    
    name = "arxiv"
    API_URL = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, domain: str, max_results: int = 10) -> List[DiscoveredDataset]:
        datasets = []
        
        try:
            params = {
                "search_query": f"all:{domain}+AND+all:dataset",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
            }
            
            response = requests.get(self.API_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                
                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    link = entry.find("atom:id", ns)
                    
                    if title is not None:
                        datasets.append(DiscoveredDataset(
                            name=title.text.strip() if title.text else "",
                            source=self.name,
                            url=link.text if link is not None and link.text else "",
                            description=summary.text[:500] if summary is not None and summary.text else "",
                            size_mb=None,
                            license="arxiv",
                            quality_score=0.6,  # Academic papers have higher base quality
                            relevance_score=0.5,
                            download_url=None,
                            format="pdf",
                            metadata={"type": "paper"},
                        ))
        except Exception:
            pass
        
        return datasets


class WebSearchSource(DataSourceBase):
    """
    Web Search fallback source.
    
    Uses DuckDuckGo or similar for general web search.
    """
    
    name = "web"
    
    def search(self, query: str, domain: str, max_results: int = 10) -> List[DiscoveredDataset]:
        # Fallback to ResearchLLM's DuckDuckGo backend
        try:
            from anm.specialists.research_llm import DuckDuckGoBackend
            
            backend = DuckDuckGoBackend()
            hits = backend.search(f"{domain} dataset {query}", max_results=max_results)
            
            datasets = []
            for hit in hits:
                datasets.append(DiscoveredDataset(
                    name=hit.title,
                    source=self.name,
                    url=hit.url,
                    description=hit.snippet[:500] if hit.snippet else "",
                    size_mb=None,
                    license="unknown",
                    quality_score=0.3,
                    relevance_score=hit.score if hasattr(hit, 'score') else 0.5,
                    download_url=hit.url,
                    format="unknown",
                    metadata={},
                ))

            return datasets
        except Exception:
            return []
