# ============================================================
#  ANM V0-OpenSource — Circuit Breaker Wrapper for Specialists
#  Fault-Tolerant Specialist Execution
# ============================================================

"""
Circuit Breaker Wrapper for Specialists

Wraps specialist calls with circuit breaker protection and retry logic.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable
from anm.core.circuit_breaker import (
    CircuitBreakerManager,
    CircuitBreaker,
    RetryPolicy,
    get_circuit_breaker_manager,
    CircuitBreakerOpenError,
)

__all__ = [
    "CircuitBreakerSpecialistWrapper",
    "wrap_specialist_with_circuit_breaker",
]


class CircuitBreakerSpecialistWrapper:
    """
    Wrapper that adds circuit breaker protection to specialist calls.
    
    Features:
    - Automatic circuit breaker per specialist domain
    - Retry logic with exponential backoff
    - Graceful degradation on failures
    - Statistics tracking
    """
    
    def __init__(
        self,
        specialist: Any,
        domain: str,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        """
        Initialize wrapper.
        
        Args:
            specialist: The specialist instance to wrap
            domain: Specialist domain name
            failure_threshold: Failures before opening circuit
            timeout_seconds: Time before attempting recovery
            retry_policy: Optional retry policy
        """
        self.specialist = specialist
        self.domain = domain
        
        # Get circuit breaker for this specialist
        manager = get_circuit_breaker_manager()
        self.breaker = manager.get_breaker_for_specialist(
            domain=domain,
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds,
        )
        
        # Default retry policy
        self.retry_policy = retry_policy or RetryPolicy(
            max_retries=2,
            initial_delay=0.2,
            max_delay=2.0,
        )
    
    def run(self, wot_packet: str) -> str:
        """
        Execute specialist.run() with circuit breaker protection.
        
        Args:
            wot_packet: WoT packet to process
        
        Returns:
            Specialist output
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from specialist
        """
        try:
            return self.breaker.call(
                self.specialist.run,
                wot_packet,
                retry_policy=self.retry_policy,
            )
        except CircuitBreakerOpenError:
            # Return graceful degradation response
            return self._get_fallback_response()
        except Exception as e:
            # Re-raise original exception
            raise
    
    def _get_fallback_response(self) -> str:
        """Get fallback response when circuit is open."""
        return f"""[{self.domain.upper()} SPECIALIST - TEMPORARILY UNAVAILABLE]

This specialist is currently unavailable due to repeated failures.
The circuit breaker has opened to prevent further issues.

Please try again later or use an alternative specialist.

WOT_REQUEST: NONE"""
    
    @property
    def is_available(self) -> bool:
        """Check if specialist is available (circuit not open)."""
        return not self.breaker.is_open()
    
    @property
    def stats(self):
        """Get circuit breaker statistics."""
        return self.breaker.stats


def wrap_specialist_with_circuit_breaker(
    specialist: Any,
    domain: str,
    failure_threshold: int = 5,
    timeout_seconds: float = 60.0,
    retry_policy: Optional[RetryPolicy] = None,
) -> CircuitBreakerSpecialistWrapper:
    """
    Convenience function to wrap a specialist with circuit breaker.
    
    Args:
        specialist: Specialist instance
        domain: Domain name
        failure_threshold: Failures before opening circuit
        timeout_seconds: Recovery timeout
        retry_policy: Optional retry policy
    
    Returns:
        Wrapped specialist with circuit breaker protection
    """
    return CircuitBreakerSpecialistWrapper(
        specialist=specialist,
        domain=domain,
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
    )

