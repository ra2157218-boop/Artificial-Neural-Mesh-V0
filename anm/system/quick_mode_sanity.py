# ============================================================
#  ANM V0-OpenSource — Quick Mode Sanity Check
#  Checks if quick mode models are downloaded
# ============================================================

"""
Quick Mode Sanity Check - Verifies quick mode models are available.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import time

from anm.system.model_downloader import ModelDownloader, DEFAULT_MODELS
from anm.config.settings import (
    MODEL_GENERAL, MODEL_MATH, MODEL_PHYSICS, MODEL_CODE, MODEL_CHEMISTRY,
    MODEL_BIOLOGY, MODEL_MEMORY, MODEL_RESEARCH, MODEL_FACTS,
    MODEL_REFINER, MODEL_VERIFIER, MODEL_ROUTER, MODEL_EXPANSION
)

__all__ = ["QuickModeSanityCheck", "QuickModeCheckResult", "check_all_models"]


@dataclass
class QuickModeCheckResult:
    """Result of quick mode sanity check."""
    passed: bool
    missing_models: List[Dict[str, Any]]
    total_size_gb: float
    messages: List[str]


class QuickModeSanityCheck:
    """
    Sanity check for Quick Mode.
    
    Checks if required models are downloaded and prompts for download if needed.
    """
    
    def __init__(self):
        self.downloader = ModelDownloader()
    
    def check(self, ask_permission: bool = False, auto_download: bool = True) -> QuickModeCheckResult:
        """
        Check if quick mode models are available.
        
        Args:
            ask_permission: If True, ask user before downloading missing models
            auto_download: If True, automatically download missing models without asking
            
        Returns:
            QuickModeCheckResult with check status
        """
        # Check for quick mode model (TinyLlama-1.1B)
        quick_model = DEFAULT_MODELS.get("tinyllama-1.1b")
        if not quick_model:
            return QuickModeCheckResult(
                passed=False,
                missing_models=[],
                total_size_gb=0.0,
                messages=["Quick mode model not found in DEFAULT_MODELS"],
            )
        
        missing = []
        messages = []
        
        # Check if model is cached
        cached = self.downloader.get_cached_path(
            repo_id=quick_model["repo_id"],
            filename=quick_model["filename"],
        )
        
        if not cached:
            missing.append({
                "name": "tinyllama-1.1b",
                "repo_id": quick_model["repo_id"],
                "filename": quick_model["filename"],
                "size_gb": quick_model["size_gb"],
            })
            messages.append(f"Missing: {quick_model['filename']} ({quick_model['size_gb']:.1f} GB)")
        else:
            messages.append(f"✓ Found: {quick_model['filename']}")
        
        total_size = sum(m["size_gb"] for m in missing)
        
        if not missing:
            return QuickModeCheckResult(
                passed=True,
                missing_models=[],
                total_size_gb=0.0,
                messages=messages,
            )
        
        # If models are missing, download them
        if missing:
            should_download = False
            
            if auto_download:
                # Auto-download without asking
                should_download = True
                if total_size > 0:
                    print(f"\n📥 Auto-downloading Quick Mode model ({total_size:.1f} GB)...")
            elif ask_permission:
                # Ask for permission
                should_download = self._ask_download_permission(missing, total_size)
            
            if should_download:
                # Download missing models
                for model in missing:
                    try:
                        messages.append(f"Downloading {model['filename']}...")
                        print(f"  Downloading {model['filename']} ({model['size_gb']:.1f} GB)...")
                        self.downloader.download(
                            repo_id=model["repo_id"],
                            filename=model["filename"],
                        )
                        messages.append(f"✓ Downloaded: {model['filename']}")
                        print(f"  ✓ Downloaded: {model['filename']}")
                    except Exception as e:
                        messages.append(f"✗ Failed to download {model['filename']}: {e}")
                        print(f"  ✗ Failed to download {model['filename']}: {e}")
                        return QuickModeCheckResult(
                            passed=False,
                            missing_models=missing,
                            total_size_gb=total_size,
                            messages=messages,
                        )
                
                print("✓ Quick Mode model download complete!\n")
                return QuickModeCheckResult(
                    passed=True,
                    missing_models=[],
                    total_size_gb=0.0,
                    messages=messages,
                )
            else:
                messages.append("Download cancelled by user")
                return QuickModeCheckResult(
                    passed=False,
                    missing_models=missing,
                    total_size_gb=total_size,
                    messages=messages,
                )
        
        return QuickModeCheckResult(
            passed=False,
            missing_models=missing,
            total_size_gb=total_size,
            messages=messages,
        )
    
    def _ask_download_permission(self, missing_models: List[Dict[str, Any]], total_size_gb: float) -> bool:
        """
        Ask user for permission to download missing models.
        
        Args:
            missing_models: List of missing model info
            total_size_gb: Total size in GB
            
        Returns:
            True if user approves, False otherwise
        """
        print("\n" + "=" * 60)
        print("QUICK MODE SANITY CHECK")
        print("=" * 60)
        print("\nMissing models for Quick Mode:")
        print()
        
        for model in missing_models:
            print(f"  • {model['name']}")
            print(f"    Repository: {model['repo_id']}")
            print(f"    File: {model['filename']}")
            print(f"    Size: {model['size_gb']:.1f} GB")
            print()
        
        print(f"Total download size: {total_size_gb:.1f} GB")
        print()
        print("Quick Mode requires these models to be downloaded.")
        print("This may take several minutes depending on your internet speed.")
        print()
        
        while True:
            response = input("Download missing models now? (yes/no): ").strip().lower()
            if response in ["yes", "y"]:
                return True
            elif response in ["no", "n"]:
                return False
            else:
                print("Please enter 'yes' or 'no'")
    
    def check_both_models(self, ask_permission: bool = False, auto_download: bool = True) -> QuickModeCheckResult:
        """
        Check if both quick mode and normal mode models are available.
        Used for auto mode which may need either model.
        
        Args:
            ask_permission: If True, ask user before downloading missing models
            auto_download: If True, automatically download missing models without asking
            
        Returns:
            QuickModeCheckResult with check status
        """
        missing = []
        messages = []
        
        # Check quick mode model (TinyLlama-1.1B)
        quick_model = DEFAULT_MODELS.get("tinyllama-1.1b")
        if quick_model:
            cached = self.downloader.get_cached_path(
                repo_id=quick_model["repo_id"],
                filename=quick_model["filename"],
            )
            if not cached:
                missing.append({
                    "name": "tinyllama-1.1b (Quick Mode)",
                    "repo_id": quick_model["repo_id"],
                    "filename": quick_model["filename"],
                    "size_gb": quick_model["size_gb"],
                })
                messages.append(f"Missing: {quick_model['filename']} ({quick_model['size_gb']:.1f} GB)")
            else:
                messages.append(f"✓ Found: {quick_model['filename']} (Quick Mode)")
        
        # Check normal mode model (DeepSeek-R1-1.5B)
        normal_model = DEFAULT_MODELS.get("deepseek-r1-1.5b")
        if normal_model:
            cached = self.downloader.get_cached_path(
                repo_id=normal_model["repo_id"],
                filename=normal_model["filename"],
            )
            if not cached:
                missing.append({
                    "name": "deepseek-r1-1.5b (Normal Mode)",
                    "repo_id": normal_model["repo_id"],
                    "filename": normal_model["filename"],
                    "size_gb": normal_model["size_gb"],
                })
                messages.append(f"Missing: {normal_model['filename']} ({normal_model['size_gb']:.1f} GB)")
            else:
                messages.append(f"✓ Found: {normal_model['filename']} (Normal Mode)")
        
        total_size = sum(m["size_gb"] for m in missing)
        
        if not missing:
            return QuickModeCheckResult(
                passed=True,
                missing_models=[],
                total_size_gb=0.0,
                messages=messages,
            )
        
        # If models are missing, download them
        if missing:
            should_download = False
            
            if auto_download:
                # Auto-download without asking
                should_download = True
                if total_size > 0:
                    print(f"\n📥 Auto-downloading Auto Mode models ({total_size:.1f} GB total)...")
            elif ask_permission:
                # Ask for permission
                should_download = self._ask_download_permission_auto_mode(missing, total_size)
            
            if should_download:
                # Download missing models
                for model in missing:
                    try:
                        messages.append(f"Downloading {model['filename']}...")
                        print(f"  Downloading {model['name']} ({model['size_gb']:.1f} GB)...")
                        self.downloader.download(
                            repo_id=model["repo_id"],
                            filename=model["filename"],
                        )
                        messages.append(f"✓ Downloaded: {model['filename']}")
                        print(f"  ✓ Downloaded: {model['name']}")
                    except Exception as e:
                        messages.append(f"✗ Failed to download {model['filename']}: {e}")
                        print(f"  ✗ Failed to download {model['name']}: {e}")
                        return QuickModeCheckResult(
                            passed=False,
                            missing_models=missing,
                            total_size_gb=total_size,
                            messages=messages,
                        )
                
                print("✓ Auto Mode model downloads complete!\n")
                return QuickModeCheckResult(
                    passed=True,
                    missing_models=[],
                    total_size_gb=0.0,
                    messages=messages,
                )
            else:
                messages.append("Download cancelled by user")
                return QuickModeCheckResult(
                    passed=False,
                    missing_models=missing,
                    total_size_gb=total_size,
                    messages=messages,
                )
        
        return QuickModeCheckResult(
            passed=False,
            missing_models=missing,
            total_size_gb=total_size,
            messages=messages,
        )
    
    def _ask_download_permission_auto_mode(self, missing_models: List[Dict[str, Any]], total_size_gb: float) -> bool:
        """
        Ask user for permission to download missing models for auto mode.
        
        Args:
            missing_models: List of missing model info
            total_size_gb: Total size in GB
            
        Returns:
            True if user approves, False otherwise
        """
        print("\n" + "=" * 60)
        print("AUTO MODE SANITY CHECK")
        print("=" * 60)
        print("\nMissing models for Auto Mode:")
        print("(Auto Mode may use either Quick Mode or Normal Mode, so both are required)")
        print()
        
        for model in missing_models:
            print(f"  • {model['name']}")
            print(f"    Repository: {model['repo_id']}")
            print(f"    File: {model['filename']}")
            print(f"    Size: {model['size_gb']:.1f} GB")
            print()
        
        print(f"Total download size: {total_size_gb:.1f} GB")
        print()
        print("Auto Mode requires both models to be downloaded.")
        print("This may take several minutes depending on your internet speed.")
        print()
        
        while True:
            response = input("Download missing models now? (yes/no): ").strip().lower()
            if response in ["yes", "y"]:
                return True
            elif response in ["no", "n"]:
                return False
            else:
                print("Please enter 'yes' or 'no'")


def _normalize_model_name(model_name: str) -> str:
    """
    Normalize model name from settings format to DEFAULT_MODELS key format.
    
    Examples:
        "deepseek-r1:1.5b" -> "deepseek-r1-1.5b"
        "nanbeige4-3b" -> "nanbeige4-3b"
        "stable-code-3b" -> "stable-code-3b"
    """
    # Replace colon with dash for DeepSeek models
    normalized = model_name.replace(":", "-")
    return normalized


def check_all_models(ask_permission: bool = False, auto_download: bool = True, verbose: bool = True) -> QuickModeCheckResult:
    """
    Check and download ALL models required by ANM at startup.
    
    This checks all models from settings.py:
    - Base models (DeepSeek-R1-1.5B, TinyLlama-1.1B)
    - Domain-specific models (Nanbeige4-3B, Stable-Code-3B)
    
    Args:
        ask_permission: If True, ask user before downloading missing models
        auto_download: If True, automatically download missing models without asking
        verbose: If True, print progress messages
        
    Returns:
        QuickModeCheckResult with check status
    """
    downloader = ModelDownloader()
    missing = []
    messages = []
    
    # Get all unique models from settings
    models_to_check = set()
    
    # Add base models (quick mode and normal mode)
    models_to_check.add("tinyllama-1.1b")  # Quick mode
    models_to_check.add("deepseek-r1-1.5b")  # Normal mode (most common)
    
    # Add all models from settings.py
    model_settings = {
        "model_general": MODEL_GENERAL,
        "model_math": MODEL_MATH,
        "model_physics": MODEL_PHYSICS,
        "model_code": MODEL_CODE,
        "model_chemistry": MODEL_CHEMISTRY,
        "model_biology": MODEL_BIOLOGY,
        "model_memory": MODEL_MEMORY,
        "model_research": MODEL_RESEARCH,
        "model_facts": MODEL_FACTS,
        "model_refiner": MODEL_REFINER,
        "model_verifier": MODEL_VERIFIER,
        "model_router": MODEL_ROUTER,
        "model_expansion": MODEL_EXPANSION,
    }
    
    # Normalize and collect unique model names
    for setting_name, model_name in model_settings.items():
        if model_name:
            normalized = _normalize_model_name(model_name)
            models_to_check.add(normalized)
    
    if verbose:
        print(f"\n📋 Checking {len(models_to_check)} required models...")
    
    # Check each model
    for model_key in sorted(models_to_check):
        if model_key not in DEFAULT_MODELS:
            if verbose:
                print(f"  ⚠️  Model '{model_key}' not found in DEFAULT_MODELS, skipping...")
            messages.append(f"⚠️  Model '{model_key}' not available for download")
            continue
        
        model_info = DEFAULT_MODELS[model_key]
        cached = downloader.get_cached_path(
            repo_id=model_info["repo_id"],
            filename=model_info["filename"],
        )
        
        if not cached:
            missing.append({
                "name": model_key,
                "repo_id": model_info["repo_id"],
                "filename": model_info["filename"],
                "size_gb": model_info["size_gb"],
            })
            if verbose:
                messages.append(f"  ❌ Missing: {model_key} ({model_info['size_gb']:.1f} GB)")
        else:
            if verbose:
                messages.append(f"  ✅ Found: {model_key}")
    
    total_size = sum(m["size_gb"] for m in missing)
    
    if not missing:
        if verbose:
            print("✅ All required models are downloaded!")
        return QuickModeCheckResult(
            passed=True,
            missing_models=[],
            total_size_gb=0.0,
            messages=messages,
        )
    
    # If models are missing, download them
    if verbose:
        print(f"\n📥 Found {len(missing)} missing model(s) ({total_size:.1f} GB total)")
    
    should_download = False
    
    if auto_download:
        should_download = True
        if verbose and total_size > 0:
            print(f"\n📥 Auto-downloading {len(missing)} missing model(s) ({total_size:.1f} GB total)...")
            print("   This may take several minutes depending on your internet speed.\n")
    elif ask_permission:
        should_download = _ask_download_permission_all_models(missing, total_size)
    
    if should_download:
        # Download missing models
        for idx, model in enumerate(missing, 1):
            try:
                if verbose:
                    print(f"[{idx}/{len(missing)}] Downloading {model['name']} ({model['size_gb']:.1f} GB)...")
                    print("   Please wait, this may take several minutes...")
                messages.append(f"Downloading {model['filename']}...")
                
                # Download with explicit error handling
                start_time = time.time()
                try:
                    downloaded_path = downloader.download(
                        repo_id=model["repo_id"],
                        filename=model["filename"],
                    )
                    elapsed = time.time() - start_time
                    
                    # Verify download succeeded
                    if not downloaded_path or not downloaded_path.exists():
                        raise RuntimeError(f"Downloaded file not found: {downloaded_path}")
                    
                    messages.append(f"✓ Downloaded: {model['filename']}")
                    if verbose:
                        print(f"  ✅ Downloaded: {model['name']} (took {elapsed:.1f}s)\n")
                except KeyboardInterrupt:
                    if verbose:
                        print(f"\n  ⚠️  Download interrupted by user")
                    raise
                except Exception as download_error:
                    if verbose:
                        print(f"  ❌ Download failed: {download_error}")
                    raise
                    
            except Exception as e:
                error_msg = f"✗ Failed to download {model['filename']}: {e}"
                messages.append(error_msg)
                if verbose:
                    print(f"  ❌ Failed to download {model['name']}: {e}\n")
                return QuickModeCheckResult(
                    passed=False,
                    missing_models=missing,
                    total_size_gb=total_size,
                    messages=messages,
                )
        
        if verbose:
            print("✅ All model downloads complete!\n")
        return QuickModeCheckResult(
            passed=True,
            missing_models=[],
            total_size_gb=0.0,
            messages=messages,
        )
    else:
        messages.append("Download cancelled by user")
        return QuickModeCheckResult(
            passed=False,
            missing_models=missing,
            total_size_gb=total_size,
            messages=messages,
        )


def _ask_download_permission_all_models(missing_models: List[Dict[str, Any]], total_size_gb: float) -> bool:
    """
    Ask user for permission to download all missing models.
    
    Args:
        missing_models: List of missing model info
        total_size_gb: Total size in GB
        
    Returns:
        True if user approves, False otherwise
    """
    print("\n" + "=" * 60)
    print("ANM MODEL CHECK")
    print("=" * 60)
    print("\nMissing models required by ANM:")
    print()
    
    for model in missing_models:
        print(f"  • {model['name']}")
        print(f"    Repository: {model['repo_id']}")
        print(f"    File: {model['filename']}")
        print(f"    Size: {model['size_gb']:.1f} GB")
        print()
    
    print(f"Total download size: {total_size_gb:.1f} GB")
    print()
    print("ANM requires these models to be downloaded.")
    print("This may take several minutes depending on your internet speed.")
    print()
    
    while True:
        response = input("Download missing models now? (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("Please enter 'yes' or 'no'")
