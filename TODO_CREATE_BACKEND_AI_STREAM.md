# TODO: Backend API - AI Streaming Endpoint

## Overview
This document outlines the implementation plan for a FastAPI backend server that provides Server-Sent Events (SSE) streaming for the "See if I'm fit for you!" AI chatbot feature. The API will stream real-time agent status updates, thinking process, and final responses to the frontend.

---

## 1. Architecture Overview

### Backend Stack (Matching `pweb/backend/`)
- **Framework:** FastAPI with async support
- **Streaming:** Server-Sent Events (SSE) via `StreamingResponse`
- **AI Integration:** LangChain + LangGraph for agent orchestration
- **LLM:** Google Gemini 3 Pro (`gemini-3-pro-preview`)

### API Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  (Next.js)                                                      │
│                                                                 │
│  1. User submits query (company name or job description)        │
│  2. Opens EventSource connection to /api/fit-check/stream       │
│  3. Receives SSE events:                                        │
│     - event: status    → Agent status update                    │
│     - event: thought   → AI reasoning step                      │
│     - event: response  → Response text chunk                    │
│     - event: complete  → Stream finished                        │
│     - event: error     → Error occurred                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼ HTTP/SSE
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND API                              │
│  (FastAPI)                                                      │
│                                                                 │
│  /api/fit-check/stream (POST)                                   │
│    → Validates request                                          │
│    → Initiates AI Agent                                         │
│    → Streams events via SSE                                     │
│                                                                 │
│  Internal Flow:                                                 │
│    1. Receive query from frontend                               │
│    2. Start AI Agent execution                                  │
│    3. Stream thinking events as agent reasons                   │
│    4. Stream response chunks as agent generates                 │
│    5. Send complete event when done                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AI AGENT                                 │
│  (LangGraph ReAct Agent)                                        │
│                                                                 │
│  Tools:                                                         │
│    - web_search: Research company/industry                      │
│    - analyze_fit: Match skills to requirements                  │
│                                                                 │
│  Callback System:                                               │
│    - on_tool_start → emit "thought" event                       │
│    - on_llm_token  → emit "response" event                      │
│    - on_agent_end  → emit "complete" event                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
res_web_backend/                    # [NEW] Backend for portfolio site
├── .env                            # Environment variables
├── .gitignore                      # Git ignore file
├── requirements.txt                # Python dependencies
├── server.py                       # FastAPI application entry point
├── routers/
│   ├── __init__.py
│   └── fit_check.py                # /api/fit-check/* endpoints
├── services/
│   ├── __init__.py
│   └── fit_check_agent.py          # AI Agent implementation
├── models/
│   ├── __init__.py
│   └── fit_check.py                # Pydantic models for requests/responses
└── prompts/
    └── fit_check_system.txt        # System prompt for the AI agent
```

---

## 3. API Endpoint Specification

### POST /api/fit-check/stream

**Purpose:** Execute AI agent to analyze fit and stream results via SSE.

**Request:**
```json
{
  "query": "string",           // Required: Company name or job description
  "include_thoughts": true     // Optional: Include thinking process in stream
}
```

**Response:** Server-Sent Events stream

**SSE Event Types:**

#### 1. `status` - Agent status update
```
event: status
data: {"status": "connecting", "message": "Initializing AI agent..."}

event: status
data: {"status": "researching", "message": "Searching for company information..."}

event: status
data: {"status": "analyzing", "message": "Analyzing skill alignment..."}

event: status
data: {"status": "generating", "message": "Crafting personalized response..."}
```

#### 2. `thought` - AI reasoning step (visible thinking)
```
event: thought
data: {"step": 1, "type": "tool_call", "tool": "web_search", "input": "Google company culture engineering"}

event: thought
data: {"step": 2, "type": "observation", "content": "Google values innovation and technical excellence..."}

event: thought
data: {"step": 3, "type": "reasoning", "content": "Based on the company's focus on AI and cloud, the candidate's Python and ML experience align well..."}
```

#### 3. `response` - Response text chunk (streaming)
```
event: response
data: {"chunk": "Based on my research, "}

event: response
data: {"chunk": "your skills in Python and cloud computing "}

event: response
data: {"chunk": "align exceptionally well with Google's engineering culture..."}
```

#### 4. `complete` - Stream finished
```
event: complete
data: {"total_tokens": 1234, "duration_ms": 5678}
```

#### 5. `error` - Error occurred
```
event: error
data: {"code": "AGENT_ERROR", "message": "Failed to research company. Please try again."}
```

---

## 4. Implementation Details

### 4.1 FastAPI Server Setup

```python
# server.py

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import fit_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    logger.info("Portfolio Backend API starting up...")
    yield
    logger.info("Portfolio Backend API shutting down...")


app = FastAPI(
    title="Portfolio Backend API",
    description="Backend API for 'See if I'm fit for you!' feature",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - Allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-portfolio-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fit_check.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 4.2 Fit Check Router

```python
# routers/fit_check.py

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.fit_check_agent import FitCheckAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fit-check", tags=["fit-check"])


class FitCheckRequest(BaseModel):
    """Request model for fit check endpoint."""
    query: str
    include_thoughts: bool = True


@router.post("/stream")
async def stream_fit_check(request: FitCheckRequest):
    """
    Stream AI agent analysis of employer query.
    
    Returns SSE stream with:
    - status: Agent status updates
    - thought: AI reasoning steps (if include_thoughts=True)
    - response: Response text chunks
    - complete: Stream finished signal
    - error: Error information
    """
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    
    if len(request.query) > 2000:
        raise HTTPException(status_code=400, detail="Query must be less than 2000 characters")

    agent = FitCheckAgent()

    async def event_generator():
        start_time = time.time()
        
        try:
            # Emit initial status
            yield _format_sse("status", {"status": "connecting", "message": "Initializing AI agent..."})
            
            # Stream agent execution
            async for event in agent.stream_analysis(
                query=request.query,
                include_thoughts=request.include_thoughts
            ):
                event_type = event.get("type", "status")
                yield _format_sse(event_type, event.get("data", {}))
            
            # Emit complete
            duration_ms = int((time.time() - start_time) * 1000)
            yield _format_sse("complete", {"duration_ms": duration_ms})
            
        except Exception as e:
            logger.error(f"Fit check stream error: {e}", exc_info=True)
            yield _format_sse("error", {"code": "AGENT_ERROR", "message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _format_sse(event_type: str, data: dict) -> str:
    """Format data as an SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
```

### 4.3 Callback Handler for Streaming

```python
# services/streaming_callback.py

import asyncio
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult


class StreamingCallbackHandler(AsyncCallbackHandler):
    """
    Custom callback handler for streaming AI agent events.
    
    Captures:
    - Tool invocations (thinking steps)
    - LLM token generation (response streaming)
    - Agent completion
    """
    
    def __init__(self, event_queue: asyncio.Queue, include_thoughts: bool = True):
        self.event_queue = event_queue
        self.include_thoughts = include_thoughts
        self.step_counter = 0
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs
    ) -> None:
        """Called when a tool starts execution."""
        if self.include_thoughts:
            self.step_counter += 1
            await self.event_queue.put({
                "type": "thought",
                "data": {
                    "step": self.step_counter,
                    "type": "tool_call",
                    "tool": serialized.get("name", "unknown"),
                    "input": input_str[:200],  # Truncate long inputs
                }
            })
            
            # Also emit status update
            await self.event_queue.put({
                "type": "status",
                "data": {
                    "status": "researching",
                    "message": f"Using {serialized.get('name', 'tool')}...",
                }
            })
    
    async def on_tool_end(
        self,
        output: str,
        **kwargs
    ) -> None:
        """Called when a tool finishes execution."""
        if self.include_thoughts:
            self.step_counter += 1
            await self.event_queue.put({
                "type": "thought",
                "data": {
                    "step": self.step_counter,
                    "type": "observation",
                    "content": output[:500],  # Truncate long outputs
                }
            })
    
    async def on_llm_new_token(
        self,
        token: str,
        **kwargs
    ) -> None:
        """Called when a new token is generated."""
        # Only stream tokens for final response, not intermediate reasoning
        if kwargs.get("tags") and "final_answer" in kwargs["tags"]:
            await self.event_queue.put({
                "type": "response",
                "data": {"chunk": token}
            })
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs
    ) -> None:
        """Called when LLM starts."""
        await self.event_queue.put({
            "type": "status",
            "data": {
                "status": "analyzing",
                "message": "Analyzing fit and generating response...",
            }
        })
    
    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs
    ) -> None:
        """Called when the agent chain ends."""
        pass  # Complete event is sent by the router
```

---

## 5. Request/Response Models

```python
# models/fit_check.py

from typing import Optional, Literal
from pydantic import BaseModel, Field


class FitCheckRequest(BaseModel):
    """Request model for fit check API."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Company name or job description to analyze"
    )
    include_thoughts: bool = Field(
        default=True,
        description="Include AI thinking process in the stream"
    )


class StatusEvent(BaseModel):
    """Status update event."""
    status: Literal["connecting", "researching", "analyzing", "generating"]
    message: str


class ThoughtEvent(BaseModel):
    """AI thinking step event."""
    step: int
    type: Literal["tool_call", "observation", "reasoning"]
    tool: Optional[str] = None
    input: Optional[str] = None
    content: Optional[str] = None


class ResponseEvent(BaseModel):
    """Response text chunk event."""
    chunk: str


class CompleteEvent(BaseModel):
    """Stream complete event."""
    duration_ms: int
    total_tokens: Optional[int] = None


class ErrorEvent(BaseModel):
    """Error event."""
    code: str
    message: str
```

---

## 6. Environment Configuration

```env
# .env

# Google AI
GOOGLE_API_KEY=your_gemini_api_key_here

# Google Custom Search Engine (for web research)
GOOGLE_CSE_API_KEY=your_cse_api_key_here
GOOGLE_CSE_ID=your_cse_id_here

# Server
HOST=0.0.0.0
PORT=8000

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:3000,https://your-portfolio.com

# Logging
LOG_LEVEL=INFO
```

---

## 7. Dependencies

```requirements
# requirements.txt

# Core Framework
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.6.0

# AI & LangChain
langchain>=0.3.0
langchain-core>=0.3.0
langchain-google-genai>=2.1.0
langgraph>=0.2.0
google-generativeai>=0.8.0

# Web Search
langchain-google-community>=2.0.0
google-api-python-client>=2.150.0

# Async Support
aiohttp>=3.9.0

# Development
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

---

## 8. Error Handling Strategy

### Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_QUERY` | 400 | Query too short or too long |
| `RATE_LIMITED` | 429 | Too many requests |
| `AGENT_ERROR` | 500 | AI agent execution failed |
| `SEARCH_ERROR` | 502 | Web search tool failed |
| `LLM_ERROR` | 503 | Gemini API unavailable |
| `TIMEOUT` | 504 | Agent execution timed out |

### Error Response Format
```python
async def handle_agent_error(error: Exception):
    """Map exceptions to SSE error events."""
    error_mapping = {
        "ResourceExhausted": ("RATE_LIMITED", "Rate limit exceeded. Please wait."),
        "InvalidArgument": ("INVALID_QUERY", "Invalid query format."),
        "DeadlineExceeded": ("TIMEOUT", "Request timed out. Try a shorter query."),
    }
    
    error_type = type(error).__name__
    code, message = error_mapping.get(error_type, ("AGENT_ERROR", str(error)))
    
    return {"type": "error", "data": {"code": code, "message": message}}
```

---

## 9. Rate Limiting (Optional)

```python
# middleware/rate_limit.py

from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 5):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/fit-check"):
            client_ip = request.client.host
            now = datetime.now()
            
            # Clean old requests
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip]
                if now - t < timedelta(minutes=1)
            ]
            
            if len(self.request_counts[client_ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please wait a minute."
                )
            
            self.request_counts[client_ip].append(now)
        
        return await call_next(request)
```

---

## 10. Testing Strategy

### Unit Tests
```python
# tests/test_fit_check.py

import pytest
from httpx import AsyncClient
from server import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_fit_check_invalid_query():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/fit-check/stream",
            json={"query": "ab"}  # Too short
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_fit_check_stream():
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/fit-check/stream",
            json={"query": "Google", "include_thoughts": True}
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            
            events = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line.split(": ")[1])
            
            assert "status" in events
            assert "complete" in events or "error" in events
```

---

## 11. Deployment Considerations

### Docker Setup
```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

---

## 12. Implementation Checklist

### Phase 1: Basic Setup
- [ ] Create directory structure
- [ ] Set up FastAPI application
- [ ] Implement health check endpoint
- [ ] Configure CORS middleware

### Phase 2: SSE Streaming
- [ ] Implement `/api/fit-check/stream` endpoint
- [ ] Create `_format_sse()` helper function
- [ ] Set up StreamingResponse with proper headers
- [ ] Test SSE connection from frontend

### Phase 3: Callback Integration
- [ ] Create `StreamingCallbackHandler` class
- [ ] Implement `on_tool_start` for thought events
- [ ] Implement `on_tool_end` for observation events
- [ ] Implement `on_llm_new_token` for response streaming

### Phase 4: Error Handling
- [ ] Define error codes and messages
- [ ] Implement error event emission
- [ ] Add request validation
- [ ] Implement timeout handling

### Phase 5: Production Readiness
- [ ] Add rate limiting middleware
- [ ] Set up logging configuration
- [ ] Write unit tests
- [ ] Create Docker configuration
- [ ] Document API endpoints

---

## 13. Frontend Integration Notes

### EventSource Usage (Browser)
```javascript
const eventSource = new EventSource('/api/fit-check/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Google' })
});

// Note: Native EventSource only supports GET.
// For POST, use fetch with ReadableStream or a library like sse.js
```

### Recommended: Fetch with ReadableStream
```javascript
async function streamFitCheck(query) {
  const response = await fetch('/api/fit-check/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, include_thoughts: true })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const events = parseSSE(chunk);
    
    for (const event of events) {
      handleEvent(event.type, event.data);
    }
  }
}

function parseSSE(chunk) {
  const events = [];
  const lines = chunk.split('\n');
  let currentEvent = {};

  for (const line of lines) {
    if (line.startsWith('event:')) {
      currentEvent.type = line.slice(7).trim();
    } else if (line.startsWith('data:')) {
      currentEvent.data = JSON.parse(line.slice(6));
      events.push(currentEvent);
      currentEvent = {};
    }
  }

  return events;
}
```

---

## Summary

This backend API provides a robust, production-ready streaming interface for the "See if I'm fit for you!" feature. Key characteristics:

1. **Real-time Streaming:** SSE-based streaming for immediate feedback
2. **Transparent AI:** Visible thinking process builds trust with employers
3. **Error Resilience:** Comprehensive error handling with meaningful messages
4. **Scalable:** Stateless design supports horizontal scaling
5. **Testable:** Clean separation of concerns for easy testing
