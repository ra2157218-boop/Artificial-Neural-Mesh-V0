"""
Embedding utilities for ANM V0-OpenSource.

This module provides shared embedding functionality used across
memory and expansion systems.
"""

from __future__ import annotations
import os
import json
import hashlib
from typing import Dict, List, Optional


class EmbeddingCache:
    """
    In-memory + disk cache for embeddings to avoid recomputation.

    This cache is shared across different systems (memory, vector stores, novelty detection)
    to avoid redundant embedding computations.
    """

    def __init__(self, cache_dir: str = ".anm_cache/embeddings"):
        """
        Initialize embedding cache.

        Args:
            cache_dir: Directory to store cached embeddings on disk
        """
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, List[float]] = {}
        os.makedirs(cache_dir, exist_ok=True)

    def _get_key(self, text: str) -> str:
        """Generate cache key from text using MD5 hash."""
        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """
        Retrieve embedding from cache.

        Args:
            text: Text to look up

        Returns:
            Cached embedding vector or None if not found
        """
        key = self._get_key(text)

        # Check memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Check disk cache
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    embedding = json.load(f)
                    self.memory_cache[key] = embedding
                    return embedding
            except Exception:
                # Cache file corrupted, ignore
                pass

        return None

    def set(self, text: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.

        Args:
            text: Text that was embedded
            embedding: Embedding vector to cache
        """
        key = self._get_key(text)

        # Store in memory
        self.memory_cache[key] = embedding

        # Store on disk
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_path, "w") as f:
                json.dump(embedding, f)
        except Exception:
            # Disk write failed, but memory cache still works
            pass

    def clear(self) -> None:
        """Clear all cached embeddings (memory and disk)."""
        self.memory_cache.clear()

        # Clear disk cache
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.cache_dir, filename))
                    except Exception:
                        pass

    def size(self) -> int:
        """Get number of cached embeddings in memory."""
        return len(self.memory_cache)


__all__ = ["EmbeddingCache"]
