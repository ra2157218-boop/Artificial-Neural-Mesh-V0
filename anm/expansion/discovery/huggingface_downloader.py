# ============================================================
# ANM V0-OpenSource — HUGGINGFACE DATASET DOWNLOADER (ENHANCED)
#  Full Dataset Download • Progress Tracking • Resume • Authentication
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import os
import json
import hashlib
from dataclasses import dataclass


@dataclass
class DownloadProgress:
    """Download progress information."""
    dataset_name: str
    total_bytes: int
    downloaded_bytes: int
    percentage: float
    status: str  # "downloading", "processing", "completed", "failed"
    current_file: Optional[str] = None
    error: Optional[str] = None


class HuggingFaceDatasetDownloader:
    """
    Enhanced HuggingFace Dataset Downloader.
    
    Features:
    - Full dataset downloading using huggingface_hub
    - Progress tracking with callbacks
    - Resume interrupted downloads
    - Authentication support (HF_TOKEN)
    - Dataset validation
    - Format conversion
    - Cache management
    """
    
    def __init__(
        self,
        cache_dir: str = ".anm_cache/datasets",
        token: Optional[str] = None,
        resume_download: bool = True,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Get token from environment if not provided
        self.token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        self.resume_download = resume_download
        
        # Check if huggingface_hub is available
        self.hf_available = self._check_hf_availability()
    
    def _check_hf_availability(self) -> bool:
        """Check if huggingface_hub is available."""
        try:
            import huggingface_hub
            return True
        except ImportError:
            return False
    
    def download_dataset(
        self,
        dataset_name: str,
        output_dir: Optional[str] = None,
        split: Optional[str] = None,
        streaming: bool = False,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Dict[str, Any]:
        """
        Download a HuggingFace dataset.
        
        Args:
            dataset_name: Name of the dataset (e.g., "squad", "glue")
            output_dir: Directory to save dataset (default: cache_dir/dataset_name)
            split: Dataset split to download (train, validation, test, or None for all)
            streaming: Use streaming mode for large datasets
            progress_callback: Callback function for progress updates
        
        Returns:
            Dict with download status and paths
        """
        if not self.hf_available:
            return {
                "success": False,
                "error": "huggingface_hub library not installed. Install with: pip install huggingface_hub datasets",
                "install_command": "pip install huggingface_hub datasets",
            }
        
        try:
            from huggingface_hub import snapshot_download, hf_hub_download
            from datasets import load_dataset
            
            output_path = Path(output_dir) if output_dir else self.cache_dir / dataset_name.replace("/", "_")
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Progress callback wrapper
            def progress_wrapper(progress: Dict[str, Any]):
                if progress_callback:
                    prog = DownloadProgress(
                        dataset_name=dataset_name,
                        total_bytes=progress.get("total_bytes", 0),
                        downloaded_bytes=progress.get("downloaded_bytes", 0),
                        percentage=progress.get("percentage", 0.0),
                        status=progress.get("status", "downloading"),
                        current_file=progress.get("current_file"),
                    )
                    progress_callback(prog)
            
            # Download dataset
            if streaming:
                # Streaming mode for very large datasets
                dataset = load_dataset(
                    dataset_name,
                    split=split,
                    streaming=True,
                    token=self.token,
                )
                
                # Save streaming data
                saved_files = self._save_streaming_dataset(dataset, output_path, progress_wrapper)
            else:
                # Standard download
                dataset = load_dataset(
                    dataset_name,
                    split=split,
                    token=self.token,
                    cache_dir=str(self.cache_dir),
                )
                
                # Save dataset
                saved_files = self._save_dataset(dataset, output_path, progress_wrapper)
            
            # Get dataset info
            dataset_info = self._get_dataset_info(dataset_name)
            
            return {
                "success": True,
                "dataset_name": dataset_name,
                "output_path": str(output_path),
                "saved_files": saved_files,
                "dataset_info": dataset_info,
                "num_samples": len(dataset) if hasattr(dataset, "__len__") else "streaming",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "dataset_name": dataset_name,
            }
    
    def _save_dataset(self, dataset, output_path: Path, progress_callback: Optional[Callable]) -> List[str]:
        """Save dataset to disk."""
        saved_files = []
        
        # Convert to JSONL format (standard for training)
        if hasattr(dataset, "to_json"):
            jsonl_path = output_path / "dataset.jsonl"
            dataset.to_json(str(jsonl_path))
            saved_files.append(str(jsonl_path))
        
        # Also save as parquet (more efficient)
        if hasattr(dataset, "to_parquet"):
            parquet_path = output_path / "dataset.parquet"
            dataset.to_parquet(str(parquet_path))
            saved_files.append(str(parquet_path))
        
        # Save metadata
        metadata = {
            "num_examples": len(dataset) if hasattr(dataset, "__len__") else None,
            "features": list(dataset.features.keys()) if hasattr(dataset, "features") else [],
        }
        
        metadata_path = output_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        saved_files.append(str(metadata_path))
        
        return saved_files
    
    def _save_streaming_dataset(self, dataset, output_path: Path, progress_callback: Optional[Callable]) -> List[str]:
        """Save streaming dataset incrementally."""
        import json
        
        jsonl_path = output_path / "dataset.jsonl"
        saved_files = [str(jsonl_path)]
        
        with open(jsonl_path, "w") as f:
            count = 0
            for example in dataset:
                f.write(json.dumps(example) + "\n")
                count += 1
                
                if progress_callback and count % 1000 == 0:
                    progress_callback({
                        "status": "downloading",
                        "downloaded_bytes": count,
                        "percentage": 0.0,  # Unknown total
                    })
        
        return saved_files
    
    def _get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """Get dataset information from HuggingFace Hub."""
        try:
            from huggingface_hub import HfApi
            
            api = HfApi(token=self.token)
            dataset_info = api.dataset_info(dataset_name)
            
            return {
                "id": dataset_info.id,
                "author": dataset_info.author,
                "downloads": dataset_info.downloads if hasattr(dataset_info, "downloads") else None,
                "likes": dataset_info.likes if hasattr(dataset_info, "likes") else None,
                "tags": dataset_info.tags if hasattr(dataset_info, "tags") else [],
                "splits": list(dataset_info.splits.keys()) if hasattr(dataset_info, "splits") else [],
            }
        except Exception as e:
            return {"error": str(e)}
    
    def download_model(
        self,
        model_name: str,
        output_dir: Optional[str] = None,
        revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download a HuggingFace model.
        
        Args:
            model_name: Name of the model (e.g., "deepseek-ai/deepseek-r1-1.5b")
            output_dir: Directory to save model
            revision: Model revision/branch (default: main)
        
        Returns:
            Dict with download status and model path
        """
        if not self.hf_available:
            return {
                "success": False,
                "error": "huggingface_hub library not installed",
            }
        
        try:
            from huggingface_hub import snapshot_download
            
            output_path = Path(output_dir) if output_dir else self.cache_dir / "models" / model_name.replace("/", "_")
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Download model
            model_path = snapshot_download(
                repo_id=model_name,
                revision=revision,
                token=self.token,
                local_dir=str(output_path),
                resume_download=self.resume_download,
            )
            
            return {
                "success": True,
                "model_name": model_name,
                "model_path": model_path,
                "output_path": str(output_path),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_name": model_name,
            }
    
    def list_datasets(
        self,
        search_query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List datasets matching search query."""
        if not self.hf_available:
            return []
        
        try:
            from huggingface_hub import HfApi
            
            api = HfApi(token=self.token)
            datasets = api.list_datasets(search=search_query, limit=limit)
            
            return [
                {
                    "id": ds.id,
                    "author": ds.author,
                    "downloads": ds.downloads if hasattr(ds, "downloads") else 0,
                    "likes": ds.likes if hasattr(ds, "likes") else 0,
                }
                for ds in datasets
            ]
        except Exception as e:
            return []
    
    def validate_dataset(
        self,
        dataset_path: str,
    ) -> Dict[str, Any]:
        """Validate downloaded dataset."""
        path = Path(dataset_path)
        
        if not path.exists():
            return {
                "valid": False,
                "error": "Dataset path does not exist",
            }
        
        # Check for required files
        jsonl_file = path / "dataset.jsonl"
        metadata_file = path / "metadata.json"
        
        validation = {
            "valid": True,
            "has_jsonl": jsonl_file.exists(),
            "has_metadata": metadata_file.exists(),
            "errors": [],
        }
        
        # Validate JSONL format
        if jsonl_file.exists():
            try:
                with open(jsonl_file, "r") as f:
                    first_line = f.readline()
                    json.loads(first_line)  # Validate JSON
            except Exception as e:
                validation["valid"] = False
                validation["errors"].append(f"Invalid JSONL format: {e}")
        
        # Validate metadata
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    if "num_examples" not in metadata:
                        validation["errors"].append("Missing num_examples in metadata")
            except Exception as e:
                validation["valid"] = False
                validation["errors"].append(f"Invalid metadata: {e}")
        
        return validation
