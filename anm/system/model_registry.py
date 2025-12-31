# ============================================================
#  ANM V0-OpenSource — Model Registry
#  Maps model names to their HuggingFace repos and configs
# ============================================================

"""
Model Registry for Research Mode Authority Models.

Maps model names (e.g., "nanbeige4-3b") to their HuggingFace repositories
and configuration for per-domain model switching in Research Mode.
"""

from __future__ import annotations
from typing import Dict, Optional
from dataclasses import dataclass

from anm.system.model_downloader import DEFAULT_MODELS
from anm.system.inference import InferenceConfig


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    repo_id: str
    filename: str
    size_gb: float


# Map model names to their configs
MODEL_REGISTRY: Dict[str, ModelConfig] = {}

# Populate registry from DEFAULT_MODELS
for model_name, model_info in DEFAULT_MODELS.items():
    MODEL_REGISTRY[model_name] = ModelConfig(
        name=model_name,
        repo_id=model_info["repo_id"],
        filename=model_info["filename"],
        size_gb=model_info.get("size_gb", 0.0),
    )

# Research Mode Authority Model Mapping (from blueprint)
RESEARCH_AUTHORITY_MODELS = {
    "nanbeige4-3b": ["math", "physics", "chemistry", "biology"],
    "stable-code-3b": ["code"],
    "qwen2.5-3b-instruct": ["internet", "research"],
    "deepseek-r1-1.5b": ["general", "metacognition", "memory", "facts", "refiner", "verifier"],
}


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a model by name."""
    # Normalize model name (handle variations like "deepseek-r1:1.5b" vs "deepseek-r1-1.5b")
    normalized = model_name.replace(":", "-").lower()
    
    # Direct lookup
    if normalized in MODEL_REGISTRY:
        return MODEL_REGISTRY[normalized]
    
    # Try partial matches
    for key, config in MODEL_REGISTRY.items():
        if normalized in key or key in normalized:
            return config
    
    return None


def get_inference_config_for_model(model_name: str) -> Optional[InferenceConfig]:
    """Get InferenceConfig for a specific model."""
    model_config = get_model_config(model_name)
    if model_config is None:
        return None
    
    return InferenceConfig(
        model_repo=model_config.repo_id,
        model_filename=model_config.filename,
        quick_mode=False,  # Research mode always uses full models
    )


def get_authority_model_for_domain(domain: str) -> Optional[str]:
    """Get the authority model name for a domain in Research Mode."""
    for model_name, domains in RESEARCH_AUTHORITY_MODELS.items():
        if domain in domains:
            return model_name
    # Default to DeepSeek R1 for general/metacognition
    return "deepseek-r1-1.5b"

