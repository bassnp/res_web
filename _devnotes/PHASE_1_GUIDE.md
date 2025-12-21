````markdown
# Phase 1: Session Isolation Implementation Guide

> **Priority:** 🔴 CRITICAL  
> **Estimated Time:** 2-4 hours  
> **Risk if Skipped:** Concurrent requests fail - only last client receives events

---

## Overview

This phase fixes the critical bug where concurrent SSE streaming requests overwrite each other's callbacks. The root cause is a shared `_callback_holder` dictionary in the singleton `FitCheckAgent` class.

### Problem Statement

```
Timeline of Bug:
─────────────────────────────────────────────────────────────────
t=0ms    Client A POST /api/fit-check/stream {"query": "Google"}
t=5ms    Agent sets: self._callback_holder["callback"] = callback_A
t=10ms   Client B POST /api/fit-check/stream {"query": "Microsoft"}
t=15ms   Agent sets: self._callback_holder["callback"] = callback_B  ← OVERWRITES A!
t=20ms   Pipeline node emits: await self._callback_holder["callback"].on_phase(...)
         → Only Client B receives the event
         → Client A's stream hangs or receives incomplete data
─────────────────────────────────────────────────────────────────
```

---

## Prerequisites

- [ ] Backend Docker container running locally (`docker compose up -d`)
- [ ] Access to `backend/` source code
- [ ] Python 3.11+ installed for local testing
- [ ] Two terminal windows for concurrent request testing

---

## Implementation Checklist

### Step 1: Remove Shared State from FitCheckAgent

**File:** `backend/services/fit_check_agent.py`

#### 1.1 Locate the Problem Code

Find the `FitCheckAgent.__init__` method (around line 310):

```python
class FitCheckAgent:
    """
    High-level interface for the Fit Check Agent.
    """
    
    def __init__(self):
        """Initialize the agent."""
        self._callback_holder = {}  # ← PROBLEM: Shared across all requests
```

#### 1.2 Remove Shared Callback Holder

**Action:** Remove the `_callback_holder` instance variable from `__init__`.

```python
# BEFORE
def __init__(self):
    """Initialize the agent."""
    self._callback_holder = {}

# AFTER
def __init__(self):
    """Initialize the agent (stateless - no shared mutable state)."""
    pass  # Agent is now stateless
```

- [x] **TODO:** Remove `self._callback_holder = {}` from `__init__`
- [x] **TODO:** Update docstring to indicate stateless design

---

### Step 2: Create Request-Scoped Callback Holder

**File:** `backend/services/fit_check_agent.py`

#### 2.1 Locate the `stream_analysis` Method

Find the method around line 340:

```python
async def stream_analysis(
    self,
    query: str,
    callback: ThoughtCallback,
    model_id: str = None,
    config_type: str = None,
) -> AsyncGenerator[str, None]:
```

#### 2.2 Replace Shared State with Local Variable

**Action:** Change from `self._callback_holder` to a local `callback_holder` variable.

```python
# BEFORE (around line 376)
# Set callback for pipeline nodes
self._callback_holder["callback"] = callback

try:
    # Build pipeline with callback
    pipeline = build_fit_check_pipeline(self._callback_holder)

# AFTER
# Create ISOLATED callback holder for this request (prevents cross-session contamination)
callback_holder = {"callback": callback}

try:
    # Build pipeline with request-local callback holder
    pipeline = build_fit_check_pipeline(callback_holder)
```

- [x] **TODO:** Create local `callback_holder` variable before try block
- [x] **TODO:** Replace `self._callback_holder` with `callback_holder` in `build_fit_check_pipeline()` call
- [x] **TODO:** Add comment explaining isolation purpose

---

### Step 3: Update the `analyze` Method (Non-Streaming Path)

**File:** `backend/services/fit_check_agent.py`

#### 3.1 Locate the `analyze` Method

Find around line 320:

```python
async def analyze(
    self,
    query: str,
    model_id: str = None,
    config_type: str = None,
) -> str:
```

#### 3.2 Replace Shared State

```python
# BEFORE
# Build pipeline without callback
pipeline = build_fit_check_pipeline(self._callback_holder)

# AFTER
# Build pipeline without callback (empty holder for non-streaming)
callback_holder = {}
pipeline = build_fit_check_pipeline(callback_holder)
```

- [x] **TODO:** Create local `callback_holder = {}` in `analyze` method
- [x] **TODO:** Pass local variable to `build_fit_check_pipeline()`

---

### Step 4: Remove Finally Block Cleanup (No Longer Needed)

**File:** `backend/services/fit_check_agent.py`

#### 4.1 Locate the Finally Block

In `stream_analysis`, find around line 420:

```python
finally:
    # Clear callback reference
    self._callback_holder.pop("callback", None)
```

#### 4.2 Remove or Simplify

Since we're using request-local state, cleanup is automatic via garbage collection:

```python
# BEFORE
finally:
    # Clear callback reference
    self._callback_holder.pop("callback", None)

# AFTER
finally:
    # Callback holder is request-local, cleaned up automatically
    pass
```

Or remove the finally block entirely if there's no other cleanup needed.

- [x] **TODO:** Remove `self._callback_holder.pop()` call
- [x] **TODO:** Optionally remove empty finally block

---

### Step 5: Add Session ID for Traceability (Recommended)

**File:** `backend/models/fit_check.py`

#### 5.1 Add Optional Session ID to Request Model

```python
from typing import Optional
import uuid

class FitCheckRequest(BaseModel):
    """Request body for the fit check endpoint."""
    
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Company name or job description to analyze"
    )
    include_thoughts: bool = Field(
        default=True,
        description="Whether to stream thinking steps"
    )
    model_id: str = Field(
        default="gemini-2.0-flash",
        description="AI model ID to use"
    )
    config_type: str = Field(
        default="reasoning",
        description="Configuration type: 'reasoning' or 'standard'"
    )
    # NEW: Optional session ID for tracing
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for request tracing (auto-generated if not provided)"
    )
```

- [x] **TODO:** Add `session_id: Optional[str]` field to `FitCheckRequest`
- [x] **TODO:** Import `Optional` and `uuid` if needed

---

### Step 6: Generate Session ID in Router

**File:** `backend/routers/fit_check.py`

#### 6.1 Add UUID Import

```python
import uuid
```

#### 6.2 Generate Session ID if Not Provided

```python
@router.post("/stream")
async def stream_fit_check(request: FitCheckRequest):
    """Stream AI fit analysis via Server-Sent Events."""
    
    # Generate session ID for tracing if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(
        f"[{session_id}] Received fit check request: query={request.query[:50]}..., "
        f"model={request.model_id}, config_type={request.config_type}"
    )
    
    # Create callback handler with session ID
    callback = StreamingCallbackHandler(
        include_thoughts=request.include_thoughts,
        session_id=session_id  # NEW: Pass session ID
    )
    # ... rest of handler
```

- [x] **TODO:** Add `import uuid` at top of file
- [x] **TODO:** Generate `session_id` from request or create new UUID
- [x] **TODO:** Include `session_id` in log messages
- [x] **TODO:** Pass `session_id` to `StreamingCallbackHandler`

---

### Step 7: Update StreamingCallbackHandler with Session ID

**File:** `backend/services/streaming_callback.py`

#### 7.1 Add Session ID Parameter

```python
class StreamingCallbackHandler(ThoughtCallback):
    """Callback handler that queues events for SSE streaming."""
    
    def __init__(self, include_thoughts: bool = True, session_id: str = None):
        """
        Initialize the streaming callback handler.
        
        Args:
            include_thoughts: Whether to emit thought events.
            session_id: Optional session identifier for tracing.
        """
        self._queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._include_thoughts = include_thoughts
        self._session_id = session_id or "unknown"
        self._completed = False
        self._error_occurred = False
        logger.debug(f"[{self._session_id}] StreamingCallbackHandler initialized")
```

#### 7.2 Include Session ID in Log Messages

Update the `_emit` method:

```python
async def _emit(self, event_type: str, data: dict) -> None:
    """Emit an SSE event by adding it to the queue."""
    if self._completed:
        logger.warning(f"[{self._session_id}] Attempted to emit after completion: {event_type}")
        return
    
    sse_event = format_sse(event_type, data)
    await self._queue.put(sse_event)
    logger.debug(f"[{self._session_id}] Emitted {event_type} event")
```

- [x] **TODO:** Add `session_id` parameter to `__init__`
- [x] **TODO:** Store as `self._session_id`
- [x] **TODO:** Update all `logger.*` calls to include `[{self._session_id}]` prefix

---

## Verification & Validation

### Test 1: Single Request Smoke Test

```bash
# Ensure container is running
cd backend
docker compose up -d

# Wait for health check
curl http://localhost:8000/health

# Run single request
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Google", "include_thoughts": true}' \
  --no-buffer
```

**Expected Result:**
- [ ] Stream begins with `event: status`
- [ ] Multiple `event: phase` and `event: thought` events appear
- [ ] Stream ends with `event: complete`
- [ ] No errors in docker logs

---

### Test 2: Concurrent Request Isolation (CRITICAL)

Open **two terminal windows** and run simultaneously:

**Terminal 1:**
```bash
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Google software engineer", "session_id": "session-A"}' \
  --no-buffer
```

**Terminal 2:** (Start within 2 seconds of Terminal 1)
```bash
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Microsoft Azure developer", "session_id": "session-B"}' \
  --no-buffer
```

**Expected Result:**
- [ ] Both terminals receive complete streams
- [ ] Terminal 1 events reference "Google" (not Microsoft)
- [ ] Terminal 2 events reference "Microsoft" (not Google)
- [ ] Both streams end with `event: complete`
- [ ] Docker logs show interleaved `[session-A]` and `[session-B]` entries

**Verification Command:**
```bash
# Check docker logs for session isolation
docker logs res_web-backend 2>&1 | grep -E "\[session-[AB]\]" | tail -20
```

---

### Test 3: Rapid-Fire Concurrent Requests

Use a load testing tool or script:

```python
# tests/integration/test_concurrent_sessions.py
import asyncio
import httpx

async def test_10_concurrent_sessions():
    """Verify 10 concurrent sessions don't interfere."""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as client:
        
        async def run_session(session_num: int) -> dict:
            """Run a single session and collect events."""
            query = f"Company {session_num} test query"
            session_id = f"test-session-{session_num}"
            events = []
            
            async with client.stream(
                "POST", "/api/fit-check/stream",
                json={"query": query, "session_id": session_id}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        events.append(line)
            
            return {
                "session_id": session_id,
                "event_count": len(events),
                "has_complete": any("complete" in e for e in events),
            }
        
        # Run 10 concurrent sessions
        results = await asyncio.gather(*[
            run_session(i) for i in range(10)
        ])
        
        # Verify all completed successfully
        for result in results:
            assert result["has_complete"], f"{result['session_id']} did not complete"
            assert result["event_count"] > 5, f"{result['session_id']} had too few events"
        
        print("✅ All 10 concurrent sessions completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_10_concurrent_sessions())
```

- [ ] **TODO:** Run the concurrent test script
- [ ] **TODO:** Verify all 10 sessions complete without interference

---

### Test 4: Client Disconnect Handling

```bash
# Start a request and cancel it mid-stream (Ctrl+C after ~5 seconds)
curl -X POST http://localhost:8000/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Test disconnect handling", "session_id": "disconnect-test"}' \
  --no-buffer

# After pressing Ctrl+C, check logs:
docker logs res_web-backend 2>&1 | grep "disconnect-test"
```

**Expected Result:**
- [ ] No unhandled exceptions in logs
- [ ] May see "Client disconnected" or "CancelledError" (both acceptable)
- [ ] No resource leaks (memory usage stable)

---

## Rollback Plan

If issues are discovered after deployment:

1. **Revert Code Changes:**
   ```bash
   git checkout HEAD~1 -- backend/services/fit_check_agent.py
   git checkout HEAD~1 -- backend/services/streaming_callback.py
   git checkout HEAD~1 -- backend/models/fit_check.py
   git checkout HEAD~1 -- backend/routers/fit_check.py
   ```

2. **Rebuild Container:**
   ```bash
   cd backend
   .\run_docker_rebuild.bat
   ```

3. **Verify Rollback:**
   ```bash
   curl http://localhost:8000/health
   ```

---

## Completion Checklist

After completing all steps and tests, update the main tracking document:

**File:** `_devnotes/MULTI_SESSION_UPGRADE_PLAN.md`

Mark Phase 1 as complete:
```markdown
| **Phase 1: Session Isolation** | ✅ Complete | 2024-XX-XX |
```

### Summary of Changes

| File | Change |
|------|--------|
| `services/fit_check_agent.py` | Removed shared `_callback_holder`, use request-local variable |
| `models/fit_check.py` | Added optional `session_id` field |
| `routers/fit_check.py` | Generate session ID, pass to callback handler |
| `services/streaming_callback.py` | Accept and log session ID |

---

## Next Steps

Once Phase 1 is complete and verified:

1. **Monitor Production:** Watch for any session-related issues
2. **Proceed to Phase 2:** Concurrency safety (circuit breakers, timeouts)
3. **Document Lessons Learned:** Note any edge cases discovered

---

## Appendix: Quick Reference Code Diff

```diff
# services/fit_check_agent.py

class FitCheckAgent:
    def __init__(self):
-       self._callback_holder = {}
+       pass  # Stateless - no shared mutable state
    
    async def stream_analysis(self, query, callback, model_id, config_type):
        start_time = time.time()
+       # Create ISOLATED callback holder for this request
+       callback_holder = {"callback": callback}
        
-       self._callback_holder["callback"] = callback
        try:
-           pipeline = build_fit_check_pipeline(self._callback_holder)
+           pipeline = build_fit_check_pipeline(callback_holder)
            # ... rest unchanged
        finally:
-           self._callback_holder.pop("callback", None)
+           pass  # Automatic cleanup via GC
```

```diff
# services/streaming_callback.py

class StreamingCallbackHandler(ThoughtCallback):
-   def __init__(self, include_thoughts: bool = True):
+   def __init__(self, include_thoughts: bool = True, session_id: str = None):
        self._queue = asyncio.Queue()
        self._include_thoughts = include_thoughts
+       self._session_id = session_id or "unknown"
        self._completed = False
```

```diff
# routers/fit_check.py

+import uuid

@router.post("/stream")
async def stream_fit_check(request: FitCheckRequest):
+   session_id = request.session_id or str(uuid.uuid4())
+   logger.info(f"[{session_id}] Received fit check request...")
    
-   callback = StreamingCallbackHandler(include_thoughts=request.include_thoughts)
+   callback = StreamingCallbackHandler(
+       include_thoughts=request.include_thoughts,
+       session_id=session_id
+   )
```
````
