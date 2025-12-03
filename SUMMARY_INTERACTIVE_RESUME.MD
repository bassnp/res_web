# Interactive Resume Website - Technical Specification

> **Single Point of Truth** for the Interactive Resume Portfolio with AI-Powered Fit Check Feature  
> **Last Verified**: December 3, 2025

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Backend (res_backend)](#backend-res_backend)
4. [Frontend (res_web)](#frontend-res_web)
5. [API Contract](#api-contract)
6. [Deployment](#deployment)
7. [Environment Variables](#environment-variables)
8. [Quick Reference](#quick-reference)

---

## 🎯 Project Overview

An interactive portfolio website featuring an **AI-powered "See if I'm fit for you!"** chatbot that allows employers to:
1. Enter a company name or job description
2. Watch the AI agent research and analyze in real-time
3. Receive a personalized fit analysis with skill matching

### Key Features
- **Real-time SSE streaming** of AI thinking process
- **LangGraph 7-phase pipeline** with conditional routing and quality gates
- **Dark/Light theme** support with system detection
- **Animated particle backgrounds** and interactive grid dots
- **Static site export** for Sevalla deployment
- **AI model selection** (Gemini 3 Pro or Gemini Flash)

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (res_web)                       │
│                    Next.js 14.2.3 Static Export                  │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │   page.js   │  │FitCheckSection│  │  useFitCheck Hook     │  │
│  │  (Sections) │  │  (Orchestrator)│  │  (SSE Client)        │  │
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
│  │ │  web_search    │  skill_matcher  │  experience_matcher  │││
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
│ • Classify query type (company/job_description/irrelevant)      │
│ • Extract entities (company_name, job_title, skills)            │
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
│ • Validate research completeness and data quality               │
│ • Assess tier: CLEAN/PARTIAL/SPARSE/UNRELIABLE/GARBAGE          │
│ • Prune unreliable sources, flag missing data                   │
│ • Route: ENHANCE_SEARCH (retry) or EARLY_EXIT or → skeptical    │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: SKEPTICAL COMPARISON (Critical Analysis)               │
│ • Compare engineer profile against employer requirements        │
│ • Identify genuine gaps (not just missing info)                 │
│ • Classify risk level (low/medium/high)                         │
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
│ • Output tier: HIGH/MEDIUM/LOW/INSUFFICIENT_DATA                │
│ • Route: → generate_results                                     │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: GENERATE RESULTS (Final Response Synthesis)            │
│ • Synthesize all phase outputs into coherent narrative          │
│ • Apply confidence-appropriate framing                          │
│ • Structure: summary → alignments → gaps → CTA                  │
│ • Stream response via SSE                                       │
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
| Data Validation | Pydantic | ≥2.6.0 |

### Directory Structure

```
res_backend/
├── server.py                 # FastAPI application entry point
├── Dockerfile                # Multi-stage production Docker build
├── docker-compose.yml        # Local development orchestration
├── requirements.txt          # Python dependencies
├── pytest.ini                # Test configuration
├── run_docker_rebuild.bat    # Full Docker rebuild script
├── run_docker_sync.bat       # Quick code sync script
│
├── config/
│   ├── __init__.py
│   ├── engineer_profile.py   # Engineer skills/experience data
│   └── llm.py                # Google Gemini LLM configuration
│
├── middleware/
│   └── __init__.py           # Middleware placeholder
│
├── models/
│   ├── __init__.py
│   └── fit_check.py          # Pydantic request/response models
│
├── prompts/                  # XML prompt templates for each phase
│   ├── __init__.py           # PROMPTS_DIR path export
│   ├── phase_1_connecting.xml
│   ├── phase_1_connecting_concise.xml
│   ├── phase_2_deep_research.xml
│   ├── phase_2_deep_research_concise.xml
│   ├── phase_2b_research_reranker.xml
│   ├── phase_2b_research_reranker_concise.xml
│   ├── phase_3_skeptical_comparison.xml
│   ├── phase_3_skeptical_comparison_concise.xml
│   ├── phase_4_skills_matching.xml
│   ├── phase_4_skills_matching_concise.xml
│   ├── phase_5_generate_results.xml
│   ├── phase_5_generate_results_concise.xml
│   ├── phase_5b_confidence_reranker.xml
│   └── phase_5b_confidence_reranker_concise.xml
│
├── routers/
│   ├── __init__.py
│   ├── fit_check.py          # SSE streaming endpoint router
│   └── prompts.py            # Prompt transparency API router
│
├── services/
│   ├── __init__.py
│   ├── fit_check_agent.py    # LangGraph 7-phase pipeline orchestrator
│   ├── pipeline_state.py     # TypedDict state definitions
│   ├── streaming_callback.py # SSE event formatter and queue handler
│   ├── callbacks.py          # Callback base classes
│   ├── prompt_loader.py      # XML prompt loading and formatting
│   ├── utils.py              # Utility functions
│   │
│   ├── nodes/                # LangGraph node implementations
│   │   ├── __init__.py
│   │   ├── connecting.py            # Phase 1: Query classification
│   │   ├── deep_research.py         # Phase 2: Web research
│   │   ├── research_reranker.py     # Phase 2B: Quality gate
│   │   ├── skeptical_comparison.py  # Phase 3: Gap analysis
│   │   ├── skills_matching.py       # Phase 4: Skill matching
│   │   ├── confidence_reranker.py   # Phase 5B: LLM-as-Judge
│   │   └── generate_results.py      # Phase 6: Response synthesis
│   │
│   └── tools/                # LangChain tools
│       ├── __init__.py
│       ├── web_search.py            # Google CSE web search
│       ├── skill_matcher.py         # Skill alignment analysis
│       └── experience_matcher.py    # Experience relevance analysis
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_fit_check_agent.py
    ├── test_integration.py
    ├── unit/                 # Unit tests
    └── simulation/           # Frontend simulation tests
        ├── simulate_full_pipeline.py
        ├── analyze_ai_outputs.py
        └── outputs/
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
| GET | `/docs` | OpenAPI (Swagger) documentation |
| POST | `/api/fit-check/stream` | SSE streaming fit analysis (via router) |
| GET | `/api/fit-check/health` | Fit check service health |
| GET | `/api/prompts` | List all pipeline phases |
| GET | `/api/prompts/{phase}` | Get prompt content for specific phase |

**Key Features**:
- Lifespan context manager for startup/shutdown events
- CORS middleware configured via `ALLOWED_ORIGINS` env var
- Configurable logging via `LOG_LEVEL` env var

---

#### `config/llm.py` - LLM Configuration

**Purpose**: Factory functions for Google Gemini LLM instances.

**Supported Models**:
| Model ID | Config Type | Settings |
|----------|-------------|----------|
| `gemini-3-pro-preview` | reasoning | `thinking_config: { thinking_budget: 10000 }`, temp=1.0 |
| `gemini-flash-latest` | standard | `temperature: 0.3, top_k: 40` |

**Configuration**:
| Parameter | Default | Env Override |
|-----------|---------|--------------|
| Model | `gemini-3-pro-preview` | `GEMINI_MODEL` |
| Max Output Tokens | 2048 | - |

**Function**: `get_llm(streaming, temperature, max_output_tokens, model_id, config_type)`
- Returns configured `ChatGoogleGenerativeAI` instance
- Raises `ValueError` if `GOOGLE_API_KEY` not set
- Automatically selects config type based on model if not specified

---

#### `config/engineer_profile.py` - Engineer Data Configuration

**Purpose**: Stores and formats the engineer's profile for AI prompts.

**Data Structure** (`ENGINEER_PROFILE`):
```python
{
    "name": "Software Engineer",
    "education": "...",
    "skills": {
        "languages": [...],
        "frameworks": [...],
        "cloud_devops": [...],
        "ai_ml": [...],
        "tools": [...],
    },
    "experience_summary": "...",
    "notable_projects": [...],
    "strengths": [...],
    "career_interests": [...],
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
    query: str                    # 3-2000 chars, company name or job description
    include_thoughts: bool = True # Include thinking process in stream
    model_id: Optional[str] = "gemini-3-pro-preview"
    config_type: Optional[Literal["reasoning", "standard"]] = "reasoning"
```

**SSE Event Models**:
| Event Type | Model | Key Fields |
|------------|-------|------------|
| `phase` | `PhaseEvent` | `phase`, `message` |
| `phase_complete` | `PhaseCompleteEvent` | `phase`, `summary`, `duration_ms` |
| `thought` | `ThoughtEvent` | `step`, `type`, `tool`, `input`, `content`, `phase` |
| `response` | `ResponseEvent` | `chunk` |
| `complete` | `CompleteEvent` | `duration_ms`, `confidence_score` |
| `error` | `ErrorEvent` | `code`, `message` |

**Pipeline Phase Names**:
| Phase | Description |
|-------|-------------|
| `connecting` | Query classification and entity extraction |
| `deep_research` | Web intelligence gathering |
| `research_reranker` | Research quality gate |
| `skeptical_comparison` | Critical gap analysis |
| `skills_matching` | Skill-to-requirement mapping |
| `confidence_reranker` | LLM-as-Judge meta-review |
| `generate_results` | Final response synthesis |

**Error Codes**:
- `INVALID_QUERY` (400) - Query too short or too long
- `RATE_LIMITED` (429) - Too many requests
- `PIPELINE_ERROR` (500) - Pipeline execution failed
- `AGENT_ERROR` (500) - AI agent execution failed
- `SEARCH_ERROR` (502) - Web search tool failed
- `LLM_ERROR` (503) - Gemini API unavailable
- `TIMEOUT` (504) - Agent execution timed out
- `EARLY_EXIT` - Query rejected or insufficient data

---

#### `services/fit_check_agent.py` - LangGraph Pipeline Orchestrator

**Purpose**: Implements the 7-phase AI pipeline using LangGraph's state machine pattern.

**State Definition** (`FitCheckPipelineState` in `pipeline_state.py`):
```python
class FitCheckPipelineState(TypedDict):
    # Input
    query: str
    
    # Orchestration
    current_phase: str
    step_count: int
    
    # Phase outputs
    phase_1_output: Optional[Phase1Output]
    phase_2_output: Optional[Phase2Output]
    research_reranker_output: Optional[ResearchRerankerOutput]
    phase_3_output: Optional[Phase3Output]
    phase_4_output: Optional[Phase4Output]
    reranker_output: Optional[RerankerOutput]
    
    # Research quality tracking
    search_attempt: int       # 1 = primary, 2 = enhanced retry
    low_data_flag: bool
    early_exit: bool
    
    # Final output
    final_response: Optional[str]
    
    # LangGraph compatibility
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Error handling
    processing_errors: List[str]
    error: Optional[str]
    rejection_reason: Optional[str]
    
    # Model configuration
    model_id: Optional[str]
    config_type: Optional[str]
```

**Graph Architecture**:
```
[START] 
   │
   ▼
[connecting] → route_after_connecting() → [END] or ↓
   │
   ▼
[deep_research] → [research_reranker] → route_after_research_reranker()
                                               │
                    ┌──────────────────────────┼────────────────┐
                    ▼                          ▼                ▼
            [deep_research]          [skeptical_comparison]  [generate_results]
              (retry)                        │                (early exit)
                                             ▼
                                   [skills_matching]
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

**Routing Functions**:
- `route_after_connecting()` - END (rejection) vs deep_research
- `route_after_research_reranker()` - deep_research (retry) vs skeptical_comparison vs generate_results (early exit)

**Class**: `FitCheckAgent`
- `analyze(query, model_id, config_type)` - Non-streaming analysis
- `stream_analysis(query, callback, model_id, config_type)` - Streaming with phase events

**Singleton**: `get_agent()` returns cached instance

---

#### `services/pipeline_state.py` - State Definitions

**Purpose**: TypedDict state schemas and helper functions.

**Phase Output Types**:
| TypedDict | Phase | Key Fields |
|-----------|-------|------------|
| `Phase1Output` | Connecting | `query_type`, `company_name`, `job_title`, `extracted_skills` |
| `Phase2Output` | Deep Research | `employer_summary`, `tech_stack`, `identified_requirements`, `culture_signals` |
| `ResearchRerankerOutput` | Research Reranker | `data_quality_tier`, `quality_flags`, `recommended_action`, `company_verifiability` |
| `Phase3Output` | Skeptical Comparison | `genuine_strengths`, `genuine_gaps`, `risk_assessment` |
| `Phase4Output` | Skills Matching | `matched_requirements`, `unmatched_requirements`, `overall_match_score` |
| `RerankerOutput` | Confidence Reranker | `calibrated_score`, `tier`, `quality_flags`, `adjustment_rationale` |

**Constants**:
```python
PHASE_ORDER = [
    "connecting",
    "deep_research",
    "research_reranker",
    "skeptical_comparison",
    "skills_matching",
    "confidence_reranker",
    "generate_results",
]
```

**Helper Functions**:
- `create_initial_state(query, model_id, config_type)` - Factory for initial state
- `get_phase_display_name(phase)` - Human-readable phase name
- `get_next_phase(current_phase)` - Next phase in sequence
- `is_terminal_phase(phase)` - Check if final phase

---

#### `services/tools/` - LangChain Tools

**web_search.py**:
- `@tool web_search(query: str) -> str`
- Uses `GoogleSearchAPIWrapper` from langchain-google-community
- Returns top 5 results
- Fallback responses if CSE not configured
- Requires: `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ID`

**skill_matcher.py**:
- `@tool analyze_skill_match(requirements: str) -> str`
- Matches engineer skills against job requirements
- Direct match, alias match, and partial match logic
- Helper: `get_skill_summary()`

**experience_matcher.py**:
- `@tool analyze_experience_relevance(context: str) -> str`
- Evaluates experience relevance to employer context
- Domain pattern matching (AI, fintech, SaaS, startup, etc.)
- Helper: `get_project_highlights()`

---

#### `routers/prompts.py` - Prompt Transparency Router

**Purpose**: API endpoints for retrieving system prompts.

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/prompts` | List all pipeline phases with metadata |
| GET | `/api/prompts/{phase}` | Get full prompt content for specific phase |

**Phase Metadata**:
| Phase | Display Name | Order |
|-------|--------------|-------|
| `connecting` | Query Classification | 1 |
| `deep_research` | Deep Research | 2 |
| `research_reranker` | Research Quality Gate | 3 |
| `skeptical_comparison` | Skeptical Comparison | 4 |
| `skills_matching` | Skills Matching | 5 |
| `confidence_reranker` | Confidence Calibration | 6 |
| `generate_results` | Response Generation | 7 |

---

## ⚛️ Frontend (res_web)

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 14.2.3 |
| UI Library | React | ^18 |
| Styling | TailwindCSS + tailwindcss-animate | ^3.4.1 / ^1.0.7 |
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
├── build_local.bat           # Local development build
├── build_production.bat      # Production build script
│
├── app/
│   ├── layout.js             # Root layout with ThemeProvider + AISettingsProvider
│   ├── page.js               # Main page with all sections
│   └── globals.css           # Global styles and CSS variables
│
├── components/
│   ├── FitCheckSection.jsx   # AI chatbot interface (phase orchestrator)
│   ├── ThinkingTimeline.jsx  # AI thoughts display (legacy)
│   ├── ThoughtNode.jsx       # Individual thought step (phase-colored)
│   ├── ParticleBackground.jsx # Animated particle canvas
│   ├── InteractiveGridDots.jsx # Interactive dot grid
│   ├── CardGridDots.jsx      # Card background dots
│   ├── HeroGridDots.jsx      # Hero section dots
│   │
│   ├── fit-check/            # Fit Check sub-components
│   │   ├── index.js          # Component exports
│   │   ├── InputPanel.jsx    # Text input with loading overlay
│   │   ├── ThinkingPanel.jsx # Expandable thinking panel
│   │   ├── ChainOfThought.jsx # Continuous pipeline trace stream
│   │   ├── ComparisonChain.jsx # Pipeline phase progress display
│   │   ├── ResultsSection.jsx # Two-column results container
│   │   ├── StrengthsCard.jsx # Strengths card (teal theme)
│   │   ├── GrowthAreasCard.jsx # Growth areas card (apricot theme)
│   │   ├── InsightCard.jsx   # Phase insight display components
│   │   ├── ReasoningDialog.jsx # Chain of thought popup dialog
│   │   ├── SystemPromptDialog.jsx # System prompt viewer
│   │   ├── WorkflowPipelinePreview.jsx # Animated pipeline showcase
│   │   └── ChainOfThoughtShowcase.jsx # Floating thought cards preview
│   │
│   └── ui/                   # shadcn/ui components
│       ├── button.jsx
│       ├── dialog.jsx
│       ├── select.jsx        # Custom styled dropdown
│       └── textarea.jsx
│
├── hooks/
│   ├── use-fit-check.js      # SSE client state machine
│   ├── use-ai-settings.js    # AI model configuration context
│   └── use-header-visibility.js # Scroll-based header visibility
│
└── lib/
    ├── utils.js              # Utility functions (cn)
    ├── particleConfig.js     # Particle animation constants
    ├── parseAIResponse.js    # AI response parser for structured display
    └── phaseInsights.js      # Phase insight extraction utilities
```

---

### Module Specifications

#### `next.config.js` - Next.js Configuration

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

#### `components/FitCheckSection.jsx` - AI Chatbot Interface

**Purpose**: Main orchestrator for the AI fit check feature with phase-based UI transitions.

**UI Phases**:
| Phase | Status | Layout |
|-------|--------|--------|
| `input` | idle | Three-column: Pipeline Preview (left) + Input (center) + Chain of Thought Showcase (right) |
| `expanded` | connecting/thinking/responding | Two-column: ComparisonChain (left) + ThinkingPanel (right) |
| `results` | complete | Compact header with action buttons |

**Props from useFitCheck**:
- `status`, `statusMessage`, `thoughts`, `response`, `error`, `durationMs`
- `uiPhase`, `parsedResponse`, `submitQuery`, `reset`, `isLoading`
- `currentPhase`, `phaseProgress`, `phaseHistory`

**Features**:
- Phase-based layout switching with smooth transitions
- Container width animation (max-w-6xl for input, max-w-5xl for expanded/results)
- Three-column input phase with animated showcase panels
- Responsive design: showcase panels hidden on smaller screens (`hidden lg:flex`)
- Error display with retry option
- Duration display on completion

---

#### `components/fit-check/InputPanel.jsx` - Input Form

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

**Props**:
| Prop | Type | Description |
|------|------|-------------|
| `thoughts` | Array | Array of thought events |
| `isThinking` | boolean | Whether AI is currently thinking |
| `isVisible` | boolean | Controls panel visibility |
| `status` | string | Current status |
| `statusMessage` | string | Current status message |
| `currentPhase` | string | Currently active phase |
| `phaseProgress` | Object | Map of phase → status |
| `phaseHistory` | Array | Completed phases with summaries |

**Phase Display Names**:
| Phase | Display Name |
|-------|--------------|
| `connecting` | Query Classification |
| `deep_research` | Deep Research |
| `research_reranker` | Research Quality Gate |
| `skeptical_comparison` | Critical Analysis |
| `skills_matching` | Skill Mapping |
| `confidence_reranker` | Confidence Calibration |
| `generate_results` | Response Generation |

---

#### `components/fit-check/ChainOfThought.jsx` - Pipeline Trace Stream

**Purpose**: Displays continuous traced stream of all pipeline steps.

**Sub-Components**:
- `ActiveNodeHeader` - Currently active phase with animated indicator
- `PhaseProgressPills` - Visual status pills for all 7 phases
- `ThoughtStep` - Individual thought with expandable data
- `PhaseInsightReveal` - Structured phase summaries

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
- Reversed timeline order (newest at top)
- Active node header with pulsing indicator
- Expandable data sections for tool inputs/outputs
- Auto-scroll to newest thought
- Enhanced insights display via `parseThoughtContent()`
- Inline badges for confidence %, quality tiers, technologies

---

#### `components/fit-check/ComparisonChain.jsx` - Pipeline Progress

**Purpose**: Visual pipeline phase progress with insight summaries.

**Sub-Components**:
- `StepInsightSummary` - Compact insight display for completed phases

**Features**:
- Phase icons with completion checkmarks
- Progress indicators (pulsing for active, check for complete)
- Insight summaries showing key metrics per phase
- Phase-specific colors matching backend output

---

#### `components/fit-check/InsightCard.jsx` - Phase Insight Components

**Exported Components**:
| Component | Purpose |
|-----------|---------|
| `InsightCard` | Variant-based card (success/warning/info/error) |
| `ConfidenceBar` | Animated progress bar with color-coded confidence |
| `MetricBadge` | Compact metric display with icon and value |
| `TechTag` | Technology pill badge |

**ConfidenceBar Color Coding**:
| Range | Color |
|-------|-------|
| ≥70% | muted-teal (green) |
| 40-69% | amber-500 (yellow) |
| <40% | red-500 (red) |

---

#### `components/fit-check/ReasoningDialog.jsx` - Chain of Thought Dialog

**Purpose**: Full-screen modal displaying complete AI reasoning chain.

**Features**:
- Phase-grouped thoughts with visual timeline
- PhaseInsightCard with structured metrics display
- Confidence bars showing calibrated percentages
- Quality gate indicators with tier badges
- Technology tags extracted from research phases
- Expandable raw data sections
- Nested SystemPromptDialog for transparency
- Accessed via "Read the Reasoning" button (Brain icon)

---

#### `components/fit-check/SystemPromptDialog.jsx` - System Prompt Viewer

**Purpose**: Nested dialog showing system prompt for each pipeline phase.

**Features**:
- Fetches from backend `/api/prompts/{phase}` endpoint
- Syntax-highlighted XML display
- Copy to clipboard functionality
- Loading and error states
- Phase-specific icon and color theming

---

#### `components/fit-check/WorkflowPipelinePreview.jsx` - Pipeline Showcase

**Purpose**: Animated preview of 7-phase pipeline on left side of input panel.

**Features**:
- Looping animation through all pipeline phases
- Phase-specific colors and glow effects
- Checkmark completion indicators
- Pulsing active phase indicator
- Compact vertical layout with connector lines

---

#### `components/fit-check/ChainOfThoughtShowcase.jsx` - Floating Cards Preview

**Purpose**: Animated showcase of floating thought cards on right side of input panel.

**Features**:
- 6 mock thought cards cycling through visibility
- 3 cards visible simultaneously at staggered positions
- Fade-in/fade-out transitions
- Floating animation for visible cards
- Decorative SVG connection lines

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
  status: 'idle',
  statusMessage: '',
  thoughts: [],
  response: '',
  error: null,
  durationMs: null,
  currentPhase: null,
  phaseHistory: [],
  phaseProgress: {},
}
```

**Functions**:
- `submitQuery(query)` - Start SSE stream with model config
- `reset()` - Clear state for new query

**AI Settings Integration**:
- Uses `useAISettings` hook for model configuration
- Passes `model_id` and `config_type` in API request

**SSE Event Handling**:
| Event Type | Action |
|------------|--------|
| `phase` | Update `currentPhase`, set phase to 'active' |
| `phase_complete` | Mark phase 'complete', add to `phaseHistory` |
| `thought` | Append to `thoughts` array with phase context |
| `response` | Append chunk to `response` string |
| `complete` | Set status to 'complete', record `durationMs` |
| `error` | Set `error` object, transition to error state |

---

#### `hooks/use-ai-settings.js` - AI Model Settings Hook

**Purpose**: React context for global AI model configuration.

**AI Models**:
| Model ID | Label | Config Type | Badge |
|----------|-------|-------------|-------|
| `gemini-3-pro-preview` | Gemini 3 Pro (Preview) | reasoning | Recommended |
| `gemini-flash-latest` | Gemini Flash (Latest) | standard | Fast |

**Default Model**: `gemini-flash-latest`

**Provider**: `AISettingsProvider` (wraps app in layout.js)

**Hook Returns**:
- `selectedModel` - Current model ID
- `modelInfo` - Full model metadata
- `models` - All available models
- `updateModel(modelId)` - Switch model
- `getModelConfig()` - Returns `{ model_id, config_type }`

---

#### `lib/parseAIResponse.js` - Response Parser

**Purpose**: Parse AI response markdown into structured data.

**Function**: `parseAIResponse(rawResponse)`

**Returns**:
```javascript
{
  title: '',           // "Why I'm a Great Fit for..."
  strengths: [],       // Array of strength strings
  valueProposition: '', // Overview text
  growthAreas: [],     // Array of growth area strings
  callToAction: '',    // Final CTA text
  rawContent: ''       // Original response
}
```

---

#### `lib/phaseInsights.js` - Phase Insight Extraction

**Purpose**: Extract structured metadata from phase outputs.

**Exported Functions**:
| Function | Purpose |
|----------|---------|
| `extractPhaseInsights(phase, summary)` | Parse phase summaries into structured data |
| `parseThoughtContent(thought)` | Enhance thought objects with displayable summaries |
| `getPhaseDisplayMeta(phase)` | Get display metadata for a phase |

**Phase-Specific Extraction**:
| Phase | Extracted Data |
|-------|----------------|
| `connecting` | `queryType`, `company`, `jobTitle`, `isValid` |
| `deep_research` | `techCount`, `technologies[]`, `requirementsCount` |
| `research_reranker` | `qualityTier`, `dataScore`, `missingData[]` |
| `skeptical_comparison` | `gapsIdentified`, `strengthsFound`, `riskLevel` |
| `skills_matching` | `matchedCount`, `matchPercentage`, `learningGaps[]` |
| `confidence_reranker` | `confidence`, `qualityTier`, `qualityFlags[]` |
| `generate_results` | `wordCount` |

---

### Design System

**Custom Colors** (tailwind.config.js):
| Name | Hex | Usage |
|------|-----|-------|
| `eggshell` | `#f4f1de` | Light background |
| `burnt-peach` | `#e07a5f` | Primary accent |
| `twilight` | `#3d405b` | Dark text/background |
| `muted-teal` | `#81b29a` | Secondary accent (strengths) |
| `apricot` | `#f2cc8f` | Tertiary accent (growth areas) |

**Key Animations** (globals.css):
| Animation | Purpose |
|-----------|---------|
| `expandContainer` | Container width expansion |
| `panelExpandRight` | Panel slide-in |
| `slideUpCard` | Result card entrance |
| `cot-slide-in` | Chain of thought entrance |
| `showcasePanelLeft/Right` | Showcase panel slide-in |
| `pipelineNodeGlow` | Pipeline node glow |
| `showcaseCardFloat` | Floating thought card animation |

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

**Response** (SSE Stream):
```
event: phase
data: {"phase": "connecting", "message": "Classifying query..."}

event: thought
data: {"step": 1, "type": "reasoning", "content": "...", "phase": "connecting"}

event: phase_complete
data: {"phase": "connecting", "summary": "Query classified as 'company', company: Google", "duration_ms": 1021}

event: phase
data: {"phase": "deep_research", "message": "Gathering employer intelligence..."}

... (more phases) ...

event: response
data: {"chunk": "### Why I'm a Great Fit"}

event: complete
data: {"duration_ms": 27523, "confidence_score": 72}
```

---

## 🚀 Deployment

### Production URLs

| Service | URL | Type |
|---------|-----|------|
| Frontend | https://resweb-w8gqi.sevalla.page | Static Site |
| Backend | https://resbackend-bxeo7.sevalla.app | Web Application |

### Backend Deployment

1. Set environment variables in Sevalla Dashboard
2. Build and push Docker image:
   ```bash
   docker build -t bassn/res_backend:latest .
   docker push bassn/res_backend:latest
   ```
3. Verify: `curl https://resbackend-bxeo7.sevalla.app/health`

### Frontend Deployment

1. Copy production env: `copy .env.deployed .env.local`
2. Build static export: `npm run build`
3. Upload `/out` folder to Sevalla static hosting

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
| `GEMINI_MODEL` | ❌ | Model name (default: `gemini-3-pro-preview`) |

### Frontend (`res_web/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_BASE_URL` | ✅ | Frontend URL |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL |

> ⚠️ `NEXT_PUBLIC_*` variables are baked into static build. Rebuild required on change.

---

## 📝 Quick Reference

### Adding New Skills
Edit `res_backend/config/engineer_profile.py`:
```python
ENGINEER_PROFILE["skills"]["category"].append("New Skill")
```

### Modifying AI Behavior
Edit the relevant phase prompt in `res_backend/prompts/`:
- `phase_1_connecting.xml` - Query classification
- `phase_2_deep_research.xml` - Web search strategy
- `phase_2b_research_reranker.xml` - Quality gate thresholds
- `phase_3_skeptical_comparison.xml` - Gap analysis criteria
- `phase_4_skills_matching.xml` - Skill matching rules
- `phase_5b_confidence_reranker.xml` - Confidence calibration
- `phase_5_generate_results.xml` - Response format/tone

### Adding a New Pipeline Phase
1. Create prompt template in `res_backend/prompts/phase_X_name.xml`
2. Create node in `res_backend/services/nodes/name.py`
3. Export node from `res_backend/services/nodes/__init__.py`
4. Add node to graph in `res_backend/services/fit_check_agent.py`
5. Add routing function if phase has conditional exits
6. Update `FitCheckPipelineState` in `services/pipeline_state.py`
7. Add phase to `PHASE_ORDER` in `services/pipeline_state.py`
8. Add phase to frontend components:
   - `ChainOfThought.jsx` (PHASE_CONFIG)
   - `ComparisonChain.jsx` (PHASE_CONFIG, PHASE_ORDER)
   - `ThinkingPanel.jsx` (PHASE_DISPLAY_NAMES)
   - `ThoughtNode.jsx` (PHASE_COLORS)

### Switching AI Models
**Frontend**: Use Settings dialog (gear icon in header)

**Backend**: Set `GEMINI_MODEL` env var or pass `model_id` in request

### Running Tests
```bash
cd res_backend
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
XML prompts use Python `.format()` for variable substitution. Literal curly braces in JSON examples must be doubled:
```xml
<!-- WRONG -->
{"key": "value"}

<!-- CORRECT -->
{{"key": "value"}}
```

### Reranker Search Retry
The research_reranker can trigger up to 2 retry searches. The `search_attempt` counter must be incremented in both success and fallback return paths.

### Default Model
The default model is `gemini-flash-latest` in the frontend (`use-ai-settings.js`) but `gemini-3-pro-preview` in the backend (`config/llm.py`). The frontend setting takes precedence when making API calls.

---

*Last Verified: December 3, 2025*
