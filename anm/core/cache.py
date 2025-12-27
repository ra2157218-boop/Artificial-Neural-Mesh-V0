# ============================================================
#  ANM V0-OpenSource — High-Performance Cache
#  Thread-Safe LRU Cache with TTL Support
# ============================================================

"""
ANM Cache Module

Provides high-performance caching with:
- LRU eviction
- TTL expiration
- Thread safety
- Statistics tracking
"""

from __future__ import annotations
from typing import Dict, Any, Optional, TypeVar, Generic, Callable, Tuple, List
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
import sys
import time

# Python version compatibility: slots=True requires Python 3.10+
_SUPPORTS_SLOTS = sys.version_info >= (3, 10)

# Use centralized hash utility
from anm.utils.hash_utils import hash_query

__all__ = [
    "LRUCache",
    "TTLCache", 
    "QueryCache",
    "CacheStats",
    "cached",
]

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


@dataclass(**({"slots": True} if _SUPPORTS_SLOTS else {}))
class CacheStats:
    """Enhanced cache statistics with detailed metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    sets: int = 0
    deletes: int = 0
    cleanups: int = 0
    total_size_bytes: int = 0
    
    # Per-domain statistics (for QueryCache)
    domain_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def total_operations(self) -> int:
        """Total cache operations."""
        return self.hits + self.misses + self.sets + self.deletes
    
    @property
    def efficiency(self) -> float:
        """Cache efficiency (hits / total operations)."""
        total = self.total_operations
        return self.hits / total if total > 0 else 0.0
    
    def update_domain_stats(self, domain: str, operation: str) -> None:
        """Update per-domain statistics."""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "deletes": 0,
            }
        if operation in self.domain_stats[domain]:
            self.domain_stats[domain][operation] += 1
    
    def get_domain_stats(self, domain: str) -> Dict[str, int]:
        """Get statistics for a specific domain."""
        return self.domain_stats.get(domain, {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        })
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.sets = 0
        self.deletes = 0
        self.cleanups = 0
        self.total_size_bytes = 0
        self.domain_stats.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "sets": self.sets,
            "deletes": self.deletes,
            "cleanups": self.cleanups,
            "hit_rate": self.hit_rate,
            "efficiency": self.efficiency,
            "total_operations": self.total_operations,
            "total_size_bytes": self.total_size_bytes,
            "domain_stats": dict(self.domain_stats),
        }


@dataclass(**({"slots": True} if _SUPPORTS_SLOTS else {}))
class CacheEntry(Generic[V]):
    """A single cache entry with metadata."""
    value: V
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_access = time.time()


class LRUCache(Generic[K, V]):
    """
    Thread-safe LRU cache with O(1) operations.
    
    Features:
    - Constant time get/set/delete
    - Automatic LRU eviction
    - Thread-safe with RLock
    - Statistics tracking
    """
    
    __slots__ = ('_cache', '_maxsize', '_lock', '_stats')
    
    def __init__(self, maxsize: int = 1000):
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._maxsize = max(1, maxsize)
        self._lock = RLock()
        self._stats = CacheStats()
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value by key, returns default if not found."""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return default
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats.hits += 1
            return self._cache[key]
    
    def set(self, key: K, value: V) -> None:
        """Set key-value pair."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                self._cache[key] = value
                if len(self._cache) > self._maxsize:
                    self._cache.popitem(last=False)
                    self._stats.evictions += 1
            self._stats.sets += 1
    
    def delete(self, key: K) -> bool:
        """Delete key. Returns True if key existed."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
    
    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._cache
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)
    
    @property
    def stats(self) -> CacheStats:
        return self._stats


class TTLCache(Generic[K, V]):
    """
    Thread-safe cache with TTL (Time To Live) support.
    
    Features:
    - Automatic expiration
    - LRU eviction when full
    - Lazy cleanup on access
    - Thread-safe
    """
    
    __slots__ = ('_cache', '_maxsize', '_default_ttl', '_lock', '_stats')
    
    def __init__(self, maxsize: int = 1000, default_ttl: float = 3600.0):
        self._cache: OrderedDict[K, CacheEntry[V]] = OrderedDict()
        self._maxsize = max(1, maxsize)
        self._default_ttl = default_ttl
        self._lock = RLock()
        self._stats = CacheStats()
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value by key."""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return default
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats.expirations += 1
                self._stats.misses += 1
                return default
            
            # Move to end and update access
            self._cache.move_to_end(key)
            entry.touch()
            self._stats.hits += 1
            return entry.value
    
    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Set value with optional TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        now = time.time()
        
        with self._lock:
            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=now + ttl if ttl > 0 else None,
            )
            
            if key in self._cache:
                self._cache.move_to_end(key)
            
            self._cache[key] = entry
            self._stats.sets += 1
            
            # Evict if over capacity
            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)
                self._stats.evictions += 1
    
    def delete(self, key: K) -> bool:
        """Delete key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def cleanup(self) -> int:
        """Remove all expired entries. Returns count removed."""
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                removed += 1
                self._stats.expirations += 1
            if removed > 0:
                self._stats.cleanups += 1
        return removed
    
    def invalidate_by_pattern(self, pattern_fn: Callable[[K], bool]) -> int:
        """Invalidate entries matching a pattern. Returns count removed."""
        removed = 0
        with self._lock:
            matching_keys = [k for k in self._cache.keys() if pattern_fn(k)]
            for key in matching_keys:
                del self._cache[key]
                removed += 1
                self._stats.deletes += 1
        return removed
    
    def invalidate_by_ttl(self, max_age: float) -> int:
        """Invalidate entries older than max_age seconds. Returns count removed."""
        removed = 0
        now = time.time()
        with self._lock:
            old_keys = [
                k for k, v in self._cache.items()
                if (now - v.created_at) > max_age
            ]
            for key in old_keys:
                del self._cache[key]
                removed += 1
                self._stats.deletes += 1
        return removed
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
    
    def __contains__(self, key: K) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            if self._cache[key].is_expired():
                del self._cache[key]
                return False
            return True
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)
    
    @property
    def stats(self) -> CacheStats:
        return self._stats


class QueryCache:
    """
    Enhanced specialized cache for query results.
    
    Features:
    - Query hash-based keys
    - Domain-aware caching
    - Confidence-weighted eviction
    - Enhanced TTL invalidation
    - Detailed statistics per domain
    - Pattern-based invalidation
    """
    
    __slots__ = ('_cache', '_max_queries', '_query_metadata')
    
    def __init__(self, max_queries: int = 500, default_ttl: float = 3600.0):
        self._cache = TTLCache[str, Dict[str, Any]](
            maxsize=max_queries,
            default_ttl=default_ttl,
        )
        self._max_queries = max_queries
        # Store metadata: query -> (domain, original_query, cached_at)
        self._query_metadata: Dict[str, Tuple[str, str, float]] = {}
    
    def _hash_query(self, query: str, domain: Optional[str] = None) -> str:
        """Create consistent hash for query."""
        return hash_query(query, domain, length=16)
    
    def get(
        self,
        query: str,
        domain: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached result for query."""
        key = self._hash_query(query, domain)
        result = self._cache.get(key)
        
        # Update domain stats
        domain_key = domain or "any"
        if result is not None:
            self._cache.stats.update_domain_stats(domain_key, "hits")
        else:
            self._cache.stats.update_domain_stats(domain_key, "misses")
        
        return result
    
    def set(
        self,
        query: str,
        result: Dict[str, Any],
        domain: Optional[str] = None,
        ttl: Optional[float] = None,
    ) -> None:
        """Cache query result with metadata."""
        key = self._hash_query(query, domain)
        domain_key = domain or "any"
        
        # Store metadata
        self._query_metadata[key] = (domain_key, query, time.time())
        
        # Cache the result
        self._cache.set(key, result, ttl)
        
        # Update domain stats
        self._cache.stats.update_domain_stats(domain_key, "sets")
    
    def invalidate(self, query: str, domain: Optional[str] = None) -> bool:
        """Invalidate cached result."""
        key = self._hash_query(query, domain)
        domain_key = domain or "any"
        
        # Update domain stats
        if self._cache.delete(key):
            self._cache.stats.update_domain_stats(domain_key, "deletes")
            self._query_metadata.pop(key, None)
            return True
        return False
    
    def invalidate_by_domain(self, domain: str) -> int:
        """Invalidate all cached results for a specific domain."""
        removed = 0
        keys_to_remove = []
        
        for key, (cached_domain, _, _) in self._query_metadata.items():
            if cached_domain == domain:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if self._cache.delete(key):
                removed += 1
                self._cache.stats.update_domain_stats(domain, "deletes")
                self._query_metadata.pop(key, None)
        
        return removed
    
    def invalidate_by_pattern(self, pattern: str, domain: Optional[str] = None) -> int:
        """Invalidate queries matching a pattern (substring match)."""
        removed = 0
        pattern_lower = pattern.lower()
        keys_to_remove = []
        
        for key, (cached_domain, original_query, _) in self._query_metadata.items():
            if domain and cached_domain != domain:
                continue
            if pattern_lower in original_query.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            cached_domain = self._query_metadata[key][0]
            if self._cache.delete(key):
                removed += 1
                self._cache.stats.update_domain_stats(cached_domain, "deletes")
                self._query_metadata.pop(key, None)
        
        return removed
    
    def invalidate_old(self, max_age_seconds: float) -> int:
        """Invalidate entries older than max_age_seconds."""
        removed = 0
        now = time.time()
        keys_to_remove = []
        
        for key, (cached_domain, _, cached_at) in self._query_metadata.items():
            if (now - cached_at) > max_age_seconds:
                keys_to_remove.append((key, cached_domain))
        
        for key, cached_domain in keys_to_remove:
            if self._cache.delete(key):
                removed += 1
                self._cache.stats.update_domain_stats(cached_domain, "deletes")
                self._query_metadata.pop(key, None)
        
        return removed
    
    def clear(self) -> None:
        """Clear all cached queries."""
        self._cache.clear()
        self._query_metadata.clear()
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        removed = self._cache.cleanup()
        # Clean up metadata for expired entries
        if removed > 0:
            current_keys = set(self._cache._cache.keys())
            expired_metadata_keys = [
                k for k in self._query_metadata.keys()
                if k not in current_keys
            ]
            for key in expired_metadata_keys:
                self._query_metadata.pop(key, None)
        return removed
    
    def get_size(self) -> int:
        """Get approximate cache size in entries."""
        return len(self._cache)
    
    def get_domain_count(self, domain: str) -> int:
        """Get number of cached queries for a domain."""
        return sum(1 for d, _, _ in self._query_metadata.values() if d == domain)
    
    def list_domains(self) -> list:
        """List all domains with cached queries."""
        return sorted(set(d for d, _, _ in self._query_metadata.values()))
    
    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._cache.stats
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics including per-domain breakdown."""
        base_stats = self.stats.to_dict()
        base_stats["cache_size"] = self.get_size()
        base_stats["domains"] = self.list_domains()
        base_stats["domain_counts"] = {
            domain: self.get_domain_count(domain)
            for domain in self.list_domains()
        }
        return base_stats


def cached(
    cache: Optional[LRUCache] = None,
    ttl: Optional[float] = None,
    key_fn: Optional[Callable[..., str]] = None,
) -> Callable:
    """
    Decorator for caching function results.
    
    Usage:
        @cached(ttl=300)
        def expensive_operation(x, y):
            return x + y
    """
    _cache = cache or (TTLCache(maxsize=1000, default_ttl=ttl or 3600) if ttl else LRUCache(maxsize=1000))
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            # Check cache
            result = _cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            if isinstance(_cache, TTLCache):
                _cache.set(key, result, ttl)
            else:
                _cache.set(key, result)
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.cache = _cache  # type: ignore
        wrapper.cache_clear = _cache.clear  # type: ignore
        
        return wrapper
    
    return decorator
