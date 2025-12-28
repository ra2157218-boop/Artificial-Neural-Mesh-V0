# ============================================================
#  ANM V0-OpenSource — Thread & Worker Pools
#  High-Performance Concurrency Primitives
# ============================================================

"""
ANM Pool Module

Provides optimized concurrency primitives:
- Managed thread pools
- Worker pools with queue
- Batch processing
- Resource limiting
"""

from __future__ import annotations
from typing import (
    Dict, Any, List, Optional, Callable, TypeVar, Generic,
    Tuple, Iterator, Sequence
)
from concurrent.futures import (
    ThreadPoolExecutor, Future, as_completed, wait, FIRST_COMPLETED
)
from dataclasses import dataclass, field
from threading import Semaphore, Event
from queue import Queue, Empty
import time

__all__ = [
    "WorkerPool",
    "BatchProcessor",
    "RateLimiter",
    "TaskResult",
    "parallel_map",
    "parallel_filter",
]

T = TypeVar('T')
R = TypeVar('R')


@dataclass(slots=True)
class TaskResult(Generic[T]):
    """Result from a pooled task execution."""
    success: bool
    value: Optional[T] = None
    error: Optional[Exception] = None
    duration_ms: float = 0.0
    task_id: Optional[str] = None
    
    @classmethod
    def ok(cls, value: T, duration_ms: float = 0.0, task_id: Optional[str] = None) -> "TaskResult[T]":
        return cls(success=True, value=value, duration_ms=duration_ms, task_id=task_id)
    
    @classmethod
    def err(cls, error: Exception, duration_ms: float = 0.0, task_id: Optional[str] = None) -> "TaskResult[T]":
        return cls(success=False, error=error, duration_ms=duration_ms, task_id=task_id)


class WorkerPool:
    """
    Managed thread pool with resource control.
    
    Features:
    - Configurable worker count
    - Task queuing
    - Graceful shutdown
    - Statistics tracking
    """
    
    __slots__ = (
        '_executor', '_max_workers', '_active_tasks',
        '_total_tasks', '_failed_tasks', '_shutdown_event'
    )
    
    def __init__(self, max_workers: int = 4):
        self._max_workers = max(1, max_workers)
        self._executor = ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="anm_worker"
        )
        self._active_tasks = 0
        self._total_tasks = 0
        self._failed_tasks = 0
        self._shutdown_event = Event()
    
    def submit(
        self,
        fn: Callable[..., T],
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Future[TaskResult[T]]:
        """Submit a task to the pool."""
        self._total_tasks += 1
        
        def wrapped() -> TaskResult[T]:
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                return TaskResult.ok(result, duration, task_id)
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                self._failed_tasks += 1
                return TaskResult.err(e, duration, task_id)
        
        return self._executor.submit(wrapped)
    
    def map(
        self,
        fn: Callable[[T], R],
        items: Sequence[T],
        timeout: Optional[float] = None,
    ) -> List[TaskResult[R]]:
        """Map function over items in parallel."""
        futures = [self.submit(fn, item) for item in items]
        return self._collect_results(futures, timeout)
    
    def _collect_results(
        self,
        futures: List[Future[TaskResult[T]]],
        timeout: Optional[float] = None,
    ) -> List[TaskResult[T]]:
        """Collect results from futures."""
        results: List[TaskResult[T]] = []
        
        try:
            for future in as_completed(futures, timeout=timeout):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(TaskResult.err(e))
        except TimeoutError:
            # Cancel remaining futures
            for f in futures:
                if not f.done():
                    f.cancel()
        
        return results
    
    def shutdown(self, wait: bool = True, cancel_pending: bool = False) -> None:
        """Shutdown the pool."""
        self._shutdown_event.set()
        self._executor.shutdown(wait=wait, cancel_futures=cancel_pending)
    
    @property
    def max_workers(self) -> int:
        return self._max_workers
    
    @property
    def total_tasks(self) -> int:
        return self._total_tasks
    
    @property
    def failed_tasks(self) -> int:
        return self._failed_tasks
    
    @property
    def success_rate(self) -> float:
        if self._total_tasks == 0:
            return 1.0
        return (self._total_tasks - self._failed_tasks) / self._total_tasks
    
    def __enter__(self) -> "WorkerPool":
        return self
    
    def __exit__(self, *args) -> None:
        self.shutdown()


class BatchProcessor(Generic[T, R]):
    """
    Process items in configurable batches.
    
    Features:
    - Configurable batch size
    - Progress callbacks
    - Error handling per batch
    """
    
    __slots__ = ('_batch_size', '_pool', '_on_batch_complete')
    
    def __init__(
        self,
        batch_size: int = 10,
        max_workers: int = 4,
        on_batch_complete: Optional[Callable[[int, int], None]] = None,
    ):
        self._batch_size = max(1, batch_size)
        self._pool = WorkerPool(max_workers)
        self._on_batch_complete = on_batch_complete
    
    def process(
        self,
        items: Sequence[T],
        processor: Callable[[T], R],
    ) -> List[TaskResult[R]]:
        """Process all items in batches."""
        results: List[TaskResult[R]] = []
        total_batches = (len(items) + self._batch_size - 1) // self._batch_size
        
        for i in range(0, len(items), self._batch_size):
            batch = items[i:i + self._batch_size]
            batch_results = self._pool.map(processor, batch)
            results.extend(batch_results)
            
            if self._on_batch_complete:
                batch_num = i // self._batch_size + 1
                self._on_batch_complete(batch_num, total_batches)
        
        return results
    
    def process_with_context(
        self,
        items: Sequence[T],
        processor: Callable[[T, int, int], R],
    ) -> List[TaskResult[R]]:
        """Process with index and total context."""
        total = len(items)
        
        def wrapped(item_with_idx: Tuple[int, T]) -> R:
            idx, item = item_with_idx
            return processor(item, idx, total)
        
        indexed_items = list(enumerate(items))
        return self.process(indexed_items, wrapped)  # type: ignore
    
    def shutdown(self) -> None:
        """Shutdown the processor."""
        self._pool.shutdown()
    
    def __enter__(self) -> "BatchProcessor[T, R]":
        return self
    
    def __exit__(self, *args) -> None:
        self.shutdown()


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Features:
    - Configurable rate and burst
    - Thread-safe
    - Non-blocking check
    """
    
    __slots__ = (
        '_rate', '_burst', '_tokens', '_last_update', '_semaphore'
    )
    
    def __init__(self, rate: float, burst: int = 1):
        """
        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._semaphore = Semaphore(1)
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_update = now
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token. Blocks until available or timeout.
        
        Returns:
            True if acquired, False if timeout
        """
        deadline = time.monotonic() + timeout if timeout else None
        
        while True:
            with self._semaphore:
                self._refill()
                
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
            
            if deadline and time.monotonic() >= deadline:
                return False
            
            # Wait a bit before retrying
            time.sleep(min(0.1, 1.0 / self._rate if self._rate > 0 else 0.1))
    
    def try_acquire(self) -> bool:
        """Non-blocking acquire attempt."""
        with self._semaphore:
            self._refill()
            
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            
            return False
    
    @property
    def available_tokens(self) -> float:
        """Current available tokens."""
        with self._semaphore:
            self._refill()
            return self._tokens


# ============================================================
#  UTILITY FUNCTIONS
# ============================================================

def parallel_map(
    fn: Callable[[T], R],
    items: Sequence[T],
    max_workers: int = 4,
    timeout: Optional[float] = None,
) -> List[R]:
    """
    Map function over items in parallel.
    
    Unlike pool.map, this returns values directly (raises on error).
    """
    with WorkerPool(max_workers) as pool:
        results = pool.map(fn, items, timeout)
    
    values: List[R] = []
    for result in results:
        if not result.success:
            raise result.error or Exception("Unknown error")
        values.append(result.value)  # type: ignore
    
    return values


def parallel_filter(
    predicate: Callable[[T], bool],
    items: Sequence[T],
    max_workers: int = 4,
) -> List[T]:
    """Filter items in parallel."""
    def check_item(item: T) -> Optional[T]:
        return item if predicate(item) else None
    
    with WorkerPool(max_workers) as pool:
        results = pool.map(check_item, items)
    
    return [r.value for r in results if r.success and r.value is not None]
