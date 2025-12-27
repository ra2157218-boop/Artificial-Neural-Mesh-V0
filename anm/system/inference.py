# ============================================================
#  ANM V0-OpenSource — Inference Engine
#  Direct Model Loading with llama-cpp-python
#  GPU Acceleration: Metal (Apple) / CUDA (NVIDIA) / CPU Fallback
# ============================================================

"""
ANM Inference Engine - Direct model inference using llama-cpp-python.

Features:
- Auto-detects GPU (Metal/CUDA) or falls back to CPU
- Singleton model cache (load once, reuse)
- Automatic GGUF model downloading from HuggingFace
- Thread-safe inference
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from threading import Lock
import os
import time
import logging

# Memory optimization
from anm.core.memory_optimizer import CleanupHook, MemoryContext

__all__ = [
    "InferenceEngine",
    "InferenceConfig",
    "InferenceResult",
    "get_inference_engine",
    "run_model",
]


@dataclass
class InferenceConfig:
    """Configuration for inference engine."""
    # Model settings
    model_path: Optional[str] = None
    model_repo: str = "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF"
    model_filename: str = "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf"
    
    # Quick mode settings (smaller, faster model)
    quick_mode: bool = False
    quick_model_repo: str = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    quick_model_filename: str = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    
    # Domain-specific model overrides (e.g., {"code": {"repo": "...", "filename": "..."}})
    domain_models: Optional[Dict[str, Dict[str, str]]] = None
    
    # Generation settings
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    # Quick mode generation settings (faster, no CoT)
    quick_max_tokens: int = 512  # Shorter responses in quick mode
    quick_temperature: float = 0.3  # Lower temperature for more direct answers
    
    # Context settings
    context_length: int = 4096
    quick_context_length: int = 2048  # Smaller context for quick mode
    
    # Hardware settings
    n_gpu_layers: int = -1  # -1 = all layers on GPU
    n_threads: Optional[int] = None  # None = auto-detect
    n_batch: int = 512
    
    # Behavior
    verbose: bool = False
    use_mmap: bool = True
    use_mlock: bool = False


@dataclass
class InferenceResult:
    """Result from inference."""
    text: str
    tokens_generated: int
    time_ms: float
    tokens_per_second: float
    success: bool
    error: Optional[str] = None


class InferenceEngine:
    """
    Direct model inference using llama-cpp-python.
    
    Features:
    - Auto-detects GPU (Metal/CUDA) or falls back to CPU
    - Singleton model cache (load once, reuse)
    - Automatic GGUF model downloading from HuggingFace
    - Thread-safe inference
    """
    
    _instance: Optional['InferenceEngine'] = None
    _lock: Lock = Lock()
    
    def __new__(cls, config: Optional[InferenceConfig] = None, _bypass_singleton: bool = False):
        """
        Singleton pattern - only one engine instance.
        
        Args:
            config: Optional configuration
            _bypass_singleton: If True, create a new instance (for domain-specific engines)
        """
        with cls._lock:
            if _bypass_singleton:
                # Create a new instance (bypass singleton for domain-specific engines)
                instance = super().__new__(cls)
                instance._initialized = False
                return instance
            
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config: Optional[InferenceConfig] = None):
        """Initialize the inference engine."""
        self._logger = logging.getLogger(__name__)
        
        if self._initialized:
            # If already initialized, update config if provided (for dynamic mode switching)
            if config is not None:
                # Only update if quick_mode changed (to avoid unnecessary model reloads)
                if self.config.quick_mode != config.quick_mode:
                    # Unload current model if mode changed
                    if self._model is not None:
                        self._logger.info(f"Mode changed, unloading model (quick_mode: {self.config.quick_mode} -> {config.quick_mode})")
                        self.unload_model()
                    # Update config
                    self.config = config
            return
        
        self.config = config or InferenceConfig()
        self._model = None
        self._model_path: Optional[Path] = None
        self._inference_lock = Lock()
        self._initialized = True
        self._llama_available = False
        
        # Check if llama-cpp-python is available
        try:
            from llama_cpp import Llama
            self._llama_available = True
            self._logger.debug("llama-cpp-python is available")
        except ImportError:
            self._llama_available = False
            self._logger.warning("llama-cpp-python not installed")
        
        # Register cleanup hook for model unloading
        cleanup_hook = CleanupHook()
        cleanup_hook.register(
            "inference_engine_model",
            self.unload_model,
            size_bytes=0,  # Will be updated when model is loaded
        )
    
    @property
    def is_available(self) -> bool:
        """Check if inference engine is available."""
        return self._llama_available
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
    
    def _detect_gpu_layers(self) -> int:
        """Detect optimal GPU layers based on hardware."""
        try:
            from anm.system.hardware import get_gpu_info, GPUVendor
            
            gpu = get_gpu_info()
            
            # Apple Silicon - use Metal
            if gpu.vendor == GPUVendor.APPLE or gpu.metal_available:
                return -1  # All layers on GPU
            
            # NVIDIA with CUDA
            if gpu.vendor == GPUVendor.NVIDIA and gpu.cuda_available:
                return -1  # All layers on GPU
            
            # AMD with ROCm
            if gpu.vendor == GPUVendor.AMD and gpu.rocm_available:
                return -1  # All layers on GPU
            
            # CPU fallback
            return 0
            
        except Exception:
            # Default to CPU if detection fails
            return 0
    
    def _get_model_path(self) -> Path:
        """Get path to model, downloading if necessary."""
        # Check environment variable first
        env_path = os.environ.get("ANM_MODEL_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Check config path
        if self.config.model_path and Path(self.config.model_path).exists():
            return Path(self.config.model_path)
        
        # Download from HuggingFace
        from anm.system.model_downloader import ModelDownloader
        
        downloader = ModelDownloader()
        
        # Choose model based on quick mode
        if self.config.quick_mode:
            repo_id = self.config.quick_model_repo
            filename = self.config.quick_model_filename
        else:
            repo_id = self.config.model_repo
            filename = self.config.model_filename
        
        return downloader.download(
            repo_id=repo_id,
            filename=filename,
        )
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Load GGUF model with GPU acceleration.
        
        Args:
            model_path: Optional path to model file
            
        Returns:
            True if model loaded successfully
        """
        if not self._llama_available:
            print("[InferenceEngine] llama-cpp-python not installed.")
            print("Install with: pip install llama-cpp-python")
            return False
        
        try:
            from llama_cpp import Llama
            
            # Get model path
            if model_path:
                path = Path(model_path)
            else:
                path = self._get_model_path()
            
            if not path.exists():
                print(f"[InferenceEngine] Model not found: {path}")
                return False
            
            self._model_path = path
            
            # Detect GPU layers
            n_gpu_layers = self.config.n_gpu_layers
            if n_gpu_layers == -1:
                n_gpu_layers = self._detect_gpu_layers()
                if n_gpu_layers == 0:
                    print("[InferenceEngine] No GPU detected, using CPU")
                else:
                    print("[InferenceEngine] GPU detected, offloading all layers")
            
            # Load model
            print(f"[InferenceEngine] Loading model: {path.name}")
            start_time = time.time()
            
            # Use appropriate context length based on mode
            ctx_length = self.config.quick_context_length if self.config.quick_mode else self.config.context_length
            
            self._model = Llama(
                model_path=str(path),
                n_ctx=ctx_length,
                n_gpu_layers=n_gpu_layers,
                n_threads=self.config.n_threads,
                n_batch=self.config.n_batch,
                use_mmap=self.config.use_mmap,
                use_mlock=self.config.use_mlock,
                verbose=self.config.verbose,
            )
            
            load_time = time.time() - start_time
            print(f"[InferenceEngine] Model loaded in {load_time:.2f}s")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load model: {e}"
            print(f"[InferenceEngine] {error_msg}")
            self._logger.error(error_msg, exc_info=True)
            self._model = None
            return False
    
    def unload_model(self) -> None:
        """Unload the current model to free memory."""
        with self._inference_lock:
            if self._model is not None:
                self._logger.info("Unloading model to free memory")
                # Explicitly delete model to help GC
                del self._model
            self._model = None
            self._model_path = None
            # Force garbage collection
            import gc
            gc.collect()
    
    def __enter__(self) -> 'InferenceEngine':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - unload model."""
        self.unload_model()
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences
            
        Returns:
            Generated text string
        """
        result = self.generate_full(prompt, max_tokens, temperature, stop)
        return result.text
    
    def generate_full(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
    ) -> InferenceResult:
        """
        Generate text with full result info.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences
            
        Returns:
            InferenceResult with text and metadata
        """
        # #region agent log
        import json
        try:
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "inference.py:generate_full", "message": "Generate called", "data": {"model_loaded": self._model is not None, "llama_available": self._llama_available, "prompt_length": len(prompt) if prompt else 0, "prompt_preview": prompt[:200] if prompt else "EMPTY", "max_tokens": max_tokens}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        if not self._llama_available:
            return InferenceResult(
                text="[ERROR: llama-cpp-python not installed]",
                tokens_generated=0,
                time_ms=0,
                tokens_per_second=0,
                success=False,
                error="llama-cpp-python not installed",
            )
        
        # Auto-load model if not loaded, or reload if mode changed
        if self._model is None:
            if not self.load_model():
                return InferenceResult(
                    text="[ERROR: Failed to load model]",
                    tokens_generated=0,
                    time_ms=0,
                    tokens_per_second=0,
                    success=False,
                    error="Failed to load model",
                )
        else:
            # Check if we need to reload model due to mode change
            # This happens when quick_mode changed but model is still loaded with old mode
            expected_path = self._get_model_path()
            if self._model_path is None or str(self._model_path) != str(expected_path):
                # Mode changed, need to reload
                self.unload_model()
                if not self.load_model():
                    return InferenceResult(
                        text="[ERROR: Failed to reload model after mode switch]",
                        tokens_generated=0,
                        time_ms=0,
                        tokens_per_second=0,
                        success=False,
                        error="Failed to reload model",
                    )
        
        # Use defaults based on mode
        if self.config.quick_mode:
            max_tokens = max_tokens or self.config.quick_max_tokens
            temperature = temperature if temperature is not None else self.config.quick_temperature
        else:
            max_tokens = max_tokens or self.config.max_tokens
            temperature = temperature or self.config.temperature
        stop = stop or []
        
        try:
            with self._inference_lock:
                start_time = time.time()
                
                # Cap max_tokens to reasonable limit based on context window
                # Model context is 4096 (or 2048 in quick mode), account for prompt size
                ctx_length = self.config.quick_context_length if self.config.quick_mode else self.config.context_length
                
                # Estimate prompt tokens (rough: ~4 chars per token for English text)
                # Be conservative: use 3.5 chars/token to overestimate slightly
                original_prompt_length = len(prompt)
                estimated_prompt_tokens = int(len(prompt) / 3.5)
                
                # If prompt itself exceeds context, truncate it
                # Reserve 80% of context for prompt, 20% for generation (minimum)
                max_prompt_tokens = int(ctx_length * 0.8)
                if estimated_prompt_tokens > max_prompt_tokens:
                    # Truncate prompt: keep the end (most recent/relevant info)
                    max_prompt_chars = int(max_prompt_tokens * 3.5)
                    prompt = prompt[-max_prompt_chars:]
                    estimated_prompt_tokens = max_prompt_tokens
                    # #region agent log
                    try:
                        with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "inference.py:generate_full", "message": "Prompt truncated", "data": {"original_length": original_prompt_length, "truncated_length": len(prompt), "reason": "Prompt exceeded 80% of context window"}, "timestamp": int(time.time() * 1000)}) + "\n")
                    except: pass
                    # #endregion
                
                # Calculate max generation tokens: context - prompt - safety margin
                # Leave 100 token safety margin for model overhead
                available_for_generation = ctx_length - estimated_prompt_tokens - 100
                max_generation_tokens = min(max_tokens, max(0, available_for_generation))
                
                # If prompt is too large, we can't generate anything
                if max_generation_tokens < 1:
                    # Try with minimal generation (64 tokens) if there's any room
                    if available_for_generation > 64:
                        max_generation_tokens = 64
                    else:
                        # Prompt exceeds context - this will fail, but let's try anyway
                        max_generation_tokens = 0
                
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "inference.py:generate_full", "message": "Capping max_tokens", "data": {"requested_max_tokens": max_tokens, "context_length": ctx_length, "estimated_prompt_tokens": estimated_prompt_tokens, "available_for_generation": available_for_generation, "capped_max_tokens": max_generation_tokens, "prompt_length": len(prompt)}, "timestamp": int(time.time() * 1000)}) + "\n")
                except: pass
                # #endregion
                
                output = self._model(
                    prompt,
                    max_tokens=max_generation_tokens,
                    temperature=temperature,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repeat_penalty=self.config.repeat_penalty,
                    stop=stop,
                    echo=False,
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                # Extract text from response
                # #region agent log
                try:
                    choices_data = output.get("choices", [])
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "inference.py:generate_full", "message": "Raw output structure", "data": {"choices_count": len(choices_data), "first_choice_keys": list(choices_data[0].keys()) if choices_data else "NO_CHOICES", "first_choice_text_preview": str(choices_data[0].get("text", "NO_TEXT"))[:200] if choices_data and choices_data[0].get("text") else "EMPTY_OR_MISSING", "usage": output.get("usage", {}), "max_tokens_requested": max_tokens}, "timestamp": int(time.time() * 1000)}) + "\n")
                except Exception as e:
                    try:
                        with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "inference.py:generate_full", "message": "Error extracting output", "data": {"error": str(e), "output_type": type(output).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
                    except: pass
                # #endregion
                
                text = output["choices"][0]["text"]
                tokens = output["usage"]["completion_tokens"]
                
                # #region agent log
                try:
                    with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "inference.py:generate_full", "message": "After model inference", "data": {"text_length": len(text) if text else 0, "text_preview": text[:200] if text else "EMPTY", "tokens": tokens, "is_empty": not text or not text.strip(), "max_tokens_requested": max_tokens}, "timestamp": int(time.time() * 1000)}) + "\n")
                except: pass
                # #endregion
                
                # Calculate tokens per second
                tps = (tokens / elapsed_ms) * 1000 if elapsed_ms > 0 else 0
                
                # Check for empty output
                if not text or not text.strip():
                    # Check if there's an error in the output
                    if output.get("error"):
                        return InferenceResult(
                            text=f"[ERROR: {output['error']}]",
                            tokens_generated=0,
                            time_ms=elapsed_ms,
                            tokens_per_second=0,
                            success=False,
                            error=output["error"],
                        )
                    # Empty output - model generated nothing
                    return InferenceResult(
                        text="",
                        tokens_generated=tokens,
                        time_ms=elapsed_ms,
                        tokens_per_second=tps,
                        success=True,
                        error="Model returned empty output",
                    )
                
                return InferenceResult(
                    text=text.strip(),
                    tokens_generated=tokens,
                    time_ms=elapsed_ms,
                    tokens_per_second=tps,
                    success=True,
                )
                
        except Exception as e:
            return InferenceResult(
                text=f"[ERROR: {e}]",
                tokens_generated=0,
                time_ms=0,
                tokens_per_second=0,
                success=False,
                error=str(e),
            )
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the engine."""
        return {
            "available": self._llama_available,
            "loaded": self.is_loaded,
            "model_path": str(self._model_path) if self._model_path else None,
            "config": {
                "model_repo": self.config.model_repo,
                "model_filename": self.config.model_filename,
                "context_length": self.config.context_length,
                "max_tokens": self.config.max_tokens,
                "n_gpu_layers": self.config.n_gpu_layers,
            },
        }


# ============================================================
#  Global Singleton Access
# ============================================================

_engine: Optional[InferenceEngine] = None
# Domain-specific engines (for models that differ from default)
_domain_engines: Dict[str, Optional[InferenceEngine]] = {}


def get_inference_engine(config: Optional[InferenceConfig] = None) -> InferenceEngine:
    """
    Get the global inference engine instance.
    
    Args:
        config: Optional configuration (used on first call or to update mode)
        
    Returns:
        InferenceEngine singleton
    """
    global _engine
    if _engine is None:
        _engine = InferenceEngine(config)
    elif config is not None:
        # Update config if engine already exists (for dynamic mode switching)
        _engine.__init__(config)
    return _engine


def get_inference_engine_for_domain(domain: str, config: Optional[InferenceConfig] = None) -> InferenceEngine:
    """
    Get inference engine for a specific domain.
    
    This allows domain-specific models (e.g., Stable-Code-3B for code domain,
    Nanbeige4-3B for math/physics/chemistry/biology domains).
    
    IMPORTANT: Domain-specific models ALWAYS use normal mode (quick_mode=False),
    regardless of any config passed. These are high-quality models that should
    never be downgraded to quick mode.
    
    Args:
        domain: Domain name (e.g., "code", "math", "physics", "chemistry", "biology")
        config: Optional configuration (note: quick_mode will be forced to False for domain-specific models)
    
    Returns:
        InferenceEngine instance for the domain
    """
    global _domain_engines, _engine
    
    # Domain-specific model configurations
    # NOTE: These models ALWAYS use normal mode (quick_mode=False)
    # Domain-specific models (stable-code-3b, nanbeige4-3b) are high-quality models
    # that should never be downgraded to quick mode, even if Auto Mode suggests it
    DOMAIN_MODEL_CONFIGS = {
        "code": InferenceConfig(
            model_repo="TheBloke/Stable-Code-3B-GGUF",
            model_filename="stable-code-3b.Q4_K_M.gguf",
            quick_mode=False,  # ALWAYS normal mode - never quick mode
            context_length=16384,  # Stable-Code-3B has 16k context
        ),
        "math": InferenceConfig(
            model_repo="enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF",
            model_filename="nanbeige4-3b-base-q4_k_m.gguf",
            quick_mode=False,  # ALWAYS normal mode - never quick mode
            context_length=4096,  # Nanbeige4-3B context length
        ),
        "physics": InferenceConfig(
            model_repo="enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF",
            model_filename="nanbeige4-3b-base-q4_k_m.gguf",
            quick_mode=False,  # ALWAYS normal mode - never quick mode
            context_length=4096,
        ),
        "chemistry": InferenceConfig(
            model_repo="enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF",
            model_filename="nanbeige4-3b-base-q4_k_m.gguf",
            quick_mode=False,  # ALWAYS normal mode - never quick mode
            context_length=4096,
        ),
        "biology": InferenceConfig(
            model_repo="enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF",
            model_filename="nanbeige4-3b-base-q4_k_m.gguf",
            quick_mode=False,  # ALWAYS normal mode - never quick mode
            context_length=4096,
        ),
    }
    
    # Check if domain has a specific model
    if domain in DOMAIN_MODEL_CONFIGS:
        # Create a fresh config (don't modify the template)
        domain_config = InferenceConfig(
            model_repo=DOMAIN_MODEL_CONFIGS[domain].model_repo,
            model_filename=DOMAIN_MODEL_CONFIGS[domain].model_filename,
            quick_mode=DOMAIN_MODEL_CONFIGS[domain].quick_mode,
            context_length=DOMAIN_MODEL_CONFIGS[domain].context_length,
        )
        
        # Merge with provided config if any
        if config:
            # Update domain config with provided values
            # BUT: Domain-specific models (stable-code-3b, nanbeige4-3b) ALWAYS use normal mode
            # Never allow quick_mode=True to override domain-specific models
            for key, value in config.__dict__.items():
                if value is not None:
                    # Enforce quick_mode=False for domain-specific models (normal mode only)
                    if key == "quick_mode":
                        # Domain-specific models should always use normal mode
                        setattr(domain_config, key, False)
                    else:
                        setattr(domain_config, key, value)
        
        # Use domain-specific engine (separate instance, not singleton)
        # Cache by domain name (simpler key)
        if domain not in _domain_engines or _domain_engines[domain] is None:
            # Create new instance bypassing singleton
            # We need to call __new__ directly with bypass flag, then __init__
            domain_engine = InferenceEngine.__new__(InferenceEngine, domain_config, _bypass_singleton=True)
            domain_engine.__init__(domain_config)
            _domain_engines[domain] = domain_engine
        elif config:
            # Update config if provided (but don't reinit if already initialized)
            if not _domain_engines[domain]._initialized:
                _domain_engines[domain].__init__(domain_config)
        
        return _domain_engines[domain]
    
    # Fall back to default engine (ensure it's separate)
    return get_inference_engine(config)


def run_model(prompt: str, max_tokens: int = 2048, domain: Optional[str] = None, force_domain_model: bool = True) -> str:
    """
    Run model inference on prompt.

    This is the main function called by specialists.
    Drop-in replacement for run_ollama.

    Args:
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        domain: Optional domain name for domain-specific models (e.g., "code", "math", "physics")
        force_domain_model: If True, when domain is specified, ALWAYS use the domain-specific
                           model regardless of Auto Mode complexity check. This ensures that
                           specialists (Math, Code, Physics, etc.) always use their configured
                           high-quality models instead of being downgraded to Quick Mode.
                           Default: True (specialists should use their assigned models)

    Returns:
        Generated text string
    """
    # #region agent log
    import json
    try:
        with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "inference.py:run_model", "message": "run_model called", "data": {"prompt_length": len(prompt) if prompt else 0, "max_tokens": max_tokens, "domain": domain, "force_domain_model": force_domain_model}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion

    # Use domain-specific engine if domain is specified AND force_domain_model is True
    # This prevents Auto Mode from overriding specialist model selection
    if domain and force_domain_model:
        # Specialist explicitly requested - use configured domain-specific model
        # (e.g., Nanbeige4-3B for math, Stable-Code-3B for code)
        engine = get_inference_engine_for_domain(domain)
    elif domain and not force_domain_model:
        # Domain specified but allowing Auto Mode to override
        # Fall back to default engine (which may use Quick Mode based on complexity)
        engine = get_inference_engine()
    else:
        # No domain specified - use default engine
        engine = get_inference_engine()

    result = engine.generate(prompt, max_tokens=max_tokens)
    
    # #region agent log
    try:
        with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "inference.py:run_model", "message": "run_model returning", "data": {"result_length": len(result) if result else 0, "result_preview": result[:200] if result else "EMPTY", "is_empty": not result or not result.strip()}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    return result
