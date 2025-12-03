# Interactive Resume Website - Technical Specification

> **Single Point of Truth** for the Interactive Resume Portfolio with AI-Powered Fit Check Feature

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Backend (res_backend)](#backend-res_backend)
4. [Frontend (res_web)](#frontend-res_web)
5. [API Contract](#api-contract)
6. [Deployment](#deployment)
7. [Environment Variables](#environment-variables)

---

## 🎯 Project Overview

An interactive portfolio website featuring an **AI-powered "See if I'm fit for you!"** chatbot that allows employers to:
1. Enter a company name or job description
2. Watch the AI agent research and analyze in real-time
3. Receive a personalized fit analysis with skill matching

### Key Features
- **Real-time SSE streaming** of AI thinking process
- **LangGraph ReAct agent** with web search and skill/experience analysis tools
- **Dark/Light theme** support
- **Animated particle backgrounds** and interactive grid dots
- **Static site export** for Sevalla deployment

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (res_web)                       │
│                    Next.js 14 Static Export                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   page.js   │  │FitCheckSection│  │  useFitCheck Hook     │  │
│  │  (Sections) │  │  (Chatbot)  │  │  (SSE Client)          │  │
│  └─────────────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└──────────────────────────┼─────────────────────┼────────────────┘
                           │ POST /api/fit-check/stream
                           ▼                     │
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND (res_backend)                    │
│                     FastAPI + LangGraph Agent                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  server.py  │  │  Router     │  │   FitCheckAgent         │  │
│  │  (FastAPI)  │──│ fit_check.py│──│   (LangGraph ReAct)     │  │
│  └─────────────┘  └─────────────┘  └───────────┬─────────────┘  │
│                                                │                 │
│  ┌────────────────────────────────────────────┼────────────────┐│
│  │                    TOOLS                    ▼                ││
│  │ ┌────────────┐ ┌──────────────┐ ┌────────────────────────┐ ││
│  │ │ web_search │ │skill_matcher │ │ experience_matcher     │ ││
│  │ │(Google CSE)│ │              │ │                        │ ││
│  │ └────────────┘ └──────────────┘ └────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🐍 Backend (res_backend)

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | ≥0.110.0 |
| Server | Uvicorn | ≥0.27.0 |
| AI Framework | LangChain + LangGraph | ≥0.3.0 / ≥0.2.0 |
| LLM Provider | Google Gemini (via langchain-google-genai) | ≥2.1.0 |
| Web Search | Google Custom Search Engine | via langchain-google-community |
| Containerization | Docker (multi-stage build) | Python 3.11-slim-bookworm |

### Directory Structure

```
res_backend/
├── server.py                 # FastAPI application entry point
├── Dockerfile                # Multi-stage production Docker build
├── docker-compose.yml        # Local development orchestration
├── requirements.txt          # Python dependencies
├── pytest.ini                # Test configuration
│
├── config/
│   ├── __init__.py
│   ├── engineer_profile.py   # Engineer skills/experience data
│   └── llm.py                # Google Gemini LLM configuration
│
├── models/
│   ├── __init__.py
│   └── fit_check.py          # Pydantic request/response models
│
├── prompts/
│   ├── __init__.py
│   └── fit_check_system.txt  # System prompt template
│
├── routers/
│   ├── __init__.py
│   └── fit_check.py          # SSE streaming endpoint router
│
├── services/
│   ├── __init__.py
│   ├── fit_check_agent.py    # LangGraph ReAct agent implementation
│   ├── streaming_callback.py # SSE event formatter and queue handler
│   └── tools/
│       ├── __init__.py
│       ├── web_search.py         # Google CSE web search tool
│       ├── skill_matcher.py      # Skill alignment analysis tool
│       └── experience_matcher.py # Experience relevance analysis tool
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_fit_check_agent.py
    └── test_integration.py
```

---

### Module Specifications

#### `server.py` - FastAPI Application Entry Point

**Purpose**: Main application entry point, CORS configuration, and router registration.

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check for load balancers |
| POST | `/api/fit-check/stream` | SSE streaming fit analysis (via router) |
| GET | `/api/fit-check/health` | Fit check service health |

**Key Features**:
- Lifespan context manager for startup/shutdown events
- CORS middleware configured via `ALLOWED_ORIGINS` env var
- Auto-reload enabled for development

---

#### `config/llm.py` - LLM Configuration

**Purpose**: Factory functions for Google Gemini LLM instances.

**Configuration**:
| Parameter | Default | Env Override |
|-----------|---------|--------------|
| Model | `gemini-flash-latest` | `GEMINI_MODEL` |
| Temperature | 0.7 | - |
| Max Output Tokens | 2048 | - |

**Function**: `get_llm(streaming, temperature, max_output_tokens)`
- Returns configured `ChatGoogleGenerativeAI` instance
- Raises `ValueError` if `GOOGLE_API_KEY` not set

---

#### `config/engineer_profile.py` - Engineer Data Configuration

**Purpose**: Stores and formats the engineer's profile for AI prompts.

**Data Structure** (`ENGINEER_PROFILE`):
```python
{
    "name": "Software Engineer",
    "education": "B.S. in Computer Science",
    "skills": {
        "languages": ["Python", "JavaScript", "TypeScript", "SQL", "HTML/CSS"],
        "frameworks": ["React", "Next.js", "FastAPI", "Node.js", "TailwindCSS"],
        "cloud_devops": ["Docker", "AWS", "PostgreSQL", "Redis", "CI/CD"],
        "ai_ml": ["LangChain", "LangGraph", "OpenAI API", "Google Gemini", "RAG Systems", "Prompt Engineering"],
        "tools": ["Git", "VS Code", "Linux", "REST APIs", "GraphQL"]
    },
    "experience_summary": "...",
    "notable_projects": [...],
    "strengths": [...],
    "career_interests": [...]
}
```

**Helper Functions**:
- `get_formatted_profile()` - Returns formatted string for system prompt
- `get_skills_list()` - Flat list of all skills
- `get_skills_by_category()` - Dict of skills by category
- `get_experience_summary()` - Experience summary text

---

#### `models/fit_check.py` - Pydantic Models

**Purpose**: Request/response models for the SSE streaming API.

**Request Model**:
```python
class FitCheckRequest(BaseModel):
    query: str       # 3-2000 chars, company name or job description
    include_thoughts: bool = True
```

**SSE Event Models (Canonical Format)**:

| Event Type | Model | Key Fields |
|------------|-------|------------|
| `status` | `StatusEvent` | `status` (connecting/researching/analyzing/generating), `message` |
| `thought` | `ThoughtEvent` | `step`, `type` (tool_call/observation/reasoning), `tool`, `input`, `content` |
| `response` | `ResponseEvent` | `chunk` (streaming text) |
| `complete` | `CompleteEvent` | `duration_ms` |
| `error` | `ErrorEvent` | `code`, `message` |

**Error Codes**:
- `INVALID_QUERY` (400) - Query too short or too long
- `RATE_LIMITED` (429) - Too many requests
- `AGENT_ERROR` (500) - AI agent execution failed
- `SEARCH_ERROR` (502) - Web search tool failed
- `LLM_ERROR` (503) - Gemini API unavailable
- `TIMEOUT` (504) - Agent execution timed out

---

#### `services/fit_check_agent.py` - LangGraph ReAct Agent

**Purpose**: Implements the AI agent using LangGraph's state machine pattern.

**State Definition** (`FitCheckState`):
```python
class FitCheckState(TypedDict):
    messages: List[BaseMessage]      # Conversation history
    query: str                        # Original user query
    query_type: Optional[str]        # 'company' or 'job_position'
    research_results: Optional[str]
    skill_analysis: Optional[str]
    experience_analysis: Optional[str]
    step_count: int                  # For thought tracking
    final_response: Optional[str]
    error: Optional[str]
```

**Graph Architecture**:
```
[START] → [agent] ─┬─ tool_calls? → [tools] → [agent]
                   └─ no tool_calls → [END]
```

**Nodes**:
- `agent_node`: Invokes LLM with tools bound, emits thoughts via callback
- `tool_node`: Executes tool calls, emits observations via callback

**Class**: `FitCheckAgent`
- `analyze(query)` - Non-streaming analysis
- `stream_analysis(query, callback)` - Streaming with ThoughtCallback

**Singleton**: `get_agent()` returns cached instance

---

#### `services/streaming_callback.py` - SSE Event Formatter

**Purpose**: Converts agent events to SSE format and queues for streaming.

**Class**: `StreamingCallbackHandler(ThoughtCallback)`

**Methods**:
- `on_status(status, message)` - Emit status event
- `on_thought(step, thought_type, content, tool, tool_input)` - Emit thought event
- `on_response_chunk(chunk)` - Emit response chunk
- `on_complete(duration_ms)` - Emit complete and close stream
- `on_error(code, message)` - Emit error and close stream
- `events()` - Async generator yielding SSE strings

**SSE Format**: `event: {type}\ndata: {json}\n\n`

---

#### `services/tools/web_search.py` - Web Search Tool

**Purpose**: Search the web using Google Custom Search Engine.

**Function**: `@tool web_search(query: str) -> str`

**Behavior**:
- Uses `GoogleSearchAPIWrapper` from langchain-google-community
- Returns top 5 results, truncated to 1500 chars
- Fallback responses for common companies if CSE not configured

**Required Env Vars**: `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ID`

---

#### `services/tools/skill_matcher.py` - Skill Analysis Tool

**Purpose**: Match engineer skills against job requirements.

**Function**: `@tool analyze_skill_match(requirements: str) -> str`

**Matching Logic**:
- Direct match: skill name appears in requirements
- Alias match: related terms (e.g., "py" → Python)
- Partial match: soft skills like "agile", "testing"

**Output**: Formatted markdown with matched skills by category

---

#### `services/tools/experience_matcher.py` - Experience Analysis Tool

**Purpose**: Evaluate experience relevance to employer context.

**Function**: `@tool analyze_experience_relevance(context: str) -> str`

**Matching Logic**:
- Domain patterns: AI, fintech, SaaS, startup, cloud, etc.
- Project relevance: AI agent, web platform, RAG system, API development

**Output**: Formatted markdown with relevant domains and projects

---

#### `routers/fit_check.py` - SSE Streaming Router

**Purpose**: API router for the fit check endpoint.

**Endpoint**: `POST /api/fit-check/stream`

**Response**: `StreamingResponse` with `media_type="text/event-stream"`

**Headers**:
```
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no  # Disable nginx buffering
```

**Flow**:
1. Create `StreamingCallbackHandler`
2. Start agent in async task
3. Yield events from callback queue
4. Map exceptions to error codes

---

#### `prompts/fit_check_system.txt` - System Prompt Template

**Purpose**: Defines agent behavior and response format.

**Template Variables**: `{engineer_profile}`

**Agent Process**:
1. Classify Query (company name vs job description)
2. Research Phase (web search)
3. Analysis Phase (skill + experience matching)
4. Response Phase (generate personalized pitch)

**Response Structure**:
```markdown
### Why I'm a Great Fit for [Company/Position]

**Key Alignments:**
- [Specific skill/experience → Company need]

**What I Bring:**
[2-3 sentences on unique value proposition]

**Growth Areas:**
[1-2 sentences on areas for growth, framed positively]

**Let's Connect:**
[Friendly call-to-action]
```

**Guidelines**: Max 400 words, always use tools, no fabrication

---

## ⚛️ Frontend (res_web)

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 14.2.3 |
| UI Library | React | ^18 |
| Styling | TailwindCSS + tailwindcss-animate | Latest |
| Component Library | Radix UI | Various |
| Icons | Lucide React | ^0.516.0 |
| Theme | next-themes | ^0.4.6 |
| Build Output | Static Export | `output: 'export'` |

### Directory Structure

```
res_web/
├── next.config.js            # Next.js configuration (static export)
├── package.json              # Dependencies and scripts
├── tailwind.config.js        # TailwindCSS with custom theme
├── postcss.config.js         # PostCSS configuration
├── components.json           # shadcn/ui configuration
│
├── app/
│   ├── layout.js             # Root layout with ThemeProvider
│   ├── page.js               # Main page with all sections
│   └── globals.css           # Global styles and CSS variables
│
├── components/
│   ├── FitCheckSection.jsx   # AI chatbot interface (phase orchestrator)
│   ├── ThinkingTimeline.jsx  # AI thoughts display
│   ├── ThoughtNode.jsx       # Individual thought step
│   ├── ParticleBackground.jsx # Animated particle canvas
│   ├── InteractiveGridDots.jsx # Interactive dot grid
│   ├── CardGridDots.jsx      # Card background dots
│   ├── HeroGridDots.jsx      # Hero section dots
│   ├── fit-check/            # Fit Check sub-components
│   │   ├── index.js          # Component exports
│   │   ├── InputPanel.jsx    # Text input with loading overlay
│   │   ├── ThinkingPanel.jsx # Expandable thinking panel
│   │   ├── ResultsSection.jsx # Two-column results container
│   │   ├── StrengthsCard.jsx # Pros/strengths card (teal)
│   │   └── GrowthAreasCard.jsx # Growth areas card (apricot)
│   └── ui/                   # shadcn/ui components
│       ├── button.jsx
│       ├── dialog.jsx
│       └── textarea.jsx
│
├── hooks/
│   ├── use-fit-check.js      # SSE client state machine
│   └── use-header-visibility.js # Scroll-based header visibility
│
└── lib/
    ├── utils.js              # Utility functions (cn)
    ├── particleConfig.js     # Particle animation constants
    └── parseAIResponse.js    # AI response parser for structured display
```

---

### Module Specifications

#### `next.config.js` - Next.js Configuration

**Purpose**: Configure static site export.

```javascript
const nextConfig = {
  output: 'export',           // Static HTML export
  images: { unoptimized: true },
  trailingSlash: false,
};
```

---

#### `app/layout.js` - Root Layout

**Purpose**: HTML structure and theme provider.

**Features**:
- `ThemeProvider` with class-based dark mode
- System theme detection
- HTML lang attribute

---

#### `app/page.js` - Main Page

**Purpose**: Single-page portfolio with all sections.

**Sections** (in order):
1. `Header` - Fixed navigation with theme toggle
2. `HeroAboutSection` - Hero intro + About me
3. `FitCheckSection` - AI chatbot
4. `ProjectsSection` - Featured projects grid
5. `ExperienceSection` - Work experience timeline
6. `ContactSection` - CTA with email
7. `Footer` - Links and copyright

**Page-Level Components**:
- `AnimatedShapes` - Background morphing blobs

---

#### `components/FitCheckSection.jsx` - AI Chatbot Interface

**Purpose**: Main orchestrator for the AI fit check feature with phase-based UI transitions.

**UI Phases**:
| Phase | Status | Layout |
|-------|--------|--------|
| `input` | idle | Single centered container with input form |
| `expanded` | connecting/thinking/responding | Two-column: Input (left) + Thinking Panel (right) |
| `results` | complete | Compact header + Two result cards below |

**Features**:
- Phase-based layout switching with smooth transitions
- Container width animation (max-w-2xl → max-w-5xl)
- Imports sub-components: `InputPanel`, `ThinkingPanel`, `ResultsSection`
- Error display with retry option
- Duration display on completion

**Uses**: `useFitCheck` hook for state management

---

#### `components/fit-check/InputPanel.jsx` - Input Form

**Purpose**: Text input with loading overlay and submit button.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `value` | string | Current input value |
| `onChange` | function | Input change handler |
| `onSubmit` | function | Form submit handler |
| `isDisabled` | boolean | Whether input is disabled |
| `isLoading` | boolean | Show spinning wheel overlay |
| `statusMessage` | string | Current status message |
| `uiPhase` | string | Current UI phase |

**Features**:
- Spinning wheel overlay when loading
- Character count display
- Glowing submit button animation

---

#### `components/fit-check/ThinkingPanel.jsx` - Thinking Panel

**Purpose**: Expandable right panel showing AI thinking process.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `thoughts` | Array | Array of thought events |
| `isThinking` | boolean | Whether AI is currently thinking |
| `isVisible` | boolean | Controls panel visibility |
| `status` | string | Current status (connecting/thinking/responding) |
| `statusMessage` | string | Current status message |

**Features**:
- Animated panel expansion from left
- Embedded `ThinkingTimeline` with `hideHeader` mode
- Status indicator dots

---

#### `components/fit-check/ResultsSection.jsx` - Results Container

**Purpose**: Two-column grid container for result cards.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `parsedResponse` | Object | Parsed AI response with structured sections |
| `durationMs` | number | Analysis duration in milliseconds |
| `isVisible` | boolean | Controls visibility/animation |

**Features**:
- Staggered card animation entry
- Title and duration header
- Responsive grid (stacks on mobile)

---

#### `components/fit-check/StrengthsCard.jsx` - Strengths Card

**Purpose**: Displays matched skills and strengths with teal/green theme.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `title` | string | Card title (default: "Key Strengths") |
| `strengths` | Array | Array of strength items |
| `valueProposition` | string | Optional value proposition text |
| `isVisible` | boolean | Controls animation |

**Features**:
- Glassmorphism background
- Gradient border animation
- Shimmer effect
- Hover lift effect

---

#### `components/fit-check/GrowthAreasCard.jsx` - Growth Areas Card

**Purpose**: Displays growth opportunities with apricot/amber theme.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `title` | string | Card title (default: "Growth Opportunities") |
| `growthAreas` | Array | Array of growth area items |
| `callToAction` | string | Optional CTA text |
| `isVisible` | boolean | Controls animation |

**Features**:
- Glassmorphism background
- Gradient border animation
- Staggered list item animation
- Delayed card entry animation

---

#### `components/ThinkingTimeline.jsx` - Thoughts Timeline

**Purpose**: Collapsible timeline showing AI thinking steps.

**Props**:
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `thoughts` | Array | `[]` | Thought events from SSE |
| `isThinking` | boolean | `false` | Show active thinking state |
| `defaultExpanded` | boolean | `true` | Initial expanded state |
| `hideHeader` | boolean | `false` | Hide collapsible header (for embedded use) |

**Features**:
- Auto-scroll to latest thought
- Animated thinking dots
- Expand/collapse toggle
- Headerless mode for ThinkingPanel integration

---

#### `components/ThoughtNode.jsx` - Individual Thought

**Purpose**: Render a single AI thought step.

**Thought Types**:
| Type | Icon | Label | Color |
|------|------|-------|-------|
| `tool_call` | Dynamic by tool | Research | burnt-peach |
| `observation` | Eye | Observation | muted-teal |
| `reasoning` | Brain | Reasoning | twilight/apricot |

**Tool Icons**:
- `web_search` → Search
- `analyze_skill_match` → Briefcase
- `analyze_experience_relevance` → Briefcase

---

#### `hooks/use-fit-check.js` - SSE Client Hook

**Purpose**: Manage fit check state, SSE streaming, and UI phase transitions.

**State Machine States**:
```
idle → connecting → thinking → responding → complete
                  ↘ error
```

**UI Phases** (derived from status):
| Status | UI Phase |
|--------|----------|
| idle | input |
| connecting/thinking/responding | expanded |
| complete | results |
| error (with thoughts) | expanded |
| error (no thoughts) | input |

**State Shape**:
```javascript
{
  status: 'idle',         // State machine status
  statusMessage: '',      // Human-readable message
  thoughts: [],           // Array of thought events
  response: '',           // Accumulated response text
  error: null,            // { code, message }
  durationMs: null,       // Total duration
}
```

**Derived State**:
- `uiPhase` - Computed UI phase (input/expanded/results)
- `parsedResponse` - Parsed response object for result cards

**Functions**:
- `submitQuery(query)` - Start SSE stream
- `reset()` - Clear state for new query

**SSE Parsing**:
- `parseSSEBuffer(buffer)` - Parse events from raw buffer
- `processEvent(event, setState)` - Update state per event type

**Status Mapping**:
| Backend Status | Frontend State |
|----------------|----------------|
| connecting | connecting |
| researching | thinking |
| analyzing | thinking |
| generating | responding |

---

#### `lib/parseAIResponse.js` - Response Parser

**Purpose**: Parse AI response markdown into structured data for result cards.

**Function**: `parseAIResponse(rawResponse)`

**Returns**:
```javascript
{
  title: '',           // "Why I'm a Great Fit for..."
  strengths: [],       // Array of strength strings
  valueProposition: '', // Overview text
  growthAreas: [],     // Array of growth area strings
  callToAction: '',    // Final call-to-action text
  rawContent: ''       // Original response
}
```

**Parsing Logic**:
- Detects `###` headers for title
- Detects `**Header:**` patterns for sections
- Extracts bullet points (`-`, `•`, `*`)
- Categorizes sections by keywords (strengths, growth, connect)

---

#### `hooks/use-header-visibility.js` - Header Scroll Hook

**Purpose**: Control header visibility based on scroll.

**Behavior**:
- Hides after scrolling down past `hideThreshold` (default: 100px)
- Shows immediately on any upward scroll
- Tracks `isAtTop` for styling

**Returns**: `{ isVisible, isAtTop }`

---

#### `components/ParticleBackground.jsx` - Animated Particles

**Purpose**: Canvas-based particle animation.

**Configuration** (from `lib/particleConfig.js`):
| Constant | Value |
|----------|-------|
| `PARTICLE_COUNT` | 60 |
| `PARTICLE_COUNT_MOBILE` | 25 |
| `PARTICLE_MAX_SPEED` | 18 |
| `PARTICLE_CONNECTION_DISTANCE` | 120 |
| `MAX_CONNECTIONS_PER_PARTICLE` | 3 |
| `TARGET_FPS` | 30 |

**Features**:
- Theme-aware colors (light/dark)
- Visibility API optimization
- Reduced motion respect
- Connection lines between particles

---

#### `components/InteractiveGridDots.jsx` - Grid Dots

**Purpose**: Interactive dot grid responding to mouse movement.

**Features**:
- Dots grow near mouse cursor
- Color change on card hover
- 30 FPS animation
- Visibility API optimization

**Constants**:
- `DOT_SPACING`: 30px
- `INFLUENCE_RADIUS`: 80px

---

#### Design System (Tailwind Config)

**Custom Colors**:
| Name | Hex | Usage |
|------|-----|-------|
| `eggshell` | `#f4f1de` | Light background |
| `burnt-peach` | `#e07a5f` | Primary accent |
| `twilight` | `#3d405b` | Dark text/background |
| `muted-teal` | `#81b29a` | Secondary accent (strengths) |
| `apricot` | `#f2cc8f` | Tertiary accent (growth areas) |

**Custom Animations (Tailwind)**:
- `fade-in`, `fade-in-left`, `fade-in-right`
- `float`, `float-delayed`
- `pulse-glow`
- `gradient-shift`
- `slide-up`, `scale-in`
- `morph`, `morph-fast`
- `rotate-slow`
- `bounce-soft`
- `shimmer`

**Fit Check Animations (globals.css)**:
| Animation | Purpose |
|-----------|---------|
| `expandContainer` | Horizontal container width expansion |
| `panelExpandRight` | Thinking panel slide-in from left |
| `slideUpCard` | Result card entrance with scale |
| `dividerGrow` | Panel separator height animation |
| `staggerItemAppear` | Staggered list item reveal |
| `checkmarkPop` | Icon bounce on completion |
| `cardShimmer` | Subtle shimmer overlay effect |
| `resultsContainerEntry` | Results section fade-in |
| `connectionPulse` | Panel connection indicator pulse |

**CSS Utility Classes**:
| Class | Effect |
|-------|--------|
| `.glass-card` | Glassmorphism background blur |
| `.strengths-card-glow` | Teal glow on hover |
| `.growth-card-glow` | Apricot glow on hover |
| `.gradient-border-strengths` | Animated gradient border (teal) |
| `.gradient-border-growth` | Animated gradient border (apricot) |
| `.card-shimmer` | Shimmer sweep effect |
| `.text-glow` | Subtle text shadow glow |

---

## 📡 API Contract

### Endpoint: `POST /api/fit-check/stream`

**Request**:
```http
POST /api/fit-check/stream HTTP/1.1
Content-Type: application/json
Accept: text/event-stream

{
  "query": "Google",
  "include_thoughts": true
}
```

**Response** (SSE Stream):
```
event: status
data: {"status": "connecting", "message": "Initializing AI agent..."}

event: status
data: {"status": "researching", "message": "Analyzing your query..."}

event: thought
data: {"step": 1, "type": "tool_call", "tool": "web_search", "input": "Google engineering culture"}

event: thought
data: {"step": 2, "type": "observation", "content": "Google is a leading technology company..."}

event: thought
data: {"step": 3, "type": "tool_call", "tool": "analyze_skill_match", "input": "Python, Go, ML..."}

event: status
data: {"status": "generating", "message": "Generating response..."}

event: response
data: {"chunk": "### Why I'm a Great Fit"}

event: response
data: {"chunk": " for Google\n\n**Key Alignments:**"}

event: complete
data: {"duration_ms": 8523}
```

---

## 🚀 Deployment

### Production URLs

| Service | URL | Type |
|---------|-----|------|
| Frontend | https://resweb-w8gqi.sevalla.page | Static Site |
| Backend | https://resbackend-bxeo7.sevalla.app | Web Application |

### Backend Deployment

1. **Set environment variables** in Sevalla Dashboard
2. **Build and push Docker image**:
   ```bash
   docker build -t bassn/res_backend:latest .
   docker push bassn/res_backend:latest
   ```
3. **Verify**: `curl https://resbackend-bxeo7.sevalla.app/health`

### Frontend Deployment

1. **Copy production env**: `copy .env.deployed .env.local`
2. **Build static export**: `npm run build`
3. **Upload** `/out` folder to Sevalla static hosting

---

## 🔐 Environment Variables

### Backend (`res_backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Gemini API key |
| `GOOGLE_CSE_API_KEY` | ✅ | Google Custom Search API key |
| `GOOGLE_CSE_ID` | ✅ | Google Custom Search Engine ID |
| `HOST` | ❌ | Server host (default: `0.0.0.0`) |
| `PORT` | ❌ | Server port (default: `8000`) |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins |
| `LOG_LEVEL` | ❌ | Logging level (default: `INFO`) |
| `GEMINI_MODEL` | ❌ | Model name (default: `gemini-flash-latest`) |

### Frontend (`res_web/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_BASE_URL` | ✅ | Frontend URL |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL |

> ⚠️ `NEXT_PUBLIC_*` variables are baked into static build. Rebuild required on change.

---

## 📝 NPM Scripts

### Frontend (`res_web/package.json`)

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `next dev --hostname 0.0.0.0 --port 3000` | Development server |
| `build` | `next build` | Production build (static export to `/out`) |
| `start` | `next start` | Production server (not used for static) |

### Build Scripts

| File | Purpose |
|------|---------|
| `build_local.bat` | Local development build |
| `build_production.bat` | Production build with deployed env |

---

## 🧪 Testing

### Backend Tests

```bash
cd res_backend
pytest
```

**Test Files**:
- `tests/test_fit_check_agent.py` - Agent unit tests
- `tests/test_integration.py` - API integration tests

### Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

---

## 📚 Quick Reference

### Adding New Skills
Edit `res_backend/config/engineer_profile.py`:
```python
ENGINEER_PROFILE["skills"]["category"].append("New Skill")
```

### Modifying AI Behavior
Edit `res_backend/prompts/fit_check_system.txt`

### Adding New SSE Event Types
1. Add model in `res_backend/models/fit_check.py`
2. Add callback in `res_backend/services/streaming_callback.py`
3. Add handler in `res_web/hooks/use-fit-check.js`

### Modifying Fit Check UI Phases
1. Update `uiPhase` logic in `res_web/hooks/use-fit-check.js`
2. Update phase rendering in `res_web/components/FitCheckSection.jsx`
3. Add/modify sub-components in `res_web/components/fit-check/`

### Modifying Result Cards
- **Strengths Card**: Edit `res_web/components/fit-check/StrengthsCard.jsx`
- **Growth Areas Card**: Edit `res_web/components/fit-check/GrowthAreasCard.jsx`
- **Response Parsing**: Edit `res_web/lib/parseAIResponse.js`

### Theming
Edit `res_web/tailwind.config.js` colors and `res_web/app/globals.css` CSS variables

---

*Last Updated: December 2025*
