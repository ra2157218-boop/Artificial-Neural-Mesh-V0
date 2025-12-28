# ============================================================
#  ANM V0-OpenSource — Resource Manager
#  Context Managers and Resource Cleanup
# ============================================================

"""
Resource Manager Module

Provides context managers and cleanup utilities for:
- File handles
- Thread pools
- Model instances
- Connections
- Temporary resources
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Callable, ContextManager, TypeVar
from dataclasses import dataclass, field
from threading import RLock
from contextlib import contextmanager, ExitStack
import atexit
import logging
import sys

from anm.core.memory_optimizer import CleanupHook

logger = logging.getLogger("anm.resource")

T = TypeVar('T')

__all__ = [
    "ResourceManager",
    "ManagedResource",
    "cleanup_on_exit",
    "register_cleanup",
    "with_cleanup",
    "ResourceContext",
]


@dataclass(slots=True)
class ManagedResource:
    """Information about a managed resource."""
    name: str
    resource: Any
    cleanup_fn: Callable[[], None]
    auto_cleanup: bool = True
    priority: int = 0  # Lower priority = cleaned up first


class ResourceManager:
    """
    Centralized resource manager for ANM.
    
    Tracks and cleans up resources in proper order.
    """
    
    _instance: Optional['ResourceManager'] = None
    _lock = RLock()
    
    def __new__(cls) -> 'ResourceManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._resources: Dict[str, ManagedResource] = {}
                    cls._instance._cleanup_hook = CleanupHook()
                    cls._instance._initialized = False
                    cls._instance._exit_registered = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Register atexit handler
        if not self._exit_registered:
            atexit.register(self.cleanup_all)
            self._exit_registered = True
            logger.debug("ResourceManager initialized with atexit handler.")
    
    def register(
        self,
        name: str,
        resource: Any,
        cleanup_fn: Callable[[], None],
        auto_cleanup: bool = True,
        priority: int = 0,
    ) -> None:
        """
        Register a resource for cleanup.
        
        Args:
            name: Resource name
            resource: Resource object
            cleanup_fn: Cleanup function
            auto_cleanup: Whether to cleanup automatically
            priority: Cleanup priority (lower = cleaned up first)
        """
        with self._lock:
            self._resources[name] = ManagedResource(
                name=name,
                resource=resource,
                cleanup_fn=cleanup_fn,
                auto_cleanup=auto_cleanup,
                priority=priority,
            )
            logger.debug(f"Registered resource: {name} (priority={priority})")
    
    def unregister(self, name: str) -> bool:
        """Unregister a resource."""
        with self._lock:
            if name in self._resources:
                del self._resources[name]
                logger.debug(f"Unregistered resource: {name}")
                return True
            return False
    
    def cleanup(self, name: str) -> bool:
        """
        Cleanup a specific resource.
        
        Args:
            name: Resource name
        
        Returns:
            True if cleanup was successful
        """
        with self._lock:
            if name not in self._resources:
                return False
            
            resource = self._resources[name]
            try:
                resource.cleanup_fn()
                logger.info(f"Cleaned up resource: {name}")
                if resource.auto_cleanup:
                    del self._resources[name]
                return True
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}", exc_info=True)
                return False
    
    def cleanup_all(self) -> Dict[str, bool]:
        """
        Cleanup all registered resources in priority order.
        
        Returns:
            Dictionary mapping resource names to cleanup success status
        """
        with self._lock:
            results = {}
            
            # Sort by priority (lower priority first)
            sorted_resources = sorted(
                self._resources.items(),
                key=lambda x: x[1].priority
            )
            
            for name, resource in sorted_resources:
                if resource.auto_cleanup:
                    try:
                        resource.cleanup_fn()
                        results[name] = True
                        logger.debug(f"Cleaned up resource: {name}")
                    except Exception as e:
                        results[name] = False
                        logger.error(f"Error cleaning up {name}: {e}", exc_info=True)
            
            # Clear auto-cleanup resources
            self._resources = {
                name: res
                for name, res in self._resources.items()
                if not res.auto_cleanup
            }
            
            logger.info(f"Cleanup completed: {sum(results.values())}/{len(results)} successful")
            return results
    
    def get_resources(self) -> Dict[str, ManagedResource]:
        """Get all registered resources."""
        with self._lock:
            return self._resources.copy()
    
    def __enter__(self) -> 'ResourceManager':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup on context exit."""
        self.cleanup_all()


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def register_cleanup(
    name: str,
    resource: Any,
    cleanup_fn: Callable[[], None],
    auto_cleanup: bool = True,
    priority: int = 0,
) -> None:
    """
    Register a resource for cleanup.
    
    Args:
        name: Resource name
        resource: Resource object
        cleanup_fn: Cleanup function
        auto_cleanup: Whether to cleanup automatically
        priority: Cleanup priority (lower = cleaned up first)
    """
    manager = get_resource_manager()
    manager.register(name, resource, cleanup_fn, auto_cleanup, priority)


def cleanup_on_exit(
    name: str,
    cleanup_fn: Callable[[], None],
    priority: int = 0,
) -> None:
    """
    Register a cleanup function to be called on exit.
    
    Args:
        name: Resource name
        cleanup_fn: Cleanup function
        priority: Cleanup priority
    """
    register_cleanup(name, None, cleanup_fn, auto_cleanup=True, priority=priority)


@contextmanager
def with_cleanup(
    name: str,
    resource: Any,
    cleanup_fn: Callable[[], None],
    priority: int = 0,
) -> ContextManager[Any]:
    """
    Context manager for automatic resource cleanup.
    
    Usage:
        with with_cleanup("my_resource", obj, lambda: obj.close()):
            # Use resource
            pass
    """
    manager = get_resource_manager()
    manager.register(name, resource, cleanup_fn, auto_cleanup=False, priority=priority)
    
    try:
        yield resource
    finally:
        manager.cleanup(name)


class ResourceContext:
    """
    Context manager for managing multiple resources.
    
    Usage:
        with ResourceContext() as ctx:
            ctx.register("file", file_obj, lambda: file_obj.close())
            ctx.register("pool", pool, lambda: pool.shutdown())
            # Use resources
    """
    
    def __init__(self, name: str = "resource_context"):
        self.name = name
        self._manager = get_resource_manager()
        self._resources: List[str] = []
    
    def __enter__(self) -> 'ResourceContext':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup all registered resources."""
        for name in reversed(self._resources):  # Cleanup in reverse order
            self._manager.cleanup(name)
        self._resources.clear()
    
    def register(
        self,
        name: str,
        resource: Any,
        cleanup_fn: Callable[[], None],
        priority: int = 0,
    ) -> None:
        """Register a resource for cleanup."""
        full_name = f"{self.name}.{name}"
        self._manager.register(full_name, resource, cleanup_fn, auto_cleanup=False, priority=priority)
        self._resources.append(full_name)
    
    def unregister(self, name: str) -> bool:
        """Unregister a resource."""
        full_name = f"{self.name}.{name}"
        if full_name in self._resources:
            self._resources.remove(full_name)
            return self._manager.unregister(full_name)
        return False

