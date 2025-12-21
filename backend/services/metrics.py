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
    try:
        LLM_CALLS.labels(model=model, status=status).inc()
        LLM_LATENCY.labels(model=model).observe(duration_seconds)
    except Exception as e:
        logger.error(f"Failed to track LLM call: {e}")


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
def measure_duration():
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
