# ============================================================
#  ANM V0-OpenSource — Centralized Thread Pool Manager
#  Dynamic Sizing & Health Monitoring
# ============================================================

"""
Centralized Thread Pool Manager

Provides:
- Centralized pool management
- Dynamic worker sizing based on load
- Health monitoring and metrics
- Automatic pool lifecycle management
- Statistics tracking
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable, List, Set
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from threading import RLock, Event
from enum import Enum
import sys
import time
import threading

# Python version compatibility: slots=True requires Python 3.10+
_SUPPORTS_SLOTS = sys.version_info >= (3, 10)

__all__ = [
    "ThreadPoolManager",
    "PoolConfig",
    "PoolHealth",
    "PoolStats",
    "get_thread_pool_manager",
]


class PoolHealth(Enum):
    """Pool health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass(**({"slots": True} if _SUPPORTS_SLOTS else {}))
class PoolStats:
    """Statistics for a thread pool."""
    pool_name: str
    max_workers: int
    current_workers: int
    active_tasks: int
    queued_tasks: int
    total_submitted: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_timeout: int = 0
    avg_task_duration_ms: float = 0.0
    max_task_duration_ms: float = 0.0
    min_task_duration_ms: float = float('inf')
    last_activity: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_completed == 0:
            return 1.0
        return (self.total_completed - self.total_failed) / self.total_completed
    
    @property
    def utilization(self) -> float:
        """Calculate pool utilization (active / max_workers)."""
        if self.max_workers == 0:
            return 0.0
        return min(1.0, (self.active_tasks + self.queued_tasks) / self.max_workers)
    
    @property
    def health(self) -> PoolHealth:
        """Determine pool health based on metrics."""
        if self.success_rate < 0.5:
            return PoolHealth.CRITICAL
        if self.success_rate < 0.7:
            return PoolHealth.UNHEALTHY
        if self.utilization > 0.95 or self.success_rate < 0.9:
            return PoolHealth.DEGRADED
        return PoolHealth.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pool_name": self.pool_name,
            "max_workers": self.max_workers,
            "current_workers": self.current_workers,
            "active_tasks": self.active_tasks,
            "queued_tasks": self.queued_tasks,
            "total_submitted": self.total_submitted,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "total_timeout": self.total_timeout,
            "success_rate": self.success_rate,
            "utilization": self.utilization,
            "health": self.health.value,
            "avg_task_duration_ms": self.avg_task_duration_ms,
            "max_task_duration_ms": self.max_task_duration_ms,
            "min_task_duration_ms": self.min_task_duration_ms if self.min_task_duration_ms != float('inf') else 0.0,
            "last_activity": self.last_activity,
            "uptime_seconds": time.time() - self.created_at,
        }


@dataclass(**({"slots": True} if _SUPPORTS_SLOTS else {}))
class PoolConfig:
    """Configuration for a thread pool."""
    name: str
    min_workers: int = 1
    max_workers: int = 10
    initial_workers: Optional[int] = None
    idle_timeout: float = 300.0  # Seconds before scaling down
    scale_up_threshold: float = 0.8  # Utilization threshold to scale up
    scale_down_threshold: float = 0.3  # Utilization threshold to scale down
    health_check_interval: float = 30.0  # Seconds between health checks
    enable_auto_scaling: bool = True
    thread_name_prefix: Optional[str] = None


class ManagedThreadPool:
    """
    Managed thread pool with dynamic sizing and health monitoring.
    """
    
    __slots__ = (
        '_executor', '_config', '_stats', '_lock',
        '_task_durations', '_shutdown_event', '_health_check_thread'
    )
    
    def __init__(self, config: PoolConfig):
        self._config = config
        self._lock = RLock()
        self._shutdown_event = Event()
        
        # Initialize stats
        initial_workers = config.initial_workers or config.min_workers
        self._stats = PoolStats(
            pool_name=config.name,
            max_workers=initial_workers,
            current_workers=initial_workers,
            active_tasks=0,
            queued_tasks=0,
        )
        
        # Create executor
        thread_prefix = config.thread_name_prefix or f"anm_{config.name}"
        self._executor = ThreadPoolExecutor(
            max_workers=initial_workers,
            thread_name_prefix=thread_prefix
        )
        
        # Track task durations for statistics
        self._task_durations: List[float] = []
        
        # Start health monitoring if enabled
        if config.enable_auto_scaling:
            self._health_check_thread = threading.Thread(
                target=self._health_monitor_loop,
                daemon=True,
                name=f"{thread_prefix}_health"
            )
            self._health_check_thread.start()
        else:
            self._health_check_thread = None
    
    def submit(
        self,
        fn: Callable[..., Any],
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Future:
        """Submit a task to the pool."""
        with self._lock:
            self._stats.total_submitted += 1
            self._stats.queued_tasks += 1
            self._stats.last_activity = time.time()
        
        start_time = time.time()
        
        def wrapped():
            with self._lock:
                self._stats.queued_tasks -= 1
                self._stats.active_tasks += 1
            
            try:
                result = fn(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                with self._lock:
                    self._stats.active_tasks -= 1
                    self._stats.total_completed += 1
                    self._update_duration_stats(duration)
                
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                with self._lock:
                    self._stats.active_tasks -= 1
                    self._stats.total_failed += 1
                    self._stats.total_completed += 1
                    self._update_duration_stats(duration)
                
                raise
        
        future = self._executor.submit(wrapped)
        
        # Handle timeout if specified
        if timeout:
            def timeout_handler():
                time.sleep(timeout)
                if not future.done():
                    with self._lock:
                        self._stats.total_timeout += 1
                    future.cancel()
            
            threading.Thread(target=timeout_handler, daemon=True).start()
        
        return future
    
    def _update_duration_stats(self, duration_ms: float) -> None:
        """Update duration statistics."""
        self._task_durations.append(duration_ms)
        
        # Keep only last 1000 durations for rolling average
        if len(self._task_durations) > 1000:
            self._task_durations = self._task_durations[-1000:]
        
        # Update stats
        self._stats.avg_task_duration_ms = sum(self._task_durations) / len(self._task_durations)
        self._stats.max_task_duration_ms = max(self._stats.max_task_duration_ms, duration_ms)
        self._stats.min_task_duration_ms = min(self._stats.min_task_duration_ms, duration_ms)
    
    def _health_monitor_loop(self) -> None:
        """Background thread for health monitoring and auto-scaling."""
        while not self._shutdown_event.is_set():
            try:
                time.sleep(self._config.health_check_interval)
                self._check_and_scale()
            except Exception:
                # Don't let health check failures crash the pool
                pass
    
    def _check_and_scale(self) -> None:
        """Check pool health and scale if needed."""
        with self._lock:
            stats = self._stats
            utilization = stats.utilization
            current_workers = stats.current_workers
            
            # Scale up if utilization is high
            if utilization > self._config.scale_up_threshold:
                if current_workers < self._config.max_workers:
                    new_workers = min(
                        current_workers + 1,
                        self._config.max_workers
                    )
                    self._resize_pool(new_workers)
            
            # Scale down if utilization is low and idle
            elif utilization < self._config.scale_down_threshold:
                idle_time = time.time() - stats.last_activity
                if idle_time > self._config.idle_timeout:
                    if current_workers > self._config.min_workers:
                        new_workers = max(
                            current_workers - 1,
                            self._config.min_workers
                        )
                        self._resize_pool(new_workers)
    
    def _resize_pool(self, new_size: int) -> None:
        """Resize the thread pool (requires recreating executor)."""
        if new_size == self._stats.current_workers:
            return
        
        # Note: ThreadPoolExecutor doesn't support dynamic resizing
        # We need to create a new executor and migrate
        old_executor = self._executor
        
        # Create new executor with new size
        thread_prefix = self._config.thread_name_prefix or f"anm_{self._config.name}"
        new_executor = ThreadPoolExecutor(
            max_workers=new_size,
            thread_name_prefix=thread_prefix
        )
        
        # Update stats
        self._stats.current_workers = new_size
        self._stats.max_workers = new_size
        
        # Replace executor (old one will finish existing tasks)
        self._executor = new_executor
        
        # Schedule old executor shutdown (non-blocking)
        def shutdown_old():
            time.sleep(5)  # Give time for tasks to complete
            old_executor.shutdown(wait=False)
        
        threading.Thread(target=shutdown_old, daemon=True).start()
    
    def get_stats(self) -> PoolStats:
        """Get current pool statistics."""
        with self._lock:
            # Update current_workers to match executor
            try:
                # ThreadPoolExecutor doesn't expose current workers directly
                # We track it ourselves
                pass
            except:
                pass
            
            return PoolStats(
                pool_name=self._stats.pool_name,
                max_workers=self._stats.max_workers,
                current_workers=self._stats.current_workers,
                active_tasks=self._stats.active_tasks,
                queued_tasks=self._stats.queued_tasks,
                total_submitted=self._stats.total_submitted,
                total_completed=self._stats.total_completed,
                total_failed=self._stats.total_failed,
                total_timeout=self._stats.total_timeout,
                avg_task_duration_ms=self._stats.avg_task_duration_ms,
                max_task_duration_ms=self._stats.max_task_duration_ms,
                min_task_duration_ms=self._stats.min_task_duration_ms,
                last_activity=self._stats.last_activity,
                created_at=self._stats.created_at,
            )
    
    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """Shutdown the pool."""
        self._shutdown_event.set()
        self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)


class ThreadPoolManager:
    """
    Centralized manager for all thread pools in ANM.
    
    Features:
    - Centralized pool creation and management
    - Dynamic sizing based on load
    - Health monitoring
    - Statistics aggregation
    - Automatic cleanup
    """
    
    _instance: Optional[ThreadPoolManager] = None
    _lock = RLock()
    
    def __init__(self):
        self._pools: Dict[str, ManagedThreadPool] = {}
        self._lock = RLock()
        self._default_config = PoolConfig(
            name="default",
            min_workers=2,
            max_workers=10,
            initial_workers=4,
        )
    
    @classmethod
    def get_instance(cls) -> ThreadPoolManager:
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_pool(
        self,
        name: str,
        config: Optional[PoolConfig] = None,
    ) -> ManagedThreadPool:
        """
        Get or create a thread pool.
        
        Args:
            name: Pool name (unique identifier)
            config: Optional pool configuration
        
        Returns:
            ManagedThreadPool instance
        """
        with self._lock:
            if name not in self._pools:
                if config is None:
                    # Create default config with name
                    config = PoolConfig(
                        name=name,
                        min_workers=self._default_config.min_workers,
                        max_workers=self._default_config.max_workers,
                        initial_workers=self._default_config.initial_workers,
                    )
                else:
                    # Ensure name matches
                    config.name = name
                
                self._pools[name] = ManagedThreadPool(config)
            
            return self._pools[name]
    
    def get_or_create_pool(
        self,
        name: str,
        min_workers: int = 1,
        max_workers: int = 10,
        initial_workers: Optional[int] = None,
        **kwargs
    ) -> ManagedThreadPool:
        """
        Convenience method to get or create a pool with simple parameters.
        
        Args:
            name: Pool name
            min_workers: Minimum workers
            max_workers: Maximum workers
            initial_workers: Initial worker count (defaults to min_workers)
            **kwargs: Additional PoolConfig parameters
        
        Returns:
            ManagedThreadPool instance
        """
        config = PoolConfig(
            name=name,
            min_workers=min_workers,
            max_workers=max_workers,
            initial_workers=initial_workers or min_workers,
            **kwargs
        )
        return self.get_pool(name, config)
    
    def shutdown_pool(self, name: str, wait: bool = True) -> bool:
        """Shutdown a specific pool."""
        with self._lock:
            if name in self._pools:
                pool = self._pools.pop(name)
                pool.shutdown(wait=wait)
                return True
            return False
    
    def shutdown_all(self, wait: bool = True) -> None:
        """Shutdown all pools."""
        with self._lock:
            pools = list(self._pools.values())
            self._pools.clear()
        
        for pool in pools:
            pool.shutdown(wait=wait)
    
    def get_pool_stats(self, name: str) -> Optional[PoolStats]:
        """Get statistics for a specific pool."""
        with self._lock:
            if name in self._pools:
                return self._pools[name].get_stats()
            return None
    
    def get_all_stats(self) -> Dict[str, PoolStats]:
        """Get statistics for all pools."""
        with self._lock:
            return {
                name: pool.get_stats()
                for name, pool in self._pools.items()
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all pools."""
        stats = self.get_all_stats()
        
        summary = {
            "total_pools": len(stats),
            "healthy_pools": 0,
            "degraded_pools": 0,
            "unhealthy_pools": 0,
            "critical_pools": 0,
            "pools": {}
        }
        
        for name, pool_stats in stats.items():
            health = pool_stats.health
            if health == PoolHealth.HEALTHY:
                summary["healthy_pools"] += 1
            elif health == PoolHealth.DEGRADED:
                summary["degraded_pools"] += 1
            elif health == PoolHealth.UNHEALTHY:
                summary["unhealthy_pools"] += 1
            else:
                summary["critical_pools"] += 1
            
            summary["pools"][name] = {
                "health": health.value,
                "utilization": pool_stats.utilization,
                "success_rate": pool_stats.success_rate,
                "active_tasks": pool_stats.active_tasks,
            }
        
        return summary
    
    def list_pools(self) -> List[str]:
        """List all active pool names."""
        with self._lock:
            return list(self._pools.keys())
    
    def __enter__(self) -> "ThreadPoolManager":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - shutdown all pools."""
        self.shutdown_all()


def get_thread_pool_manager() -> ThreadPoolManager:
    """Get the global thread pool manager instance."""
    return ThreadPoolManager.get_instance()

