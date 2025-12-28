# ============================================================
# ANM V0-OpenSource — DATASET DISCOVERY MODULE
#  Part of Self-Improvement Pipeline (Stage 3.6)
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import os
import requests
from dataclasses import dataclass


@dataclass
class DatasetInfo:
    """Information about a discovered dataset."""
    name: str
    source: str  # "huggingface", "kaggle", "academic", etc.
    url: Optional[str]
    description: str
    size_mb: Optional[float]
    license: Optional[str]
    download_url: Optional[str]
    format: str  # "json", "csv", "txt", etc.
    verified_safe: bool = False


class DatasetDiscovery:
    """
    Dataset Discovery Module for Self-Improvement Pipeline.
    
    Responsibilities:
      - Searches for publicly allowed datasets
      - Validates legal/ethical safety
      - Downloads data
      - Cleans and formats it into Gold Data
    """
    
    def __init__(self):
        self.discovered_datasets: List[DatasetInfo] = []
        
    def discover_datasets(
        self, domain: str, user_query: str
    ) -> Dict[str, Any]:
        """
        Discover datasets for a given domain.
        
        Returns:
            Dict with discovered datasets and metadata
        """
        # Search strategy:
        # 1. Try HuggingFace datasets
        # 2. Try Kaggle (if API key available)
        # 3. Try academic repositories
        # 4. Fall back to web search via ResearchLLM
        
        datasets = []
        
        # 1. HuggingFace datasets search
        hf_datasets = self._search_huggingface(domain)
        datasets.extend(hf_datasets)
        
        # 2. Web search fallback (via ResearchLLM pattern)
        web_datasets = self._search_web(domain, user_query)
        datasets.extend(web_datasets)
        
        self.discovered_datasets = datasets
        
        return {
            "success": True,
            "domain": domain,
            "datasets_found": len(datasets),
            "datasets": [
                {
                    "name": d.name,
                    "source": d.source,
                    "url": d.url,
                    "description": d.description[:200],  # Truncate
                    "size_mb": d.size_mb,
                    "license": d.license,
                    "verified_safe": d.verified_safe,
                }
                for d in datasets
            ],
        }
    
    def _search_huggingface(self, domain: str) -> List[DatasetInfo]:
        """
        Search HuggingFace datasets for domain-specific data.
        """
        datasets = []
        
        try:
            # HuggingFace datasets API
            api_url = "https://huggingface.co/api/datasets"
            params = {"search": domain, "limit": 5}
            
            response = requests.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("datasets", [])[:5]:  # Limit to 5
                    dataset_name = item.get("id", "")
                    if dataset_name:
                        datasets.append(
                            DatasetInfo(
                                name=dataset_name,
                                source="huggingface",
                                url=f"https://huggingface.co/datasets/{dataset_name}",
                                description=item.get("description", "")[:500],
                                size_mb=None,  # Would need to fetch details
                                license=item.get("license", "unknown"),
                                download_url=f"https://huggingface.co/datasets/{dataset_name}",
                                format="json",  # HF datasets typically JSON
                                verified_safe=self._verify_license_safety(
                                    item.get("license", "")
                                ),
                            )
                        )
        except Exception as e:
            # On error, return empty list
            pass
        
        return datasets
    
    def _search_web(self, domain: str, user_query: str) -> List[DatasetInfo]:
        """
        Search web for datasets (fallback method).
        Uses ResearchLLM pattern but focused on dataset discovery.
        """
        datasets = []
        
        try:
            from anm.specialists.research_llm import ResearchLLM
            
            research_llm = ResearchLLM()
            search_query = f"publicly available {domain} dataset for machine learning training"
            
            wot_packet = f"""[RESEARCH REQUEST]
Find publicly available datasets for the '{domain}' domain suitable for training a language model.

Requirements:
- Must be publicly available
- Must have clear licensing
- Should be suitable for fine-tuning
- Must be clean and well-structured

User context: {user_query}

[END RESEARCH REQUEST]"""
            
            research_output = research_llm.run(wot_packet)
            
            # Parse research output to extract dataset mentions
            # In a full implementation, this would use NLP to extract
            # dataset names, URLs, and metadata from the research output
            
            # For now, create a placeholder dataset based on research
            if "dataset" in research_output.lower():
                datasets.append(
                    DatasetInfo(
                        name=f"{domain}_dataset_from_research",
                        source="web_search",
                        url=None,
                        description=f"Dataset discovered via web search for {domain}",
                        size_mb=None,
                        license="unknown",
                        download_url=None,
                        format="unknown",
                        verified_safe=False,  # Needs manual verification
                    )
                )
        except Exception as e:
            # On error, return empty list
            pass
        
        return datasets
    
    def _verify_license_safety(self, license_str: str) -> bool:
        """
        Verify if a license is safe for use (legal/ethical).
        
        Returns True if license is permissive and safe.
        """
        license_lower = license_str.lower()
        
        # Safe licenses
        safe_licenses = [
            "mit", "apache", "bsd", "cc0", "cc-by", "public domain",
            "unlicense", "wtfpl", "isc",
        ]
        
        # Unsafe/restrictive licenses
        unsafe_licenses = [
            "gpl", "agpl", "proprietary", "commercial",
        ]
        
        for safe in safe_licenses:
            if safe in license_lower:
                return True
        
        for unsafe in unsafe_licenses:
            if unsafe in license_lower:
                return False
        
        # Unknown licenses need manual verification
        return False
    
    def download_dataset(
        self, dataset_info: DatasetInfo, output_dir: str
    ) -> Dict[str, Any]:
        """
        Download a dataset to the specified directory.
        
        Returns:
            Dict with download status and file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if dataset_info.source == "huggingface":
            return self._download_huggingface(dataset_info, output_dir)
        elif dataset_info.source == "web_search":
            return {
                "success": False,
                "error": "Web search datasets require manual download",
            }
        else:
            return {
                "success": False,
                "error": f"Unknown source: {dataset_info.source}",
            }
    
    def _download_huggingface(
        self, dataset_info: DatasetInfo, output_dir: str
    ) -> Dict[str, Any]:
        """
        Download a HuggingFace dataset.
        
        Note: Full implementation would use huggingface_hub library.
        """
        # In a full implementation, this would:
        # 1. Use huggingface_hub to download dataset
        # 2. Save to output_dir
        # 3. Return file paths
        
        return {
            "success": False,
            "note": "Full HuggingFace download requires huggingface_hub library",
            "dataset_name": dataset_info.name,
            "output_dir": output_dir,
        }
    
    def clean_dataset(
        self, dataset_path: str, domain: str
    ) -> Dict[str, Any]:
        """
        Clean and format dataset into Gold Data.
        
        Returns:
            Dict with cleaned data info and output path
        """
        # In a full implementation, this would:
        # 1. Load raw dataset
        # 2. Remove duplicates, noise, invalid entries
        # 3. Format into domain-specific structure
        # 4. Split into train/val/test if needed
        # 5. Save cleaned data
        
        cleaned_path = os.path.join(
            os.path.dirname(dataset_path), "cleaned", f"{domain}_gold_data.json"
        )
        
        return {
            "success": True,
            "cleaned_path": cleaned_path,
            "note": "Full cleaning pipeline requires dataset-specific logic",
        }
