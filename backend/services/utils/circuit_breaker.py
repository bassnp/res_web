"""
Async-Safe Circuit Breaker for External Service Protection.

Prevents cascading failures by temporarily blocking requests to failing services.
Uses asyncio.Lock for thread-safe state mutations in concurrent environments.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Optional, Callable, Any
from functools import wraps
from contextlib import asynccontextmanager

from services.metrics import update_circuit_breaker_state

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Failure threshold exceeded, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class AsyncCircuitBreaker:
    """
    Async-safe circuit breaker pattern implementation.
    
    Prevents repeated calls to failing external services by:
    1. Tracking failure count with async-safe mutations
    2. Opening circuit after threshold exceeded
    3. Allowing periodic test requests in half-open state
    
    Usage:
        breaker = AsyncCircuitBreaker(max_failures=3, reset_timeout=60.0)
        
        @breaker.protect
        async def call_external_api():
            return await http_client.get("https://api.example.com")
    """
    
    def __init__(
        self,
        max_failures: int = 3,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1,
        name: str = "default"
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            max_failures: Number of failures before opening circuit.
            reset_timeout: Seconds to wait before attempting reset.
            half_open_max_calls: Max concurrent calls in half-open state.
            name: Identifier for logging.
        """
        self._name = name
        self._max_failures = max_failures
        self._reset_timeout = reset_timeout
        self._half_open_max_calls = half_open_max_calls
        
        # Async-safe state
        self._lock = asyncio.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        
        logger.info(
            f"[{self._name}] Circuit breaker initialized: "
            f"max_failures={max_failures}, reset_timeout={reset_timeout}s"
        )
        # Initialize metric
        update_circuit_breaker_state(self._name, self._state.value)
    
    def _set_state(self, new_state: CircuitState):
        """Update state and metrics."""
        if self._state != new_state:
            logger.info(f"[{self._name}] Circuit state transition: {self._state.value} -> {new_state.value}")
            self._state = new_state
            update_circuit_breaker_state(self._name, new_state.value)
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state (read-only, may be stale)."""
        return self._state
    
    async def is_open(self) -> bool:
        """
        Check if circuit is open (requests should be blocked).
        
        This method is async-safe and handles state transitions.
        
        Returns:
            True if requests should be blocked.
        """
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return False
            
            if self._state == CircuitState.OPEN:
                # Check if reset timeout has passed
                if self._last_failure_time is not None:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self._reset_timeout:
                        # Transition to half-open
                        self._set_state(CircuitState.HALF_OPEN)
                        self._half_open_calls = 0
                        return False
                return True
            
            if self._state == CircuitState.HALF_OPEN:
                # Allow limited calls in half-open state
                if self._half_open_calls >= self._half_open_max_calls:
                    return True
                self._half_open_calls += 1
                return False
            
            return False
    
    async def record_success(self) -> None:
        """Record a successful call (resets failure count)."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                # Success in half-open means service recovered
                self._set_state(CircuitState.CLOSED)
                self._failure_count = 0
                self._last_failure_time = None
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    async def record_failure(self, error: Optional[Exception] = None) -> None:
        """
        Record a failed call.
        
        Args:
            error: Optional exception for logging.
        """
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            error_msg = str(error) if error else "Unknown error"
            logger.warning(
                f"[{self._name}] Failure recorded ({self._failure_count}/{self._max_failures}): "
                f"{error_msg[:100]}"
            )
            
            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open means service still failing
                self._set_state(CircuitState.OPEN)
            elif self._failure_count >= self._max_failures:
                self._set_state(CircuitState.OPEN)
    
    def protect(self, func: Callable) -> Callable:
        """
        Decorator to protect an async function with circuit breaker.
        
        Usage:
            @breaker.protect
            async def risky_call():
                return await external_api()
        """
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if await self.is_open():
                raise CircuitOpenError(
                    f"Circuit breaker [{self._name}] is OPEN - request blocked"
                )
            
            try:
                result = await func(*args, **kwargs)
                await self.record_success()
                return result
            except Exception as e:
                await self.record_failure(e)
                raise
        
        return wrapper
    
    @asynccontextmanager
    async def call(self):
        """
        Context manager for circuit breaker.
        
        Usage:
            async with breaker.call():
                await risky_call()
        """
        if await self.is_open():
            raise CircuitOpenError(
                f"Circuit breaker [{self._name}] is OPEN - request blocked"
            )
        
        try:
            yield self
            await self.record_success()
        except Exception as e:
            await self.record_failure(e)
            raise

    async def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        async with self._lock:
            self._set_state(CircuitState.CLOSED)
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0


class CircuitOpenError(Exception):
    """Raised when a request is blocked by an open circuit."""
    pass


# =============================================================================
# Pre-configured Circuit Breakers for Common Services
# =============================================================================

# Web search circuit breaker (Google CSE)
search_breaker = AsyncCircuitBreaker(
    max_failures=3,
    reset_timeout=60.0,
    name="google-search"
)

# LLM API circuit breaker (Gemini)
llm_breaker = AsyncCircuitBreaker(
    max_failures=5,
    reset_timeout=30.0,
    name="gemini-llm"
)

# Content fetch circuit breaker (web scraping)
fetch_breaker = AsyncCircuitBreaker(
    max_failures=10,
    reset_timeout=120.0,
    name="content-fetch"
)
