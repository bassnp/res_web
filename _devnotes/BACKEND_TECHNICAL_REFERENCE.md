````markdown
# Backend Technical Reference: Portfolio Fit Check API

## 1. System Overview
The Portfolio Backend is a high-performance FastAPI service powering the "See if I'm fit for you!" feature. It orchestrates a multi-phase AI agent using **LangGraph** and **Google Gemini** to analyze employer queries against a candidate's profile.

### Core Architecture
- **Framework**: FastAPI (Web), LangGraph (Agent Orchestration), LangChain (AI Abstraction).
- **LLM**: Google Gemini 3 (Flash/Pro) via `langchain-google-genai`.
- **Search**: Google Custom Search Engine (CSE).
- **Streaming**: Server-Sent Events (SSE) for real-time agent transparency.
- **Concurrency**: Multi-session capable with isolated callback holders per request.

---

## 2. Directory Structure
```text
backend/
├── server.py                # FastAPI entry point & middleware
├── requirements.txt         # Dependency manifest
├── Dockerfile               # Container definition (Sevalla-optimized)
├── docker-compose.yml       # Local development orchestration
├── pytest.ini               # Test configuration
├── config/
│   ├── engineer_profile.py  # Auto-generated candidate data
│   └── llm.py               # Gemini model configurations & LLM throttling
├── models/
│   └── fit_check.py         # Pydantic schemas, SSE events, scoring models
├── routers/
│   ├── fit_check.py         # SSE streaming endpoint with session tracking
│   ├── prompts.py           # Prompt management API
│   └── examples.py          # Example query provider
├── services/
│   ├── fit_check_agent.py   # LangGraph pipeline definition (stateless)
│   ├── pipeline_state.py    # TypedDict state schemas & phase order
│   ├── prompt_loader.py     # Model-specific prompt selection (concise/full)
│   ├── callbacks.py         # ThoughtCallback interface
│   ├── streaming_callback.py # SSE event emission handler
│   ├── metrics.py           # Prometheus-compatible observability metrics
│   ├── nodes/               # Pipeline phase implementations
│   │   ├── connecting.py        # Phase 1: Query classification
│   │   ├── deep_research.py     # Phase 2: Web research with CSE
│   │   ├── research_reranker.py # Phase 2B: Quality scoring & pruning
│   │   ├── content_enrich.py    # Phase 2C: Full content extraction
│   │   ├── skeptical_comparison.py # Phase 3: Gap/risk analysis
│   │   ├── skills_matching.py   # Phase 4: Skill/experience mapping
│   │   ├── confidence_reranker.py # Phase 5B: LLM-as-Judge calibration
│   │   └── generate_results.py  # Phase 5: Final response synthesis
│   ├── tools/               # Agent tools
│   │   ├── web_search.py        # Google CSE wrapper with circuit breaker
│   │   ├── skill_matcher.py     # Profile skill matching
│   │   └── experience_matcher.py # Profile experience matching
│   └── utils/               # Utilities
│       ├── circuit_breaker.py   # AsyncCircuitBreaker for fault tolerance
│       ├── query_expander.py    # CSE-optimized query generation
│       ├── parallel_scorer.py   # Concurrent document scoring
│       └── error_handling.py    # Categorized error management
└── tests/                   # Comprehensive test suite
    ├── unit/                    # Node-level tests
    ├── integration/             # Full pipeline tests (including concurrency)
    ├── simulation/              # SSE event flow and accuracy validation
    └── performance/             # Benchmark tests
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
- **LLM Throttling**: `with_llm_throttle()` limits concurrent LLM calls via semaphore.
- **LLM Circuit Breaker**: `llm_breaker` (5 failures, 30s reset) protects against cascading failures.

---

## 4. Multi-Session Architecture

### Session Isolation (Critical)
Each concurrent request is fully isolated with no shared mutable state:

```python
# services/fit_check_agent.py
class FitCheckAgent:
    def __init__(self):
        pass  # Stateless - no shared _callback_holder

    async def stream_analysis(self, query, callback, ...):
        # CREATE ISOLATED callback holder PER REQUEST
        callback_holder = {"callback": callback}
        pipeline = build_fit_check_pipeline(callback_holder)
        # ... execution with request-local holder
```

### Concurrency Safety Components

| Component | Location | Protection |
|-----------|----------|------------|
| `AsyncCircuitBreaker` | `utils/circuit_breaker.py` | Async-safe with `asyncio.Lock` |
| `search_breaker` | `tools/web_search.py` | 3 failures, 60s reset |
| `llm_breaker` | `utils/circuit_breaker.py` | 5 failures, 30s reset |
| `content_breaker` | `utils/circuit_breaker.py` | 10 failures, 120s reset |
| `get_llm_semaphore()` | `config/llm.py` | Limits concurrent LLM calls |

### Session ID Tracking
- **Request Model**: `FitCheckRequest.session_id` (optional, auto-generated via `uuid.uuid4()`).
- **Logging**: All log entries include `session_id` for request tracing.
- **Header Support**: `X-Session-ID` header for client-provided session tracking.

---

## 5. Data Models (`models/fit_check.py`)
### API Request: `FitCheckRequest`
- `query`: `str` (3-2000 chars) - Company name or job description.
- `include_thoughts`: `bool` (default: `True`) - Stream agent reasoning.
- `model_id`: `str` - Target Gemini model.
- `config_type`: `reasoning` | `standard`.
- `session_id`: `Optional[str]` - Session ID for request tracing.

### Document Scoring: `DocumentScore`
- `document_id`: Unique identifier.
- `relevance_score`, `quality_score`, `usefulness_score`: 0.0-1.0 range.
- `raw_composite`, `final_score`: Weighted composite scores.
- `extractability_multiplier`: Source-type adjustment (0.8-1.2).
- `source_type`: `SourceType` enum (VIDEO, SOCIAL_MEDIA, WIKI, etc.).
- `scoring_rationale`: LLM reasoning for scores.

### SSE Event Contract (Canonical)
| Event | Data Schema | Description |
| :--- | :--- | :--- |
| `phase` | `{"phase": str, "message": str, "data": dict}` | Phase start with metadata. |
| `phase_complete` | `{"phase": str, "data": dict}` | Phase completion with output. |
| `thought` | `{"step": int, "type": str, "content": str}` | Tool calls, observations, reasoning. |
| `response` | `{"text": str}` | Final analysis text chunks. |
| `complete` | `{"duration_ms": int}` | Successful termination. |
| `error` | `{"code": str, "message": str}` | Failure details. |

---

## 6. Core Logic: LangGraph Pipeline
The agent follows a directed acyclic graph (DAG) with conditional routing.

### Pipeline Topology
```
START → connecting → (route) → deep_research → research_reranker → (route)
      → content_enrich → skeptical_comparison → skills_matching 
      → confidence_reranker → generate_results → END
```

### Phase Details

| Phase | Node | Purpose | Key Outputs |
|-------|------|---------|-------------|
| 1 | `connecting` | Query classification | `query_type`, `company_name`, `extracted_skills` |
| 2 | `deep_research` | Web research via CSE | `employer_summary`, `tech_stack`, `culture_signals` |
| 2B | `research_reranker` | Quality scoring & routing | `data_status` (CLEAN/SPARSE/GARBAGE), `top_sources` |
| 2C | `content_enrich` | Full content extraction | `enriched_content`, `enriched_count`, `success_rate` |
| 3 | `skeptical_comparison` | Gap/risk analysis | `genuine_gaps`, `genuine_strengths`, `risk_assessment` |
| 4 | `skills_matching` | Profile alignment | `matched_skills`, `unmatched_skills`, `overall_match_score` |
| 5B | `confidence_reranker` | LLM-as-Judge calibration | `calibrated_score`, `confidence_tier`, `quality_flags` |
| 5 | `generate_results` | Final synthesis | `final_response` (streaming markdown) |

### Routing Logic

1. **After Connecting**:
   - `irrelevant` → **END** (query rejected)
   - Valid → **deep_research**

2. **After Research Reranker**:
   - `SPARSE` (iteration < 3) → **deep_research** (enhanced retry)
   - `GARBAGE` → **generate_results** (early exit with warning)
   - `CLEAN`/`PARTIAL` → **content_enrich**

3. **Job Description Optimization**:
   - For job descriptions with ≥2 extracted skills, proceeds regardless of web research quality.

### Pipeline State (`services/pipeline_state.py`)
Uses `FitCheckPipelineState` (TypedDict) to pass data between nodes:
- **Query Info**: `query`, `query_type`, `company_name`, `job_title`, `extracted_skills`.
- **Research Data**: `employer_summary`, `tech_stack`, `culture_signals`, `identified_requirements`.
- **Scoring**: `top_sources` (List[DocumentScore]), `enriched_content`.
- **Analysis**: `genuine_strengths`, `genuine_gaps`, `risk_assessment`.
- **Output**: `match_score`, `calibrated_score`, `confidence_tier`, `final_response`.
- **Control**: `current_phase`, `step_count`, `iteration_count`, `should_abort`.

---

## 7. Services & Utilities

### Circuit Breakers (`services/utils/circuit_breaker.py`)
```python
class AsyncCircuitBreaker:
    """Async-safe circuit breaker with state management."""
    
    # States: CLOSED → OPEN (on failures) → HALF_OPEN (on reset) → CLOSED
    # Thread-safe via asyncio.Lock
    
    async def call(self):
        """Context manager for protected calls."""
        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit [{self._name}] is OPEN")
        # ... execute with failure tracking
```

**Configured Breakers**:
- `search_breaker`: 3 failures, 60s reset (Google CSE protection).
- `llm_breaker`: 5 failures, 30s reset (Gemini API protection).
- `content_breaker`: 10 failures, 120s reset (HTTP fetch protection).

### Query Expansion (`services/utils/query_expander.py`)
- **Function**: `expand_queries(phase_1_output, original_query, iteration) -> QueryExpansionResult`
- **Output**: 3-5 CSE-optimized queries with operators.
- **Operators**: `intitle:`, `site:`, `-site:`, exact phrase quotes.
- **Iteration Reformulation**: Broadens queries on retry (removes operators).

### Web Search Tool (`services/tools/web_search.py`)
- **Function**: `web_search_structured(query: str) -> str`
- **Implementation**: Uses `GoogleSearchAPIWrapper` from `langchain-google-community`.
- **Circuit Protection**: Wrapped with `search_breaker` for fault tolerance.
- **Domain Exclusions**: Filters Pinterest, Facebook, Instagram, etc.

### Parallel Scorer (`services/utils/parallel_scorer.py`)
- **Function**: `score_documents_parallel(documents, query) -> List[DocumentScore]`
- **Concurrency**: Async gather with semaphore limiting.
- **Scoring Weights**: Relevance (50%), Quality (30%), Usefulness (20%).
- **Source Types**: `classify_source(url)` returns type-specific multipliers.

### Metrics (`services/metrics.py`)
Prometheus-compatible metrics (optional `prometheus_client` dependency):
- `fit_check_active_sessions`: Gauge for concurrent sessions.
- `fit_check_requests_total`: Counter by status (success/error/timeout).
- `fit_check_request_duration_seconds`: Histogram for request latency.
- `fit_check_phase_completions_total`: Counter by phase and status.
- `fit_check_llm_calls_total`: Counter by model and status.
- `fit_check_circuit_breaker_state`: Gauge for circuit states.

---

## 8. API Surface

### `POST /api/fit-check/stream`
- **Endpoint**: `routers.fit_check.stream_fit_check`
- **Input**: `FitCheckRequest`
- **Output**: `StreamingResponse` (SSE)
- **Behavior**:
    1. Generates session_id if not provided.
    2. Initializes `StreamingCallbackHandler` with session_id.
    3. Creates isolated callback holder for this request.
    4. Executes `build_fit_check_pipeline` with isolated holder.
    5. Streams events: `phase` → `thought` → `response` → `complete`.
- **Timeout**: 5-minute maximum per request.
- **Disconnect Handling**: Graceful cleanup on client disconnect.

### `GET /health`
- **Endpoint**: `server.health_check`
- **Response**: `{"status": "healthy", "timestamp": float}`

### `GET /api/prompts`
- **Endpoint**: `routers.prompts.list_prompts`
- **Description**: Returns metadata about available XML prompt templates.

### `GET /metrics` (Optional)
- **Endpoint**: Prometheus metrics exposition (if `prometheus_client` installed).

---

## 9. Infrastructure & Deployment

### Sevalla PaaS Deployment
The backend is optimized for Sevalla Docker Application deployment:

- **Dockerfile**: Optimized CMD for SSE streaming:
  ```dockerfile
  CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", 
       "--workers", "1", "--timeout-keep-alive", "75"]
  ```
- **Workers**: Single worker (async handles concurrency internally).
- **Keep-Alive**: Extended to 75s for long SSE connections.

**Sevalla Handles Automatically**:
- ✅ SSL/HTTPS certificates
- ✅ Reverse proxy / load balancing
- ✅ CDN for static assets
- ✅ Health check endpoints (`/health`)
- ✅ Environment variables (dashboard UI)
- ✅ Git-based auto-deployments

### Testing
- **Unit Tests**: `tests/unit/` - Node-level logic (226+ tests).
- **Integration Tests**: `tests/integration/` - Full pipeline flow, concurrency tests.
- **Simulation Tests**: `tests/simulation/` - SSE event flow validation.
- **Run**: `pytest tests/unit/ tests/integration/ -v`

---

## 10. Accuracy & Validation

### Anti-Sycophancy Measures
- **Phase 3 (Skeptical Comparison)**: Specifically identifies gaps and risks.
- **Phase 5B (Confidence Reranker)**: LLM-as-a-Judge calibrates scores against evidence.
- **Quality Flags**: `high_risk_unaddressed`, `sparse_tech_stack`, `low_evidence` flags propagate to output.

### Security
- **Pre-LLM Validation**: Pattern matching in `connecting.py` blocks prompt injection.
- **Input Validation**: Pydantic models enforce length limits (3-2000 chars).
- **Query Sanitization**: Malicious patterns trigger early rejection.

### Prompt Format (`prompts/phase_5_generate_results_concise.xml`)
- **Output**: Markdown with `**Key Strengths**` and `**Growth Opportunities**`.
- **Bullet Format**: **[Tech]**: [evidence] → [outcome] → [employer relevance].
- **Word Limit**: 250-400 words (scannable in 60 seconds).
- **Data Injection**: `{genuine_strengths}`, `{genuine_gaps}`, `{calibrated_score}`, `{confidence_tier}`.

---

## 11. Change Log

### Multi-Session Upgrade (2025-12-20)
**Phase 1: Session Isolation** ✅
- Removed shared `_callback_holder` from `FitCheckAgent`.
- Each request creates isolated callback holder.
- No cross-session contamination.

**Phase 2: Concurrency Safety** ✅
- `AsyncCircuitBreaker` with async-safe locking.
- LLM throttling via semaphore.
- Graceful timeout handling (5-minute max).

**Phase 3: Observability** ✅
- Prometheus metrics (`services/metrics.py`).
- Session ID tracking in logs.
- Circuit breaker state monitoring.

**Phase 4: Sevalla Deployment** ✅
- Dockerfile optimized for SSE.
- Environment variable configuration.
- Single-worker async model.
````
