# ============================================================
#  ANM V0-OpenSource — Memory Optimizer
#  Memory Profiling, Weak References, and Cleanup Hooks
# ============================================================

"""
Memory Optimizer Module

Provides:
- Memory profiling and monitoring
- Weak reference utilities for large objects
- Cleanup hooks and context managers
- Automatic memory management
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Callable, Set, TypeVar, Generic, ContextManager
from dataclasses import dataclass, field
from threading import RLock
from weakref import WeakValueDictionary, WeakKeyDictionary, WeakSet, ref, ReferenceType
import gc
import sys
import tracemalloc
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger("anm.memory")

T = TypeVar('T')

__all__ = [
    "MemoryProfiler",
    "MemoryMonitor",
    "WeakRefCache",
    "CleanupHook",
    "MemoryContext",
    "track_memory",
    "cleanup_resources",
    "get_memory_usage",
]


@dataclass(slots=True)
class MemorySnapshot:
    """Memory usage snapshot."""
    timestamp: float
    current_mb: float
    peak_mb: float
    objects_count: int
    gc_collections: Dict[str, int]
    top_allocations: List[tuple] = field(default_factory=list)


@dataclass(slots=True)
class ResourceInfo:
    """Information about a tracked resource."""
    name: str
    size_bytes: int
    created_at: float
    cleanup_fn: Optional[Callable[[], None]] = None
    weak_ref: Optional[ReferenceType] = None


class MemoryProfiler:
    """
    Memory profiler for tracking memory usage and allocations.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._lock = RLock()
        self._snapshots: List[MemorySnapshot] = []
        self._tracemalloc_started = False
        self._gc_collections_baseline: Dict[str, int] = {}
        
        if self.enabled:
            self._start_tracing()
    
    def _start_tracing(self):
        """Start tracemalloc if not already started."""
        with self._lock:
            if not self._tracemalloc_started:
                try:
                    tracemalloc.start()
                    self._tracemalloc_started = True
                    logger.debug("Memory profiling started.")
                except RuntimeError:
                    # Already started
                    self._tracemalloc_started = True
    
    def snapshot(self, top_n: int = 10) -> MemorySnapshot:
        """
        Take a memory snapshot.
        
        Args:
            top_n: Number of top allocations to track
        
        Returns:
            Memory snapshot
        """
        with self._lock:
            if not self.enabled:
                return MemorySnapshot(
                    timestamp=time.time(),
                    current_mb=0.0,
                    peak_mb=0.0,
                    objects_count=0,
                    gc_collections={},
                )
            
            # Get current memory usage
            current_mb = self._get_current_memory_mb()
            peak_mb = self._get_peak_memory_mb()
            
            # Get GC collections
            gc_collections = {}
            for gen in range(3):
                gen_name = f"generation_{gen}"
                gc_collections[gen_name] = gc.get_count()[gen]
            
            # Get top allocations if tracemalloc is active
            top_allocations = []
            if self._tracemalloc_started:
                try:
                    snapshot = tracemalloc.take_snapshot()
                    top_stats = snapshot.statistics('lineno')[:top_n]
                    top_allocations = [
                        (stat.traceback.format()[-1], stat.size / 1024 / 1024)
                        for stat in top_stats
                    ]
                except Exception as e:
                    logger.warning(f"Failed to get tracemalloc stats: {e}")
            
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                current_mb=current_mb,
                peak_mb=peak_mb,
                objects_count=len(gc.get_objects()),
                gc_collections=gc_collections,
                top_allocations=top_allocations,
            )
            
            self._snapshots.append(snapshot)
            return snapshot
    
    def _get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback: use sys.getsizeof (less accurate)
            total = sum(sys.getsizeof(obj) for obj in gc.get_objects())
            return total / 1024 / 1024
    
    def _get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().peak_wss / 1024 / 1024 if hasattr(process.memory_info(), 'peak_wss') else 0.0
        except (ImportError, AttributeError):
            # Fallback: use tracemalloc peak
            if self._tracemalloc_started:
                try:
                    current, peak = tracemalloc.get_traced_memory()
                    return peak / 1024 / 1024
                except Exception:
                    pass
            return 0.0
    
    def get_diff(self, snapshot1: MemorySnapshot, snapshot2: MemorySnapshot) -> Dict[str, Any]:
        """
        Get difference between two snapshots.
        
        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot
        
        Returns:
            Dictionary with differences
        """
        return {
            "time_diff_seconds": snapshot2.timestamp - snapshot1.timestamp,
            "memory_diff_mb": snapshot2.current_mb - snapshot1.current_mb,
            "peak_diff_mb": snapshot2.peak_mb - snapshot1.peak_mb,
            "objects_diff": snapshot2.objects_count - snapshot1.objects_count,
            "gc_collections_diff": {
                k: snapshot2.gc_collections.get(k, 0) - snapshot1.gc_collections.get(k, 0)
                for k in set(snapshot1.gc_collections.keys()) | set(snapshot2.gc_collections.keys())
            },
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all snapshots."""
        with self._lock:
            if not self._snapshots:
                return {"message": "No snapshots taken."}
            
            first = self._snapshots[0]
            last = self._snapshots[-1]
            
            return {
                "snapshot_count": len(self._snapshots),
                "first_snapshot": {
                    "timestamp": first.timestamp,
                    "memory_mb": first.current_mb,
                },
                "last_snapshot": {
                    "timestamp": last.timestamp,
                    "memory_mb": last.current_mb,
                },
                "total_memory_growth_mb": last.current_mb - first.current_mb,
                "peak_memory_mb": max(s.current_mb for s in self._snapshots),
            }
    
    def clear_snapshots(self):
        """Clear all snapshots."""
        with self._lock:
            self._snapshots.clear()
    
    def __del__(self):
        """Cleanup on deletion."""
        if self._tracemalloc_started:
            try:
                tracemalloc.stop()
            except Exception:
                pass


class WeakRefCache(Generic[T]):
    """
    Cache using weak references to avoid keeping objects alive.
    
    Useful for caching large objects that should be garbage collected
    when no longer referenced elsewhere.
    
    Note: Only works with mutable objects (weak references cannot be
    created for immutable types like str, int, tuple, etc.).
    """
    
    def __init__(self, name: str = "weak_cache"):
        self.name = name
        self._cache: WeakValueDictionary[str, T] = WeakValueDictionary()
        self._lock = RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            try:
                value = self._cache[key]
                self._stats["hits"] += 1
                return value
            except KeyError:
                self._stats["misses"] += 1
                return None
    
    def set(self, key: str, value: T) -> None:
        """
        Set value in cache.
        
        Note: Only works with mutable objects. For immutable types,
        use a regular dict or wrap the value in a list/dict.
        """
        with self._lock:
            try:
                self._cache[key] = value
            except TypeError as e:
                # Cannot create weak reference to immutable type
                raise TypeError(
                    f"Cannot create weak reference to {type(value).__name__}. "
                    "WeakRefCache only works with mutable objects. "
                    "Consider wrapping the value in a list or dict."
                ) from e
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            try:
                del self._cache[key]
                return True
            except KeyError:
                return False
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._stats["evictions"] += len(self._cache)
    
    def keys(self) -> List[str]:
        """Get all keys (only those still alive)."""
        with self._lock:
            return list(self._cache.keys())
    
    def __len__(self) -> int:
        """Get number of entries."""
        with self._lock:
            return len(self._cache)
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return self._stats.copy()


class CleanupHook:
    """
    Registry for cleanup hooks that are called when resources should be freed.
    """
    
    _instance: Optional['CleanupHook'] = None
    _lock = RLock()
    
    def __new__(cls) -> 'CleanupHook':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._hooks: List[Callable[[], None]] = []
                    cls._instance._resources: Dict[str, ResourceInfo] = {}
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.debug("CleanupHook registry initialized.")
    
    def register(
        self,
        name: str,
        cleanup_fn: Callable[[], None],
        size_bytes: int = 0,
    ) -> None:
        """
        Register a cleanup hook.
        
        Args:
            name: Resource name
            cleanup_fn: Function to call for cleanup
            size_bytes: Estimated size in bytes
        """
        with self._lock:
            self._hooks.append(cleanup_fn)
            self._resources[name] = ResourceInfo(
                name=name,
                size_bytes=size_bytes,
                created_at=time.time(),
                cleanup_fn=cleanup_fn,
            )
            logger.debug(f"Registered cleanup hook: {name}")
    
    def register_weak(
        self,
        name: str,
        obj: Any,
        cleanup_fn: Optional[Callable[[], None]] = None,
        size_bytes: int = 0,
    ) -> None:
        """
        Register an object with weak reference tracking.
        
        Args:
            name: Resource name
            obj: Object to track
            cleanup_fn: Optional cleanup function
            size_bytes: Estimated size in bytes
        """
        with self._lock:
            def cleanup():
                if cleanup_fn:
                    cleanup_fn()
                logger.debug(f"Cleaned up weak reference: {name}")
            
            weak_ref = ref(obj, cleanup)
            self._resources[name] = ResourceInfo(
                name=name,
                size_bytes=size_bytes,
                created_at=time.time(),
                cleanup_fn=cleanup_fn,
                weak_ref=weak_ref,
            )
            logger.debug(f"Registered weak reference: {name}")
    
    def cleanup(self, name: Optional[str] = None) -> bool:
        """
        Run cleanup for a specific resource or all resources.
        
        Args:
            name: Resource name (None for all)
        
        Returns:
            True if cleanup was successful
        """
        with self._lock:
            if name:
                if name in self._resources:
                    resource = self._resources[name]
                    if resource.cleanup_fn:
                        try:
                            resource.cleanup_fn()
                            del self._resources[name]
                            logger.info(f"Cleaned up resource: {name}")
                            return True
                        except Exception as e:
                            logger.error(f"Error cleaning up {name}: {e}")
                            return False
                    return False
                return False
            else:
                # Cleanup all
                success = True
                for name, resource in list(self._resources.items()):
                    if resource.cleanup_fn:
                        try:
                            resource.cleanup_fn()
                            logger.debug(f"Cleaned up resource: {name}")
                        except Exception as e:
                            logger.error(f"Error cleaning up {name}: {e}")
                            success = False
                self._resources.clear()
                self._hooks.clear()
                return success
    
    def get_resources(self) -> Dict[str, ResourceInfo]:
        """Get all registered resources."""
        with self._lock:
            return self._resources.copy()
    
    def get_total_size_bytes(self) -> int:
        """Get total estimated size of tracked resources."""
        with self._lock:
            return sum(r.size_bytes for r in self._resources.values())


class MemoryMonitor:
    """
    Continuous memory monitoring with automatic cleanup triggers.
    """
    
    def __init__(
        self,
        threshold_mb: float = 1024.0,  # 1GB default
        check_interval_seconds: float = 60.0,
        auto_cleanup: bool = True,
    ):
        self.threshold_mb = threshold_mb
        self.check_interval_seconds = check_interval_seconds
        self.auto_cleanup = auto_cleanup
        self._profiler = MemoryProfiler(enabled=True)
        self._cleanup_hook = CleanupHook()
        self._running = False
        self._lock = RLock()
    
    def start(self):
        """Start monitoring."""
        with self._lock:
            if not self._running:
                self._running = True
                logger.info(f"Memory monitoring started (threshold: {self.threshold_mb}MB)")
                self._monitor_loop()
    
    def stop(self):
        """Stop monitoring."""
        with self._lock:
            self._running = False
            logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop (should run in background thread)."""
        while self._running:
            snapshot = self._profiler.snapshot()
            
            if snapshot.current_mb > self.threshold_mb:
                logger.warning(
                    f"Memory usage ({snapshot.current_mb:.2f}MB) exceeds threshold "
                    f"({self.threshold_mb}MB)"
                )
                
                if self.auto_cleanup:
                    self._trigger_cleanup()
            
            time.sleep(self.check_interval_seconds)
    
    def _trigger_cleanup(self):
        """Trigger cleanup of tracked resources."""
        logger.info("Triggering automatic cleanup...")
        
        # Force garbage collection
        collected = gc.collect()
        logger.debug(f"GC collected {collected} objects")
        
        # Cleanup tracked resources
        self._cleanup_hook.cleanup()


@contextmanager
def track_memory(name: str = "operation", top_n: int = 10):
    """
    Context manager for tracking memory usage of an operation.
    
    Usage:
        with track_memory("my_operation"):
            # Do work
            pass
    """
    profiler = MemoryProfiler(enabled=True)
    before = profiler.snapshot(top_n=top_n)
    
    try:
        yield profiler
    finally:
        after = profiler.snapshot(top_n=top_n)
        diff = profiler.get_diff(before, after)
        
        logger.info(
            f"Memory usage for '{name}': "
            f"{diff['memory_diff_mb']:.2f}MB change, "
            f"{diff['objects_diff']} objects"
        )


def cleanup_resources(name: Optional[str] = None) -> bool:
    """
    Cleanup tracked resources.
    
    Args:
        name: Resource name (None for all)
    
    Returns:
        True if cleanup was successful
    """
    hook = CleanupHook()
    return hook.cleanup(name)


def get_memory_usage() -> Dict[str, Any]:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary with memory statistics
    """
    profiler = MemoryProfiler(enabled=True)
    snapshot = profiler.snapshot()
    
    return {
        "current_mb": snapshot.current_mb,
        "peak_mb": snapshot.peak_mb,
        "objects_count": snapshot.objects_count,
        "gc_collections": snapshot.gc_collections,
    }


class MemoryContext(ContextManager):
    """
    Context manager for automatic resource cleanup.
    
    Usage:
        with MemoryContext() as ctx:
            ctx.register("my_resource", cleanup_fn)
            # Use resource
    """
    
    def __init__(self, name: str = "memory_context"):
        self.name = name
        self._cleanup_hook = CleanupHook()
        self._resources: Set[str] = set()
    
    def __enter__(self) -> 'MemoryContext':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup all registered resources on exit."""
        for name in list(self._resources):
            self._cleanup_hook.cleanup(name)
        self._resources.clear()
    
    def register(
        self,
        name: str,
        cleanup_fn: Callable[[], None],
        size_bytes: int = 0,
    ) -> None:
        """Register a resource for cleanup."""
        self._cleanup_hook.register(name, cleanup_fn, size_bytes)
        self._resources.add(name)
    
    def register_weak(
        self,
        name: str,
        obj: Any,
        cleanup_fn: Optional[Callable[[], None]] = None,
        size_bytes: int = 0,
    ) -> None:
        """Register an object with weak reference tracking."""
        self._cleanup_hook.register_weak(name, obj, cleanup_fn, size_bytes)
        self._resources.add(name)

