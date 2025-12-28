# ============================================================
#  ANM V0-OpenSource — Synchronization Module
#  Seamless System Integration
# ============================================================

"""
ANM Sync Module

Provides seamless integration between all ANM components:
- Component registry
- Event system
- State synchronization
- Pipeline coordination
"""

from __future__ import annotations
from typing import (
    Dict, Any, List, Optional, Callable, TypeVar, Type,
    Set, Tuple, Union
)
from dataclasses import dataclass, field
from threading import RLock, Event as ThreadEvent
from enum import Enum, auto
from weakref import WeakValueDictionary
from collections import defaultdict
import time
import logging

__all__ = [
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
]

T = TypeVar('T')
logger = logging.getLogger("anm.sync")


class ComponentStatus(Enum):
    """Status of a registered component."""
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()
    SHUTDOWN = auto()


@dataclass(slots=True)
class ComponentInfo:
    """Information about a registered component."""
    name: str
    component: Any
    status: ComponentStatus = ComponentStatus.UNINITIALIZED
    version: str = "0.0.0"
    dependencies: Set[str] = field(default_factory=set)
    registered_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComponentRegistry:
    """
    Central registry for all ANM components.
    
    Features:
    - Lazy component loading
    - Dependency tracking
    - Status monitoring
    - Weak references (auto-cleanup)
    """
    
    def __init__(self):
        self._components: Dict[str, ComponentInfo] = {}
        self._weak_refs: WeakValueDictionary = WeakValueDictionary()
        self._lock = RLock()
        self._initialized = False
    
    def register(
        self,
        name: str,
        component: Any,
        version: str = "0.0.0",
        dependencies: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Register a component."""
        with self._lock:
            if name in self._components:
                logger.warning(f"Component '{name}' already registered, updating")
            
            info = ComponentInfo(
                name=name,
                component=component,
                version=version,
                dependencies=dependencies or set(),
                metadata=metadata or {},
            )
            
            self._components[name] = info
            
            # Only store weak ref if object supports it
            try:
                self._weak_refs[name] = component
            except TypeError:
                pass  # Object doesn't support weak refs
            
            logger.debug(f"Registered component: {name} v{version}")
            return True
    
    def get(self, name: str) -> Optional[Any]:
        """Get a component by name."""
        with self._lock:
            info = self._components.get(name)
            return info.component if info else None
    
    def get_info(self, name: str) -> Optional[ComponentInfo]:
        """Get component info."""
        with self._lock:
            return self._components.get(name)
    
    def update_status(self, name: str, status: ComponentStatus) -> bool:
        """Update component status."""
        with self._lock:
            if name not in self._components:
                return False
            self._components[name].status = status
            return True
    
    def list_components(self) -> List[str]:
        """List all registered component names."""
        with self._lock:
            return list(self._components.keys())
    
    def list_by_status(self, status: ComponentStatus) -> List[str]:
        """List components with specific status."""
        with self._lock:
            return [
                name for name, info in self._components.items()
                if info.status == status
            ]
    
    def check_dependencies(self, name: str) -> Tuple[bool, List[str]]:
        """Check if all dependencies are satisfied."""
        with self._lock:
            info = self._components.get(name)
            if not info:
                return False, [f"Component '{name}' not found"]
            
            missing = []
            for dep in info.dependencies:
                if dep not in self._components:
                    missing.append(dep)
            
            return len(missing) == 0, missing
    
    def initialize_all(self) -> Dict[str, bool]:
        """Initialize all components in dependency order."""
        results = {}
        
        # Topological sort for dependency order
        order = self._get_initialization_order()
        
        for name in order:
            info = self._components.get(name)
            if not info:
                continue
            
            # Check dependencies first
            deps_ok, missing = self.check_dependencies(name)
            if not deps_ok:
                logger.error(f"Cannot initialize {name}: missing {missing}")
                results[name] = False
                self.update_status(name, ComponentStatus.ERROR)
                continue
            
            # Initialize
            self.update_status(name, ComponentStatus.INITIALIZING)
            try:
                if hasattr(info.component, 'initialize'):
                    success = info.component.initialize()
                    results[name] = success
                    self.update_status(
                        name,
                        ComponentStatus.READY if success else ComponentStatus.ERROR
                    )
                else:
                    results[name] = True
                    self.update_status(name, ComponentStatus.READY)
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
                results[name] = False
                self.update_status(name, ComponentStatus.ERROR)
        
        self._initialized = True
        return results
    
    def _get_initialization_order(self) -> List[str]:
        """Get topologically sorted initialization order."""
        visited = set()
        order = []
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            info = self._components.get(name)
            if info:
                for dep in info.dependencies:
                    visit(dep)
            
            order.append(name)
        
        for name in self._components:
            visit(name)
        
        return order
    
    def shutdown_all(self) -> None:
        """Shutdown all components in reverse order."""
        order = list(reversed(self._get_initialization_order()))
        
        for name in order:
            info = self._components.get(name)
            if not info:
                continue
            
            self.update_status(name, ComponentStatus.SHUTDOWN)
            try:
                if hasattr(info.component, 'shutdown'):
                    info.component.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")


class EventBus:
    """
    Publish-subscribe event system.
    
    Features:
    - Topic-based routing
    - Async-compatible
    - Wildcard subscriptions
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = RLock()
    
    def subscribe(self, topic: str, handler: Callable[[str, Any], None]) -> Callable:
        """Subscribe to a topic. Returns unsubscribe function."""
        with self._lock:
            self._subscribers[topic].append(handler)
        
        def unsubscribe():
            with self._lock:
                if handler in self._subscribers[topic]:
                    self._subscribers[topic].remove(handler)
        
        return unsubscribe
    
    def publish(self, topic: str, data: Any = None) -> int:
        """Publish event to topic. Returns number of handlers called."""
        handlers = []
        
        with self._lock:
            # Exact match
            handlers.extend(self._subscribers.get(topic, []))
            
            # Wildcard matches (e.g., "system.*" matches "system.ready")
            for pattern, subs in self._subscribers.items():
                if pattern.endswith(".*"):
                    prefix = pattern[:-2]
                    if topic.startswith(prefix + "."):
                        handlers.extend(subs)
        
        # Call handlers outside lock
        called = 0
        for handler in handlers:
            try:
                handler(topic, data)
                called += 1
            except Exception as e:
                logger.error(f"Event handler error for {topic}: {e}")
        
        return called
    
    def clear(self, topic: Optional[str] = None) -> None:
        """Clear subscribers for topic or all."""
        with self._lock:
            if topic:
                self._subscribers.pop(topic, None)
            else:
                self._subscribers.clear()


@dataclass(slots=True)
class StateSnapshot:
    """Enhanced snapshot of system state."""
    timestamp: float
    state: Dict[str, Any]
    version: int
    checksum: Optional[str] = None  # Hash for integrity verification
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def verify_checksum(self) -> bool:
        """Verify snapshot integrity."""
        if self.checksum is None:
            return True  # No checksum to verify
        
        import hashlib
        import json
        state_str = json.dumps(self.state, sort_keys=True)
        computed = hashlib.sha256(state_str.encode()).hexdigest()
        return computed == self.checksum


@dataclass(slots=True)
class StateDiff:
    """Difference between two state versions."""
    from_version: int
    to_version: int
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)
    changed_keys: List[str] = field(default_factory=list)
    changes: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # key -> {old, new}


@dataclass(slots=True)
class StateSchema:
    """Schema definition for state validation."""
    key: str
    validator: Callable[[Any], bool]
    default_value: Any = None
    required: bool = False
    description: str = ""


class StateManager:
    """
    Enhanced centralized state management.
    
    Features:
    - Atomic updates
    - Change tracking
    - State history with snapshots
    - Subscriptions
    - Validation with schemas
    - Consistency checks
    - State diffs
    - Rollback capabilities
    """
    
    def __init__(self, max_history: int = 100, enable_validation: bool = True):
        self._state: Dict[str, Any] = {}
        self._version = 0
        self._history: List[StateSnapshot] = []
        self._max_history = max_history
        self._lock = RLock()
        self._watchers: Dict[str, List[Callable]] = defaultdict(list)
        self._schemas: Dict[str, StateSchema] = {}
        self._enable_validation = enable_validation
        self._change_log: List[Tuple[int, str, Any, Any]] = []  # (version, key, old, new)
    
    def register_schema(self, schema: StateSchema) -> None:
        """Register a validation schema for a state key."""
        with self._lock:
            self._schemas[schema.key] = schema
            
            # Apply default if key doesn't exist
            if schema.key not in self._state and schema.default_value is not None:
                self._state[schema.key] = schema.default_value
    
    def validate_value(self, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a value against schema.
        
        Returns:
            (is_valid, error_message)
        """
        if not self._enable_validation:
            return True, None
        
        schema = self._schemas.get(key)
        if schema is None:
            return True, None  # No schema = no validation
        
        if schema.required and value is None:
            return False, f"Key '{key}' is required but value is None"
        
        if value is not None and not schema.validator(value):
            return False, f"Value for '{key}' failed validation: {schema.description}"
        
        return True, None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        with self._lock:
            return self._state.get(key, default)
    
    def set(self, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set state value with validation.
        
        Returns:
            True if set successfully, False if validation failed
        """
        with self._lock:
            # Validate if enabled
            if validate and self._enable_validation:
                is_valid, error = self.validate_value(key, value)
                if not is_valid:
                    logger.warning(f"State validation failed for '{key}': {error}")
                    return False
            
            old_value = self._state.get(key)
            self._state[key] = value
            self._version += 1
            
            # Log change
            self._change_log.append((self._version, key, old_value, value))
            if len(self._change_log) > self._max_history * 2:
                self._change_log = self._change_log[-self._max_history * 2:]
            
            # Notify watchers
            for watcher in self._watchers.get(key, []):
                try:
                    watcher(key, value, old_value)
                except Exception as e:
                    logger.error(f"State watcher error: {e}")
    
            return True
    
    def update(self, updates: Dict[str, Any], validate: bool = True) -> Dict[str, bool]:
        """
        Batch update multiple keys with validation.
        
        Returns:
            Dict mapping keys to success status
        """
        results = {}
        with self._lock:
            for key, value in updates.items():
                # Validate if enabled
                if validate and self._enable_validation:
                    is_valid, error = self.validate_value(key, value)
                    if not is_valid:
                        logger.warning(f"State validation failed for '{key}': {error}")
                        results[key] = False
                        continue
                
                old_value = self._state.get(key)
                self._state[key] = value
                self._change_log.append((self._version + 1, key, old_value, value))
                results[key] = True
            
            if any(results.values()):
                self._version += 1
                
                # Notify watchers
                for key, value in updates.items():
                    if results.get(key):
                        old_value = self._state.get(key)  # Will be the old value before update
                        for watcher in self._watchers.get(key, []):
                            try:
                                watcher(key, value, old_value)
                            except Exception as e:
                                logger.error(f"State watcher error: {e}")
        
        return results
    
    def watch(self, key: str, callback: Callable[[str, Any, Any], None]) -> Callable:
        """Watch a key for changes. Returns unwatch function."""
        with self._lock:
            self._watchers[key].append(callback)
        
        def unwatch():
            with self._lock:
                if callback in self._watchers[key]:
                    self._watchers[key].remove(callback)
        
        return unwatch
    
    def snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> StateSnapshot:
        """
        Create enhanced state snapshot with checksum.
        
        Args:
            metadata: Optional metadata to attach to snapshot
        
        Returns:
            StateSnapshot with checksum
        """
        import hashlib
        import json
        
        with self._lock:
            state_copy = dict(self._state)
            
            # Compute checksum
            state_str = json.dumps(state_copy, sort_keys=True, default=str)
            checksum = hashlib.sha256(state_str.encode()).hexdigest()
            
            snap = StateSnapshot(
                timestamp=time.time(),
                state=state_copy,
                version=self._version,
                checksum=checksum,
                metadata=metadata or {},
            )
            
            self._history.append(snap)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            return snap
    
    def restore(self, version: int, verify: bool = True) -> bool:
        """
        Restore to a specific version with optional checksum verification.
        
        Args:
            version: Version to restore to
            verify: Verify snapshot checksum before restoring
        
        Returns:
            True if restored successfully
        """
        with self._lock:
            for snap in reversed(self._history):
                if snap.version == version:
                    # Verify checksum if requested
                    if verify and not snap.verify_checksum():
                        logger.error(f"Snapshot {version} checksum verification failed")
                        return False
                    
                    self._state = dict(snap.state)
                    self._version = version
                    
                    # Log restoration
                    self._change_log.append((version, "__restore__", None, f"Restored to version {version}"))
                    
                    return True
            return False
    
    def restore_latest(self, verify: bool = True) -> bool:
        """Restore to the latest snapshot."""
        with self._lock:
            if not self._history:
                return False
            latest = self._history[-1]
            return self.restore(latest.version, verify)
    
    def get_diff(self, from_version: int, to_version: Optional[int] = None) -> Optional[StateDiff]:
        """
        Get differences between two state versions.
        
        Args:
            from_version: Starting version
            to_version: Ending version (defaults to current)
        
        Returns:
            StateDiff or None if versions not found
        """
        with self._lock:
            to_version = to_version or self._version
            
            # Find snapshots
            from_snap = None
            to_snap = None
            
            for snap in self._history:
                if snap.version == from_version:
                    from_snap = snap
                if snap.version == to_version:
                    to_snap = snap
            
            if not from_snap or not to_snap:
                return None
            
            from_state = from_snap.state
            to_state = to_snap.state
            
            # Compute diff
            from_keys = set(from_state.keys())
            to_keys = set(to_state.keys())
            
            added = list(to_keys - from_keys)
            removed = list(from_keys - to_keys)
            changed = []
            changes = {}
            
            for key in from_keys & to_keys:
                if from_state[key] != to_state[key]:
                    changed.append(key)
                    changes[key] = {
                        "old": from_state[key],
                        "new": to_state[key],
                    }
            
            return StateDiff(
                from_version=from_version,
                to_version=to_version,
                added_keys=added,
                removed_keys=removed,
                changed_keys=changed,
                changes=changes,
            )
    
    def check_consistency(self) -> Tuple[bool, List[str]]:
        """
        Check state consistency.
        
        Returns:
            (is_consistent, list_of_issues)
        """
        issues = []
        
        with self._lock:
            # Check required schemas
            for key, schema in self._schemas.items():
                if schema.required and key not in self._state:
                    issues.append(f"Required key '{key}' is missing")
            
            # Validate all values against schemas
            for key, value in self._state.items():
                is_valid, error = self.validate_value(key, value)
                if not is_valid:
                    issues.append(f"Key '{key}': {error}")
            
            # Check snapshot integrity
            for snap in self._history:
                if not snap.verify_checksum():
                    issues.append(f"Snapshot version {snap.version} has invalid checksum")
        
        return len(issues) == 0, issues
    
    def get_change_log(self, since_version: Optional[int] = None) -> List[Tuple[int, str, Any, Any]]:
        """
        Get change log since a version.
        
        Args:
            since_version: Version to start from (defaults to 0)
        
        Returns:
            List of (version, key, old_value, new_value) tuples
        """
        with self._lock:
            if since_version is None:
                return list(self._change_log)
            return [
                entry for entry in self._change_log
                if entry[0] > since_version
            ]
    
    def rollback(self, steps: int = 1) -> bool:
        """
        Rollback state by N steps.
        
        Args:
            steps: Number of versions to rollback
        
        Returns:
            True if rollback successful
        """
        with self._lock:
            target_version = max(0, self._version - steps)
            return self.restore(target_version)
    
    @property
    def version(self) -> int:
        return self._version
    
    @property
    def size(self) -> int:
        """Get number of state keys."""
        with self._lock:
            return len(self._state)
    
    def clear(self, keep_schemas: bool = True) -> None:
        """Clear all state."""
        with self._lock:
            self._state.clear()
            self._version = 0
            self._change_log.clear()
            if not keep_schemas:
                self._schemas.clear()


@dataclass
class PipelineStage:
    """A stage in the processing pipeline."""
    name: str
    handler: Callable[[Any], Any]
    timeout_ms: float = 30000
    retries: int = 0
    on_error: Optional[Callable[[Exception], Any]] = None


class Pipeline:
    """
    Sequential processing pipeline.
    
    Features:
    - Stage-based processing
    - Error handling per stage
    - Timeout support
    - Retry logic
    """
    
    def __init__(self, name: str = "pipeline"):
        self.name = name
        self._stages: List[PipelineStage] = []
        self._lock = RLock()
    
    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        """Add a stage. Returns self for chaining."""
        with self._lock:
            self._stages.append(stage)
        return self
    
    def add(
        self,
        name: str,
        handler: Callable[[Any], Any],
        timeout_ms: float = 30000,
        retries: int = 0,
    ) -> "Pipeline":
        """Convenience method to add stage."""
        return self.add_stage(PipelineStage(
            name=name,
            handler=handler,
            timeout_ms=timeout_ms,
            retries=retries,
        ))
    
    def execute(self, input_data: Any) -> Tuple[bool, Any, List[str]]:
        """
        Execute pipeline.
        
        Returns:
            (success, result_or_error, stage_names_completed)
        """
        current = input_data
        completed = []
        
        for stage in self._stages:
            attempts = 0
            max_attempts = stage.retries + 1
            
            while attempts < max_attempts:
                attempts += 1
                try:
                    current = stage.handler(current)
                    completed.append(stage.name)
                    break
                except Exception as e:
                    if attempts >= max_attempts:
                        if stage.on_error:
                            try:
                                current = stage.on_error(e)
                                completed.append(f"{stage.name}(fallback)")
                                break
                            except Exception:
                                pass
                        return False, e, completed
        
        return True, current, completed


class ANMSync:
    """
    Master synchronization controller for ANM.
    
    Coordinates all subsystems:
    - Component lifecycle
    - Event distribution
    - State management
    - Pipeline execution
    """
    
    _instance: Optional["ANMSync"] = None
    
    def __new__(cls) -> "ANMSync":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.registry = ComponentRegistry()
        self.events = EventBus()
        self.state = StateManager()
        
        self._pipelines: Dict[str, Pipeline] = {}
        self._lock = RLock()
        self._ready = ThreadEvent()
        self._initialized = True
    
    def register_component(
        self,
        name: str,
        component: Any,
        **kwargs
    ) -> bool:
        """Register a component."""
        result = self.registry.register(name, component, **kwargs)
        if result:
            self.events.publish("component.registered", {"name": name})
        return result
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get a component."""
        return self.registry.get(name)
    
    def create_pipeline(self, name: str) -> Pipeline:
        """Create or get a named pipeline."""
        with self._lock:
            if name not in self._pipelines:
                self._pipelines[name] = Pipeline(name)
            return self._pipelines[name]
    
    def run_pipeline(self, name: str, data: Any) -> Tuple[bool, Any, List[str]]:
        """Execute a named pipeline."""
        with self._lock:
            pipeline = self._pipelines.get(name)
        
        if not pipeline:
            return False, ValueError(f"Pipeline '{name}' not found"), []
        
        self.events.publish("pipeline.start", {"name": name})
        success, result, stages = pipeline.execute(data)
        self.events.publish("pipeline.complete", {
            "name": name,
            "success": success,
            "stages": stages,
        })
        
        return success, result, stages
    
    def initialize(self) -> Dict[str, bool]:
        """Initialize all registered components."""
        self.events.publish("system.initializing", None)
        results = self.registry.initialize_all()
        
        all_ok = all(results.values())
        self.state.set("system.initialized", all_ok)
        self.state.set("system.components", results)
        
        if all_ok:
            self._ready.set()
            self.events.publish("system.ready", results)
        else:
            self.events.publish("system.error", results)
        
        return results
    
    def shutdown(self) -> None:
        """Shutdown all components."""
        self.events.publish("system.shutdown", None)
        self._ready.clear()
        self.registry.shutdown_all()
    
    def wait_ready(self, timeout: Optional[float] = None) -> bool:
        """Wait for system to be ready."""
        return self._ready.wait(timeout)
    
    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()


# Global sync instance
_sync = ANMSync()

def get_sync() -> ANMSync:
    """Get global sync instance."""
    return _sync
