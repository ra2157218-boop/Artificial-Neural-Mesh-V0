# ============================================================
#  ANM V0-OpenSource — Circuit Breaker Pattern
#  Fault Tolerance for Specialists with Retry Logic
# ============================================================

"""
Circuit Breaker Pattern Implementation

Provides:
- Circuit breaker for failing services/specialists
- Automatic failure detection and recovery
- Retry logic with exponential backoff
- Health tracking and statistics
- Graceful degradation
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, List
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
import time
import random

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "RetryPolicy",
    "CircuitBreakerStats",
    "CircuitBreakerConfig",
    "with_circuit_breaker",
    "CircuitBreakerManager",
    "get_circuit_breaker_manager",
]


T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, requests blocked immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass(slots=True)
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Rejected when circuit is open
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    def reset(self) -> None:
        """Reset statistics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rejected_requests = 0
        self.state_changes = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rejected_requests": self.rejected_requests,
            "state_changes": self.state_changes,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
        }


@dataclass(slots=True)
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Open circuit after N consecutive failures
    success_threshold: int = 2  # Close circuit after N consecutive successes (half-open)
    timeout_seconds: float = 60.0  # Time before attempting half-open
    expected_exception: type = Exception  # Exception type to catch
    name: str = "default"  # Circuit breaker name


@dataclass(slots=True)
class RetryPolicy:
    """Retry policy configuration."""
    max_retries: int = 3
    initial_delay: float = 0.1  # Initial delay in seconds
    max_delay: float = 10.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff base
    jitter: bool = True  # Add random jitter to delays
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add ±20% jitter
            jitter_amount = delay * 0.2
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0.0, delay)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by:
    1. Tracking failures
    2. Opening circuit when threshold reached
    3. Blocking requests when open
    4. Testing recovery in half-open state
    5. Closing circuit when service recovers
    """
    
    __slots__ = (
        '_config', '_state', '_lock', '_stats',
        '_failure_count', '_success_count', '_last_failure_time',
        '_opened_at'
    )
    
    def __init__(self, config: CircuitBreakerConfig):
        self._config = config
        self._state = CircuitState.CLOSED
        self._lock = RLock()
        self._stats = CircuitBreakerStats()
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._opened_at = None
    
    def call(
        self,
        func: Callable[..., T],
        *args,
        retry_policy: Optional[RetryPolicy] = None,
        **kwargs
    ) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            retry_policy: Optional retry policy
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        # Check if circuit is open
        if self._state == CircuitState.OPEN:
            if self._should_attempt_half_open():
                self._transition_to_half_open()
            else:
                with self._lock:
                    self._stats.rejected_requests += 1
                    self._stats.total_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self._config.name}' is OPEN. "
                    f"Last failure: {self._last_failure_time}"
                )
        
        # Attempt call with retry if policy provided
        if retry_policy:
            return self._call_with_retry(func, retry_policy, *args, **kwargs)
        else:
            return self._call_once(func, *args, **kwargs)
    
    def _call_once(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function once and update circuit state."""
        with self._lock:
            self._stats.total_requests += 1
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self._config.expected_exception as e:
            self._record_failure()
            raise
    
    def _call_with_retry(
        self,
        func: Callable[..., T],
        retry_policy: RetryPolicy,
        *args,
        **kwargs
    ) -> T:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(retry_policy.max_retries + 1):
            try:
                return self._call_once(func, *args, **kwargs)
            except self._config.expected_exception as e:
                last_exception = e
                
                # Don't retry if circuit is open
                if self._state == CircuitState.OPEN:
                    break
                
                # Don't retry on last attempt
                if attempt < retry_policy.max_retries:
                    delay = retry_policy.get_delay(attempt)
                    time.sleep(delay)
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        raise Exception("Retry exhausted without exception")
    
    def _record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            self._stats.successful_requests += 1
            self._stats.last_success_time = time.time()
            self._failure_count = 0
            self._success_count += 1
            self._stats.consecutive_successes = self._success_count
            self._stats.consecutive_failures = 0
            
            # Transition from half-open to closed if threshold met
            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self._config.success_threshold:
                    self._transition_to_closed()
    
    def _record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            self._stats.failed_requests += 1
            self._last_failure_time = time.time()
            self._failure_count += 1
            self._success_count = 0
            self._stats.consecutive_failures = self._failure_count
            self._stats.consecutive_successes = 0
            
            # Transition to open if threshold met
            if self._failure_count >= self._config.failure_threshold:
                if self._state != CircuitState.OPEN:
                    self._transition_to_open()
    
    def _should_attempt_half_open(self) -> bool:
        """Check if enough time has passed to attempt half-open."""
        if self._opened_at is None:
            return False
        
        elapsed = time.time() - self._opened_at
        return elapsed >= self._config.timeout_seconds
    
    def _transition_to_open(self) -> None:
        """Transition circuit to open state."""
        with self._lock:
            if self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                self._stats.state_changes += 1
    
    def _transition_to_half_open(self) -> None:
        """Transition circuit to half-open state."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                self._state = CircuitState.HALF_OPEN
                self._failure_count = 0
                self._success_count = 0
                self._stats.state_changes += 1
    
    def _transition_to_closed(self) -> None:
        """Transition circuit to closed state."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._opened_at = None
                self._stats.state_changes += 1
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._opened_at = None
            self._stats.reset()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        with self._lock:
            return CircuitBreakerStats(
                total_requests=self._stats.total_requests,
                successful_requests=self._stats.successful_requests,
                failed_requests=self._stats.failed_requests,
                rejected_requests=self._stats.rejected_requests,
                state_changes=self._stats.state_changes,
                last_failure_time=self._stats.last_failure_time,
                last_success_time=self._stats.last_success_time,
                consecutive_failures=self._stats.consecutive_failures,
                consecutive_successes=self._stats.consecutive_successes,
            )
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == CircuitState.OPEN
    
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED
    
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self._state == CircuitState.HALF_OPEN


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """
    Centralized manager for circuit breakers.
    
    Provides:
    - Centralized circuit breaker creation
    - Per-specialist circuit breakers
    - Statistics aggregation
    - Health monitoring
    """
    
    _instance: Optional[CircuitBreakerManager] = None
    _lock = RLock()
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = RLock()
        self._default_config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60.0,
        )
    
    @classmethod
    def get_instance(cls) -> CircuitBreakerManager:
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name (e.g., specialist domain)
            config: Optional configuration
        
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._breakers:
                if config is None:
                    config = CircuitBreakerConfig(
                        name=name,
                        failure_threshold=self._default_config.failure_threshold,
                        success_threshold=self._default_config.success_threshold,
                        timeout_seconds=self._default_config.timeout_seconds,
                    )
                else:
                    config.name = name
                
                self._breakers[name] = CircuitBreaker(config)
            
            return self._breakers[name]
    
    def get_breaker_for_specialist(
        self,
        domain: str,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
    ) -> CircuitBreaker:
        """Get circuit breaker for a specialist domain."""
        return self.get_breaker(
            f"specialist_{domain}",
            CircuitBreakerConfig(
                name=f"specialist_{domain}",
                failure_threshold=failure_threshold,
                success_threshold=2,
                timeout_seconds=timeout_seconds,
            )
        )
    
    def reset_breaker(self, name: str) -> bool:
        """Reset a circuit breaker."""
        with self._lock:
            if name in self._breakers:
                self._breakers[name].reset()
                return True
            return False
    
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {
                name: breaker.stats
                for name, breaker in self._breakers.items()
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all circuit breakers."""
        stats = self.get_all_stats()
        
        summary = {
            "total_breakers": len(stats),
            "open_breakers": 0,
            "half_open_breakers": 0,
            "closed_breakers": 0,
            "breakers": {}
        }
        
        with self._lock:
            for name, breaker in self._breakers.items():
                state = breaker.state
                if state == CircuitState.OPEN:
                    summary["open_breakers"] += 1
                elif state == CircuitState.HALF_OPEN:
                    summary["half_open_breakers"] += 1
                else:
                    summary["closed_breakers"] += 1
                
                breaker_stats = breaker.stats
                summary["breakers"][name] = {
                    "state": state.value,
                    "success_rate": breaker_stats.success_rate,
                    "failure_rate": breaker_stats.failure_rate,
                    "consecutive_failures": breaker_stats.consecutive_failures,
                    "total_requests": breaker_stats.total_requests,
                }
        
        return summary


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager instance."""
    return CircuitBreakerManager.get_instance()


def with_circuit_breaker(
    breaker_name: str,
    retry_policy: Optional[RetryPolicy] = None,
    config: Optional[CircuitBreakerConfig] = None,
):
    """
    Decorator for applying circuit breaker to a function.
    
    Usage:
        @with_circuit_breaker("my_service", RetryPolicy(max_retries=3))
        def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        manager = get_circuit_breaker_manager()
        breaker = manager.get_breaker(breaker_name, config)
        
        def wrapper(*args, **kwargs) -> T:
            return breaker.call(func, *args, retry_policy=retry_policy, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.circuit_breaker = breaker  # type: ignore
        
        return wrapper
    
    return decorator

