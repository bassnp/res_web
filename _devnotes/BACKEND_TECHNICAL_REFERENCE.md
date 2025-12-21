# Backend Technical Reference: Portfolio Fit Check API

## 1. System Overview
The Portfolio Backend is a high-performance FastAPI service powering the "See if I'm fit for you!" feature. It orchestrates a multi-phase AI agent using **LangGraph** and **Google Gemini** to analyze employer queries against a candidate's profile.

### Core Architecture
- **Framework**: FastAPI (Web), LangGraph (Agent Orchestration), LangChain (AI Abstraction).
- **LLM**: Google Gemini 3 (Flash/Pro) via `langchain-google-genai`.
- **Search**: Google Custom Search Engine (CSE).
- **Streaming**: Server-Sent Events (SSE) for real-time agent transparency.

---

## 2. Directory Structure
```text
backend/
├── server.py                # FastAPI entry point & middleware
├── requirements.txt         # Dependency manifest
├── Dockerfile               # Container definition
├── docker-compose.yml       # Service orchestration
├── config/
│   ├── engineer_profile.py  # Auto-generated candidate data
│   └── llm.py               # Gemini model configurations
├── models/
│   └── fit_check.py         # Pydantic schemas & SSE events
├── routers/
│   ├── fit_check.py         # SSE streaming endpoint
│   ├── prompts.py           # Prompt management API
│   └── examples.py          # Example query provider
├── services/
│   ├── fit_check_agent.py   # LangGraph pipeline definition
│   ├── pipeline_state.py    # TypedDict state schemas
│   ├── prompt_loader.py     # Model-specific prompt selection
│   ├── nodes/               # Pipeline phase implementations
│   ├── tools/               # Agent tools (Web Search, etc.)
│   └── utils/               # Circuit breakers, scoring, etc.
└── tests/                   # Integration, unit, and simulation tests
```

---

## 3. Configuration & Environment
### Environment Variables
| Variable | Purpose | Default |
| :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Gemini LLM authentication | **Required** |
| `GOOGLE_CSE_API_KEY` | Google Search API key | **Required** |
| `GOOGLE_CSE_ID` | Google Search Engine ID | **Required** |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3003` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `GEMINI_MODEL` | Default LLM model ID | `gemini-3-flash-preview` |

### LLM Configurations (`config/llm.py`)
- **Reasoning Config**: Native reasoning for Gemini 3 Pro/Flash. Disables "think step-by-step" to avoid double-think.
- **Standard Config**: Uses `temperature` (0.3) and `top_k` (40) for deterministic accuracy.

---

## 4. Data Models (`models/fit_check.py`)
### API Request: `FitCheckRequest`
- `query`: `str` (3-2000 chars) - Company name or job description.
- `include_thoughts`: `bool` (default: `True`) - Stream agent reasoning.
- `model_id`: `str` - Target Gemini model.
- `config_type`: `reasoning` | `standard`.

### SSE Event Contract (Canonical)
| Event | Data Schema | Description |
| :--- | :--- | :--- |
| `status` | `{"status": str, "message": str}` | Current pipeline phase. |
| `thought` | `{"type": str, "content": str}` | Tool calls, observations, reasoning. |
| `response` | `{"text": str}` | Final analysis text chunks. |
| `complete` | `{"duration": float}` | Successful termination. |
| `error` | `{"code": str, "message": str}` | Failure details. |

---

## 5. Core Logic: LangGraph Pipeline
The agent follows a directed acyclic graph (DAG) with conditional routing.

### Pipeline Topology
1. **CONNECTING**: Classifies query (Company vs. Job vs. Irrelevant).
   - *Route*: If `irrelevant` → **END**.
2. **DEEP_RESEARCH**: Expands queries and executes Google CSE searches.
3. **RESEARCH_RERANKER**: Scores search results (Relevance, Quality, Usefulness).
   - *Route*: If `SPARSE` → **DEEP_RESEARCH** (Retry up to 3 attempts).
   - *Route*: If `GARBAGE` → **GENERATE_RESULTS** (Early Exit).
   - *Route*: Otherwise → **CONTENT_ENRICH** (Always visited for frontend visibility).
4. **CONTENT_ENRICH**: Fetches full content for top-scored sources.
   - **Graceful Skip**: Emits phase events even when no sources available (`skipped: true`).
   - **Output**: `enriched_count`, `total_count`, `sources[]`, `success_rate`.
5. **SKEPTICAL_COMPARISON**: Devil's advocate analysis for gaps/risks.
6. **SKILLS_MATCHING**: Maps requirements to `ENGINEER_PROFILE`.
7. **CONFIDENCE_RERANKER**: LLM-as-a-Judge calibration of match scores.
8. **GENERATE_RESULTS**: Synthesizes final personalized response.

### Pipeline State (`services/pipeline_state.py`)
Uses `FitCheckPipelineState` (TypedDict) to pass data between nodes:
- `query_type`, `company_name`, `job_title`, `extracted_skills`.
- `employer_summary`, `tech_stack`, `culture_signals`.
- `genuine_strengths`, `genuine_gaps`, `risk_assessment`.
- `match_score`, `confidence_score`.

---

## 6. Services & Utilities
### Web Search Tool (`services/tools/web_search.py`)
- **Tool**: `web_search(query: str) -> str`.
- **Implementation**: Uses `GoogleSearchAPIWrapper` from `langchain-google-community`.
- **Configuration**: `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ID`.
- **Circuit Breaker**: `search_breaker` (Max 3 failures, 60s reset).
- **Behavior**: Returns top 5 results with snippets; falls back to "Search Unavailable" message if unconfigured.

### Parallel Scorer (`services/utils/parallel_scorer.py`)
- **Function**: `score_documents_parallel(documents: List[Dict], query: str) -> ScoringResult`.
- **Logic**: Evaluates documents concurrently using LLM.
- **Weights**: Relevance (50%), Quality (30%), Usefulness (20%).
- **Source Classification**: `classify_source(url: str)` returns `SourceType` and `extractability_multiplier` (e.g., Video: 0.8, Wiki: 1.2).

### Content Enrichment Node (`services/nodes/content_enrich.py`)
- **Phase**: 2C - Full content extraction from top research sources.
- **Behavior**: Fetches HTML content in parallel with semaphore-controlled concurrency.
- **Event Emission**: Always emits `on_phase` and `on_phase_complete` events, even when skipping.
- **Skip Handling**: When no top sources available, emits `skipped: true` with `skip_reason` for frontend transparency.
- **Output Data**: `enriched_count`, `total_count`, `total_kb`, `sources[]`, `success_rate`.

### Error Handling (`services/utils/error_handling.py`)
- **Base Class**: `PipelineError(message, category, phase, context)`.
- **Categories**: `RECOVERABLE`, `FATAL`, `EXTERNAL`, `VALIDATION`.
- **Node Wrapper**: `handle_node_error` catches exceptions and updates state with `error_info`.

### Callbacks (`services/callbacks.py`)
- **Interface**: `ThoughtCallback`.
- **Key Methods**:
    - `on_status(status, message)`: Phase transitions.
    - `on_thought(step, type, content, tool, tool_input)`: Reasoning steps.
    - `on_response_chunk(chunk)`: Streaming text.
    - `on_error(code, message)`: Failure reporting.

---

## 7. API Surface
### `POST /api/fit-check/stream`
- **Endpoint**: `routers.fit_check.stream_fit_check`.
- **Input**: `FitCheckRequest`.
- **Output**: `StreamingResponse` (SSE).
- **Behavior**:
    1. Validates query length and security patterns.
    2. Initializes `StreamingCallbackHandler`.
    3. Executes `build_fit_check_pipeline`.
    4. Streams events: `status` → `thought` → `response` → `complete`.

### `GET /health`
- **Endpoint**: `server.health_check`.
- **Response**: `{"status": "healthy", "timestamp": float}`.

### `GET /api/prompts`
- **Endpoint**: `routers.prompts.list_prompts`.
- **Description**: Returns metadata about available XML prompt templates.

---

## 8. Infrastructure & Deployment
- **Dockerfile**: Multi-stage build using `python:3.13-slim`.
- **Docker Compose**: Orchestrates `api` service on port 8000.
- **Testing**:
    - **Unit**: `tests/unit/` (Node-level logic).
    - **Integration**: `tests/integration/` (Full pipeline flow).
    - **Simulation**: `tests/simulation/` (SSE event flow and accuracy validation).
- **Circuit Breakers**: `services/utils/circuit_breaker.py` uses `tenacity` for retries and custom state for breaking.

---

## 9. Accuracy & Validation
### Documentation Protocol
- **Verifiability**: Every symbol and behavior documented is cross-referenced with `backend/` source code.
- **Types**: Reflect actual Pydantic models and TypedDict definitions in `models/` and `services/pipeline_state.py`.
- **Omissions**: Trivial boilerplate (e.g., `__init__.py` contents) and standard library imports are omitted for density.

### System Integrity
- **Anti-Sycophancy**: Phase 3 (`SKEPTICAL_COMPARISON`) is specifically designed to identify gaps and risks, preventing the LLM from being overly agreeable.
- **Confidence Calibration**: Phase 5B (`CONFIDENCE_RERANKER`) uses LLM-as-a-Judge to calibrate match scores against evidence, ensuring high-confidence results.
- **Security**: Pre-LLM pattern matching in `connecting.py` prevents prompt injection and harmful content before reaching the LLM.

### Prompt Format (`prompts/phase_5_generate_results_concise.xml`)
- **Output Format**: Uses `**Key Strengths**` and `**Growth Opportunities**` (bold markdown headers).
- **Bullet Depth**: Each bullet 25-40 words with format: **[Tech]**: [evidence] → [outcome] → [employer relevance].
- **Strength Format**: Technology + What was built → Key outcome → Employer stack alignment.
- **Gap Format**: Missing skill → Gap context → Transferable bridge → Ramp-up timeframe estimate.
- **Word Limit**: 250-400 words total - concise yet insightful, scannable in 60 seconds.
- **Data Injection**: Template receives `{genuine_strengths}`, `{genuine_gaps}`, `{calibrated_score}`, `{confidence_tier}`.
- **Alignment**: Format designed to match frontend `parseAIResponse.js` parser expectations.
