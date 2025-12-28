# ============================================================
#  ANM V0-OpenSource — Core Module
#  High-Performance Unified Core
# ============================================================

"""
ANM Core - Unified High-Performance Core Module

This module provides:
- Optimized data structures
- Thread-safe utilities
- Performance primitives
- Unified type definitions
"""

__version__ = "0.1.0-opensource"

# Types
from anm.core.types import (
    ANM_VERSION,
    ANM_CODENAME,
    Domain,
    QueryType,
    ResponseQuality,
    ProcessingPhase,
    Timestamp,
    Score,
    Confidence,
    ReasoningStep,
    DomainResult,
    QueryResult,
    ANMResult,
    Specialist,
    MemoryStore,
    Verifiable,
    ANMComponent,
    TimedOperation,
)

# Cache
from anm.core.cache import (
    LRUCache,
    TTLCache,
    QueryCache,
    CacheStats,
    CacheEntry,
    cached,
)

# Pool
from anm.core.pool import (
    WorkerPool,
    BatchProcessor,
    RateLimiter,
    TaskResult,
    parallel_map,
    parallel_filter,
)

# Thread Pool Manager
from anm.core.thread_pool_manager import (
    ThreadPoolManager,
    PoolConfig,
    PoolHealth,
    PoolStats,
    ManagedThreadPool,
    get_thread_pool_manager,
)

# Circuit Breaker
from anm.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    RetryPolicy,
    CircuitBreakerStats,
    CircuitBreakerConfig,
    CircuitBreakerManager,
    CircuitBreakerOpenError,
    get_circuit_breaker_manager,
    with_circuit_breaker,
)

# Sync
from anm.core.sync import (
    ComponentRegistry,
    ComponentInfo,
    ComponentStatus,
    EventBus,
    StateManager,
    StateSnapshot,
    StateDiff,
    StateSchema,
    Pipeline,
    PipelineStage,
    ANMSync,
    get_sync,
)

# Memory Optimizer
from anm.core.memory_optimizer import (
    MemoryProfiler,
    MemoryMonitor,
    WeakRefCache,
    CleanupHook,
    MemoryContext,
    MemorySnapshot,
    ResourceInfo,
    track_memory,
    cleanup_resources,
    get_memory_usage,
)

# Resource Manager
from anm.core.resource_manager import (
    ResourceManager,
    ManagedResource,
    ResourceContext,
    cleanup_on_exit,
    register_cleanup,
    with_cleanup,
    get_resource_manager,
)

__all__ = [
    # Version
    "ANM_VERSION",
    "ANM_CODENAME",
    
    # Types
    "Domain",
    "QueryType",
    "ResponseQuality",
    "ProcessingPhase",
    "Timestamp",
    "Score",
    "Confidence",
    "ReasoningStep",
    "DomainResult",
    "QueryResult",
    "ANMResult",
    "Specialist",
    "MemoryStore",
    "Verifiable",
    "ANMComponent",
    "TimedOperation",
    
    # Cache
    "LRUCache",
    "TTLCache",
    "QueryCache",
    "CacheStats",
    "CacheEntry",
    "cached",
    
    # Pool
    "WorkerPool",
    "BatchProcessor",
    "RateLimiter",
    "TaskResult",
    "parallel_map",
    "parallel_filter",
    
    # Thread Pool Manager
    "ThreadPoolManager",
    "PoolConfig",
    "PoolHealth",
    "PoolStats",
    "ManagedThreadPool",
    "get_thread_pool_manager",
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "RetryPolicy",
    "CircuitBreakerStats",
    "CircuitBreakerConfig",
    "CircuitBreakerManager",
    "CircuitBreakerOpenError",
    "get_circuit_breaker_manager",
    "with_circuit_breaker",
    
    # Sync
    "ComponentRegistry",
    "ComponentInfo",
    "ComponentStatus",
    "EventBus",
    "StateManager",
    "StateSnapshot",
    "StateDiff",
    "StateSchema",
    "Pipeline",
    "PipelineStage",
    "ANMSync",
    "get_sync",
    
    # Memory Optimizer
    "MemoryProfiler",
    "MemoryMonitor",
    "WeakRefCache",
    "CleanupHook",
    "MemoryContext",
    "MemorySnapshot",
    "ResourceInfo",
    "track_memory",
    "cleanup_resources",
    "get_memory_usage",
    
    # Resource Manager
    "ResourceManager",
    "ManagedResource",
    "ResourceContext",
    "cleanup_on_exit",
    "register_cleanup",
    "with_cleanup",
    "get_resource_manager",
]
