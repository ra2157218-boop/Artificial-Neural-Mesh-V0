# ============================================================
#  ANM V0-OpenSource — Hardware Detection
#  CPU, GPU, RAM, NPU Detection Across Platforms
# ============================================================

"""
Hardware detection for ANM.

Detects:
- CPU (cores, threads, speed, architecture)
- GPU (NVIDIA, AMD, Intel, Apple)
- RAM (total, available)
- NPU/Neural Engine (Apple, Intel, Qualcomm)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import platform
import os
import subprocess
import json
import logging

from anm.system.platform import get_platform, Platform

__all__ = [
    "HardwareInfo",
    "CPUInfo",
    "GPUInfo",
    "MemoryInfo",
    "GPUVendor",
    "get_hardware_info",
    "get_cpu_info",
    "get_gpu_info",
    "get_memory_info",
    "can_run_local_llm",
]


class GPUVendor(Enum):
    """GPU vendors."""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


@dataclass
class CPUInfo:
    """CPU information."""
    name: str = "Unknown"
    cores: int = 1
    threads: int = 1
    architecture: str = "unknown"
    frequency_mhz: Optional[float] = None
    is_arm: bool = False
    is_x86: bool = False
    has_avx: bool = False
    has_avx2: bool = False
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cores": self.cores,
            "threads": self.threads,
            "architecture": self.architecture,
            "frequency_mhz": self.frequency_mhz,
            "is_arm": self.is_arm,
            "is_x86": self.is_x86,
        }


@dataclass
class GPUInfo:
    """GPU information."""
    name: str = "Unknown"
    vendor: GPUVendor = GPUVendor.UNKNOWN
    memory_mb: Optional[int] = None
    driver_version: Optional[str] = None
    cuda_available: bool = False
    cuda_version: Optional[str] = None
    metal_available: bool = False
    rocm_available: bool = False
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "vendor": self.vendor.value,
            "memory_mb": self.memory_mb,
            "driver_version": self.driver_version,
            "cuda_available": self.cuda_available,
            "cuda_version": self.cuda_version,
            "metal_available": self.metal_available,
            "rocm_available": self.rocm_available,
        }


@dataclass
class MemoryInfo:
    """Memory information."""
    total_mb: int = 0
    available_mb: int = 0
    used_mb: int = 0
    percent_used: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "total_mb": self.total_mb,
            "available_mb": self.available_mb,
            "used_mb": self.used_mb,
            "percent_used": self.percent_used,
        }


@dataclass
class HardwareInfo:
    """Complete hardware information."""
    cpu: CPUInfo = field(default_factory=CPUInfo)
    gpu: GPUInfo = field(default_factory=GPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    gpus: List[GPUInfo] = field(default_factory=list)
    has_neural_engine: bool = False
    neural_engine_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "cpu": self.cpu.to_dict(),
            "gpu": self.gpu.to_dict(),
            "memory": self.memory.to_dict(),
            "gpus": [g.to_dict() for g in self.gpus],
            "has_neural_engine": self.has_neural_engine,
            "neural_engine_type": self.neural_engine_type,
        }
    
    def summary(self) -> str:
        """Get a human-readable summary."""
        lines = [
            f"CPU: {self.cpu.name} ({self.cpu.cores}C/{self.cpu.threads}T)",
            f"GPU: {self.gpu.name}",
            f"RAM: {self.memory.total_mb // 1024} GB ({self.memory.available_mb // 1024} GB free)",
        ]
        if self.has_neural_engine:
            lines.append(f"NPU: {self.neural_engine_type}")
        return "\n".join(lines)


def get_cpu_info() -> CPUInfo:
    """Get CPU information."""
    info = CPUInfo()
    plat = get_platform()
    
    # Basic info
    info.architecture = platform.machine()
    info.is_arm = info.architecture in ("arm64", "aarch64", "armv7l", "armv8l")
    info.is_x86 = info.architecture in ("x86_64", "AMD64", "x86", "i386", "i686")
    
    # Get CPU count
    try:
        info.cores = os.cpu_count() or 1
        info.threads = info.cores  # Default to same as cores
    except Exception as e:
        logging.warning(f"Failed to get CPU count: {e}")
    
    if plat == Platform.MACOS:
        info = _get_macos_cpu_info(info)
    elif plat == Platform.LINUX:
        info = _get_linux_cpu_info(info)
    elif plat == Platform.WINDOWS:
        info = _get_windows_cpu_info(info)
    
    return info


def _get_macos_cpu_info(info: CPUInfo) -> CPUInfo:
    """Get macOS CPU info via sysctl."""
    try:
        # CPU name
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info.name = result.stdout.strip()
        
        # Physical cores
        result = subprocess.run(
            ["sysctl", "-n", "hw.physicalcpu"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info.cores = int(result.stdout.strip())
        
        # Logical cores
        result = subprocess.run(
            ["sysctl", "-n", "hw.logicalcpu"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info.threads = int(result.stdout.strip())

    except Exception as e:
        logging.warning(f"Failed to get macOS CPU info: {e}")

    return info


def _get_linux_cpu_info(info: CPUInfo) -> CPUInfo:
    """Get Linux CPU info from /proc/cpuinfo."""
    try:
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
            
            for line in cpuinfo.split("\n"):
                if "model name" in line:
                    info.name = line.split(":")[1].strip()
                    break
            
            # Count physical cores
            cores = set()
            for line in cpuinfo.split("\n"):
                if "core id" in line:
                    cores.add(line.split(":")[1].strip())
            if cores:
                info.cores = len(cores)
            
            # Count threads
            info.threads = cpuinfo.count("processor")

    except Exception as e:
        logging.warning(f"Failed to get Linux CPU info: {e}")

    return info


def _get_windows_cpu_info(info: CPUInfo) -> CPUInfo:
    """Get Windows CPU info via WMIC."""
    try:
        # CPU name
        result = subprocess.run(
            ["wmic", "cpu", "get", "name"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                info.name = lines[1].strip()
        
        # Cores
        result = subprocess.run(
            ["wmic", "cpu", "get", "NumberOfCores"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                info.cores = int(lines[1].strip())
        
        # Threads
        result = subprocess.run(
            ["wmic", "cpu", "get", "NumberOfLogicalProcessors"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                info.threads = int(lines[1].strip())

    except Exception as e:
        logging.warning(f"Failed to get Windows CPU info: {e}")

    return info


def get_gpu_info() -> GPUInfo:
    """Get primary GPU information."""
    info = GPUInfo()
    plat = get_platform()
    
    if plat == Platform.MACOS:
        info = _get_macos_gpu_info(info)
    elif plat == Platform.LINUX:
        info = _get_linux_gpu_info(info)
    elif plat == Platform.WINDOWS:
        info = _get_windows_gpu_info(info)
    
    # Check for CUDA
    info = _check_cuda(info)
    
    return info


def _get_macos_gpu_info(info: GPUInfo) -> GPUInfo:
    """Get macOS GPU info via system_profiler."""
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            displays = data.get("SPDisplaysDataType", [])
            if displays:
                gpu = displays[0]
                info.name = gpu.get("sppci_model", "Unknown")
                
                # Check vendor
                name_lower = info.name.lower()
                if "apple" in name_lower or "m1" in name_lower or "m2" in name_lower or "m3" in name_lower:
                    info.vendor = GPUVendor.APPLE
                    info.metal_available = True
                elif "amd" in name_lower or "radeon" in name_lower:
                    info.vendor = GPUVendor.AMD
                    info.metal_available = True
                elif "intel" in name_lower:
                    info.vendor = GPUVendor.INTEL
                    info.metal_available = True
                elif "nvidia" in name_lower:
                    info.vendor = GPUVendor.NVIDIA
                    
                # Get VRAM
                vram = gpu.get("sppci_vram", "")
                if vram:
                    # Parse "8 GB" format
                    try:
                        parts = vram.split()
                        if len(parts) >= 2:
                            value = float(parts[0])
                            unit = parts[1].upper()
                            if unit == "GB":
                                info.memory_mb = int(value * 1024)
                            elif unit == "MB":
                                info.memory_mb = int(value)
                    except Exception as e:
                        logging.debug(f"Failed to parse VRAM: {e}")

    except Exception as e:
        logging.warning(f"Failed to get macOS GPU info: {e}")

    return info


def _get_linux_gpu_info(info: GPUInfo) -> GPUInfo:
    """Get Linux GPU info via lspci."""
    try:
        # Try lspci
        result = subprocess.run(
            ["lspci"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "VGA" in line or "3D" in line or "Display" in line:
                    info.name = line.split(":")[-1].strip()
                    
                    # Detect vendor
                    name_lower = info.name.lower()
                    if "nvidia" in name_lower:
                        info.vendor = GPUVendor.NVIDIA
                    elif "amd" in name_lower or "radeon" in name_lower:
                        info.vendor = GPUVendor.AMD
                    elif "intel" in name_lower:
                        info.vendor = GPUVendor.INTEL
                    break
        
        # Check for ROCm (AMD)
        if os.path.exists("/opt/rocm"):
            info.rocm_available = True

    except Exception as e:
        logging.warning(f"Failed to get Linux GPU info: {e}")

    return info


def _get_windows_gpu_info(info: GPUInfo) -> GPUInfo:
    """Get Windows GPU info via WMIC."""
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "name"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                info.name = lines[1].strip()
                
                # Detect vendor
                name_lower = info.name.lower()
                if "nvidia" in name_lower:
                    info.vendor = GPUVendor.NVIDIA
                elif "amd" in name_lower or "radeon" in name_lower:
                    info.vendor = GPUVendor.AMD
                elif "intel" in name_lower:
                    info.vendor = GPUVendor.INTEL

    except Exception as e:
        logging.warning(f"Failed to get Windows GPU info: {e}")

    return info


def _check_cuda(info: GPUInfo) -> GPUInfo:
    """Check for CUDA availability."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            info.cuda_available = True
            info.driver_version = result.stdout.strip()
            info.vendor = GPUVendor.NVIDIA
            
            # Get CUDA version
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=cuda_version", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                info.cuda_version = result.stdout.strip()

    except Exception as e:
        logging.debug(f"CUDA not available: {e}")

    return info


def get_memory_info() -> MemoryInfo:
    """Get memory information."""
    info = MemoryInfo()
    plat = get_platform()
    
    try:
        # Try psutil first (cross-platform)
        try:
            import psutil
            mem = psutil.virtual_memory()
            info.total_mb = mem.total // (1024 * 1024)
            info.available_mb = mem.available // (1024 * 1024)
            info.used_mb = mem.used // (1024 * 1024)
            info.percent_used = mem.percent
            return info
        except ImportError:
            pass
        
        if plat == Platform.MACOS:
            # macOS
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                info.total_mb = int(result.stdout.strip()) // (1024 * 1024)
                
        elif plat == Platform.LINUX:
            # Linux
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            info.total_mb = int(line.split()[1]) // 1024
                        elif line.startswith("MemAvailable:"):
                            info.available_mb = int(line.split()[1]) // 1024
                            
        elif plat == Platform.WINDOWS:
            # Windows
            result = subprocess.run(
                ["wmic", "OS", "get", "TotalVisibleMemorySize"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    info.total_mb = int(lines[1].strip()) // 1024

    except Exception as e:
        logging.warning(f"Failed to get memory info: {e}")

    if info.total_mb > 0 and info.available_mb > 0:
        info.used_mb = info.total_mb - info.available_mb
        info.percent_used = (info.used_mb / info.total_mb) * 100
    
    return info


def get_hardware_info() -> HardwareInfo:
    """Get complete hardware information."""
    info = HardwareInfo()
    
    info.cpu = get_cpu_info()
    info.gpu = get_gpu_info()
    info.memory = get_memory_info()
    
    # Check for Neural Engine
    plat = get_platform()
    if plat == Platform.MACOS and info.cpu.is_arm:
        info.has_neural_engine = True
        info.neural_engine_type = "Apple Neural Engine"
    
    return info


def can_run_local_llm(min_ram_gb: float = 8.0, require_gpu: bool = False) -> bool:
    """
    Check if the system can run a local LLM.
    
    Args:
        min_ram_gb: Minimum RAM required in GB
        require_gpu: Whether GPU is required
        
    Returns:
        True if system meets requirements
    """
    hw = get_hardware_info()
    
    # Check RAM
    if hw.memory.total_mb < min_ram_gb * 1024:
        return False
    
    # Check GPU if required
    if require_gpu:
        if hw.gpu.vendor == GPUVendor.UNKNOWN:
            return False
        if not (hw.gpu.cuda_available or hw.gpu.metal_available or hw.gpu.rocm_available):
            return False
    
    return True
