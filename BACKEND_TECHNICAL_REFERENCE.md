# Backend Technical Reference: Portfolio Fit-Check System

## 1. System Overview
The Portfolio Backend is a high-precision AI agent system built with **FastAPI** and **LangGraph**. It analyzes employer queries (company names or job descriptions) against an engineer's profile to determine fit. The system uses **Google Gemini** (3 Flash/Pro) with a multi-phase pipeline, streaming real-time reasoning and results via **Server-Sent Events (SSE)**.

### Core Architecture
- **API Layer**: FastAPI handles requests and SSE streaming.
- **Orchestration**: LangGraph manages a 5-phase stateful pipeline with conditional routing and error recovery.
- **LLM Integration**: `ChatGoogleGenerativeAI` with model-specific prompt variants (concise for reasoning models, verbose for standard).
- **Resilience**: Circuit breakers and adaptive retries for external tool calls (Tavily search).

---

## 2. Directory Structure
```text
backend/
├── config/                 # System & LLM configuration
├── middleware/             # FastAPI middleware (CORS, etc.)
├── models/                 # Pydantic schemas for API & internal state
├── prompts/                # XML-based prompt templates (Phase 1-5)
├── routers/                # API route definitions (Fit Check, Examples)
├── services/               # Core business logic
│   ├── nodes/              # LangGraph pipeline nodes (Phase logic)
│   ├── tools/              # Agent tools (Web search, Skill matching)
│   └── utils/              # Utilities (Parsing, Error handling, Circuit breaker)
├── tests/                  # Multi-level test suite (Unit, Integration, Simulation)
├── server.py               # Application entry point
├── Dockerfile              # Container definition
├── docker-compose.yml      # Infrastructure orchestration
├── requirements.txt        # Python dependencies
├── pytest.ini              # Test configuration
├── run_docker_rebuild.bat  # Infrastructure management script
└── run_docker_sync.bat     # Fast-sync development script
```

---

## 3. Configuration & Environment
| Variable | Default | Description |
| :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Required | API key for Google Gemini models. |
| `TAVILY_API_KEY` | Required | API key for Tavily web search. |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Primary LLM for agent phases. |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR). |
| `ALLOWED_ORIGINS` | `http://localhost:3003` | CORS allowed origins (comma-separated). |

### LLM Config (`config/llm.py`)
- **Reasoning Config**: Used for Gemini 3 Pro/Flash. Disables explicit "think step-by-step" to leverage native reasoning.
- **Standard Config**: Used for Flash-Lite. Uses temperature (0.3) and Top-K (40) for deterministic output.

---

## 4. Data Models (`models/fit_check.py`)
### API Request/Response
- `FitCheckRequest`: `query` (3-2000 chars), `include_thoughts` (bool), `model_id` (str), `config_type` (reasoning/standard).
- **SSE Events**:
    - `StatusEvent`: `status` (connecting, researching, etc.), `message`.
    - `ThoughtEvent`: `type` (tool_call, observation, reasoning), `content`.
    - `ResponseEvent`: `chunk` (text).
    - `CompleteEvent`: `duration`, `final_status`.
    - `ErrorEvent`: `code`, `message`.

### Pipeline State (`services/pipeline_state.py`)
`FitCheckPipelineState` (TypedDict) tracks the complete lifecycle:
- **Metadata**: `query: str`, `model_id: str`, `start_time: float`.
- **Phase Outputs**: 
    - `phase_1_connecting: Phase1Output` (query_type, company_name, job_title, extracted_skills).
    - `phase_2_deep_research: Phase2Output` (employer_summary, requirements, tech_stack).
    - `phase_3_skeptical_comparison: Phase3Output` (strengths, gaps, risk_assessment).
- **Routing**: `next_phase: str`, `is_complete: bool`, `error: Optional[str]`.
- **Quality**: `data_quality: Literal["CLEAN", "PARTIAL", "SPARSE", "GARBAGE"]`.

---

## 5. Agent Workflow (LangGraph)
The pipeline is defined in `services/fit_check_agent.py`.

### Core Functions
- `build_fit_check_pipeline(callback_holder: Dict) -> CompiledGraph`: Constructs the LangGraph with all nodes and conditional edges.
- `get_agent(model_id: str, config_type: str) -> CompiledGraph`: Factory function to retrieve a configured agent instance.
- `create_node_wrapper(node_func, callback_holder, phase_name) -> Callable`: Wraps async nodes for LangGraph compatibility and error handling.

### Graph Topology
1. **START** → `connecting`
2. `connecting` → `deep_research` (if `query_type` != "irrelevant") OR **END**
3. `deep_research` → `research_reranker`
4. `research_reranker` → `skeptical_comparison` (if `data_quality` >= PARTIAL) OR `deep_research` (retry if SPARSE) OR `generate_results` (if GARBAGE)
5. `skeptical_comparison` → `skills_matching`
6. `skills_matching` → `confidence_reranker`
7. `confidence_reranker` → `generate_results`
8. `generate_results` → **END**

### Phase Details
| Phase | Node Function | Responsibility |
| :--- | :--- | :--- |
| 1 | `connecting_node` | Query classification, entity extraction, security validation. |
| 2 | `deep_research_node` | Multi-query web research via Tavily, requirement synthesis. |
| 2B | `research_reranker_node` | LLM-as-a-Judge quality check, data pruning, retry routing. |
| 3 | `skeptical_comparison_node` | Critical gap analysis, anti-sycophancy check, risk scoring. |
| 4 | `skills_matching_node` | Requirement-to-skill mapping, match score calculation. |
| 5B | `confidence_reranker_node` | Calibration of match confidence using LLM-as-a-Judge. |
| 5 | `generate_results_node` | Final synthesis of personalized fit analysis response. |

---

## 6. API Surface
### `POST /api/fit-check/stream`
- **Handler**: `stream_fit_check(request: FitCheckRequest) -> StreamingResponse`
- **Logic**:
    1. Validates `FitCheckRequest` using Pydantic.
    2. Initializes `StreamingCallbackHandler` for SSE formatting.
    3. Executes LangGraph pipeline via `agent.astream()`.
    4. Formats and yields SSE events: `status` → `thought` → `response` → `complete`.

### `GET /health`
- **Handler**: `health_check() -> Dict[str, str]`
- **Returns**: `{"status": "healthy", "timestamp": "..."}`.

---

## 7. Services & Utilities
### Tools (`services/tools/`)
- `web_search(queries: List[str]) -> List[Dict]`: Executes parallel Tavily searches with domain filtering.
- `skill_matcher(requirements: List[str]) -> List[Dict]`: Semantic matching of skills using vector similarity or LLM.
- `experience_matcher(requirements: List[str]) -> List[Dict]`: Maps candidate projects to employer needs.

### Utilities (`services/utils/`)
- `llm_breaker`: `CircuitBreaker` instance for LLM API calls.
- `load_prompt(phase: str, config: str) -> str`: Loads model-specific XML templates.
- `handle_node_error(e: Exception, phase: str, state: State) -> Dict`: Graceful recovery and error state mutation.
- `get_response_text(response: Any) -> str`: Robust extraction of text from various LLM response formats.

---

## 8. Infrastructure & Deployment
- **Containerization**: `Dockerfile` uses `python:3.11-slim`.
- **Orchestration**: `docker-compose.yml` manages the API service and environment.
- **Sync Scripts**:
    - `run_docker_rebuild.bat`: Full clean rebuild of the container.
    - `run_docker_sync.bat`: Fast sync for code changes without full rebuild.

---

## 9. Testing Strategy
- **Unit Tests**: Individual node logic and utility functions.
- **Integration Tests**: End-to-end pipeline execution with mocked LLM.
- **Simulation Tests**: High-volume testing of agent behavior across diverse query types.
- **Performance Tests**: Latency and token usage monitoring.
