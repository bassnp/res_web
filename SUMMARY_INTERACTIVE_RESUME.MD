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
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │   page.js   │  │FitCheckSection│  │  useFitCheck Hook     │  │
│  │  (Sections) │  │ ComparisonChain│  │  (SSE Client)        │  │
│  └─────────────┘  └───────┬───────┘  └───────────┬───────────┘  │
└───────────────────────────┼──────────────────────┼──────────────┘
                            │ POST /api/fit-check/stream
                            ▼                      │
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (res_backend)                         │
│                FastAPI + LangGraph State Machine                 │
│  ┌──────────┐  ┌─────────────┐  ┌────────────────────────────┐  │
│  │ server.py│  │  Router     │  │   FitCheckAgent            │  │
│  │ (FastAPI)│──│fit_check.py │──│   (7-Phase Pipeline)       │  │
│  └──────────┘  └─────────────┘  └─────────────┬──────────────┘  │
│                                               │                  │
│  ┌────────────────────────────────────────────┼────────────────┐│
│  │              PIPELINE PHASES               ▼                ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐││
│  │ │ 1.connecting│→│2.deep_research│→│2B.research_reranker  │││
│  │ │(classification)│ │(web search) │ │ (quality gate)       │││
│  │ └─────────────┘ └─────────────┘ └─────────────────────────┘││
│  │                                         │                   ││
│  │                      ┌──────────────────┘                   ││
│  │                      ▼                                      ││
│  │ ┌─────────────────────────────────────────────────────────┐││
│  │ │ 3.skeptical_comparison → 4.skills_matching             │││
│  │ │  (critical gap analysis)   (skill-to-req mapping)      │││
│  │ └─────────────────────────────────────────────────────────┘││
│  │                      │                                      ││
│  │                      ▼                                      ││
│  │ ┌─────────────────────────────────────────────────────────┐││
│  │ │ 5B.confidence_reranker → 6.generate_results            │││
│  │ │  (LLM-as-Judge calibration) (final response synthesis) │││
│  │ └─────────────────────────────────────────────────────────┘││
│  │                                                             ││
│  │ ┌─────────────────────────────────────────────────────────┐││
│  │ │                    TOOLS                                │││
│  │ │  web_search (Google CSE)  │  skills_db (engineer data)  │││
│  │ └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow Diagram

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: CONNECTING (Query Classification)                      │
│ • Classify query type (company/job_position)                    │
│ • Extract entities (company_name, job_title)                    │
│ • Early rejection: prompt injection, irrelevant queries         │
│ • Route: EARLY_EXIT or → deep_research                          │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: DEEP RESEARCH (Web Intelligence Gathering)             │
│ • Execute strategic web searches via Google CSE                 │
│ • Extract: tech stack, culture, requirements, values            │
│ • Build company profile from search results                     │
│ • Route: → research_reranker                                    │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2B: RESEARCH RERANKER (Quality Gate)                      │
│ • Validate research completeness (0-100 data score)             │
│ • Assess data quality tier (HIGH/ACCEPTABLE/LOW)                │
│ • Prune unreliable sources, flag missing data                   │
│ • Route: ENHANCE_SEARCH (retry) or → skeptical_comparison       │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: SKEPTICAL COMPARISON (Critical Analysis)               │
│ • Compare engineer profile against employer requirements        │
│ • Identify genuine gaps (not just missing info)                 │
│ • Classify risk level (low/medium/high/critical)                │
│ • Generate calibrated initial confidence score                  │
│ • Route: INSUFFICIENT_DATA (exit) or → skills_matching          │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: SKILLS MATCHING (Skill-to-Requirement Mapping)         │
│ • Match engineer skills to job requirements                     │
│ • Calculate match percentages per category                      │
│ • Identify transferable skills and learning gaps                │
│ • Generate detailed skill alignment analysis                    │
│ • Route: → confidence_reranker                                  │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5B: CONFIDENCE RERANKER (LLM-as-Judge Calibration)        │
│ • Meta-cognitive review of all prior phase outputs              │
│ • Detect reasoning flaws, score inflation, contradictions       │
│ • Adjust confidence with explicit audit trail                   │
│ • Flag quality issues for response generation                   │
│ • Route: → generate_results                                     │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: GENERATE RESULTS (Final Response Synthesis)            │
│ • Synthesize all phase outputs into coherent narrative          │
│ • Apply confidence-appropriate framing (hedging for low conf)   │
│ • Structure: summary → alignments → gaps → CTA                  │
│ • Maintain honest, calibrated tone based on reranker output     │
│ • Route: END                                                    │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
 END
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
├── prompts/                  # XML prompt templates for each phase
│   ├── __init__.py
│   ├── phase_1_connecting.xml         # Query classification prompt
│   ├── phase_2_deep_research.xml      # Web research prompt
│   ├── phase_2b_research_reranker.xml # Research quality gate prompt
│   ├── phase_3_skeptical_comparison.xml # Gap analysis prompt
│   ├── phase_4_skills_matching.xml    # Skill matching prompt
│   ├── phase_5_generate_results.xml   # Response generation prompt
│   └── phase_5b_confidence_reranker.xml # LLM-as-Judge prompt
│
├── routers/
│   ├── __init__.py
│   ├── fit_check.py          # SSE streaming endpoint router
│   └── prompts.py            # Prompt transparency API router (NEW)
│
├── services/
│   ├── __init__.py
│   ├── fit_check_agent.py    # LangGraph 7-phase pipeline orchestrator
│   ├── pipeline_state.py     # TypedDict state definitions
│   ├── streaming_callback.py # SSE event formatter and queue handler
│   ├── callbacks.py          # Callback handlers for streaming
│   ├── utils.py              # Utility functions
│   ├── nodes/                # LangGraph node implementations
│   │   ├── __init__.py
│   │   ├── connecting.py            # Phase 1: Query classification
│   │   ├── deep_research.py         # Phase 2: Web research
│   │   ├── research_reranker.py     # Phase 2B: Quality gate
│   │   ├── skeptical_comparison.py  # Phase 3: Gap analysis
│   │   ├── skills_matching.py       # Phase 4: Skill matching
│   │   ├── confidence_reranker.py   # Phase 5B: LLM-as-Judge
│   │   └── generate_results.py      # Phase 6: Response synthesis
│   └── tools/
│       ├── __init__.py
│       ├── web_search.py     # Google CSE web search tool
│       └── skills_db.py      # Engineer profile database
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_fit_check_agent.py
    ├── test_integration.py
    ├── unit/                 # Unit tests
    │   └── ...
    └── simulation/           # Frontend simulation tests
        ├── simulate_full_pipeline.py  # Full SSE simulation
        ├── analyze_ai_outputs.py      # Quality metrics analyzer
        └── outputs/                   # Test output JSON files
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
    model_id: Optional[str] = "gemini-3-pro-preview"  # AI model to use
    config_type: Optional[Literal["reasoning", "standard"]] = "reasoning"  # Model config type
```

**SSE Event Models (Canonical Format)**:

| Event Type | Model | Key Fields |
|------------|-------|------------|
| `phase` | `PhaseEvent` | `phase` (phase name), `message` (status text) |
| `phase_complete` | `PhaseCompleteEvent` | `phase`, `summary` (phase result summary), `duration_ms` |
| `thought` | `ThoughtEvent` | `step`, `type` (tool_call/observation/reasoning), `tool`, `input`, `content`, `phase` |
| `response` | `ResponseEvent` | `chunk` (streaming text) |
| `complete` | `CompleteEvent` | `duration_ms`, `confidence_score` |
| `error` | `ErrorEvent` | `code`, `message` |

**Phase Names**:
| Phase | Display Name | Description |
|-------|--------------|-------------|
| `connecting` | Query Classification | Entity extraction and query routing |
| `deep_research` | Deep Research | Web intelligence gathering |
| `research_reranker` | Research Quality Gate | Data validation and pruning |
| `skeptical_comparison` | Critical Analysis | Gap identification and risk assessment |
| `skills_matching` | Skill Mapping | Skill-to-requirement alignment |
| `confidence_reranker` | Confidence Calibration | LLM-as-Judge meta-review |
| `generate_results` | Response Generation | Final response synthesis |

**Error Codes**:
- `INVALID_QUERY` (400) - Query too short or too long
- `RATE_LIMITED` (429) - Too many requests
- `AGENT_ERROR` (500) - AI agent execution failed
- `SEARCH_ERROR` (502) - Web search tool failed
- `LLM_ERROR` (503) - Gemini API unavailable
- `TIMEOUT` (504) - Agent execution timed out

---

#### `services/fit_check_agent.py` - LangGraph Pipeline Orchestrator

**Purpose**: Implements the 7-phase AI pipeline using LangGraph's state machine pattern.

**State Definition** (`FitCheckState` in `pipeline_state.py`):
```python
class FitCheckState(TypedDict):
    # Query info
    query: str                        # Original user query
    query_type: str                   # 'company' or 'job_position'
    company_name: Optional[str]
    job_title: Optional[str]
    
    # Research data
    search_results: List[Dict]        # Raw web search results
    research_summary: Optional[str]   # Structured research output
    
    # Analysis outputs
    comparison_result: Optional[str]  # Skeptical comparison output
    skills_match: Optional[str]       # Skills matching output
    
    # Reranker outputs
    research_reranker_output: Optional[Dict]     # Quality gate decision
    confidence_reranker_output: Optional[Dict]   # Calibrated confidence
    
    # Control flow
    search_attempt: int               # For retry logic in reranker
    current_phase: str                # Current pipeline phase
    
    # Final output
    final_response: Optional[str]     # Generated response
    confidence_score: int             # 0-100 calibrated score
    error: Optional[str]
```

**Graph Architecture**:
```
[START] 
   │
   ▼
[connecting] → route_after_connecting() → [EARLY_EXIT] or ↓
   │
   ▼
[deep_research] → [research_reranker] → route_after_reranker()
                                               │
                    ┌──────────────────────────┤
                    ▼                          ▼
            [deep_research]              [skeptical_comparison]
              (retry)                          │
                                               ▼
                                    route_after_skeptical()
                                               │
                    ┌──────────────────────────┤
                    ▼                          ▼
             [INSUFFICIENT_DATA]        [skills_matching]
                                               │
                                               ▼
                                    [confidence_reranker]
                                               │
                                               ▼
                                    [generate_results]
                                               │
                                               ▼
                                            [END]
```

**Nodes**:
| Node | Phase | Purpose |
|------|-------|---------|
| `connecting_node` | 1 | Query classification, entity extraction, early rejection |
| `deep_research_node` | 2 | Web search execution, company profile building |
| `research_reranker_node` | 2B | Research quality validation, retry/proceed decision |
| `skeptical_comparison_node` | 3 | Critical gap analysis, risk assessment |
| `skills_matching_node` | 4 | Skill-to-requirement mapping, match scoring |
| `confidence_reranker_node` | 5B | LLM-as-Judge meta-cognitive review |
| `generate_results_node` | 6 | Final response synthesis |

**Routing Functions**:
- `route_after_connecting()` - EARLY_EXIT vs continue to research
- `route_after_research_reranker()` - ENHANCE_SEARCH (retry) vs proceed
- `route_after_skeptical()` - INSUFFICIENT_DATA vs continue to matching

**Class**: `FitCheckAgent`
- `stream_analysis(query, callback)` - Streaming analysis with phase events

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

#### `routers/prompts.py` - Prompt Transparency Router (NEW)

**Purpose**: API router for retrieving system prompts used in the AI pipeline.

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prompts` | List all pipeline phases with metadata |
| GET | `/api/prompts/{phase}` | Get full prompt content for a specific phase |

**Response Models**:
- `PromptListResponse`: List of `PhaseInfo` objects with phase name, display name, description, order
- `PromptContentResponse`: Full prompt XML content with metadata

**Available Phases**:
| Phase | Display Name | Order |
|-------|--------------|-------|
| `connecting` | Query Classification | 1 |
| `deep_research` | Deep Research | 2 |
| `research_reranker` | Research Quality Gate | 3 |
| `skeptical_comparison` | Skeptical Comparison | 4 |
| `skills_matching` | Skills Matching | 5 |
| `confidence_reranker` | Confidence Calibration | 6 |
| `generate_results` | Response Generation | 7 |

**Features**:
- Reads XML prompt files from `prompts/` directory
- Provides transparency for users to understand AI reasoning
- Used by frontend `SystemPromptDialog` component

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
│   ├── layout.js             # Root layout with ThemeProvider + AISettingsProvider
│   ├── page.js               # Main page with all sections + Settings dialog
│   └── globals.css           # Global styles and CSS variables
│
├── components/
│   ├── FitCheckSection.jsx   # AI chatbot interface (phase orchestrator)
│   ├── ThinkingTimeline.jsx  # AI thoughts display
│   ├── ThoughtNode.jsx       # Individual thought step (phase-colored)
│   ├── ParticleBackground.jsx # Animated particle canvas
│   ├── InteractiveGridDots.jsx # Interactive dot grid
│   ├── CardGridDots.jsx      # Card background dots
│   ├── HeroGridDots.jsx      # Hero section dots
│   ├── fit-check/            # Fit Check sub-components
│   │   ├── index.js          # Component exports
│   │   ├── InputPanel.jsx    # Text input with loading overlay
│   │   ├── ThinkingPanel.jsx # Expandable thinking panel
│   │   ├── ChainOfThought.jsx # Continuous pipeline trace stream
│   │   ├── ComparisonChain.jsx # Pipeline phase progress display
│   │   ├── ResultsSection.jsx # Two-column results container
│   │   ├── StrengthsCard.jsx # Pros/strengths card (teal)
│   │   ├── GrowthAreasCard.jsx # Growth areas card (apricot)
│   │   ├── InsightCard.jsx   # Phase insight display components (NEW)
│   │   ├── ReasoningDialog.jsx # Chain of thought popup dialog
│   │   └── SystemPromptDialog.jsx # System prompt viewer
│   └── ui/                   # shadcn/ui components
│       ├── button.jsx
│       ├── dialog.jsx
│       ├── select.jsx        # Custom styled dropdown (NEW)
│       └── textarea.jsx
│
├── hooks/
│   ├── use-fit-check.js      # SSE client state machine + AI settings integration
│   ├── use-ai-settings.js    # AI model configuration context (NEW)
│   └── use-header-visibility.js # Scroll-based header visibility
│
└── lib/
    ├── utils.js              # Utility functions (cn)
    ├── particleConfig.js     # Particle animation constants
    ├── parseAIResponse.js    # AI response parser for structured display
    └── phaseInsights.js      # Phase insight extraction utilities (NEW)
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

**Purpose**: HTML structure, theme provider, and AI settings context.

**Features**:
- `ThemeProvider` with class-based dark mode
- `AISettingsProvider` for global AI model configuration
- System theme detection
- HTML lang attribute

---

#### `app/page.js` - Main Page

**Purpose**: Single-page portfolio with all sections.

**Sections** (in order):
1. `Header` - Fixed navigation with theme toggle + Settings button
2. `HeroAboutSection` - Hero intro + About me
3. `FitCheckSection` - AI chatbot
4. `ProjectsSection` - Featured projects grid
5. `ExperienceSection` - Work experience timeline
6. `ContactSection` - CTA with email
7. `Footer` - Links and copyright

**Page-Level Components**:
- `AnimatedShapes` - Background morphing blobs
- `Settings Dialog` - AI model selection dropdown with Gemini 3 Pro and Gemini Flash options

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

**Purpose**: Expandable right panel showing AI thinking process, grouped by phase.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `thoughts` | Array | Array of thought events |
| `isThinking` | boolean | Whether AI is currently thinking |
| `isVisible` | boolean | Controls panel visibility |
| `status` | string | Current status (connecting/thinking/responding) |
| `statusMessage` | string | Current status message |
| `currentPhase` | string | Currently active phase from backend |

**Phase Display Names** (`PHASE_DISPLAY_NAMES`):
| Phase | Display Name |
|-------|--------------|
| `connecting` | Query Classification |
| `deep_research` | Deep Research |
| `research_reranker` | Research Quality Gate |
| `skeptical_comparison` | Critical Analysis |
| `skills_matching` | Skill Mapping |
| `confidence_reranker` | Confidence Calibration |
| `generate_results` | Response Generation |

**Features**:
- Animated panel expansion from left
- Groups thoughts by phase with headers
- Embedded `ChainOfThought` component for continuous pipeline trace
- Status indicator dots

---

#### `components/fit-check/ChainOfThought.jsx` - Pipeline Trace Stream

**Purpose**: Displays a continuous traced stream of all pipeline steps, ordered newest at top with active node header and expandable data sections.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `thoughts` | Array | Array of thought events from SSE stream |
| `currentPhase` | string | Currently active phase name |
| `phaseProgress` | Object | Map of phase name → status (active/complete/error) |
| `phaseHistory` | Array | Completed phase entries with summaries |
| `isThinking` | boolean | Whether AI is currently processing |

**Sub-Components**:
- `ActiveNodeHeader` - Displays currently active phase with animated indicator
- `PhaseProgressPills` - Visual status pills for all 7 phases
- `ThoughtStep` - Individual thought with expandable data revelation

**Phase Configuration** (`PHASE_CONFIG`):
| Phase | Label | Icon | Color |
|-------|-------|------|-------|
| `connecting` | Connecting | Wifi | blue-400 |
| `deep_research` | Deep Research | Search | purple-400 |
| `research_reranker` | Research Quality Gate | CheckCircle2 | violet-400 |
| `skeptical_comparison` | Skeptical Comparison | Scale | amber-400 |
| `skills_matching` | Skills Matching | Briefcase | green-400 |
| `confidence_reranker` | Confidence Calibration | CheckCircle2 | emerald-400 |
| `generate_results` | Generating Results | Sparkles | burnt-peach |

**Features**:
- Reversed timeline order (newest at top, oldest at bottom)
- Active node header with phase-specific styling and pulsing indicator
- Expandable data sections showing tool inputs and outputs
- Phase progress pills showing completion status
- Auto-scroll to newest thought
- Phase-colored left borders for visual grouping
- **Enhanced insights display** via `parseThoughtContent()` integration
- **Inline badges** showing confidence %, quality tiers, and technologies
- **PhaseInsightReveal** component for structured phase summaries

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

#### `components/fit-check/ReasoningDialog.jsx` - Chain of Thought Dialog

**Purpose**: Full-screen modal displaying the complete AI reasoning chain with phase-grouped thoughts and enhanced insight display.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `open` | boolean | Whether dialog is open |
| `onOpenChange` | function | Callback when open state changes |
| `thoughts` | Array | Array of thought events from pipeline |
| `phaseHistory` | Array | Completed phase entries with summaries |
| `durationMs` | number | Total analysis duration in milliseconds |

**Sub-Components**:
- `PhaseSection` - Phase header with expandable thought list
- `PhaseInsightCard` - Structured insight display with metrics (NEW)
- `ThoughtItem` - Individual thought with parsed content display (ENHANCED)

**Features**:
- Modern glassmorphism design with gradient accents
- Phase-grouped thoughts with visual timeline
- **PhaseInsightCard** with structured metrics display
- **Confidence bars** showing calibrated percentages
- **Quality gate indicators** with tier badges (HIGH/MEDIUM/LOW)
- **Technology tags** extracted from research phases
- Expandable raw data sections (de-emphasized)
- Click on any phase header to view system prompt
- Phase progress pills for quick navigation
- Smooth animations and transitions
- Nested SystemPromptDialog for transparency

**Accessed via**: "Read the Reasoning" button (Brain icon) in results phase

---

#### `components/fit-check/SystemPromptDialog.jsx` - System Prompt Viewer (NEW)

**Purpose**: Nested dialog showing the actual system prompt used for each pipeline phase.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `open` | boolean | Whether dialog is open |
| `onOpenChange` | function | Callback when open state changes |
| `phase` | string | Phase name to fetch prompt for |

**Features**:
- Fetches prompt content from backend `/api/prompts/{phase}` endpoint
- Syntax-highlighted XML display with color coding
- Copy to clipboard functionality
- Loading and error states with graceful handling
- Phase-specific icon and color theming
- Terminal-style code block presentation

**API Integration**: Uses `/api/prompts/{phase}` endpoint for transparency

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

**Purpose**: Render a single AI thought step with phase-specific styling.

**Phase Colors** (left border):
| Phase | Color |
|-------|-------|
| `connecting` | blue-400 |
| `deep_research` | purple-400 |
| `research_reranker` | violet-400 |
| `skeptical_comparison` | amber-400 |
| `skills_matching` | green-400 |
| `confidence_reranker` | emerald-400 |
| `generate_results` | burnt-peach |

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

#### `components/fit-check/ComparisonChain.jsx` - Pipeline Progress

**Purpose**: Displays pipeline phase progress with visual status indicators and enhanced insight summaries.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `currentPhase` | string | Currently active phase name |
| `phaseProgress` | Object | Map of phase name → status (active/complete/error) |
| `phaseHistory` | Array | Completed phase entries with summaries |
| `status` | string | Overall status (connecting/thinking/responding) |
| `statusMessage` | string | Current status message |

**Sub-Components**:
- `StepInsightSummary` - Compact insight display for completed phases (NEW)

**Phase Configuration** (`PHASE_CONFIG`):
| Phase | Label | Icon | Description |
|-------|-------|------|-------------|
| `connecting` | Connecting | Wifi | Classifying query and extracting entities |
| `deep_research` | Deep Research | Search | Gathering employer intelligence |
| `research_reranker` | Research Quality Gate | CheckCircle2 | Validating research completeness |
| `skeptical_comparison` | Skeptical Comparison | Scale | Critical gap analysis |
| `skills_matching` | Skills Matching | Briefcase | Mapping skills to requirements |
| `confidence_reranker` | Confidence Calibration | CheckCircle2 | LLM-as-Judge quality assessment |
| `generate_results` | Generating Results | Sparkles | Synthesizing final response |

**Phase Order**: `PHASE_ORDER` array maintains pipeline sequence for rendering.

**StepInsightSummary Display** (per phase):
| Phase | Displayed Metrics |
|-------|-------------------|
| `connecting` | Company name, query type badge |
| `deep_research` | Source count, technology count |
| `research_reranker` | Quality tier badge (HIGH/MEDIUM/LOW), confidence % |
| `skeptical_comparison` | Gap count, match strength badge |
| `skills_matching` | Matched count, match percentage |
| `confidence_reranker` | Quality tier badge, confidence % |

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

**Pipeline Phases** (from backend):
| Phase | Description |
|-------|-------------|
| `connecting` | Query classification and entity extraction |
| `deep_research` | Web search and intelligence gathering |
| `research_reranker` | Research quality gate and data validation |
| `skeptical_comparison` | Critical gap analysis |
| `skills_matching` | Skill-to-requirement mapping |
| `confidence_reranker` | LLM-as-Judge confidence calibration |
| `generate_results` | Final response synthesis |

**State Shape**:
```javascript
{
  status: 'idle',         // State machine status
  statusMessage: '',      // Human-readable message
  thoughts: [],           // Array of thought events
  response: '',           // Accumulated response text
  error: null,            // { code, message }
  durationMs: null,       // Total duration
  
  // Phase tracking
  currentPhase: null,     // Currently active phase
  phaseProgress: {},      // Map: phase name → status (active/complete)
  phaseHistory: [],       // Completed phases with summaries
}
```

**Derived State**:
- `uiPhase` - Computed UI phase (input/expanded/results)
- `parsedResponse` - Parsed response object for result cards

**Functions**:
- `submitQuery(query)` - Start SSE stream with model configuration from AI settings
- `reset()` - Clear state for new query

**AI Settings Integration**:
- Uses `useAISettings` hook to get model configuration
- Passes `model_id` and `config_type` in API request body
- Supports switching between Gemini 3 Pro (reasoning) and Gemini Flash (standard)

**SSE Event Handling**:
| Event Type | Handler Action |
|------------|----------------|
| `phase` | Update `currentPhase`, set phase to 'active' in `phaseProgress` |
| `phase_complete` | Mark phase 'complete', add to `phaseHistory` with summary |
| `thought` | Append to `thoughts` array with phase context |
| `response` | Append chunk to `response` string |
| `complete` | Set status to 'complete', record `durationMs` |
| `error` | Set `error` object, transition to error state |

**Status Mapping**:
| Backend Phase | Frontend Status |
|---------------|-----------------|
| connecting | connecting |
| deep_research, research_reranker | thinking |
| skeptical_comparison, skills_matching, confidence_reranker | thinking |
| generate_results | responding |

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

#### `lib/phaseInsights.js` - Phase Insight Extraction Utilities (NEW)

**Purpose**: Extract meaningful metadata from phase outputs to display rich context instead of raw JSON data.

**Exported Functions**:

| Function | Purpose |
|----------|---------|
| `extractPhaseInsights(phase, summary)` | Parse phase completion summaries into structured data |
| `parseThoughtContent(thought)` | Enhance thought objects with displayable summaries and extracted data |
| `getPhaseDisplayMeta(phase)` | Get display metadata (icon, color, label) for a phase |

**Phase-Specific Extraction**:

| Phase | Extracted Data |
|-------|----------------|
| `connecting` | `queryType`, `company`, `jobTitle`, `isValid` |
| `deep_research` | `sourceCount`, `technologies[]`, `requirementsFound`, `cultureValues[]` |
| `research_reranker` | `qualityTier` (HIGH/MEDIUM/LOW), `dataScore`, `isClean`, `missingData[]` |
| `skeptical_comparison` | `gapsIdentified`, `strengthsFound`, `riskLevel`, `matchStrength` |
| `skills_matching` | `matchedCount`, `matchPercentage`, `learningGaps[]`, `transferableSkills[]` |
| `confidence_reranker` | `confidence` (0-100), `qualityTier`, `qualityFlags[]`, `adjustmentReason` |
| `generate_results` | `wordCount` |

**Thought Content Parsing**:
```javascript
parseThoughtContent(thought) → {
  ...thought,
  displaySummary: string,    // Human-readable summary
  extractedData: {           // Structured metadata
    confidence?: number,
    tier?: string,
    technologies?: string[],
    // ... phase-specific fields
  }
}
```

**Usage in Components**:
- `ChainOfThought.jsx` - Enhanced ThoughtEntry with inline badges
- `ReasoningDialog.jsx` - PhaseInsightCard with metrics and confidence bars
- `ComparisonChain.jsx` - StepInsightSummary with compact phase metrics

---

#### `components/fit-check/InsightCard.jsx` - Phase Insight Display Components (NEW)

**Purpose**: Visual components for displaying rich phase insights with consistent styling.

**Exported Components**:

| Component | Purpose |
|-----------|---------|
| `InsightCard` | Variant-based card for phase insights (success/warning/info/error) |
| `ConfidenceBar` | Animated progress bar with color-coded confidence display |
| `MetricBadge` | Compact metric display with icon and value |
| `TechTag` | Technology pill badge with code icon |

**InsightCard Props**:
| Prop | Type | Description |
|------|------|-------------|
| `variant` | string | Visual style: `success`, `warning`, `info`, `error` |
| `icon` | Component | Lucide icon component |
| `title` | string | Card title |
| `children` | ReactNode | Card content |

**ConfidenceBar Props**:
| Prop | Type | Description |
|------|------|-------------|
| `value` | number | Confidence percentage (0-100) |
| `label` | string | Optional label text |
| `size` | string | Size variant: `sm`, `md`, `lg` |

**Color Coding**:
| Confidence Range | Color |
|------------------|-------|
| ≥70% | muted-teal (green) |
| 40-69% | amber-500 (yellow) |
| <40% | red-500 (red) |

**MetricBadge Props**:
| Prop | Type | Description |
|------|------|-------------|
| `icon` | Component | Lucide icon component |
| `value` | string/number | Metric value |
| `label` | string | Metric label |
| `color` | string | Tailwind color class |

---

#### `hooks/use-ai-settings.js` - AI Model Settings Hook

**Purpose**: React context and hook for global AI model configuration.

**Exported Constants**:
- `AI_MODELS` - Object defining available models with metadata
- `DEFAULT_MODEL` - Default model ID (`gemini-3-pro-preview`)

**AI Models Configuration**:
| Model ID | Label | Config Type | Badge |
|----------|-------|-------------|-------|
| `gemini-3-pro-preview` | Gemini 3 Pro (Preview) | reasoning | Recommended |
| `gemini-flash-latest` | Gemini Flash (Latest) | standard | Fast |

**Provider**: `AISettingsProvider`
- Wraps application to provide AI settings context
- Manages selected model state
- Used in `layout.js` at app root

**Hook**: `useAISettings()`
- Returns:
  - `selectedModel` - Current model ID
  - `modelInfo` - Full model metadata object
  - `models` - All available models
  - `updateModel(modelId)` - Switch to different model
  - `getModelConfig()` - Returns `{ model_id, config_type }` for API calls

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

#### `components/ui/select.jsx` - Styled Dropdown Select

**Purpose**: Custom styled dropdown component for AI model selection.

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `value` | string | Currently selected value |
| `onValueChange` | function | Callback when selection changes |
| `options` | Array | Array of option objects with id, label, description, badge |
| `placeholder` | string | Placeholder text when no selection |
| `className` | string | Additional CSS classes |

**Option Object Shape**:
```javascript
{
  id: 'model-id',
  label: 'Display Label',
  description: 'Option description',
  badge: 'Badge text (optional)'
}
```

**Features**:
- Glassmorphism dropdown styling
- Badge support for option labels (e.g., "Recommended", "Fast")
- Description text for each option
- Keyboard navigation support
- Dark/light theme aware
- Animated dropdown with smooth transitions

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
| `cot-slide-in` | Chain of Thought item slide-in entrance |
| `cot-fade-in` | Chain of Thought fade-in animation |
| `cot-pulse` | Active node pulsing indicator |
| `cot-expand` | Data section expand/collapse animation |

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
  "include_thoughts": true,
  "model_id": "gemini-3-pro-preview",
  "config_type": "reasoning"
}
```

**Request Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Company name or job description (3-2000 chars) |
| `include_thoughts` | boolean | `true` | Include thinking process in stream |
| `model_id` | string | `gemini-3-pro-preview` | AI model to use |
| `config_type` | string | `reasoning` | Config type: `reasoning` or `standard` |

**Response** (SSE Stream):
```
event: phase
data: {"phase": "connecting", "message": "Classifying query and extracting entities..."}

event: thought
data: {"step": 1, "type": "reasoning", "content": "Analyzing query: Google", "phase": "connecting"}

event: phase_complete
data: {"phase": "connecting", "summary": "Query classified as 'company', company: Google", "duration_ms": 1021}

event: phase
data: {"phase": "deep_research", "message": "Gathering employer intelligence..."}

event: thought
data: {"step": 2, "type": "tool_call", "tool": "web_search", "input": "Google engineering culture tech stack", "phase": "deep_research"}

event: thought
data: {"step": 3, "type": "observation", "content": "Found 5 relevant results about Google engineering...", "phase": "deep_research"}

event: phase_complete
data: {"phase": "deep_research", "summary": "Identified 5 technologies, 3 requirements, 4 culture values", "duration_ms": 6500}

event: phase
data: {"phase": "research_reranker", "message": "Validating research quality..."}

event: phase_complete
data: {"phase": "research_reranker", "summary": "Data: CLEAN | Quality: HIGH", "duration_ms": 2100}

event: phase
data: {"phase": "skeptical_comparison", "message": "Performing critical gap analysis..."}

event: phase_complete
data: {"phase": "skeptical_comparison", "summary": "Found 3 gaps, 4 strengths. Risk level: medium", "duration_ms": 5200}

event: phase
data: {"phase": "skills_matching", "message": "Mapping skills to requirements..."}

event: phase_complete
data: {"phase": "skills_matching", "summary": "85% skill alignment, 2 learning gaps identified", "duration_ms": 4100}

event: phase
data: {"phase": "confidence_reranker", "message": "Calibrating confidence score..."}

event: phase_complete
data: {"phase": "confidence_reranker", "summary": "Calibrated confidence: 72% (MEDIUM), 1 quality flag", "duration_ms": 3800}

event: phase
data: {"phase": "generate_results", "message": "Synthesizing final response..."}

event: response
data: {"chunk": "### Why I'm a Great Fit"}

event: response
data: {"chunk": " for Google\n\n**Key Alignments:**"}

event: phase_complete
data: {"phase": "generate_results", "summary": "Generated 350 word response", "duration_ms": 4200}

event: complete
data: {"duration_ms": 27523, "confidence_score": 72}
```

### Error Responses

```
event: error
data: {"code": "EARLY_EXIT", "message": "Query appears to be prompt injection attempt"}

event: error
data: {"code": "INSUFFICIENT_DATA", "message": "Could not find enough information about XyzFakeCompany"}
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
Edit the relevant phase prompt in `res_backend/prompts/`:
- `phase_1_connecting.xml` - Query classification logic
- `phase_2_deep_research.xml` - Web search strategy
- `phase_2b_research_reranker.xml` - Quality gate thresholds
- `phase_3_skeptical_comparison.xml` - Gap analysis criteria
- `phase_4_skills_matching.xml` - Skill matching rules
- `phase_5b_confidence_reranker.xml` - Confidence calibration
- `phase_5_generate_results.xml` - Response format/tone

### Switching AI Models
The application supports multiple Gemini models with different configurations:

**Frontend (Settings Dialog)**:
1. Open Settings dialog via gear icon in header
2. Select model from "AI Model" dropdown
3. Model configuration is automatically applied to next analysis

**Backend Model Configuration** (`res_backend/config/llm.py`):
| Model | Config Type | Settings |
|-------|-------------|----------|
| `gemini-3-pro-preview` | reasoning | `thinking_config: { thinking_budget: 10000 }` |
| `gemini-flash-latest` | standard | `temperature: 0.3, top_k: 40` |

**Adding a New Model**:
1. Add model entry to `SUPPORTED_MODELS` in `res_backend/config/llm.py`
2. Add model entry to `AI_MODELS` in `res_web/hooks/use-ai-settings.js`
3. Rebuild frontend for changes to take effect

### Adding a New Pipeline Phase
1. Create prompt template in `res_backend/prompts/phase_X_name.xml`
2. Create node in `res_backend/services/nodes/name.py`
3. Export node from `res_backend/services/nodes/__init__.py`
4. Add node to graph in `res_backend/services/fit_check_agent.py`
5. Add routing function if phase has conditional exits
6. Update `FitCheckState` in `res_backend/services/pipeline_state.py`
7. Add phase to frontend `PHASE_CONFIG` and `PHASE_ORDER` in:
   - `res_web/components/fit-check/ChainOfThought.jsx`
   - `res_web/components/fit-check/ComparisonChain.jsx`
   - `res_web/components/fit-check/ThinkingPanel.jsx`
   - `res_web/components/ThoughtNode.jsx`

### Modifying Reranker Logic
Rerankers use LLM-as-Judge pattern with structured JSON output:
- Research Reranker: `res_backend/services/nodes/research_reranker.py`
- Confidence Reranker: `res_backend/services/nodes/confidence_reranker.py`

Key configuration in each reranker:
```python
MAX_SEARCH_ATTEMPTS = 2  # Retry limit before proceeding
LLM_TEMPERATURE = 0.1    # Low temp for consistent judging
```

### Adding New SSE Event Types
1. Add model in `res_backend/models/fit_check.py`
2. Add callback in `res_backend/services/streaming_callback.py`
3. Add handler in `res_web/hooks/use-fit-check.js` `processEvent()` function

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

### Running Backend Tests
```bash
cd res_backend
.\.venv\Scripts\Activate.ps1
pytest                                    # All tests
python tests/simulation/simulate_full_pipeline.py --query "Google"  # Simulation
```

### Docker Development
```bash
cd res_backend
.\run_docker_rebuild.bat   # Full rebuild
.\run_docker_sync.bat      # Sync code changes
docker logs res_web-backend --follow  # View logs
```

---

## 🔧 Known Issues & Workarounds

### Prompt Template Escaping
XML prompt templates use Python `.format()` for variable substitution. Literal curly braces in JSON examples must be doubled:
```xml
<!-- WRONG -->
{"key": "value"}

<!-- CORRECT -->
{{"key": "value"}}
```

### Reranker Search Retry
The research_reranker can trigger up to 2 retry searches if data quality is insufficient. The `search_attempt` counter must be incremented in both success and fallback return paths.

---

*Last Updated: January 2025*
