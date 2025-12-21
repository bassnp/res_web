````markdown
# Multi-Session Streaming Upgrade Plan

## Executive Summary

This document outlines a phased approach to upgrade the Portfolio Backend from a single-session-at-a-time architecture to a robust multi-session system capable of handling concurrent fit check assessments, deep researcher live updates, and results streaming.

---

## Current Architecture Issues

### Critical Problems

| Issue | Location | Impact |
|-------|----------|--------|
| **Shared `_callback_holder`** | `services/fit_check_agent.py:307-308` | Concurrent requests overwrite each other's callbacks - only the last request receives events |
| **No session isolation** | `routers/fit_check.py` | Pipeline state can bleed between sessions |
| **Singleton agent** | `services/fit_check_agent.py:458-463` | Single agent instance with mutable callback holder |

### Root Cause Analysis

```
Request A: FitCheckAgent._callback_holder["callback"] = callback_A
Request B: FitCheckAgent._callback_holder["callback"] = callback_B  # Overwrites A!
Pipeline Node: await self._callback_holder["callback"].on_phase(...)  # Only B receives
```

---

## Phase 1: Session Isolation (Critical - Must Do First)

**Goal:** Ensure concurrent requests are completely isolated with no shared mutable state.

### 1.1 Create Session-Scoped Pipeline Builder

**File:** `services/fit_check_agent.py`

**Change:** Remove singleton pattern and shared `_callback_holder`. Each request gets a fresh pipeline instance with its own callback.

```python
# BEFORE (problematic)
class FitCheckAgent:
    def __init__(self):
        self._callback_holder = {}  # Shared across all requests!

# AFTER (isolated)
class FitCheckAgent:
    def __init__(self):
        pass  # No shared state
    
    async def stream_analysis(self, query, callback, model_id, config_type):
        # Create isolated callback holder per-request
        callback_holder = {"callback": callback}
        pipeline = build_fit_check_pipeline(callback_holder)
        # ... rest of execution
```

### 1.2 Add Session ID Tracking (Optional but Recommended)

**Files:** 
- `models/fit_check.py` - Add optional `session_id` to request
- `services/streaming_callback.py` - Log session ID with events
- `routers/fit_check.py` - Generate session ID if not provided

```python
# models/fit_check.py
class FitCheckRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Auto-generated if not provided
    # ...

# routers/fit_check.py
@router.post("/stream")
async def stream_fit_check(request: FitCheckRequest):
    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"[{session_id}] Starting fit check...")
    # Pass session_id to callback for tracing
```

### 1.3 Implement Graceful Disconnect Handling

**File:** `routers/fit_check.py`

**Change:** Detect client disconnection and clean up resources.

```python
async def generate_events():
    try:
        async for event in callback.events():
            yield event
    except asyncio.CancelledError:
        logger.info(f"[{session_id}] Client disconnected - cleaning up")
        # Cancel any running pipeline tasks
        agent_task.cancel()
        await callback.on_error("CLIENT_DISCONNECT", "Client closed connection")
```

---

## Phase 2: Concurrency Safety (Important)

**Goal:** Ensure all shared resources are thread-safe for async concurrent access.

### 2.1 Review Shared Resources

| Resource | Location | Safe? | Action |
|----------|----------|-------|--------|
| `_agent_instance` | `fit_check_agent.py:458` | ⚠️ | Make truly stateless |
| `search_breaker` | `tools/web_search.py` | ⚠️ | Use async-safe circuit breaker |
| LLM client | `config/llm.py` | ✅ | langchain handles this |
| Prompt loader | `prompt_loader.py` | ✅ | Read-only after startup |

### 2.2 Make Circuit Breaker Async-Safe

**File:** `services/utils/circuit_breaker.py`

```python
import asyncio

class AsyncCircuitBreaker:
    def __init__(self, max_failures: int = 3, reset_timeout: float = 60.0):
        self._lock = asyncio.Lock()
        self._failure_count = 0
        self._last_failure_time = None
        self._max_failures = max_failures
        self._reset_timeout = reset_timeout
    
    async def is_open(self) -> bool:
        async with self._lock:
            if self._failure_count >= self._max_failures:
                elapsed = time.time() - self._last_failure_time
                if elapsed < self._reset_timeout:
                    return True
                # Reset after timeout
                self._failure_count = 0
            return False
```

### 2.3 Add Request Timeout Handling

**File:** `routers/fit_check.py`

```python
from async_timeout import timeout

async def generate_events():
    try:
        async with timeout(300):  # 5 minute max per request
            async for event in callback.events():
                yield event
    except asyncio.TimeoutError:
        await callback.on_error("TIMEOUT", "Request exceeded 5 minute limit")
```

---

## Phase 3: Observability & Monitoring

**Goal:** Add structured logging and metrics for production debugging.

### 3.1 Structured Session Logging

**File:** `services/streaming_callback.py`

```python
class StreamingCallbackHandler(ThoughtCallback):
    def __init__(self, session_id: str, include_thoughts: bool = True):
        self._session_id = session_id
        self._queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        # ...
    
    async def _emit(self, event_type: str, data: dict) -> None:
        # Add session context to all logs
        logger.info(
            f"[{self._session_id}] Emitting {event_type}",
            extra={"session_id": self._session_id, "event_type": event_type}
        )
        # ...
```

### 3.2 Add Metrics Collection (Optional)

**New File:** `services/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge

# Active sessions gauge
active_sessions = Gauge(
    'fit_check_active_sessions',
    'Number of active fit check sessions'
)

# Request duration histogram
request_duration = Histogram(
    'fit_check_request_duration_seconds',
    'Time spent processing fit check requests',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Phase completion counter
phase_completions = Counter(
    'fit_check_phase_completions_total',
    'Number of phase completions',
    ['phase', 'status']
)
```

### 3.3 Health Check Enhancement

**File:** `routers/fit_check.py`

```python
@router.get("/health")
async def fit_check_health():
    return {
        "status": "healthy",
        "service": "fit-check",
        "active_sessions": active_sessions._value._value,  # Current count
        "agent_ready": True,
    }
```

---

## Phase 4: Sevalla Deployment Configuration

**Goal:** Configure the application for Sevalla PaaS deployment (Docker Application + Static Site).

> **Sevalla Handles Automatically:**
> - ✅ SSL/HTTPS certificates (free, automatic)
> - ✅ Reverse proxy / load balancing
> - ✅ CDN for static assets
> - ✅ Health check endpoints
> - ✅ Environment variables (dashboard UI)
> - ✅ Git-based auto-deployments
> - ✅ Custom domains
> - ✅ Logging and monitoring

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SEVALLA PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │  STATIC SITE        │    │  APPLICATION (Docker)       │ │
│  │  ───────────────    │    │  ───────────────────────    │ │
│  │  Frontend (Next.js) │───▶│  Backend (FastAPI)          │ │
│  │  - Static export    │    │  - Dockerfile deployment    │ │
│  │  - CDN cached       │    │  - Env vars via dashboard   │ │
│  │  - Custom domain    │    │  - Auto SSL/HTTPS           │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.1 Optimize Dockerfile for Sevalla

**File:** `backend/Dockerfile`

Sevalla runs single-container Docker apps. Optimize CMD for SSE:

```dockerfile
# Optimized for SSE streaming on Sevalla
# - Single worker (async handles concurrency)
# - Extended keep-alive for long SSE connections
CMD ["uvicorn", "server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "75"]
```

### 4.2 Configure Environment Variables (Sevalla Dashboard)

Set these in Sevalla Application → Settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `GOOGLE_API_KEY` | `<your-key>` | Gemini LLM API key |
| `GOOGLE_CSE_API_KEY` | `<your-key>` | Google Custom Search |
| `GOOGLE_CSE_ID` | `<your-id>` | Search Engine ID |
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | Frontend URL |
| `LOG_LEVEL` | `INFO` | Production logging |
| `LOG_FORMAT` | `json` | Structured logs (optional) |

**Tip:** Use Sevalla's **Global Environment Variables** for shared keys across apps.

### 4.3 Frontend Static Site Configuration

**Build Command:** `npm run build`  
**Output Directory:** `out/` (Next.js static export)

Ensure `next.config.js` has static export enabled:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // ... other config
};
```

### 4.4 Update CORS for Production Domain

**File:** `backend/server.py` - Uses `ALLOWED_ORIGINS` env var automatically.

Set `ALLOWED_ORIGINS` in Sevalla dashboard to your frontend domain.

### 4.5 NOT NEEDED (Sevalla Handles)

The following are **NOT required** for Sevalla deployment:

- ❌ Nginx reverse proxy configuration
- ❌ SSL certificate setup
- ❌ Docker Compose for production
- ❌ Load balancer configuration
- ❌ Custom health check scripts (Sevalla probes `/health`)
- ❌ CDN configuration
- ❌ Multi-container orchestration

---

## Phase 5: Frontend Enhancements (Optional)

**Goal:** Improve client-side session management and resilience.

### 5.1 Add Session ID to Requests

**File:** `hooks/use-fit-check.js`

```javascript
const submitQuery = useCallback(async (query) => {
    // Generate unique session ID
    const sessionId = crypto.randomUUID();
    
    const response = await fetch(`${API_URL}/api/fit-check/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': sessionId,  // Track on server
        },
        body: JSON.stringify({
            query,
            session_id: sessionId,
            // ...
        }),
    });
}, []);
```

### 5.2 Add Reconnection Logic

**File:** `hooks/use-fit-check.js`

```javascript
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

const submitQueryWithRetry = useCallback(async (query, attempt = 1) => {
    try {
        await submitQuery(query);
    } catch (error) {
        if (attempt < MAX_RETRIES && error.name !== 'AbortError') {
            console.log(`Retry attempt ${attempt}/${MAX_RETRIES}`);
            await new Promise(r => setTimeout(r, RETRY_DELAY * attempt));
            return submitQueryWithRetry(query, attempt + 1);
        }
        throw error;
    }
}, [submitQuery]);
```

---

## Implementation Priority Matrix

| Phase | Priority | Effort | Risk if Skipped |
|-------|----------|--------|-----------------|
| **Phase 1: Session Isolation** | 🔴 Critical | 2-4 hours | Concurrent requests fail |
| **Phase 2: Concurrency Safety** | 🟠 High | 2-3 hours | Race conditions under load |
| **Phase 3: Observability** | 🟡 Medium | 1-2 hours | Debugging blind spots |
| **Phase 4: Sevalla Deployment** | 🟢 Low | 30 min | Simple config changes |
| **Phase 5: Frontend Enhancements** | 🟢 Low | 1-2 hours | Nice-to-have |

> **Note:** Phase 4 is significantly simplified for Sevalla deployment. Most infrastructure concerns (SSL, nginx, load balancing, health checks) are handled by the platform automatically.

---

## Quick Start: Minimum Viable Fix (Phase 1 Only)

If you need concurrent sessions working immediately, here's the minimal change:

### Step 1: Update `fit_check_agent.py`

```python
# Line ~307: Change this method signature
async def stream_analysis(
    self,
    query: str,
    callback: ThoughtCallback,
    model_id: str = None,
    config_type: str = None,
) -> AsyncGenerator[str, None]:
    start_time = time.time()
    
    # CREATE ISOLATED CALLBACK HOLDER PER REQUEST
    callback_holder = {"callback": callback}  # <-- NEW: Not self._callback_holder
    
    logger.info(f"Starting streaming analysis for query: {query[:50]}... model={model_id}")
    
    await callback.on_status("connecting", "Initializing AI agent...")
    
    try:
        # Build pipeline with REQUEST-LOCAL callback holder
        pipeline = build_fit_check_pipeline(callback_holder)  # <-- Uses local holder
        # ... rest unchanged
```

### Step 2: Remove Shared State

```python
class FitCheckAgent:
    def __init__(self):
        # Remove: self._callback_holder = {}
        pass  # Agent is now stateless
```

That's it! This single change isolates each request's callback holder, fixing the critical multi-session bug.

---

## Testing Multi-Session Support

### Manual Test: Concurrent Requests

```bash
# Terminal 1: Long-running company query
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Google"}' --no-buffer

# Terminal 2: Quick job description query (should not interfere with Terminal 1)
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "React developer job"}' --no-buffer
```

Both streams should run independently without event mixing.

### Automated Integration Test

```python
# tests/integration/test_multi_session.py
import asyncio
import httpx

async def test_concurrent_sessions():
    """Verify two concurrent sessions don't interfere."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Start two concurrent requests
        async def session(query: str, expected_marker: str):
            events = []
            async with client.stream(
                "POST", "/api/fit-check/stream",
                json={"query": query}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        events.append(line)
            # Verify no cross-contamination
            return all(expected_marker in str(e) for e in events if "phase" in str(e))
        
        results = await asyncio.gather(
            session("Google", "Google"),
            session("Microsoft", "Microsoft"),
        )
        
        assert all(results), "Sessions should be isolated"
```

---

## Conclusion

The critical fix is **Phase 1** - removing the shared `_callback_holder` and creating isolated callback holders per-request. This is a minimal code change (2-3 lines) with maximum impact.

Phases 2-5 are progressive enhancements for production readiness, but not required for local development or demo purposes.
````
