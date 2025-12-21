````markdown
# Phase 2: Concurrency Safety Implementation Guide

> **Priority:** 🟠 HIGH  
> **Estimated Time:** 2-3 hours  
> **Prerequisite:** Phase 1 (Session Isolation) must be complete  
> **Risk if Skipped:** Race conditions and resource exhaustion under high load

---

## Overview

This phase ensures all shared resources are thread-safe for async concurrent access. Even with session isolation from Phase 1, shared utilities like circuit breakers and HTTP clients can cause issues under load.

### Scope

| Resource | Issue | Solution |
|----------|-------|----------|
| Circuit Breaker | Synchronous state mutations | Async-safe with `asyncio.Lock` |
| Request Timeouts | Unbounded execution time | Add `async_timeout` wrapper |
| LLM Client Concurrency | Potential rate limiting | Semaphore-based throttling |
| HTTP Sessions | Connection pool exhaustion | Explicit limits and reuse |

---

## Prerequisites

- [x] Phase 1 (Session Isolation) completed and verified
- [x] Backend Docker container running locally
- [x] Concurrent test script from Phase 1 passing

---

## Implementation Checklist

### Step 1: Create Async-Safe Circuit Breaker

**File:** `backend/services/utils/circuit_breaker.py`

#### 1.1 Review Current Implementation

First, check if a circuit breaker exists:

```bash
# Check for existing circuit breaker
ls backend/services/utils/ | findstr circuit
cat backend/services/utils/circuit_breaker.py 2>nul || echo "File not found"
```

#### 1.2 Create or Update Circuit Breaker

If the file doesn't exist or uses synchronous state:

```python
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
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        logger.info(f"[{self._name}] Circuit transitioned to HALF_OPEN")
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
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._last_failure_time = None
                logger.info(f"[{self._name}] Circuit CLOSED after successful recovery")
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
                self._state = CircuitState.OPEN
                logger.warning(f"[{self._name}] Circuit OPEN (failed during half-open test)")
            elif self._failure_count >= self._max_failures:
                self._state = CircuitState.OPEN
                logger.warning(f"[{self._name}] Circuit OPEN (threshold exceeded)")
    
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
    
    async def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
            logger.info(f"[{self._name}] Circuit manually reset to CLOSED")


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
```

- [x] **DONE:** Create or update `circuit_breaker.py`
- [x] **DONE:** Ensure all state mutations use `async with self._lock`
- [x] **DONE:** Export pre-configured breakers for common services

---

### Step 2: Add Request Timeout Wrapper

**File:** `backend/routers/fit_check.py`

#### 2.1 Install async-timeout (if needed)

```bash
# Add to requirements.txt if not present
echo "async-timeout>=4.0.0" >> backend/requirements.txt
```

Or check if it's already available (often bundled with aiohttp):

```python
# Test in Python REPL
python -c "import asyncio; from async_timeout import timeout; print('OK')"
```

#### 2.2 Add Timeout to SSE Generator

```python
import asyncio
from async_timeout import timeout as async_timeout

# Add timeout constant at module level
REQUEST_TIMEOUT_SECONDS = 300  # 5 minutes max per request

@router.post("/stream")
async def stream_fit_check(request: FitCheckRequest):
    """Stream AI fit analysis via Server-Sent Events."""
    
    session_id = request.session_id or str(uuid.uuid4())
    callback = StreamingCallbackHandler(
        include_thoughts=request.include_thoughts,
        session_id=session_id
    )
    
    async def generate_events() -> AsyncGenerator[str, None]:
        """Async generator with timeout protection."""
        agent = get_agent()
        start_time = time.time()
        
        try:
            # Wrap entire execution with timeout
            async with async_timeout(REQUEST_TIMEOUT_SECONDS):
                async def run_agent():
                    try:
                        async for chunk in agent.stream_analysis(
                            query=request.query,
                            callback=callback,
                            model_id=request.model_id,
                            config_type=request.config_type,
                        ):
                            pass
                    except asyncio.CancelledError:
                        logger.warning(f"[{session_id}] Agent task cancelled")
                        if not callback.is_completed:
                            await callback.on_error("CANCELLED", "Request was cancelled")
                    except Exception as e:
                        logger.error(f"[{session_id}] Agent error: {e}")
                        if not callback.is_completed:
                            await callback.on_error(_map_exception_to_code(e), str(e))
                
                agent_task = asyncio.create_task(run_agent())
                
                try:
                    async for event in callback.events():
                        yield event
                except asyncio.CancelledError:
                    agent_task.cancel()
                    raise
                
                await agent_task
                
        except asyncio.TimeoutError:
            logger.error(f"[{session_id}] Request timed out after {REQUEST_TIMEOUT_SECONDS}s")
            if not callback.is_completed:
                yield format_sse("error", {
                    "code": "TIMEOUT",
                    "message": f"Request exceeded {REQUEST_TIMEOUT_SECONDS} second limit",
                })
        except asyncio.CancelledError:
            logger.info(f"[{session_id}] Stream cancelled by client")
            raise
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [x] **DONE:** Add `async-timeout` to requirements.txt
- [x] **DONE:** Import `timeout as async_timeout` 
- [x] **DONE:** Wrap `generate_events` execution with timeout
- [x] **DONE:** Handle `asyncio.TimeoutError` gracefully

---

### Step 3: Add LLM Concurrency Throttling

**File:** `backend/config/llm.py`

#### 3.1 Add Semaphore for Rate Limiting

```python
import asyncio

# Maximum concurrent LLM requests (adjust based on Gemini rate limits)
MAX_CONCURRENT_LLM_REQUESTS = 10

# Global semaphore for LLM rate limiting
_llm_semaphore: asyncio.Semaphore = None

def get_llm_semaphore() -> asyncio.Semaphore:
    """
    Get or create the global LLM concurrency semaphore.
    
    This limits concurrent requests to the Gemini API to prevent
    rate limiting errors under high load.
    
    Returns:
        asyncio.Semaphore with MAX_CONCURRENT_LLM_REQUESTS permits.
    """
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_REQUESTS)
    return _llm_semaphore


async def with_llm_throttle(coro):
    """
    Execute a coroutine with LLM rate limiting.
    
    Usage:
        result = await with_llm_throttle(llm.ainvoke(prompt))
    
    Args:
        coro: Coroutine to execute.
    
    Returns:
        Result of the coroutine.
    """
    async with get_llm_semaphore():
        return await coro
```

#### 3.2 Apply Throttling in Pipeline Nodes (Example)

In any node that calls the LLM directly:

```python
from config.llm import with_llm_throttle

async def some_pipeline_node(state, callback):
    # Instead of: result = await llm.ainvoke(prompt)
    result = await with_llm_throttle(llm.ainvoke(prompt))
    return result
```

- [x] **DONE:** Add `get_llm_semaphore()` function to `config/llm.py`
- [x] **DONE:** Add `with_llm_throttle()` helper
- [x] **DONE:** Apply throttling in high-throughput LLM calls

---

### Step 4: HTTP Client Connection Pool Management

**File:** `backend/services/utils/http_client.py` (new file)

#### 4.1 Create Shared HTTP Client with Limits

```python
"""
Shared HTTP Client for External Requests.

Provides a connection-pooled, timeout-configured HTTP client for
content fetching and API calls. Reuses connections for efficiency.
"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import httpx

logger = logging.getLogger(__name__)

# Connection pool limits
MAX_CONNECTIONS = 100
MAX_CONNECTIONS_PER_HOST = 10
DEFAULT_TIMEOUT = 30.0  # seconds

# Global client instance (lazy initialization)
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


async def get_http_client() -> httpx.AsyncClient:
    """
    Get or create the shared HTTP client.
    
    The client is created lazily on first use and reused for all requests.
    Connection pooling reduces overhead for repeated requests.
    
    Returns:
        Configured httpx.AsyncClient instance.
    """
    global _http_client
    
    async with _client_lock:
        if _http_client is None or _http_client.is_closed:
            _http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(DEFAULT_TIMEOUT),
                limits=httpx.Limits(
                    max_connections=MAX_CONNECTIONS,
                    max_keepalive_connections=MAX_CONNECTIONS_PER_HOST,
                ),
                follow_redirects=True,
                http2=True,  # Enable HTTP/2 for better multiplexing
            )
            logger.info(
                f"HTTP client initialized: max_connections={MAX_CONNECTIONS}, "
                f"timeout={DEFAULT_TIMEOUT}s"
            )
    
    return _http_client


async def close_http_client() -> None:
    """
    Close the shared HTTP client.
    
    Call this during application shutdown to release resources.
    """
    global _http_client
    
    async with _client_lock:
        if _http_client is not None and not _http_client.is_closed:
            await _http_client.aclose()
            _http_client = None
            logger.info("HTTP client closed")


@asynccontextmanager
async def managed_request():
    """
    Context manager for making HTTP requests with automatic cleanup.
    
    Usage:
        async with managed_request() as client:
            response = await client.get("https://example.com")
    """
    client = await get_http_client()
    try:
        yield client
    except httpx.TimeoutException as e:
        logger.warning(f"HTTP request timed out: {e}")
        raise
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code}: {e}")
        raise
```

#### 4.2 Register Cleanup in Server Lifespan

**File:** `backend/server.py`

```python
from services.utils.http_client import close_http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("Portfolio Backend API starting up...")
    logger.info(f"Log level: {log_level}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Portfolio Backend API shutting down...")
    await close_http_client()
    logger.info("HTTP client closed")
```

- [ ] **TODO:** Create `services/utils/http_client.py`
- [ ] **TODO:** Add `httpx` to requirements.txt if not present
- [ ] **TODO:** Register cleanup in server lifespan handler
- [ ] **TODO:** Use `get_http_client()` in content fetch nodes

---

### Step 5: Update Web Search Tool with Circuit Breaker

**File:** `backend/services/tools/web_search.py`

#### 5.1 Apply Async Circuit Breaker

```python
from services.utils.circuit_breaker import search_breaker, CircuitOpenError

async def web_search(query: str) -> str:
    """
    Search the web using Google Custom Search Engine.
    
    Protected by circuit breaker to prevent repeated calls to failing API.
    
    Args:
        query: Search query string.
    
    Returns:
        Search results as formatted string.
    
    Raises:
        CircuitOpenError: If search service is temporarily unavailable.
    """
    # Check circuit breaker before making request
    if await search_breaker.is_open():
        logger.warning(f"Search circuit breaker is OPEN - returning fallback")
        return "Search temporarily unavailable. Analysis will proceed with available data."
    
    try:
        # Existing search implementation
        results = await _perform_search(query)
        await search_breaker.record_success()
        return results
    except Exception as e:
        await search_breaker.record_failure(e)
        logger.error(f"Search failed: {e}")
        return "Search unavailable. Proceeding with analysis using existing data."
```

- [ ] **TODO:** Import circuit breaker in web_search.py
- [ ] **TODO:** Check `is_open()` before requests
- [ ] **TODO:** Call `record_success()` / `record_failure()` appropriately
- [ ] **TODO:** Return graceful fallback when circuit is open

---

## Verification & Validation

### Test 1: Circuit Breaker Behavior

```python
# tests/unit/test_circuit_breaker.py
import asyncio
import pytest
from services.utils.circuit_breaker import AsyncCircuitBreaker, CircuitOpenError

@pytest.mark.asyncio
async def test_circuit_opens_after_failures():
    """Circuit should open after max_failures exceeded."""
    breaker = AsyncCircuitBreaker(max_failures=3, reset_timeout=5.0, name="test")
    
    # Record 3 failures
    for i in range(3):
        await breaker.record_failure(Exception(f"Failure {i}"))
    
    # Circuit should be open
    assert await breaker.is_open() == True
    assert breaker.state.value == "open"

@pytest.mark.asyncio
async def test_circuit_half_open_after_timeout():
    """Circuit should transition to half-open after reset_timeout."""
    breaker = AsyncCircuitBreaker(max_failures=1, reset_timeout=0.1, name="test")
    
    await breaker.record_failure(Exception("Test"))
    assert await breaker.is_open() == True
    
    # Wait for reset timeout
    await asyncio.sleep(0.15)
    
    # Should allow one call (half-open)
    assert await breaker.is_open() == False
    assert breaker.state.value == "half_open"

@pytest.mark.asyncio
async def test_circuit_closes_on_success():
    """Circuit should close after successful call in half-open."""
    breaker = AsyncCircuitBreaker(max_failures=1, reset_timeout=0.1, name="test")
    
    await breaker.record_failure(Exception("Test"))
    await asyncio.sleep(0.15)  # Move to half-open
    
    await breaker.record_success()
    
    assert breaker.state.value == "closed"
    assert await breaker.is_open() == False
```

- [ ] **TODO:** Run circuit breaker unit tests
- [ ] **TODO:** Verify all tests pass

---

### Test 2: Request Timeout Enforcement

```bash
# Simulate a slow query (should timeout after 5 minutes in production)
# For testing, temporarily set REQUEST_TIMEOUT_SECONDS = 5

curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "A very obscure company that will trigger extensive research"}' \
  --no-buffer

# Watch for timeout error event after 5 seconds (test config)
```

- [ ] **TODO:** Test with reduced timeout (5s) in development
- [ ] **TODO:** Verify `event: error` with `"code": "TIMEOUT"` is emitted
- [ ] **TODO:** Restore production timeout (300s) after testing

---

### Test 3: Concurrent Load Test

```python
# tests/integration/test_concurrency.py
import asyncio
import time
import httpx

async def test_20_concurrent_without_failures():
    """Verify 20 concurrent requests complete without circuit breaker triggers."""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as client:
        
        async def run_request(i: int) -> tuple[int, float, str]:
            start = time.time()
            try:
                response = await client.post(
                    "/api/fit-check/stream",
                    json={"query": f"Test company {i}", "session_id": f"load-{i}"}
                )
                # Consume stream
                async for _ in response.aiter_lines():
                    pass
                return (i, time.time() - start, "success")
            except Exception as e:
                return (i, time.time() - start, f"error: {e}")
        
        results = await asyncio.gather(*[run_request(i) for i in range(20)])
        
        successes = [r for r in results if r[2] == "success"]
        failures = [r for r in results if r[2] != "success"]
        
        print(f"Successes: {len(successes)}, Failures: {len(failures)}")
        assert len(failures) == 0, f"Expected 0 failures, got: {failures}"
        
        avg_time = sum(r[1] for r in results) / len(results)
        print(f"Average response time: {avg_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_20_concurrent_without_failures())
```

- [ ] **TODO:** Run load test with 20 concurrent requests
- [ ] **TODO:** Verify no failures or circuit breaker triggers
- [ ] **TODO:** Check docker logs for warnings/errors

---

### Test 4: HTTP Client Cleanup

```bash
# Start server, make requests, then stop gracefully
docker compose down

# Check logs for cleanup message
docker logs res_web-backend 2>&1 | grep -i "http client closed"
```

- [ ] **TODO:** Verify HTTP client is closed on shutdown
- [ ] **TODO:** No resource leak warnings in logs

---

## Completion Checklist

After completing all steps and tests:

**File:** `_devnotes/MULTI_SESSION_UPGRADE_PLAN.md`

Mark Phase 2 as complete:
```markdown
| **Phase 2: Concurrency Safety** | ✅ Complete | 2024-XX-XX |
```

### Summary of Changes

| File | Change |
|------|--------|
| `services/utils/circuit_breaker.py` | New async-safe circuit breaker |
| `services/utils/http_client.py` | Shared HTTP client with pooling |
| `routers/fit_check.py` | Request timeout wrapper |
| `config/llm.py` | LLM concurrency semaphore |
| `services/tools/web_search.py` | Circuit breaker integration |
| `server.py` | HTTP client cleanup on shutdown |
| `requirements.txt` | Added async-timeout, httpx |

---

## Next Steps

Once Phase 2 is complete and verified:

1. **Proceed to Phase 3:** Observability & Monitoring
2. **Monitor Metrics:** Watch circuit breaker states, timeout rates
3. **Tune Parameters:** Adjust timeouts and limits based on real traffic

---

## Appendix: Configuration Reference

| Parameter | File | Default | Description |
|-----------|------|---------|-------------|
| `REQUEST_TIMEOUT_SECONDS` | `routers/fit_check.py` | 300 | Max request duration |
| `MAX_CONCURRENT_LLM_REQUESTS` | `config/llm.py` | 10 | LLM rate limit |
| `MAX_CONNECTIONS` | `http_client.py` | 100 | HTTP pool size |
| `search_breaker.max_failures` | `circuit_breaker.py` | 3 | Search circuit threshold |
| `search_breaker.reset_timeout` | `circuit_breaker.py` | 60.0 | Search circuit reset time |
````
