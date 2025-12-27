# ============================================================
#  ANM V0-OpenSource — Model Downloader
#  GGUF Model Download from HuggingFace Hub
# ============================================================

"""
ANM Model Downloader - Download GGUF models from HuggingFace Hub.

Features:
- Automatic download with progress
- Local caching in platform-specific directories
- Resume interrupted downloads
- Model verification
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Callable
from pathlib import Path
import os
import sys
import time

__all__ = [
    "ModelDownloader",
    "ModelInfo",
    "get_models_directory",
    "list_cached_models",
]


@dataclass
class ModelInfo:
    """Information about a model."""
    repo_id: str
    filename: str
    size_bytes: int
    local_path: Optional[Path]
    is_cached: bool


# ============================================================
#  Default Models
# ============================================================

DEFAULT_MODELS = {
    "deepseek-r1-1.5b": {
        "repo_id": "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "size_gb": 1.0,
    },
    "deepseek-r1-7b": {
        "repo_id": "bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "size_gb": 4.4,
    },
    "deepseek-r1-14b": {
        "repo_id": "bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "size_gb": 8.7,
    },
    "qwen2.5-1.5b": {
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "size_gb": 1.0,
    },
    "llama-3.2-1b": {
        "repo_id": "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "size_gb": 0.8,
    },
    "llama-3.2-3b": {
        "repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size_gb": 2.0,
    },
    "tinyllama-1.1b": {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size_gb": 0.67,
    },
    "stable-code-3b": {
        "repo_id": "TheBloke/stable-code-3b-GGUF",
        "filename": "stable-code-3b.Q4_K_M.gguf",
        "size_gb": 1.71,
    },
    "nanbeige4-3b": {
        "repo_id": "enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF",
        "filename": "nanbeige4-3b-base-q4_k_m.gguf",
        "size_gb": 2.44,
    },
}


def get_models_directory() -> Path:
    """Get the platform-specific models directory."""
    try:
        from anm.system.paths import get_anm_paths
        paths = get_anm_paths()
        return paths.models
    except ImportError:
        # Fallback
        return Path.home() / ".anm" / "models"


def list_cached_models() -> List[ModelInfo]:
    """List all cached models."""
    models_dir = get_models_directory()
    if not models_dir.exists():
        return []
    
    cached = []
    for file in models_dir.glob("*.gguf"):
        cached.append(ModelInfo(
            repo_id="local",
            filename=file.name,
            size_bytes=file.stat().st_size,
            local_path=file,
            is_cached=True,
        ))
    
    return cached


class ModelDownloader:
    """
    Download GGUF models from HuggingFace Hub.
    
    Features:
    - Automatic download with progress
    - Local caching
    - Resume interrupted downloads
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize downloader.
        
        Args:
            cache_dir: Directory for model cache (default: platform-specific)
        """
        self.cache_dir = cache_dir or get_models_directory()
        self._hf_available = False
        
        # Check if huggingface_hub is available
        try:
            from huggingface_hub import hf_hub_download
            self._hf_available = True
        except ImportError:
            self._hf_available = False
    
    @property
    def is_available(self) -> bool:
        """Check if downloader is available."""
        return self._hf_available
    
    def get_cached_path(self, repo_id: str, filename: str) -> Optional[Path]:
        """
        Get path if model is already cached.
        
        Args:
            repo_id: HuggingFace repo ID
            filename: Model filename
            
        Returns:
            Path to cached model or None
        """
        # Check in local cache directory
        local_path = self.cache_dir / filename
        if local_path.exists():
            return local_path
        
        # Check in HuggingFace cache
        if self._hf_available:
            try:
                from huggingface_hub import try_to_load_from_cache
                
                cached = try_to_load_from_cache(
                    repo_id=repo_id,
                    filename=filename,
                )
                if cached and Path(cached).exists():
                    return Path(cached)
            except Exception:
                pass
        
        return None
    
    def download(
        self,
        repo_id: str,
        filename: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """
        Download model from HuggingFace Hub.
        
        Args:
            repo_id: HuggingFace repo ID (e.g., "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF")
            filename: Model filename (e.g., "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf")
            progress_callback: Optional callback(downloaded, total)
            
        Returns:
            Path to downloaded model
        """
        # Check if already cached
        cached = self.get_cached_path(repo_id, filename)
        if cached:
            print(f"[ModelDownloader] Using cached model: {cached}")
            return cached
        
        if not self._hf_available:
            raise RuntimeError(
                "huggingface_hub not installed. "
                "Install with: pip install huggingface-hub"
            )
        
        from huggingface_hub import hf_hub_download
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[ModelDownloader] Downloading: {repo_id}/{filename}")
        print(f"[ModelDownloader] This may take a few minutes...")
        sys.stdout.flush()  # Ensure message is printed immediately
        
        try:
            # Download to HuggingFace cache first
            # Note: hf_hub_download is blocking and will wait for completion
            # Downloads automatically resume if interrupted (resume_download deprecated)
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
            )
            
            # Verify the download completed
            if not downloaded_path:
                raise RuntimeError("Download returned None - download may have failed")
            
            downloaded_path_obj = Path(downloaded_path)
            if not downloaded_path_obj.exists():
                raise RuntimeError(f"Downloaded file not found at: {downloaded_path}")
            
            # Verify file size is reasonable (at least 1MB)
            file_size = downloaded_path_obj.stat().st_size
            if file_size < 1024 * 1024:  # Less than 1MB is suspicious
                raise RuntimeError(f"Downloaded file is too small ({file_size} bytes) - download may be incomplete")
            
            file_size_mb = file_size / (1024 * 1024)
            print(f"[ModelDownloader] Download complete: {file_size_mb:.1f} MB")
            sys.stdout.flush()
            
            # Copy to our cache directory for easy access
            local_path = self.cache_dir / filename
            if not local_path.exists():
                print(f"[ModelDownloader] Copying to local cache...")
                sys.stdout.flush()
                import shutil
                shutil.copy2(downloaded_path, local_path)
                print(f"[ModelDownloader] ✓ Copied to: {local_path}")
                sys.stdout.flush()
            else:
                print(f"[ModelDownloader] ✓ Already in local cache: {local_path}")
                sys.stdout.flush()
            
            return local_path
            
        except KeyboardInterrupt:
            print(f"\n[ModelDownloader] Download interrupted by user")
            raise
        except Exception as e:
            error_msg = f"Failed to download model: {e}"
            print(f"[ModelDownloader] ❌ {error_msg}")
            sys.stdout.flush()
            raise RuntimeError(error_msg) from e
    
    def download_default(self, model_name: str = "deepseek-r1-1.5b") -> Path:
        """
        Download a default model by name.
        
        Args:
            model_name: One of the default model names
            
        Returns:
            Path to downloaded model
        """
        if model_name not in DEFAULT_MODELS:
            available = ", ".join(DEFAULT_MODELS.keys())
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Available: {available}"
            )
        
        model = DEFAULT_MODELS[model_name]
        return self.download(
            repo_id=model["repo_id"],
            filename=model["filename"],
        )
    
    def get_model_info(self, repo_id: str, filename: str) -> ModelInfo:
        """Get information about a model."""
        cached = self.get_cached_path(repo_id, filename)
        
        if cached:
            return ModelInfo(
                repo_id=repo_id,
                filename=filename,
                size_bytes=cached.stat().st_size,
                local_path=cached,
                is_cached=True,
            )
        
        return ModelInfo(
            repo_id=repo_id,
            filename=filename,
            size_bytes=0,
            local_path=None,
            is_cached=False,
        )
    
    def list_available_models(self) -> List[str]:
        """List available default models."""
        return list(DEFAULT_MODELS.keys())
    
    def print_available_models(self) -> None:
        """Print available default models."""
        print("\nAvailable Models:")
        print("=" * 60)
        for name, info in DEFAULT_MODELS.items():
            cached = self.get_cached_path(info["repo_id"], info["filename"])
            status = "✓ cached" if cached else "○ not downloaded"
            print(f"  {name:<20} ({info['size_gb']:.1f} GB) [{status}]")
        print()
