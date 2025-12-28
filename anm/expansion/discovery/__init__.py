# ============================================================
# ANM V0-OpenSource — DISCOVERY MODULE
#  Multi-Source Dataset Discovery • Quality Scoring • Parallel Search
# ============================================================

from anm.expansion.discovery.multi_source import MultiSourceDiscovery
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

__all__ = [
    "MultiSourceDiscovery",
    "HuggingFaceSource",
    "KaggleSource",
    "GitHubSource",
    "ArxivSource",
    "HuggingFaceDatasetDownloader",
    "DownloadProgress",
]
