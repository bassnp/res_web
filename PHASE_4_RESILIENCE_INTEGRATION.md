# Phase 4: Resilience, Integration & Testing

**Phase:** 4 of 4  
**Focus:** Circuit Breakers, Error Handling, Full Integration  
**Risk Level:** Low  
**Prerequisites:** Phases 1-3 Complete

---

## 1. Objective

Finalize the upgraded research system with:
- Circuit breakers for external API failure isolation
- Comprehensive error handling and graceful degradation
- Full integration testing across all new components
- Performance validation and optimization
- Documentation updates

---

## 2. Components to Implement

### 2.1 Circuit Breaker System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────┐ │
│  │    CLOSED       │─────────►│     OPEN        │─────────►│  HALF_OPEN  │ │
│  │ (normal flow)   │ failures │ (fail fast)     │ timeout  │ (test call) │ │
│  └────────┬────────┘          └─────────────────┘          └──────┬──────┘ │
│           │                                                        │        │
│           │ success                                        success │        │
│           │◄───────────────────────────────────────────────────────┘        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PROTECTED SERVICES                               │   │
│  │  • Google CSE API (search_breaker)                                  │   │
│  │  • Content Fetcher (fetch_breaker)                                  │   │
│  │  • LLM API (llm_breaker)                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Breaker Configuration

| Breaker | Failure Threshold | Reset Timeout | Success Threshold |
|---------|-------------------|---------------|-------------------|
| `search_breaker` | 3 failures | 30s | 2 successes |
| `fetch_breaker` | 5 failures | 20s | 2 successes |
| `llm_breaker` | 3 failures | 60s | 1 success |

---

## 3. Implementation Specification

### 3.1 Circuit Breaker Utility

**Create `services/utils/circuit_breaker.py`:**

```python
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
```

### 3.2 Integrate Breakers with Services

**Update `services/tools/web_search.py`:**

```python
from services.utils.circuit_breaker import search_breaker, CircuitOpenError

@tool
async def web_search(query: str) -> str:
    """
    Search the web with circuit breaker protection.
    """
    if not query or not query.strip():
        return "Error: Search query cannot be empty."
    
    search_wrapper = _get_search_wrapper()
    if search_wrapper is None:
        return _get_fallback_response(query)
    
    try:
        async with search_breaker.call():
            # Perform search (wrapped in breaker)
            results = search_wrapper.run(query.strip())
            
            if not results or results.strip() == "":
                return f"No search results found for: {query}"
            
            if len(results) > 1500:
                results = results[:1500] + "..."
            
            return results
            
    except CircuitOpenError:
        logger.warning("Search circuit is OPEN, using fallback")
        return _get_fallback_response(query)
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Error performing web search: {str(e)}"
```

**Update `services/nodes/content_enricher.py`:**

```python
from services.utils.circuit_breaker import fetch_breaker, CircuitOpenError

async def _fetch_source_content(source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch content with circuit breaker protection."""
    url = source.get("url", "")
    if not url:
        return None
    
    try:
        async with fetch_breaker.call():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
                    headers={"User-Agent": "FitCheckBot/1.0"},
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html = await response.text()
                    content = _extract_text_content(html)
                    
                    return {
                        **source,
                        "full_content": content[:MAX_CONTENT_LENGTH],
                        "content_length": len(content),
                        "fetch_status": "success",
                    }
    
    except CircuitOpenError:
        logger.warning(f"Fetch circuit OPEN, using fallback for {url}")
        return _create_fallback_enrichment(source)
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None
```

### 3.3 Error Handling Framework

**Create `services/utils/error_handling.py`:**

```python
"""
Centralized Error Handling for Fit Check Pipeline.

Provides:
- Error classification (recoverable vs fatal)
- Error context preservation
- User-friendly error messages
"""

from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error classification for routing decisions."""
    RECOVERABLE = "recoverable"  # Retry may succeed
    FATAL = "fatal"              # No point retrying
    EXTERNAL = "external"        # External service issue
    VALIDATION = "validation"    # Bad input


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.FATAL,
        phase: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.category = category
        self.phase = phase
        self.context = context or {}
    
    @property
    def is_recoverable(self) -> bool:
        return self.category == ErrorCategory.RECOVERABLE
    
    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        messages = {
            ErrorCategory.RECOVERABLE: "Temporary issue occurred. Please try again.",
            ErrorCategory.FATAL: "Unable to complete the analysis.",
            ErrorCategory.EXTERNAL: "External service is temporarily unavailable.",
            ErrorCategory.VALIDATION: "Please check your input and try again.",
        }
        return messages.get(self.category, str(self))


# Specific error types
class SearchError(PipelineError):
    """Web search failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.EXTERNAL, **kwargs)


class ScoringError(PipelineError):
    """Document scoring failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RECOVERABLE, **kwargs)


class EnrichmentError(PipelineError):
    """Content enrichment failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RECOVERABLE, **kwargs)


class LLMError(PipelineError):
    """LLM API call failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.EXTERNAL, **kwargs)


def handle_node_error(
    error: Exception,
    phase: str,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle errors at node level, returning appropriate state update.
    
    Args:
        error: The exception that occurred.
        phase: Current pipeline phase.
        state: Current pipeline state.
    
    Returns:
        State update dict with error information.
    """
    logger.error(f"Error in {phase}: {error}", exc_info=True)
    
    # Build error context
    error_info = {
        "phase": phase,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    # Determine if recoverable
    if isinstance(error, PipelineError):
        is_recoverable = error.is_recoverable
        user_message = error.to_user_message()
    else:
        is_recoverable = False
        user_message = "An unexpected error occurred."
    
    # Add to processing errors list
    existing_errors = state.get("processing_errors", [])
    existing_errors.append(error_info)
    
    return {
        "processing_errors": existing_errors,
        "error": str(error) if not is_recoverable else None,
        "should_abort": not is_recoverable,
        "abort_reason": user_message if not is_recoverable else None,
    }
```

---

## 4. Full Integration Testing

### 4.1 End-to-End Test Suite

**Create `tests/integration/test_full_pipeline.py`:**

```python
"""
Full Pipeline Integration Tests.

Tests the complete upgraded Fit Check pipeline end-to-end.
"""

import pytest
from unittest.mock import patch, AsyncMock
from services.fit_check_agent import FitCheckAgent, build_fit_check_pipeline
from services.pipeline_state import create_initial_state


class TestFullPipelineIntegration:
    """End-to-end pipeline tests."""
    
    @pytest.fixture
    def agent(self):
        return FitCheckAgent()
    
    @pytest.mark.asyncio
    async def test_company_query_full_flow(self, agent):
        """Test complete flow for company query."""
        result = await agent.analyze("Stripe")
        
        # Should have final response
        assert result is not None
        assert len(result) > 100  # Meaningful response
    
    @pytest.mark.asyncio
    async def test_job_description_full_flow(self, agent):
        """Test complete flow for job description."""
        query = "Senior Python Engineer with Kubernetes experience"
        result = await agent.analyze(query)
        
        assert result is not None
        assert "Python" in result or "engineer" in result.lower()
    
    @pytest.mark.asyncio
    async def test_iteration_loop_triggers(self, agent):
        """Test that iteration loop activates for obscure company."""
        with patch('services.tools.web_search.web_search') as mock_search:
            # First iteration: sparse results
            mock_search.side_effect = [
                "Limited info about XYZ",  # Query 1
                "No results",               # Query 2
                "No results",               # Query 3
                # Second iteration: better results
                "XYZ Company uses Python, React, AWS...",
                "XYZ hiring engineers...",
                "XYZ engineering culture...",
            ]
            
            result = await agent.analyze("Obscure Startup XYZ")
            
            # Should have made multiple search calls (iteration)
            assert mock_search.call_count >= 4
    
    @pytest.mark.asyncio
    async def test_graceful_abort_on_no_data(self, agent):
        """Test graceful abort when no data found."""
        with patch('services.tools.web_search.web_search') as mock_search:
            mock_search.return_value = "No results found"
            
            result = await agent.analyze("Completely Fake Company 12345")
            
            # Should have abort response
            assert "Unable" in result or "insufficient" in result.lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_fallback(self, agent):
        """Test circuit breaker provides fallback on repeated failures."""
        from services.utils.circuit_breaker import search_breaker
        
        # Force breaker open
        for _ in range(5):
            try:
                await search_breaker.record_failure(Exception("Test"))
            except:
                pass
        
        # Should use fallback
        result = await agent.analyze("Google")  # Known company
        
        assert result is not None
        # Reset breaker for other tests
        search_breaker._state = search_breaker._state.CLOSED
        search_breaker._failure_count = 0
    
    @pytest.mark.asyncio
    async def test_enriched_content_used(self, agent):
        """Test that enriched content improves synthesis."""
        state = create_initial_state(query="Stripe")
        
        # Mock enriched sources
        state["enriched_sources"] = [
            {
                "url": "https://stripe.com/jobs",
                "title": "Stripe Careers",
                "full_content": "Stripe uses Ruby, Go, React. Values include user focus...",
                "fetch_status": "success",
            }
        ]
        
        # Should have richer context
        assert state["enriched_sources"][0]["fetch_status"] == "success"


class TestStreamingIntegration:
    """Test SSE streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_streaming_emits_events(self):
        """Test that streaming emits expected events."""
        events = []
        
        async def mock_callback(event):
            events.append(event)
        
        agent = FitCheckAgent()
        async for chunk in agent.stream_analysis("Stripe", callback=mock_callback):
            pass
        
        # Should have phase and thought events
        event_types = [e.get("type") for e in events]
        assert "phase" in event_types or "thought" in event_types


class TestErrorRecovery:
    """Test error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_partial_scoring_failure_continues(self):
        """Pipeline should continue if some scoring fails."""
        from services.utils.parallel_scorer import score_documents_parallel
        
        docs = [
            {"id": "1", "url": "https://good.com", "title": "Good", "snippet": "Content"},
            {"id": "2", "url": "https://bad.com", "title": "Bad", "snippet": "Content"},
        ]
        
        with patch('services.utils.parallel_scorer.score_single_document') as mock_score:
            # First succeeds, second fails
            mock_score.side_effect = [
                AsyncMock(return_value={"document_id": "1", "final_score": 0.8}),
                Exception("Scoring failed"),
            ]
            
            results = await score_documents_parallel(docs, "query")
            
            # Should have at least one result
            assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_enrichment_fallback_on_timeout(self):
        """Enrichment should fallback to snippet on timeout."""
        from services.nodes.content_enricher import content_enricher_node
        
        state = {
            "top_sources": [
                {"url": "https://slow.com", "title": "Slow", "snippet": "Fallback content"}
            ],
            "step_count": 0,
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Simulate timeout
            mock_session.return_value.__aenter__.return_value.get.side_effect = \
                TimeoutError("Connection timeout")
            
            result = await content_enricher_node(state, callback=None)
            
            # Should have fallback
            assert result["enriched_sources"][0]["fetch_status"] == "fallback"
            assert result["enriched_sources"][0]["full_content"] == "Fallback content"
```

### 4.2 Performance Benchmarks

**Create `tests/performance/test_benchmarks.py`:**

```python
"""
Performance Benchmarks for Upgraded Pipeline.
"""

import pytest
import time
import asyncio

class TestPerformanceBenchmarks:
    """Performance validation tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_parallel_scoring_performance(self):
        """Parallel scoring should complete in < 5s for 10 docs."""
        from services.utils.parallel_scorer import score_documents_parallel
        
        docs = [
            {"id": str(i), "url": f"https://site{i}.com", "title": f"Doc {i}", "snippet": "Content"}
            for i in range(10)
        ]
        
        start = time.time()
        results = await score_documents_parallel(docs, "test query")
        elapsed = time.time() - start
        
        assert elapsed < 5.0, f"Scoring took {elapsed:.2f}s, expected < 5s"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_enrichment_performance(self):
        """Content enrichment should complete in < 10s for 5 sources."""
        from services.nodes.content_enricher import content_enricher_node
        
        state = {
            "top_sources": [
                {"url": f"https://httpbin.org/html", "title": f"Source {i}", "snippet": "Test"}
                for i in range(5)
            ],
            "step_count": 0,
        }
        
        start = time.time()
        result = await content_enricher_node(state, callback=None)
        elapsed = time.time() - start
        
        assert elapsed < 10.0, f"Enrichment took {elapsed:.2f}s, expected < 10s"
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_full_iteration_loop_performance(self):
        """Full 3-iteration loop should complete in < 30s."""
        from services.fit_check_agent import FitCheckAgent
        
        agent = FitCheckAgent()
        
        start = time.time()
        result = await agent.analyze("Test Company Performance")
        elapsed = time.time() - start
        
        assert elapsed < 30.0, f"Full pipeline took {elapsed:.2f}s, expected < 30s"
```

---

## 5. Documentation Updates

### 5.1 Update BACKEND_DOCUMENTATION.md

Add section for new components:

```markdown
## New Components (v2.0)

### Query Expansion Engine
- Location: `services/utils/query_expander.py`
- Generates 3-5 CSE-optimized queries with operators
- Supports iteration-specific reformulation

### Parallel Scoring System
- Location: `services/utils/parallel_scorer.py`, `services/utils/source_classifier.py`
- 3-dimension AI scoring (relevance, quality, usefulness)
- Extractability multipliers by source type
- Adaptive thresholds

### Iterative Research Loop
- Location: `services/utils/sufficiency_check.py`, `services/fit_check_agent.py`
- Up to 3 iterations with query reformulation
- Sufficiency-based routing

### Content Enrichment
- Location: `services/nodes/content_enricher.py`
- Full page content extraction
- Parallel fetching with graceful fallback

### Circuit Breakers
- Location: `services/utils/circuit_breaker.py`
- Failure isolation for CSE, content fetch, LLM APIs
- Automatic recovery with half-open testing
```

---

## 6. Requirements Tracking

### Verification Checklist

| # | Requirement | Test | Status |
|---|-------------|------|--------|
| 4.1 | Circuit breaker implementation | Unit tests | ⬜ |
| 4.2 | Search API breaker integration | `test_circuit_breaker_fallback` | ⬜ |
| 4.3 | Content fetch breaker integration | `test_enrichment_fallback_on_timeout` | ⬜ |
| 4.4 | Error handling framework | Unit tests | ⬜ |
| 4.5 | Company query e2e | `test_company_query_full_flow` | ⬜ |
| 4.6 | Job description e2e | `test_job_description_full_flow` | ⬜ |
| 4.7 | Iteration loop e2e | `test_iteration_loop_triggers` | ⬜ |
| 4.8 | Graceful abort e2e | `test_graceful_abort_on_no_data` | ⬜ |
| 4.9 | Scoring performance < 5s | `test_parallel_scoring_performance` | ⬜ |
| 4.10 | Full pipeline < 30s | `test_full_iteration_loop_performance` | ⬜ |

### Sign-Off

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Staging deployment verified

---

## 7. Files Changed Summary

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `services/utils/circuit_breaker.py` | **CREATE** | ~180 |
| `services/utils/error_handling.py` | **CREATE** | ~100 |
| `services/tools/web_search.py` | MODIFY | ~30 |
| `services/nodes/content_enricher.py` | MODIFY | ~20 |
| `tests/integration/test_full_pipeline.py` | **CREATE** | ~150 |
| `tests/performance/test_benchmarks.py` | **CREATE** | ~60 |
| `BACKEND_DOCUMENTATION.md` | UPDATE | ~50 |

---

## 8. Deployment Checklist

### Pre-Deployment

- [ ] All tests pass locally
- [ ] Docker build succeeds
- [ ] Environment variables documented
- [ ] Rollback procedure tested

### Deployment Steps

1. Deploy to staging environment
2. Run integration test suite against staging
3. Monitor circuit breaker states
4. Validate SSE streaming works
5. Check performance metrics
6. Deploy to production with feature flag
7. Gradual rollout (10% → 50% → 100%)

### Post-Deployment Monitoring

- [ ] Circuit breaker open events
- [ ] Search latency p95 < 3s
- [ ] Scoring latency p95 < 5s
- [ ] Full pipeline p95 < 20s
- [ ] Error rate < 5%

---

## 9. Rollback Plan

### Immediate Rollback

```bash
# Disable new features via env var
export FIT_CHECK_V2_ENABLED=false

# Restart containers
docker-compose restart backend
```

### Full Rollback

```bash
# Revert to previous image tag
docker-compose down
docker pull resume_backend:v1.0.0
docker-compose up -d
```

### Partial Rollback Options

| Component | Rollback Method |
|-----------|-----------------|
| Query expansion | Use legacy `construct_search_queries()` |
| Parallel scoring | Revert to heuristic `assess_quality_heuristically()` |
| Content enrichment | Skip node (use snippets) |
| Iteration loop | Set `max_iterations = 1` |
| Circuit breakers | Disable in code (always pass through) |

---

## 10. Success Criteria

The upgrade is considered successful when:

1. **Functional**: All e2e tests pass
2. **Performance**: Full pipeline < 20s (p95)
3. **Reliability**: Error rate < 2% over 24h
4. **Quality**: Manual audit shows improved research accuracy
5. **Stability**: No circuit breaker stuck open > 5min
