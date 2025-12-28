# ============================================================
#  ANM V0-OpenSource — Dependency Manager
#  Auto-Detection & Installation of Dependencies
# ============================================================

"""
Dependency management for ANM.

Handles:
- Checking for required dependencies
- Auto-installation of Python packages
- System dependency detection
- Ollama installation
- Model downloads
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import subprocess
import sys
import os
import shutil
import urllib.request
import json

from anm.system.platform import get_platform, Platform

__all__ = [
    "DependencyManager",
    "Dependency",
    "DependencyStatus",
    "DependencyType",
    "check_dependencies",
    "install_dependency",
    "auto_setup",
]


class DependencyType(Enum):
    """Types of dependencies."""
    PYTHON_PACKAGE = "python_package"
    SYSTEM_BINARY = "system_binary"
    OLLAMA_MODEL = "ollama_model"
    EXTERNAL_SERVICE = "external_service"


class DependencyStatus(Enum):
    """Status of a dependency."""
    INSTALLED = "installed"
    MISSING = "missing"
    OUTDATED = "outdated"
    ERROR = "error"
    CHECKING = "checking"


@dataclass
class Dependency:
    """A single dependency."""
    name: str
    type: DependencyType
    required: bool = True
    version: Optional[str] = None
    install_cmd: Optional[str] = None
    check_cmd: Optional[str] = None
    url: Optional[str] = None
    description: str = ""
    status: DependencyStatus = DependencyStatus.CHECKING
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "required": self.required,
            "version": self.version,
            "status": self.status.value,
            "error_message": self.error_message,
        }


# ============================================================
#  Core Dependencies
# ============================================================

PYTHON_DEPENDENCIES = [
    Dependency(
        name="llama_cpp",
        type=DependencyType.PYTHON_PACKAGE,
        required=True,
        description="Local LLM inference (llama-cpp-python)",
    ),
    Dependency(
        name="huggingface_hub",
        type=DependencyType.PYTHON_PACKAGE,
        required=True,
        description="Model downloading from HuggingFace",
    ),
    Dependency(
        name="requests",
        type=DependencyType.PYTHON_PACKAGE,
        required=True,
        description="HTTP library for web requests",
    ),
    Dependency(
        name="numpy",
        type=DependencyType.PYTHON_PACKAGE,
        required=False,
        description="Numerical computing",
    ),
    Dependency(
        name="psutil",
        type=DependencyType.PYTHON_PACKAGE,
        required=False,
        description="System monitoring",
    ),
]

SYSTEM_DEPENDENCIES = [
    Dependency(
        name="ffmpeg",
        type=DependencyType.SYSTEM_BINARY,
        required=False,
        check_cmd="ffmpeg -version",
        description="Video/audio processing",
    ),
]

# GGUF models (auto-downloaded from HuggingFace)
GGUF_MODELS = [
    Dependency(
        name="DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M",
        type=DependencyType.PYTHON_PACKAGE,  # Uses HuggingFace download
        required=True,
        description="Primary reasoning model (GGUF)",
    ),
]


class DependencyManager:
    """
    Manages ANM dependencies across platforms.
    
    Features:
    - Checks for Python packages
    - Checks for system binaries
    - Auto-installs when possible
    - Provides installation instructions
    """
    
    def __init__(self):
        self.platform = get_platform()
        self.dependencies: List[Dependency] = []
        self._load_default_dependencies()
    
    def _load_default_dependencies(self) -> None:
        """Load default dependency list."""
        self.dependencies = []
        self.dependencies.extend(PYTHON_DEPENDENCIES)
        self.dependencies.extend(SYSTEM_DEPENDENCIES)
    
    def check_all(self) -> Dict[str, Dependency]:
        """Check all dependencies."""
        results = {}
        
        for dep in self.dependencies:
            self._check_dependency(dep)
            results[dep.name] = dep
        
        return results
    
    def _check_dependency(self, dep: Dependency) -> None:
        """Check a single dependency."""
        try:
            if dep.type == DependencyType.PYTHON_PACKAGE:
                self._check_python_package(dep)
            elif dep.type == DependencyType.SYSTEM_BINARY:
                self._check_system_binary(dep)
            else:
                dep.status = DependencyStatus.ERROR
                dep.error_message = "Unknown dependency type"
        except Exception as e:
            dep.status = DependencyStatus.ERROR
            dep.error_message = str(e)
    
    def _check_python_package(self, dep: Dependency) -> None:
        """Check if a Python package is installed."""
        try:
            __import__(dep.name)
            dep.status = DependencyStatus.INSTALLED
        except ImportError:
            dep.status = DependencyStatus.MISSING
    
    def _check_system_binary(self, dep: Dependency) -> None:
        """Check if a system binary is available."""
        # First try shutil.which
        if shutil.which(dep.name):
            dep.status = DependencyStatus.INSTALLED
            return
        
        # Try the check command if provided
        if dep.check_cmd:
            try:
                result = subprocess.run(
                    dep.check_cmd.split(),
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    dep.status = DependencyStatus.INSTALLED
                    return
            except Exception:
                pass
        
        dep.status = DependencyStatus.MISSING
    
    def _check_ollama_model(self, dep: Dependency) -> None:
        """Check if an Ollama model is installed."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                if dep.name in result.stdout:
                    dep.status = DependencyStatus.INSTALLED
                else:
                    dep.status = DependencyStatus.MISSING
            else:
                dep.status = DependencyStatus.ERROR
                dep.error_message = "Ollama not available"
        except FileNotFoundError:
            dep.status = DependencyStatus.ERROR
            dep.error_message = "Ollama not installed"
        except Exception as e:
            dep.status = DependencyStatus.ERROR
            dep.error_message = str(e)
    
    def install(self, dep: Dependency, interactive: bool = True) -> bool:
        """
        Install a dependency.
        
        Args:
            dep: The dependency to install
            interactive: Whether to prompt user
            
        Returns:
            True if installation successful
        """
        try:
            if dep.type == DependencyType.PYTHON_PACKAGE:
                return self._install_python_package(dep)
            elif dep.type == DependencyType.SYSTEM_BINARY:
                return self._install_system_binary(dep, interactive)
            elif dep.type == DependencyType.OLLAMA_MODEL:
                return self._install_ollama_model(dep)
            else:
                return False
        except Exception as e:
            dep.error_message = str(e)
            return False
    
    def _install_python_package(self, dep: Dependency) -> bool:
        """Install a Python package via pip."""
        try:
            cmd = [sys.executable, "-m", "pip", "install", dep.name]
            if dep.version:
                cmd[-1] = f"{dep.name}=={dep.version}"
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if result.returncode == 0:
                dep.status = DependencyStatus.INSTALLED
                return True
            else:
                dep.error_message = result.stderr
                return False
                
        except Exception as e:
            dep.error_message = str(e)
            return False
    
    def _install_system_binary(self, dep: Dependency, interactive: bool) -> bool:
        """Provide instructions for installing system binary."""
        if dep.name == "ollama":
            return self._install_ollama(interactive)
        
        # For other binaries, provide platform-specific instructions
        instructions = self._get_install_instructions(dep)
        if instructions:
            print(f"\nTo install {dep.name}:")
            print(instructions)
        
        return False
    
    def _install_ollama(self, interactive: bool) -> bool:
        """Install Ollama."""
        plat = self.platform
        
        print("\n📦 Installing Ollama...")
        
        try:
            if plat == Platform.MACOS:
                # macOS: Use curl installer
                cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
                print(f"Running: {cmd}")
                result = subprocess.run(
                    ["sh", "-c", cmd],
                    timeout=300,
                )
                return result.returncode == 0
            
            elif plat == Platform.LINUX:
                # Linux: Use curl installer
                cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
                print(f"Running: {cmd}")
                result = subprocess.run(
                    ["sh", "-c", cmd],
                    timeout=300,
                )
                return result.returncode == 0
            
            elif plat == Platform.WINDOWS:
                # Windows: Download and run installer
                print("Please download Ollama from: https://ollama.ai/download")
                print("After installation, restart your terminal and run ANM again.")
                
                if interactive:
                    # Try to open browser
                    try:
                        import webbrowser
                        webbrowser.open("https://ollama.ai/download")
                    except Exception:
                        pass
                
                return False
            
        except Exception as e:
            print(f"Error installing Ollama: {e}")
            return False
        
        return False
    
    def _install_ollama_model(self, dep: Dependency) -> bool:
        """Pull an Ollama model."""
        try:
            print(f"\n📥 Pulling model: {dep.name}")
            result = subprocess.run(
                ["ollama", "pull", dep.name],
                timeout=1800,  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                dep.status = DependencyStatus.INSTALLED
                return True
            else:
                return False
                
        except Exception as e:
            dep.error_message = str(e)
            return False
    
    def _get_install_instructions(self, dep: Dependency) -> str:
        """Get platform-specific install instructions."""
        plat = self.platform
        
        if dep.name == "ffmpeg":
            if plat == Platform.MACOS:
                return "brew install ffmpeg"
            elif plat == Platform.LINUX:
                return "sudo apt install ffmpeg  # or: sudo dnf install ffmpeg"
            elif plat == Platform.WINDOWS:
                return "winget install ffmpeg  # or download from https://ffmpeg.org"
        
        if dep.url:
            return f"Download from: {dep.url}"
        
        return ""
    
    def get_missing(self, required_only: bool = True) -> List[Dependency]:
        """Get list of missing dependencies."""
        missing = []
        for dep in self.dependencies:
            if dep.status == DependencyStatus.MISSING:
                if required_only and not dep.required:
                    continue
                missing.append(dep)
        return missing
    
    def get_status_report(self) -> str:
        """Get a formatted status report."""
        lines = ["ANM Dependency Status", "=" * 40]
        
        for dep in self.dependencies:
            status_icon = {
                DependencyStatus.INSTALLED: "✅",
                DependencyStatus.MISSING: "❌",
                DependencyStatus.OUTDATED: "⚠️",
                DependencyStatus.ERROR: "💥",
                DependencyStatus.CHECKING: "🔍",
            }.get(dep.status, "?")
            
            req = "required" if dep.required else "optional"
            lines.append(f"{status_icon} {dep.name} ({req})")
            
            if dep.error_message:
                lines.append(f"   └─ {dep.error_message}")
        
        return "\n".join(lines)


def check_dependencies() -> Dict[str, Dependency]:
    """Check all ANM dependencies."""
    manager = DependencyManager()
    return manager.check_all()


def install_dependency(name: str) -> bool:
    """Install a specific dependency."""
    manager = DependencyManager()
    manager.check_all()
    
    for dep in manager.dependencies:
        if dep.name == name:
            return manager.install(dep)
    
    return False


def auto_setup(interactive: bool = True) -> bool:
    """
    Automatically set up ANM dependencies.
    
    Args:
        interactive: Whether to prompt user for confirmations
        
    Returns:
        True if all required dependencies are satisfied
    """
    print("🔧 ANM V0-OpenSource Auto-Setup")
    print("=" * 40)
    
    manager = DependencyManager()
    results = manager.check_all()
    
    # Show status
    print(manager.get_status_report())
    print()
    
    # Get missing required dependencies
    missing = manager.get_missing(required_only=True)
    
    if not missing:
        print("✅ All required dependencies are installed!")
        return True
    
    print(f"\n⚠️  {len(missing)} required dependencies missing:")
    for dep in missing:
        print(f"   - {dep.name}: {dep.description}")
    
    # Ask for confirmation
    if interactive:
        try:
            response = input("\nInstall missing dependencies? [Y/n]: ").strip().lower()
            if response and response != "y":
                print("Skipping installation.")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping installation.")
            return False
    
    # Install missing dependencies
    all_success = True
    for dep in missing:
        print(f"\n📦 Installing {dep.name}...")
        success = manager.install(dep, interactive=interactive)
        if success:
            print(f"   ✅ {dep.name} installed successfully")
        else:
            print(f"   ❌ Failed to install {dep.name}")
            if dep.error_message:
                print(f"      Error: {dep.error_message}")
            all_success = False
    
    if all_success:
        print("\n✅ All dependencies installed successfully!")
    else:
        print("\n⚠️  Some dependencies could not be installed automatically.")
        print("Please install them manually and try again.")
    
    return all_success
