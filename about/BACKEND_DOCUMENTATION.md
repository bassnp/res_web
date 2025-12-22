# Backend Technical Documentation: Fit Check System

## 1. System Overview
The backend is a FastAPI-based service orchestrating a multi-phase AI agent pipeline using **LangGraph**. It analyzes employer queries (company names or job descriptions) against a pre-defined engineer profile to determine "fit". The system uses **Google Gemini** (3 Pro/Flash) and streams real-time reasoning and results via **Server-Sent Events (SSE)**.

**Core Stack:** FastAPI, LangGraph, LangChain, Pydantic, Google Gemini API, Docker.

---

## 2. Directory Structure
```
backend/
├── server.py                # FastAPI entry point & app configuration
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container definition
├── docker-compose.yml       # Service orchestration
├── pytest.ini               # Pytest configuration
├── .dockerignore            # Docker ignore rules
├── run_docker_*.bat         # Docker management scripts (rebuild, refresh, sync)
├── config/                  # System configuration
│   ├── engineer_profile.py  # Auto-generated engineer data (Single Source of Truth)
│   └── llm.py               # Gemini LLM factory & rate limiting
├── models/                  # Pydantic schemas & SSE event models
│   └── fit_check.py         # API request/response & scoring models
├── routers/                 # API endpoint definitions
│   ├── fit_check.py         # Main SSE streaming endpoint
│   ├── prompts.py           # Prompt management utilities
│   └── examples.py          # Example query provider
├── services/                # Core business logic
│   ├── fit_check_agent.py   # LangGraph pipeline orchestration
│   ├── pipeline_state.py    # TypedDict state definitions for the graph
│   ├── prompt_loader.py     # Model-specific prompt selection logic
│   ├── callbacks.py         # SSE event generation & streaming
│   ├── nodes/               # Individual pipeline phase implementations
│   │   ├── connecting.py, deep_research.py, research_reranker.py, 
│   │   ├── skeptical_comparison.py, skills_matching.py, 
│   │   ├── confidence_reranker.py, generate_results.py
│   ├── tools/               # Agent tools (web search, matching)
│   └── utils/               # Shared utilities (circuit breaker, scoring)
└── tests/                   # Comprehensive test suite (unit, integration, simulation)
```

---

## 3. Configuration
### 3.1 LLM Configuration (`config/llm.py`)
- **Models:** Supports `gemini-3-pro-preview` (reasoning) and `gemini-3-flash-preview` (standard/reasoning).
- **Throttling:** Global `asyncio.Semaphore` (default 10) limits concurrent API calls.
- **Variants:** `reasoning` config (thinking_config) vs `standard` config (temp/topK).

### 3.2 Engineer Profile (`config/engineer_profile.py`)
- **Source:** Auto-generated from `profile/*.json` via `scripts/generate-profile-config.py`.
- **Content:** Skills (Languages, Frameworks, AI/ML, Cloud), Experience Summary, Notable Projects.

---

## 4. Data Models & State
### 4.1 API Models (`models/fit_check.py`)
- `FitCheckRequest`: `query` (3-2000 chars), `include_thoughts` (bool), `model_id`, `config_type`.
- **SSE Events:** `status`, `thought` (tool_call, observation, reasoning), `response` (chunks), `complete`, `error`.

### 4.2 Pipeline State (`services/pipeline_state.py`)
`FitCheckPipelineState` (TypedDict) tracks:
- `query`, `session_id`, `config_type`.
- `phase_outputs`: Dict mapping phase names to their specific outputs (Phase1Output to Phase5Output).
- `messages`: Annotated list of `BaseMessage` for LangGraph history.
- `errors`: List of phase-specific errors.
- `metadata`: Execution timing and quality flags.

---

## 5. Core Logic: Fit Check Agent (`services/fit_check_agent.py`)
The agent is a directed graph with conditional routing.

### 5.1 Pipeline Phases (Nodes)
1.  **Connecting (`connecting.py`):** Validates input (security/relevance). Classifies as `company`, `job_description`, or `irrelevant`.
2.  **Deep Research (`deep_research.py`):** Executes web searches via Google CSE. Synthesizes employer summary, requirements, and tech stack.
3.  **Research Reranker (`research_reranker.py`):** Evaluates research quality. Routes to:
    - `CONTINUE`: Sufficient data found.
    - `RETRY`: Sparse data, triggers enhanced search.
    - `EARLY_EXIT`: Garbage/unreliable data.
4.  **Skeptical Comparison (`skeptical_comparison.py`):** Anti-sycophancy phase. Identifies genuine gaps and unverified claims.
5.  **Skills Matching (`skills_matching.py`):** Maps candidate skills to requirements with match scores.
6.  **Confidence Reranker (`confidence_reranker.py`):** LLM-as-a-Judge calibration of match scores and risk assessment.
7.  **Generate Results (`generate_results.py`):** Final synthesis of personalized fit analysis.

---

## 6. API Surface
### 6.1 SSE Stream (`POST /api/fit-check/stream`)
- **Input:** `FitCheckRequest` JSON.
- **Output:** `text/event-stream`.
- **Logic:** Initializes `StreamingCallbackHandler`, builds LangGraph, and streams events as nodes execute.
- **Streaming Mechanism:** `StreamingCallbackHandler` uses an `asyncio.Queue` to buffer events (`status`, `thought`, `response`, `complete`, `error`) which are then yielded as SSE-formatted strings.

### 6.2 Utility Endpoints
- `GET /health`: Returns system status and Prometheus availability.
- `GET /api/prompts/list`: Lists available prompt templates.
- `GET /api/examples/list`: Returns curated example queries for the frontend.

---

## 7. Services & Utilities
### 7.1 Parallel Scorer (`services/utils/parallel_scorer.py`)
- Concurrently scores search results on **Relevance (50%)**, **Quality (30%)**, and **Usefulness (20%)**.
- Uses `SourceType` classification (Video, Wiki, Social Media, etc.) with extractability multipliers.

### 7.2 Circuit Breaker (`services/utils/circuit_breaker.py`)
- Prevents cascading failures during LLM outages.
- Threshold: 5 failures; Reset timeout: 60s.

### 7.3 Error Handling (`services/utils/error_handling.py`)
- `handle_node_error`: Centralized error handler for LangGraph nodes.
- Maps exceptions to `ErrorEvent` with specific codes (LLM_ERROR, TOOL_ERROR, VALIDATION_ERROR).
- Ensures the SSE stream is gracefully closed with an error event.

### 7.4 Prompt Loader (`services/prompt_loader.py`)
- Selects `_concise.xml` for reasoning models to prevent "double-think" and `verbose.xml` for standard models.

### 7.4 Tools (`services/tools/`)
- `web_search.py`: Interface for Google Custom Search Engine.
- `skill_matcher.py`: Logic for comparing extracted requirements against `ENGINEER_PROFILE`.

---

## 8. External Integrations
- **Google Gemini API:** Primary LLM for all pipeline phases.
- **Google Custom Search Engine (CSE):** Used in `deep_research` phase for real-time employer data.
- **Prometheus:** (Optional) Metrics collection for request counts and latencies.

---

## 9. Infrastructure
- **Docker:** Multi-stage build for Python 3.13-slim.
- **Environment:** Configured via `.env` (GEMINI_API_KEY, GOOGLE_CSE_ID, GOOGLE_API_KEY).
- **Logging:** Structured JSON logging for production; human-readable for dev.
