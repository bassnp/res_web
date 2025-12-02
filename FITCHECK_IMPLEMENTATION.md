# FitCheck AI Agent - Implementation Summary

> **"See if I'm fit for you!"** - An AI-powered feature that analyzes employer queries and provides personalized fit analysis using real-time web research and skill matching.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                                  │
│                                                                                  │
│   ┌──────────────────┐    ┌────────────────────┐    ┌─────────────────────┐    │
│   │  FitCheckSection │───▶│   useFitCheck()    │───▶│  SSE EventSource    │    │
│   │    (Component)   │    │     (Hook)         │    │   (Streaming)       │    │
│   └──────────────────┘    └────────────────────┘    └──────────┬──────────┘    │
│           │                                                     │               │
│           ▼                                                     │               │
│   ┌──────────────────┐    ┌────────────────────┐               │               │
│   │ ThinkingTimeline │    │  ResponseRenderer  │               │               │
│   │   (Component)    │    │    (Component)     │               │               │
│   └──────────────────┘    └────────────────────┘               │               │
└─────────────────────────────────────────────────────────────────┼───────────────┘
                                                                  │
                                                    HTTP POST /api/fit-check/stream
                                                                  │
┌─────────────────────────────────────────────────────────────────▼───────────────┐
│                              BACKEND (FastAPI)                                   │
│                                                                                  │
│   ┌──────────────────┐    ┌────────────────────┐    ┌─────────────────────┐    │
│   │   /api/fit-check │───▶│  FitCheckAgent     │───▶│  StreamingCallback  │    │
│   │     /stream      │    │   (LangGraph)      │    │     (SSE Emit)      │    │
│   └──────────────────┘    └─────────┬──────────┘    └─────────────────────┘    │
│                                     │                                           │
│                                     ▼                                           │
│                           ┌─────────────────┐                                   │
│                           │     TOOLS       │                                   │
│                           ├─────────────────┤                                   │
│                           │ • web_search    │ ──▶ Google Custom Search API     │
│                           │ • skill_match   │ ──▶ Engineer Profile Analysis     │
│                           │ • exp_match     │ ──▶ Experience Relevance          │
│                           └─────────────────┘                                   │
│                                     │                                           │
│                                     ▼                                           │
│                           ┌─────────────────┐                                   │
│                           │   Gemini LLM    │                                   │
│                           │ (gemini-flash)  │                                   │
│                           └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

### Frontend (`res_web/`)
```
res_web/
├── app/
│   ├── page.js                    # Main page with FitCheckSection
│   └── globals.css                # Animations (fadeIn, pulse, blink, etc.)
├── components/
│   ├── FitCheckSection.jsx        # Main chatbot container
│   ├── ThinkingTimeline.jsx       # AI reasoning timeline display
│   └── ThoughtNode.jsx            # Individual thought step
├── hooks/
│   └── use-fit-check.js           # SSE streaming & state management
└── .env.local                     # NEXT_PUBLIC_API_URL
```

### Backend (`res_web_backend/`)
```
res_web_backend/
├── server.py                      # FastAPI entry point
├── config/
│   ├── llm.py                     # Gemini LLM configuration
│   └── engineer_profile.py        # Engineer skills/experience data
├── routers/
│   └── fit_check.py               # POST /api/fit-check/stream endpoint
├── services/
│   ├── fit_check_agent.py         # LangGraph ReAct agent
│   ├── streaming_callback.py      # SSE event emission
│   └── tools/
│       ├── web_search.py          # Google CSE integration
│       ├── skill_matcher.py       # Skill analysis tool
│       └── experience_matcher.py  # Experience analysis tool
├── models/
│   └── fit_check.py               # Pydantic request/response models
├── prompts/
│   └── fit_check_system.txt       # System prompt for AI agent
├── .env                           # API keys (GOOGLE_API_KEY, CSE keys)
├── Dockerfile                     # Multi-stage Docker build
├── docker-compose.yml             # Container orchestration
└── run_server.bat                 # Quick restart script
```

---

## 🔄 Data Flow

### 1. User Submits Query
```javascript
// Frontend: FitCheckSection.jsx
const handleSubmit = (e) => {
  e.preventDefault();
  submitQuery(input.trim());  // "Google" or "Looking for Python AI engineer..."
};
```

### 2. SSE Connection Established
```javascript
// Frontend: use-fit-check.js
const response = await fetch(`${API_URL}/api/fit-check/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query, include_thoughts: true }),
});
```

### 3. Backend Processes with AI Agent
```python
# Backend: fit_check_agent.py
async for event in self.graph.astream(current_state):
    # Agent reasons → calls tools → observes → reasons again
    # Emits thoughts via callback
    await callback.on_thought(step=1, thought_type="tool_call", tool="web_search")
```

### 4. SSE Events Streamed
```
event: status
data: {"status": "researching", "message": "Analyzing your query..."}

event: thought
data: {"step": 1, "type": "tool_call", "tool": "web_search", "input": "..."}

event: thought
data: {"step": 2, "type": "observation", "content": "Found company info..."}

event: response
data: {"chunk": "### Why I'm a Great Fit for Google\n\n"}

event: complete
data: {"duration_ms": 14500}
```

### 5. Frontend Renders in Real-Time
```javascript
// Frontend: use-fit-check.js - processEvent()
case 'thought':
  setState(prev => ({
    ...prev,
    thoughts: [...prev.thoughts, event.data],  // Timeline updates
  }));
  break;

case 'response':
  setState(prev => ({
    ...prev,
    response: prev.response + event.data.chunk,  // Typewriter effect
  }));
  break;
```

---

## 🛠️ Key Components

### Frontend

#### `useFitCheck()` Hook
**State Machine:**
```
idle → connecting → thinking → responding → complete
                                    ↓
                                  error
```

**Exposed State:**
```javascript
{
  status: 'idle' | 'connecting' | 'thinking' | 'responding' | 'complete' | 'error',
  statusMessage: string,
  thoughts: Array<{ step, type, tool?, content?, input? }>,
  response: string,
  error: { code, message } | null,
  durationMs: number | null,
}
```

#### `ThinkingTimeline` Component
- Displays AI reasoning steps in vertical timeline
- Auto-scrolls to latest thought
- Supports expand/collapse
- Shows loading skeleton during active thinking

#### `ResponseRenderer` Component
- Parses markdown-like formatting (headers, bold, bullets)
- Displays streaming cursor during response generation
- Handles `**bold**`, `### headers`, `- bullets`

### Backend

#### `FitCheckAgent` (LangGraph)
**ReAct Pattern:**
```
Query → Reason → Tool Call → Observe → Reason → ... → Final Response
```

**Tools:**
| Tool | Purpose |
|------|---------|
| `web_search` | Google Custom Search for company/job info |
| `analyze_skill_match` | Match engineer skills to requirements |
| `analyze_experience_relevance` | Evaluate experience alignment |

#### `StreamingCallbackHandler`
- Implements `ThoughtCallback` interface
- Queues SSE events for async streaming
- Formats events as `event: type\ndata: {json}\n\n`

---

## 🔌 API Contract

### `POST /api/fit-check/stream`

**Request:**
```json
{
  "query": "Google",           // 3-2000 characters
  "include_thoughts": true     // Optional, default true
}
```

**Response:** `text/event-stream`

**SSE Events:**

| Event | Data | Description |
|-------|------|-------------|
| `status` | `{status, message}` | Agent status update |
| `thought` | `{step, type, tool?, content?, input?}` | AI reasoning step |
| `response` | `{chunk}` | Response text chunk |
| `complete` | `{duration_ms}` | Stream finished |
| `error` | `{code, message}` | Error occurred |

**Error Codes:**
- `INVALID_QUERY` - Query validation failed
- `AGENT_ERROR` - AI agent processing error
- `SEARCH_ERROR` - Web search failed
- `LLM_ERROR` - Gemini API error
- `TIMEOUT` - Request timeout
- `CONNECTION_ERROR` - Network error

---

## ⚙️ Configuration

### Environment Variables

**Backend (`.env`):**
```env
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CSE_API_KEY=your_cse_api_key
GOOGLE_CSE_ID=your_cse_id
GEMINI_MODEL=gemini-flash-latest
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

**Frontend (`.env.local`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Engineer Profile (`config/engineer_profile.py`)
```python
ENGINEER_PROFILE = {
    "skills": {
        "languages": ["Python", "JavaScript", "TypeScript"],
        "ai_ml": ["LangChain", "LangGraph", "RAG Systems", "Gemini"],
        "backend": ["FastAPI", "Node.js", "PostgreSQL"],
        "frontend": ["React", "Next.js", "Tailwind CSS"],
        # ...
    },
    "experience": [...],
    "projects": [...],
}
```

---

## 🚀 Running the System

### Backend (Docker)
```bash
cd res_web_backend
.\run_server.bat          # Windows: Rebuild & restart
# OR
docker-compose up --build -d
```

### Frontend
```bash
cd res_web
npm run dev
```

### Health Checks
```bash
# Main health
curl http://localhost:8000/health

# Fit-check service health
curl http://localhost:8000/api/fit-check/health
```

---

## 🧪 Testing

### Diagnostic Test Suite
```bash
cd res_web_backend
python diagnostic_test.py
```

**Tests:**
- ✅ Health Check Endpoints (3 tests)
- ✅ Request Validation (5 tests)
- ✅ SSE Headers (2 tests)
- ✅ SSE Stream Parsing (7 tests)
- ✅ Full End-to-End Flow (4 tests)
- ✅ Include Thoughts Flag (1 test)

**Result:** 22/22 tests passing

---

## 🎨 UI/UX Features

### Animations (`globals.css`)
- `fadeInUp` - Section entrance
- `thoughtAppear` - Thought node slide-in
- `thoughtGlow` - Active thought highlight
- `pulse` - Thinking indicator dots
- `blink` - Streaming cursor effect
- `pulseGlow` - Submit button glow

### Theme Integration
- Uses existing `burnt-peach`, `twilight`, `eggshell` colors
- `InteractiveGridDots` background pattern
- Responsive design (mobile-first)
- Dark mode support

---

## 🐛 Issues Fixed

### 1. Docker Health Check Failure
**Problem:** `docker-compose.yml` used `curl` but slim Python image doesn't include it.
**Fix:** Changed to Python-based health check:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
```

### 2. Response Displayed as `[object Object]`
**Problem:** Gemini API returns content as structured objects `[{"type": "text", "text": "..."}]`
**Fix:** Extract text from content blocks in `fit_check_agent.py`:
```python
if isinstance(content, list):
    text_parts = []
    for part in content:
        if isinstance(part, dict) and part.get("type") == "text":
            text_parts.append(part.get("text", ""))
    content = "".join(text_parts)
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Average Response Time | 12-18 seconds |
| Response Length | 1500-2000 chars |
| Thought Steps | 6-8 steps |
| Web Searches | 1-2 per query |

---

## 📝 Future Improvements

- [ ] Add rate limiting middleware
- [ ] Implement response caching for common queries
- [ ] Add user feedback mechanism
- [ ] Support for follow-up questions
- [ ] Analytics/telemetry for query patterns
- [ ] Production deployment (Vercel + Railway/Fly.io)

---

*Last Updated: December 2, 2025*
