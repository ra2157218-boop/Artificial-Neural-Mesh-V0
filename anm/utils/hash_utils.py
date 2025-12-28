# ============================================================
#  ANM V0-OpenSource — Hash Utilities
#  Common hashing functions for keys and queries
# ============================================================

"""
Hash Utilities

Common functions for hashing:
- Query hashing
- Key generation
- Consistent hashing
"""

from __future__ import annotations
from typing import Optional
import hashlib

__all__ = [
    "hash_query",
    "hash_string",
    "generate_cache_key",
]


def hash_string(text: str, length: int = 16) -> str:
    """
    Generate consistent hash from string.
    
    Args:
        text: Text to hash
        length: Hash length (default 16)
    
    Returns:
        Hexadecimal hash string
    """
    if not text:
        return ""
    
    return hashlib.sha256(text.encode()).hexdigest()[:length]


def hash_query(query: str, domain: Optional[str] = None, length: int = 16) -> str:
    """
    Create consistent hash for query.
    
    Args:
        query: Query text
        domain: Optional domain name
        length: Hash length (default 16)
    
    Returns:
        Hexadecimal hash string
    """
    # Normalize query
    normalized = query.lower().strip()
    
    # Build key
    if domain:
        key = f"{domain}:{normalized}"
    else:
        key = f"any:{normalized}"
    
    return hash_string(key, length)


def generate_cache_key(
    prefix: str,
    *args,
    separator: str = ":",
    length: Optional[int] = None,
) -> str:
    """
    Generate cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Additional key components
        separator: Separator between components
        length: Optional hash length (if None, returns full key)
    
    Returns:
        Cache key string
    """
    components = [str(prefix)] + [str(arg) for arg in args]
    key = separator.join(components)
    
    if length:
        return hash_string(key, length)
    
    return key

