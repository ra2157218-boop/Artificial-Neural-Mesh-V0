# ============================================================
#  ANM V0-OpenSource — SYSTEM MODULE
#  Cross-Platform Support • Hardware Detection • Model Inference
# ============================================================

"""
ANM System Module - Cross-platform utilities.

Provides:
- OS detection (Windows, macOS, Linux)
- Hardware detection (CPU, GPU, RAM, NPU)
- Platform-specific paths
- Dependency management
- Model inference (llama-cpp-python)
- Model downloading (HuggingFace Hub)
"""

__version__ = "0.1.0-opensource"

from anm.system.platform import (
    Platform,
    PlatformInfo,
    get_platform,
    get_platform_info,
    is_windows,
    is_macos,
    is_linux,
)

from anm.system.hardware import (
    HardwareInfo,
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    get_hardware_info,
    get_cpu_info,
    get_gpu_info,
    get_memory_info,
    can_run_local_llm,
)

from anm.system.paths import (
    ANMPaths,
    get_anm_paths,
    ensure_directories,
)

from anm.system.dependencies import (
    DependencyManager,
    Dependency,
    DependencyStatus,
    check_dependencies,
    install_dependency,
    auto_setup,
)

from anm.system.inference import (
    InferenceEngine,
    InferenceConfig,
    InferenceResult,
    get_inference_engine,
    run_model,
)

from anm.system.model_downloader import (
    ModelDownloader,
    ModelInfo,
    get_models_directory,
    list_cached_models,
)

__all__ = [
    # Platform
    "Platform",
    "PlatformInfo",
    "get_platform",
    "get_platform_info",
    "is_windows",
    "is_macos",
    "is_linux",
    
    # Hardware
    "HardwareInfo",
    "CPUInfo",
    "GPUInfo",
    "MemoryInfo",
    "get_hardware_info",
    "get_cpu_info",
    "get_gpu_info",
    "get_memory_info",
    "can_run_local_llm",
    
    # Paths
    "ANMPaths",
    "get_anm_paths",
    "ensure_directories",
    
    # Dependencies
    "DependencyManager",
    "Dependency",
    "DependencyStatus",
    "check_dependencies",
    "install_dependency",
    "auto_setup",
    
    # Inference
    "InferenceEngine",
    "InferenceConfig",
    "InferenceResult",
    "get_inference_engine",
    "run_model",
    
    # Model Downloader
    "ModelDownloader",
    "ModelInfo",
    "get_models_directory",
    "list_cached_models",
]
