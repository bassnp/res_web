"""
Circuit Breaker Implementation for External API Protection.

Provides failure isolation for:
- Google CSE API calls
- Content fetching
- LLM API calls

States:
    CLOSED: Normal operation, failures tracked
    OPEN: Failing fast, no calls made
    HALF_OPEN: Testing if service recovered
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Async-compatible circuit breaker for external service protection.
    
    Usage:
        breaker = CircuitBreaker(name="search", failure_threshold=3)
        
        @breaker.protect
        async def search(query):
            ...
        
        # Or with context manager:
        async with breaker.call():
            result = await external_api()
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        reset_timeout: float = 30.0,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Breaker identifier for logging.
            failure_threshold: Failures before opening.
            success_threshold: Successes in half-open to close.
            reset_timeout: Seconds before transitioning open → half-open.
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.reset_timeout = reset_timeout
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Current breaker state."""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """True if breaker is closed (normal operation)."""
        return self._state == CircuitState.CLOSED
    
    async def _check_state(self) -> bool:
        """
        Check and update state. Returns True if call should proceed.
        """
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if reset timeout has passed
                if self._last_failure_time and \
                   time.time() - self._last_failure_time >= self.reset_timeout:
                    logger.info(f"Circuit {self.name}: OPEN → HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    return True
                return False
            
            # HALF_OPEN: Allow test calls
            return True
    
    async def record_success(self):
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    logger.info(f"Circuit {self.name}: HALF_OPEN → CLOSED")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    async def record_failure(self, error: Exception):
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens
                logger.warning(f"Circuit {self.name}: HALF_OPEN → OPEN (failure: {error})")
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit {self.name}: CLOSED → OPEN (threshold reached)")
                    self._state = CircuitState.OPEN
    
    def protect(self, func: Callable) -> Callable:
        """
        Decorator to protect an async function with circuit breaker.
        
        Usage:
            @breaker.protect
            async def api_call():
                ...
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await self._check_state():
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                await self.record_success()
                return result
            except Exception as e:
                await self.record_failure(e)
                raise
        
        return wrapper
    
    class CallContext:
        """Context manager for circuit breaker."""
        def __init__(self, breaker: 'CircuitBreaker'):
            self.breaker = breaker
        
        async def __aenter__(self):
            if not await self.breaker._check_state():
                raise CircuitOpenError(f"Circuit {self.breaker.name} is OPEN")
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                await self.breaker.record_success()
            else:
                await self.breaker.record_failure(exc_val)
            return False
    
    def call(self) -> 'CallContext':
        """Get context manager for protected call."""
        return self.CallContext(self)


class CircuitOpenError(Exception):
    """Raised when circuit is open and call is rejected."""
    pass


# =============================================================================
# Pre-configured Breakers (Singletons)
# =============================================================================

# Search API breaker (Google CSE)
search_breaker = CircuitBreaker(
    name="google_cse",
    failure_threshold=3,
    success_threshold=2,
    reset_timeout=30.0,
)

# Content fetcher breaker
fetch_breaker = CircuitBreaker(
    name="content_fetch",
    failure_threshold=5,
    success_threshold=2,
    reset_timeout=20.0,
)

# LLM API breaker
llm_breaker = CircuitBreaker(
    name="llm_api",
    failure_threshold=3,
    success_threshold=1,
    reset_timeout=60.0,
)
