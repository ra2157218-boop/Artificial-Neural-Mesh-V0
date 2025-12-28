# ============================================================
#  ANM V0-OpenSource — Cross-Platform Paths
#  Platform-Specific Directory Management
# ============================================================

"""
Cross-platform path management for ANM.

Handles:
- Data directories
- Cache directories
- Config directories
- Model storage
- Log directories
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from anm.system.platform import get_platform, Platform

__all__ = [
    "ANMPaths",
    "get_anm_paths",
    "ensure_directories",
]


@dataclass
class ANMPaths:
    """All ANM directory paths."""
    
    # Base directories
    root: Path
    data: Path
    cache: Path
    config: Path
    logs: Path
    
    # Specific directories
    models: Path
    embeddings: Path
    memory: Path
    diary: Path
    learning: Path
    simulations: Path
    voice: Path
    temp: Path
    
    def ensure_all(self) -> None:
        """Create all directories if they don't exist."""
        for field_name in self.__dataclass_fields__:
            path = getattr(self, field_name)
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        return {
            name: str(getattr(self, name))
            for name in self.__dataclass_fields__
        }


def _get_app_data_dir() -> Path:
    """Get the platform-specific app data directory."""
    plat = get_platform()
    
    if plat == Platform.WINDOWS:
        # Windows: %LOCALAPPDATA%\ANM or %APPDATA%\ANM
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "ANM"
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "ANM"
        return Path.home() / "AppData" / "Local" / "ANM"
    
    elif plat == Platform.MACOS:
        # macOS: ~/Library/Application Support/ANM
        return Path.home() / "Library" / "Application Support" / "ANM"
    
    elif plat == Platform.LINUX:
        # Linux: ~/.local/share/ANM (XDG compliant)
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / "ANM"
        return Path.home() / ".local" / "share" / "ANM"
    
    else:
        # Fallback
        return Path.home() / ".anm"


def _get_cache_dir() -> Path:
    """Get the platform-specific cache directory."""
    plat = get_platform()
    
    if plat == Platform.WINDOWS:
        # Windows: %LOCALAPPDATA%\ANM\Cache
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "ANM" / "Cache"
        return Path.home() / "AppData" / "Local" / "ANM" / "Cache"
    
    elif plat == Platform.MACOS:
        # macOS: ~/Library/Caches/ANM
        return Path.home() / "Library" / "Caches" / "ANM"
    
    elif plat == Platform.LINUX:
        # Linux: ~/.cache/ANM (XDG compliant)
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / "ANM"
        return Path.home() / ".cache" / "ANM"
    
    else:
        return Path.home() / ".anm" / "cache"


def _get_config_dir() -> Path:
    """Get the platform-specific config directory."""
    plat = get_platform()
    
    if plat == Platform.WINDOWS:
        # Windows: %APPDATA%\ANM
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "ANM"
        return Path.home() / "AppData" / "Roaming" / "ANM"
    
    elif plat == Platform.MACOS:
        # macOS: ~/Library/Preferences/ANM
        return Path.home() / "Library" / "Preferences" / "ANM"
    
    elif plat == Platform.LINUX:
        # Linux: ~/.config/ANM (XDG compliant)
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "ANM"
        return Path.home() / ".config" / "ANM"
    
    else:
        return Path.home() / ".anm" / "config"


def _get_log_dir() -> Path:
    """Get the platform-specific log directory."""
    plat = get_platform()
    
    if plat == Platform.WINDOWS:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "ANM" / "Logs"
        return Path.home() / "AppData" / "Local" / "ANM" / "Logs"
    
    elif plat == Platform.MACOS:
        return Path.home() / "Library" / "Logs" / "ANM"
    
    elif plat == Platform.LINUX:
        xdg_state = os.environ.get("XDG_STATE_HOME")
        if xdg_state:
            return Path(xdg_state) / "ANM" / "logs"
        return Path.home() / ".local" / "state" / "ANM" / "logs"
    
    else:
        return Path.home() / ".anm" / "logs"


def _get_temp_dir() -> Path:
    """Get the platform-specific temp directory."""
    plat = get_platform()
    
    if plat == Platform.WINDOWS:
        temp = os.environ.get("TEMP") or os.environ.get("TMP")
        if temp:
            return Path(temp) / "ANM"
        return Path.home() / "AppData" / "Local" / "Temp" / "ANM"
    
    elif plat == Platform.MACOS:
        return Path("/tmp") / "ANM"
    
    elif plat == Platform.LINUX:
        return Path("/tmp") / "ANM"
    
    else:
        return Path.home() / ".anm" / "temp"


def get_anm_paths(
    root_override: Optional[Path] = None,
    portable: bool = False,
) -> ANMPaths:
    """
    Get all ANM paths.
    
    Args:
        root_override: Override the root directory
        portable: If True, use portable mode (all in one directory)
        
    Returns:
        ANMPaths with all directory paths
    """
    if root_override:
        root = Path(root_override)
    elif portable:
        # Portable mode: everything in the current directory
        root = Path.cwd() / ".anm"
    else:
        root = _get_app_data_dir()
    
    if portable:
        # All directories under root in portable mode
        return ANMPaths(
            root=root,
            data=root / "data",
            cache=root / "cache",
            config=root / "config",
            logs=root / "logs",
            models=root / "models",
            embeddings=root / "embeddings",
            memory=root / "memory",
            diary=root / "diary",
            learning=root / "learning",
            simulations=root / "simulations",
            voice=root / "voice",
            temp=root / "temp",
        )
    else:
        # Platform-specific directories
        data = root
        cache = _get_cache_dir()
        config = _get_config_dir()
        logs = _get_log_dir()
        temp = _get_temp_dir()
        
        return ANMPaths(
            root=root,
            data=data,
            cache=cache,
            config=config,
            logs=logs,
            models=data / "models",
            embeddings=cache / "embeddings",
            memory=data / "memory",
            diary=data / "diary",
            learning=data / "learning",
            simulations=data / "simulations",
            voice=data / "voice",
            temp=temp,
        )


def ensure_directories(paths: Optional[ANMPaths] = None) -> ANMPaths:
    """
    Ensure all ANM directories exist.
    
    Args:
        paths: Paths to ensure (if None, uses default)
        
    Returns:
        ANMPaths with all directories created
    """
    if paths is None:
        paths = get_anm_paths()
    
    paths.ensure_all()
    return paths
