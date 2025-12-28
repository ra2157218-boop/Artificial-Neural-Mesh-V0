# ============================================================
#  ANM V0-OpenSource — EXPANSION MODULE
#  Self-Improvement Pipeline
# ============================================================

"""
ANM Self-Improvement Pipeline V0-OpenSource

Components:
- Core: Novelty detection, voting system, orchestration, metrics
- Discovery: Multi-source dataset search (HuggingFace, Kaggle, GitHub, ArXiv)
- Code: Code generation, validation, testing, Git integration
- Training: LoRA/QLoRA fine-tuning, data pipeline
- Integration: Module registration, device awareness
"""

__version__ = "0.1.0-opensource"

# V2 Components (Main)
from anm.expansion.expansion_engine_v2 import ExpansionEngineV2, ExpansionConfig

# Core
from anm.expansion.core.novelty_detector import NoveltyDetectorV2, NoveltyResult
from anm.expansion.core.voting_system import VotingSystemV2, VotingResult, Vote, VoteType
from anm.expansion.core.metrics import ExpansionMetrics
from anm.expansion.core.orchestrator import PipelineOrchestrator, StageConfig

# Discovery
from anm.expansion.discovery.multi_source import MultiSourceDiscovery, DiscoveredDataset
from anm.expansion.discovery.sources import (
    HuggingFaceSource,
    KaggleSource,
    GitHubSource,
    ArxivSource,
)
from anm.expansion.discovery.huggingface_downloader import (
    HuggingFaceDatasetDownloader,
    DownloadProgress,
)

# Code
from anm.expansion.code.writer_v2 import CodeWriterV2
from anm.expansion.code.validator import CodeValidator, ValidationResult
from anm.expansion.code.git_integration import GitIntegration

# Training
from anm.expansion.training.trainer import LoRATrainer, TrainingConfig
from anm.expansion.training.data_pipeline import DataPipeline

# Integration
from anm.expansion.dataset_discovery import DatasetDiscovery, DatasetInfo
from anm.expansion.device_awareness import DeviceAwareness
from anm.expansion.module_registration import ModuleRegistration

# Aliases for compatibility
ExpansionEngine = ExpansionEngineV2
CodeWriter = CodeWriterV2

__all__ = [
    # Version
    "__version__",
    
    # Main Engine
    "ExpansionEngineV2",
    "ExpansionEngine",  # Alias
    "ExpansionConfig",
    
    # Core
    "NoveltyDetectorV2",
    "NoveltyResult",
    "VotingSystemV2",
    "VotingResult",
    "Vote",
    "VoteType",
    "ExpansionMetrics",
    "PipelineOrchestrator",
    "StageConfig",
    
    # Discovery
    "MultiSourceDiscovery",
    "DiscoveredDataset",
    "HuggingFaceSource",
    "KaggleSource",
    "GitHubSource",
    "ArxivSource",
    "HuggingFaceDatasetDownloader",
    "DownloadProgress",
    "DatasetDiscovery",
    "DatasetInfo",
    
    # Code
    "CodeWriterV2",
    "CodeWriter",  # Alias
    "CodeValidator",
    "ValidationResult",
    "GitIntegration",
    
    # Training
    "LoRATrainer",
    "TrainingConfig",
    "DataPipeline",
    
    # Integration
    "DeviceAwareness",
    "ModuleRegistration",
]
