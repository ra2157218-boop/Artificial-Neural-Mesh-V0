# ============================================================
#  ANM V0-OpenSource — Platform Detection
#  Cross-Platform OS Detection & Information
# ============================================================

"""
Platform detection for ANM.

Supports:
- Windows (10, 11)
- macOS (Intel, Apple Silicon)
- Linux (Ubuntu, Debian, Fedora, Arch, etc.)
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
import platform
import sys
import os
import subprocess

__all__ = [
    "Platform",
    "PlatformInfo",
    "get_platform",
    "get_platform_info",
    "is_windows",
    "is_macos",
    "is_linux",
]


class Platform(Enum):
    """Supported platforms."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """Detailed platform information."""
    platform: Platform
    os_name: str
    os_version: str
    os_release: str
    architecture: str
    machine: str
    python_version: str
    is_64bit: bool
    
    # macOS specific
    is_apple_silicon: bool = False
    macos_version: Optional[str] = None
    
    # Linux specific
    linux_distro: Optional[str] = None
    linux_distro_version: Optional[str] = None
    
    # Windows specific
    windows_edition: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [f"{self.os_name} {self.os_version}"]
        if self.linux_distro:
            parts[0] = f"{self.linux_distro} {self.linux_distro_version or ''}"
        parts.append(f"({self.architecture})")
        if self.is_apple_silicon:
            parts.append("[Apple Silicon]")
        return " ".join(parts)
    
    def to_dict(self) -> dict:
        return {
            "platform": self.platform.value,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "os_release": self.os_release,
            "architecture": self.architecture,
            "machine": self.machine,
            "python_version": self.python_version,
            "is_64bit": self.is_64bit,
            "is_apple_silicon": self.is_apple_silicon,
            "macos_version": self.macos_version,
            "linux_distro": self.linux_distro,
            "linux_distro_version": self.linux_distro_version,
            "windows_edition": self.windows_edition,
        }


def get_platform() -> Platform:
    """Get the current platform."""
    system = platform.system().lower()
    
    if system == "windows":
        return Platform.WINDOWS
    elif system == "darwin":
        return Platform.MACOS
    elif system == "linux":
        return Platform.LINUX
    else:
        return Platform.UNKNOWN


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == Platform.WINDOWS


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform() == Platform.MACOS


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == Platform.LINUX


def get_platform_info() -> PlatformInfo:
    """Get detailed platform information."""
    plat = get_platform()
    
    info = PlatformInfo(
        platform=plat,
        os_name=platform.system(),
        os_version=platform.version(),
        os_release=platform.release(),
        architecture=platform.machine(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        is_64bit=sys.maxsize > 2**32,
    )
    
    if plat == Platform.MACOS:
        info = _enrich_macos_info(info)
    elif plat == Platform.LINUX:
        info = _enrich_linux_info(info)
    elif plat == Platform.WINDOWS:
        info = _enrich_windows_info(info)
    
    return info


def _enrich_macos_info(info: PlatformInfo) -> PlatformInfo:
    """Add macOS-specific information."""
    try:
        # Get macOS version
        mac_ver = platform.mac_ver()
        info.macos_version = mac_ver[0]
        
        # Check for Apple Silicon
        info.is_apple_silicon = info.machine in ("arm64", "aarch64")
        
        # Get marketing name
        try:
            result = subprocess.run(
                ["sw_vers", "-productVersion"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info.os_version = result.stdout.strip()
        except Exception:
            pass
            
    except Exception:
        pass
    
    return info


def _enrich_linux_info(info: PlatformInfo) -> PlatformInfo:
    """Add Linux-specific information."""
    try:
        # Try /etc/os-release first (most modern distros)
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("NAME="):
                        info.linux_distro = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        info.linux_distro_version = line.split("=")[1].strip().strip('"')
        
        # Fallback to lsb_release
        if not info.linux_distro:
            try:
                result = subprocess.run(
                    ["lsb_release", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    info.linux_distro = result.stdout.split(":")[1].strip()
            except Exception:
                pass
        
        # Detect common distros
        if not info.linux_distro:
            distro_files = {
                "/etc/debian_version": "Debian",
                "/etc/fedora-release": "Fedora",
                "/etc/arch-release": "Arch Linux",
                "/etc/gentoo-release": "Gentoo",
                "/etc/centos-release": "CentOS",
                "/etc/redhat-release": "Red Hat",
            }
            for path, name in distro_files.items():
                if os.path.exists(path):
                    info.linux_distro = name
                    break
                    
    except Exception:
        pass
    
    return info


def _enrich_windows_info(info: PlatformInfo) -> PlatformInfo:
    """Add Windows-specific information."""
    try:
        # Get Windows edition
        win_ver = platform.win32_ver()
        info.windows_edition = win_ver[0]
        
        # Try to get more details via WMI
        try:
            import subprocess
            result = subprocess.run(
                ["wmic", "os", "get", "Caption"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    info.os_name = lines[1].strip()
        except Exception:
            pass
            
    except Exception:
        pass
    
    return info
