````markdown
# Phase 3: Observability & Monitoring Implementation Guide

> **Priority:** 🟡 MEDIUM  
> **Estimated Time:** 1-2 hours  
> **Prerequisite:** Phase 1 & 2 complete  
> **Risk if Skipped:** Debugging blind spots, difficult incident response

---

## Overview

This phase adds structured logging, metrics collection, and monitoring capabilities to provide visibility into system behavior under load. Essential for production debugging and performance optimization.

### Scope

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| Structured Logging | Machine-parseable logs | JSON format with session context |
| Request Metrics | Performance tracking | Prometheus-compatible counters/histograms |
| Health Check Enhancement | Operational visibility | Active session count, circuit breaker status |
| Trace Correlation | Request tracing | Session ID propagation through all layers |

---

## Prerequisites

- [ ] Phase 1 & 2 completed and verified
- [ ] Backend Docker container running
- [ ] Session ID tracking from Phase 1 working

---

## Implementation Checklist

### Step 1: Add Structured Logging Configuration

**File:** `backend/server.py`

#### 1.1 Update Logging Configuration for JSON Format

```python
import json
import logging
import sys
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Outputs log records as JSON objects for easy parsing by log aggregators
    (e.g., ELK Stack, CloudWatch Logs, Datadog).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields (e.g., session_id)
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "phase"):
            log_data["phase"] = record.phase
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


def configure_logging(json_format: bool = False):
    """
    Configure application logging.
    
    Args:
        json_format: If True, use JSON format (for production).
                     If False, use human-readable format (for development).
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.INFO)
    
    return root_logger


# Call in module-level initialization
USE_JSON_LOGS = os.getenv("LOG_FORMAT", "text").lower() == "json"
logger = configure_logging(json_format=USE_JSON_LOGS)
```

- [ ] **TODO:** Create `JSONFormatter` class
- [ ] **TODO:** Add `configure_logging()` function
- [ ] **TODO:** Add `LOG_FORMAT` environment variable support
- [ ] **TODO:** Reduce noise from third-party loggers

---

### Step 2: Create Metrics Module

**File:** `backend/services/metrics.py` (new file)

#### 2.1 Define Prometheus-Compatible Metrics

```python
"""
Application Metrics for Observability.

Provides counters, gauges, and histograms for monitoring system behavior.
Uses prometheus_client for Prometheus-compatible metrics exposition.

Note: If prometheus_client is not installed, metrics are no-op.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import prometheus_client (optional dependency)
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed - metrics disabled")


# =============================================================================
# Metric Definitions
# =============================================================================

if PROMETHEUS_AVAILABLE:
    # Active sessions gauge
    ACTIVE_SESSIONS = Gauge(
        "fit_check_active_sessions",
        "Number of active fit check sessions"
    )
    
    # Request counter
    REQUEST_TOTAL = Counter(
        "fit_check_requests_total",
        "Total number of fit check requests",
        ["status"]  # Labels: success, error, timeout, cancelled
    )
    
    # Request duration histogram
    REQUEST_DURATION = Histogram(
        "fit_check_request_duration_seconds",
        "Time spent processing fit check requests",
        buckets=[1, 5, 10, 30, 60, 120, 300, 600]
    )
    
    # Phase completion counter
    PHASE_COMPLETIONS = Counter(
        "fit_check_phase_completions_total",
        "Number of phase completions",
        ["phase", "status"]  # Labels: phase name, success/error
    )
    
    # Phase duration histogram
    PHASE_DURATION = Histogram(
        "fit_check_phase_duration_seconds",
        "Time spent in each pipeline phase",
        ["phase"],
        buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
    )
    
    # LLM call counter
    LLM_CALLS = Counter(
        "fit_check_llm_calls_total",
        "Total number of LLM API calls",
        ["model", "status"]
    )
    
    # LLM latency histogram
    LLM_LATENCY = Histogram(
        "fit_check_llm_latency_seconds",
        "LLM API call latency",
        ["model"],
        buckets=[0.5, 1, 2, 5, 10, 30]
    )
    
    # Circuit breaker state gauge
    CIRCUIT_BREAKER_STATE = Gauge(
        "fit_check_circuit_breaker_state",
        "Circuit breaker state (0=closed, 1=open, 2=half_open)",
        ["service"]
    )
    
    # Build info
    BUILD_INFO = Info(
        "fit_check_build",
        "Build information"
    )
    BUILD_INFO.info({
        "version": "1.0.0",
        "python_version": "3.11",
    })
else:
    # No-op placeholders when Prometheus is not available
    class NoOpMetric:
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def time(self): return self._timer()
        @contextmanager
        def _timer(self): yield
    
    ACTIVE_SESSIONS = NoOpMetric()
    REQUEST_TOTAL = NoOpMetric()
    REQUEST_DURATION = NoOpMetric()
    PHASE_COMPLETIONS = NoOpMetric()
    PHASE_DURATION = NoOpMetric()
    LLM_CALLS = NoOpMetric()
    LLM_LATENCY = NoOpMetric()
    CIRCUIT_BREAKER_STATE = NoOpMetric()


# =============================================================================
# Helper Functions
# =============================================================================

def track_request_start():
    """Call when a new request starts."""
    ACTIVE_SESSIONS.inc()


def track_request_end(status: str, duration_seconds: float):
    """
    Call when a request ends.
    
    Args:
        status: One of 'success', 'error', 'timeout', 'cancelled'.
        duration_seconds: Total request duration.
    """
    ACTIVE_SESSIONS.dec()
    REQUEST_TOTAL.labels(status=status).inc()
    REQUEST_DURATION.observe(duration_seconds)


def track_phase_complete(phase: str, status: str, duration_seconds: float):
    """
    Track phase completion.
    
    Args:
        phase: Phase name (e.g., 'connecting', 'deep_research').
        status: 'success' or 'error'.
        duration_seconds: Phase duration.
    """
    PHASE_COMPLETIONS.labels(phase=phase, status=status).inc()
    PHASE_DURATION.labels(phase=phase).observe(duration_seconds)


def track_llm_call(model: str, status: str, duration_seconds: float):
    """
    Track LLM API call.
    
    Args:
        model: Model ID (e.g., 'gemini-2.0-flash').
        status: 'success' or 'error'.
        duration_seconds: Call duration.
    """
    LLM_CALLS.labels(model=model, status=status).inc()
    LLM_LATENCY.labels(model=model).observe(duration_seconds)


def update_circuit_breaker_state(service: str, state: str):
    """
    Update circuit breaker state metric.
    
    Args:
        service: Service name (e.g., 'google-search').
        state: One of 'closed', 'open', 'half_open'.
    """
    state_map = {"closed": 0, "open": 1, "half_open": 2}
    CIRCUIT_BREAKER_STATE.labels(service=service).set(state_map.get(state, -1))


@contextmanager
def measure_duration(metric_name: str = None):
    """
    Context manager to measure duration.
    
    Usage:
        with measure_duration() as timer:
            do_work()
        print(f"Took {timer.duration:.2f}s")
    """
    class Timer:
        def __init__(self):
            self.start = time.time()
            self.duration = 0
    
    timer = Timer()
    try:
        yield timer
    finally:
        timer.duration = time.time() - timer.start


def timed(metric: Optional[Any] = None, labels: Dict[str, str] = None):
    """
    Decorator to measure function execution time.
    
    Usage:
        @timed(LLM_LATENCY, labels={"model": "gemini"})
        async def call_llm():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if metric and PROMETHEUS_AVAILABLE:
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if metric and PROMETHEUS_AVAILABLE:
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
```

- [ ] **TODO:** Create `services/metrics.py`
- [ ] **TODO:** Add `prometheus-client` to requirements.txt (optional)
- [ ] **TODO:** Define all metric types (Counter, Gauge, Histogram)
- [ ] **TODO:** Implement no-op fallback when Prometheus not installed

---

### Step 3: Integrate Metrics in Router

**File:** `backend/routers/fit_check.py`

#### 3.1 Add Request Tracking

```python
from services.metrics import (
    track_request_start,
    track_request_end,
    measure_duration,
)

@router.post("/stream")
async def stream_fit_check(request: FitCheckRequest):
    """Stream AI fit analysis via Server-Sent Events."""
    
    session_id = request.session_id or str(uuid.uuid4())
    
    # Track request start
    track_request_start()
    start_time = time.time()
    request_status = "success"  # Will be updated on error/timeout
    
    logger.info(
        f"[{session_id}] Request started",
        extra={"session_id": session_id, "query_length": len(request.query)}
    )
    
    async def generate_events() -> AsyncGenerator[str, None]:
        nonlocal request_status
        
        try:
            # ... existing implementation ...
            pass
        except asyncio.TimeoutError:
            request_status = "timeout"
            # ... handle timeout ...
        except asyncio.CancelledError:
            request_status = "cancelled"
            raise
        except Exception as e:
            request_status = "error"
            # ... handle error ...
        finally:
            # Track request end
            duration = time.time() - start_time
            track_request_end(request_status, duration)
            logger.info(
                f"[{session_id}] Request completed",
                extra={
                    "session_id": session_id,
                    "status": request_status,
                    "duration_ms": int(duration * 1000),
                }
            )
    
    return StreamingResponse(generate_events(), ...)
```

- [ ] **TODO:** Import metrics functions
- [ ] **TODO:** Call `track_request_start()` at request start
- [ ] **TODO:** Track status and call `track_request_end()` in finally
- [ ] **TODO:** Add structured log with extra fields

---

### Step 4: Add Phase Timing to Callback

**File:** `backend/services/streaming_callback.py`

#### 4.1 Track Phase Durations

```python
import time
from services.metrics import track_phase_complete

class StreamingCallbackHandler(ThoughtCallback):
    """Callback handler with phase timing."""
    
    def __init__(self, include_thoughts: bool = True, session_id: str = None):
        self._queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._include_thoughts = include_thoughts
        self._session_id = session_id or "unknown"
        self._completed = False
        self._error_occurred = False
        
        # Phase timing tracking
        self._phase_start_times: Dict[str, float] = {}
        
        logger.debug(
            f"[{self._session_id}] StreamingCallbackHandler initialized",
            extra={"session_id": self._session_id}
        )
    
    async def on_phase(self, phase: str, message: str) -> None:
        """Emit a phase transition event and start timing."""
        # Record phase start time
        self._phase_start_times[phase] = time.time()
        
        await self._emit("phase", {
            "phase": phase,
            "message": message,
        })
        
        logger.info(
            f"[{self._session_id}] Phase started: {phase}",
            extra={"session_id": self._session_id, "phase": phase}
        )
    
    async def on_phase_complete(self, phase: str, summary: str, data: dict = None) -> None:
        """Emit phase completion and record metrics."""
        # Calculate phase duration
        start_time = self._phase_start_times.get(phase)
        duration_seconds = time.time() - start_time if start_time else 0
        
        # Track metric
        track_phase_complete(phase, "success", duration_seconds)
        
        await self._emit("phase_complete", {
            "phase": phase,
            "summary": summary,
            "data": data or {},
            "duration_ms": int(duration_seconds * 1000),  # Include in event
        })
        
        logger.info(
            f"[{self._session_id}] Phase completed: {phase} ({duration_seconds:.2f}s)",
            extra={
                "session_id": self._session_id,
                "phase": phase,
                "duration_ms": int(duration_seconds * 1000),
            }
        )
```

- [ ] **TODO:** Add `_phase_start_times` dict to callback
- [ ] **TODO:** Record start time in `on_phase()`
- [ ] **TODO:** Calculate and track duration in `on_phase_complete()`
- [ ] **TODO:** Include `duration_ms` in phase_complete event data

---

### Step 5: Enhance Health Check Endpoint

**File:** `backend/routers/fit_check.py`

#### 5.1 Add Operational Metrics to Health Check

```python
from services.metrics import ACTIVE_SESSIONS, PROMETHEUS_AVAILABLE
from services.utils.circuit_breaker import search_breaker, llm_breaker

@router.get("/health")
async def fit_check_health():
    """
    Fit Check service health with operational metrics.
    
    Returns detailed status for monitoring dashboards.
    """
    try:
        agent = get_agent()
        
        # Get active session count
        active_sessions = 0
        if PROMETHEUS_AVAILABLE:
            active_sessions = int(ACTIVE_SESSIONS._value._value)
        
        # Get circuit breaker states
        circuit_breakers = {
            "search": search_breaker.state.value,
            "llm": llm_breaker.state.value,
        }
        
        # Determine overall health
        any_open = any(s == "open" for s in circuit_breakers.values())
        status = "degraded" if any_open else "healthy"
        
        return {
            "status": status,
            "service": "fit-check",
            "agent_ready": agent is not None,
            "active_sessions": active_sessions,
            "circuit_breakers": circuit_breakers,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "fit-check",
            "error": str(e),
            "timestamp": time.time(),
        }
```

- [ ] **TODO:** Import metrics and circuit breakers
- [ ] **TODO:** Add `active_sessions` count
- [ ] **TODO:** Add `circuit_breakers` status map
- [ ] **TODO:** Return "degraded" if any circuit is open

---

### Step 6: Add Prometheus Metrics Endpoint (Optional)

**File:** `backend/server.py`

#### 6.1 Expose /metrics Endpoint

```python
# Only if prometheus_client is installed
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint."""
        from fastapi.responses import Response
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("Prometheus metrics endpoint enabled at /metrics")
except ImportError:
    logger.info("prometheus_client not installed - /metrics endpoint disabled")
```

- [ ] **TODO:** Add conditional metrics endpoint
- [ ] **TODO:** Import prometheus_client safely

---

### Step 7: Update Docker Compose for Logging

**File:** `backend/docker-compose.yml`

#### 7.1 Add Logging Configuration

```yaml
services:
  backend:
    # ... existing config ...
    
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_FORMAT=${LOG_FORMAT:-text}  # NEW: 'text' or 'json'
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3003}
    
    # Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

- [ ] **TODO:** Add `LOG_FORMAT` environment variable
- [ ] **TODO:** Add logging driver configuration

---

## Verification & Validation

### Test 1: JSON Logging Format

```bash
# Set JSON logging
export LOG_FORMAT=json
docker compose up -d --build

# Make a request and check logs
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Test logging", "session_id": "log-test-123"}' \
  --no-buffer > /dev/null

# View JSON logs
docker logs res_web-backend 2>&1 | tail -5
```

**Expected Output:**
```json
{"timestamp": "2024-XX-XXTXX:XX:XX.XXXXXXZ", "level": "INFO", "logger": "routers.fit_check", "message": "[log-test-123] Request started", "session_id": "log-test-123", ...}
```

- [ ] **TODO:** Verify logs are valid JSON
- [ ] **TODO:** Verify `session_id` appears in log fields
- [ ] **TODO:** Verify `duration_ms` appears in completion logs

---

### Test 2: Health Check with Metrics

```bash
curl http://localhost:8000/api/fit-check/health | python -m json.tool
```

**Expected Output:**
```json
{
    "status": "healthy",
    "service": "fit-check",
    "agent_ready": true,
    "active_sessions": 0,
    "circuit_breakers": {
        "search": "closed",
        "llm": "closed"
    },
    "timestamp": 1234567890.123
}
```

- [ ] **TODO:** Verify `active_sessions` field present
- [ ] **TODO:** Verify `circuit_breakers` status map present
- [ ] **TODO:** Start a request and verify `active_sessions` increments

---

### Test 3: Prometheus Metrics Endpoint

```bash
# If prometheus_client is installed
curl http://localhost:8000/metrics

# Should see Prometheus format output:
# fit_check_active_sessions 0.0
# fit_check_requests_total{status="success"} 5.0
# ...
```

- [ ] **TODO:** Verify /metrics endpoint returns Prometheus format
- [ ] **TODO:** Verify custom metrics appear with correct labels

---

### Test 4: Phase Duration Tracking

```bash
# Run a request and check phase durations in logs
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Google", "session_id": "duration-test"}' \
  --no-buffer > /dev/null

# Check logs for phase durations
docker logs res_web-backend 2>&1 | grep "duration-test" | grep "Phase completed"
```

**Expected Log (JSON format):**
```json
{"timestamp": "...", "level": "INFO", "message": "[duration-test] Phase completed: connecting (0.45s)", "phase": "connecting", "duration_ms": 450, ...}
```

- [ ] **TODO:** Verify `duration_ms` in phase completion logs
- [ ] **TODO:** Verify durations are reasonable (not 0 or negative)

---

## Completion Checklist

After completing all steps and tests:

**File:** `_devnotes/MULTI_SESSION_UPGRADE_PLAN.md`

Mark Phase 3 as complete:
```markdown
| **Phase 3: Observability** | ✅ Complete | 2024-XX-XX |
```

### Summary of Changes

| File | Change |
|------|--------|
| `server.py` | JSON logging formatter, /metrics endpoint |
| `services/metrics.py` | New metrics module with Prometheus support |
| `services/streaming_callback.py` | Phase duration tracking |
| `routers/fit_check.py` | Request metrics, enhanced health check |
| `docker-compose.yml` | LOG_FORMAT env, logging driver config |
| `requirements.txt` | prometheus-client (optional) |

---

## Next Steps

Once Phase 3 is complete and verified:

1. **Set Up Monitoring Dashboard:** Grafana with Prometheus datasource
2. **Configure Alerts:** Alert on high error rates, circuit breaker opens
3. **Proceed to Phase 4:** Docker Production Readiness

---

## Appendix: Grafana Dashboard Queries

For reference when setting up monitoring:

```promql
# Active sessions
fit_check_active_sessions

# Request rate by status
rate(fit_check_requests_total[5m])

# 95th percentile request duration
histogram_quantile(0.95, rate(fit_check_request_duration_seconds_bucket[5m]))

# Phase completion rate
rate(fit_check_phase_completions_total[5m])

# Circuit breaker status (1 = open, 0 = closed)
fit_check_circuit_breaker_state

# Error rate
rate(fit_check_requests_total{status="error"}[5m]) / rate(fit_check_requests_total[5m])
```
````
