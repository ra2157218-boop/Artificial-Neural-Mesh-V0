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

from anm.system.model_downloader import ModelDownloader, DEFAULT_MODELS

__all__ = ["QuickModeSanityCheck", "QuickModeCheckResult", "check_all_models"]


def _safe_yes_no_prompt(prompt: str, default: bool = False, max_attempts: int = 5) -> bool:
    """
    Safely prompt user for yes/no input with timeout protection.

    Args:
        prompt: Question to ask user
        default: Default value if non-interactive or max attempts reached
        max_attempts: Maximum number of invalid input attempts

    Returns:
        bool: True for yes, False for no
    """
    import sys

    # Security: Detect non-interactive environment to prevent infinite loops
    if not sys.stdin.isatty():
        print(f"[Non-interactive mode detected - defaulting to {'yes' if default else 'no'}]")
        return default

    # Add max attempts to prevent infinite loops
    for attempt in range(max_attempts):
        try:
            response = input(prompt).strip().lower()
            if response in ["yes", "y"]:
                return True
            elif response in ["no", "n"]:
                return False
            else:
                print("Please enter 'yes' or 'no'")
        except (EOFError, KeyboardInterrupt):
            print(f"\n[Input interrupted - defaulting to {'yes' if default else 'no'}]")
            return default

    # If max attempts reached, use default
    print(f"[Max attempts ({max_attempts}) reached - defaulting to {'yes' if default else 'no'}]")
    return default


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

        return _safe_yes_no_prompt("Download missing models now? (yes/no): ", default=False)
    
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

        return _safe_yes_no_prompt("Download missing models now? (yes/no): ", default=False)


def check_all_models(ask_permission: bool = False, auto_download: bool = True, verbose: bool = True) -> QuickModeCheckResult:
    """
    Check and download ALL required models from DEFAULT_MODELS.
    
    This checks all models (base models + domain-specific models) and downloads
    any that are missing.
    
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
    
    if verbose:
        print("Checking all required models...")
    
    # Check all models in DEFAULT_MODELS
    for model_name, model_info in DEFAULT_MODELS.items():
        cached = downloader.get_cached_path(
            repo_id=model_info["repo_id"],
            filename=model_info["filename"],
        )
        
        if not cached:
            missing.append({
                "name": model_name,
                "repo_id": model_info["repo_id"],
                "filename": model_info["filename"],
                "size_gb": model_info["size_gb"],
            })
            if verbose:
                messages.append(f"Missing: {model_info['filename']} ({model_info['size_gb']:.1f} GB)")
        else:
            if verbose:
                messages.append(f"✓ Found: {model_info['filename']}")
    
    total_size = sum(m["size_gb"] for m in missing)
    
    if not missing:
        if verbose:
            messages.append("All required models are available")
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
            should_download = True
            if total_size > 0 and verbose:
                print(f"\n📥 Auto-downloading missing models ({total_size:.1f} GB total)...")
        elif ask_permission:
            print("\n" + "=" * 60)
            print("MODEL CHECK")
            print("=" * 60)
            print(f"\nMissing {len(missing)} model(s) ({total_size:.1f} GB total):")
            for model in missing:
                print(f"  • {model['name']}: {model['filename']}")
            print()

            should_download = _safe_yes_no_prompt("Download missing models now? (yes/no): ", default=False)
        
        if should_download:
            # Download missing models
            for model in missing:
                try:
                    if verbose:
                        messages.append(f"Downloading {model['filename']}...")
                        print(f"  Downloading {model['name']} ({model['size_gb']:.1f} GB)...")
                    downloader.download(
                        repo_id=model["repo_id"],
                        filename=model["filename"],
                    )
                    if verbose:
                        messages.append(f"✓ Downloaded: {model['filename']}")
                        print(f"  ✓ Downloaded: {model['name']}")
                except Exception as e:
                    error_msg = f"✗ Failed to download {model['filename']}: {e}"
                    messages.append(error_msg)
                    if verbose:
                        print(f"  {error_msg}")
                    return QuickModeCheckResult(
                        passed=False,
                        missing_models=missing,
                        total_size_gb=total_size,
                        messages=messages,
                    )
            
            if verbose:
                print("✓ All model downloads complete!\n")
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

