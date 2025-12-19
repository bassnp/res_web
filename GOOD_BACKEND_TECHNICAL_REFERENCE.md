# AI Deep Researcher - Backend Technical Reference

> **Generated**: 2024-12-18 | **Framework**: FastAPI + LangGraph | **Lines**: ~1500

---

## 1. System Overview

### Architecture Summary
AI Deep Researcher is a multi-agent research pipeline using LangGraph for orchestration. The system implements a cyclic graph pattern with:
- **Entry Gate**: Classifier node for intent routing and safety filtering
- **Research Loop**: Search → ReRank → Enrich → Sufficiency Check (cycles until quality threshold met)
- **Synthesis**: Compression → Generator → Structured output (ResearchReport)

### Core Technologies
| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI (async) |
| Agent Framework | LangGraph StateGraph |
| LLM Provider | Google Gemini (gemini-3-pro-preview, gemini-flash-latest) |
| Session Persistence | Redis (RedisSaver) / Memory fallback |
| Authentication | Firebase Admin SDK + Backend JWT |
| Rate Limiting | SlowAPI with Redis backend |

### Model Configuration (Strict Two-Model Stack)
| Role | Model | Purpose |
|------|-------|---------|
| Classifier | gemini-3-pro-preview | Intent detection, query expansion |
| ReRanker | gemini-flash-latest | Document scoring (parallel) |
| Compressor | gemini-3-pro-preview | Fact extraction, summarization |
| Generator | gemini-3-pro-preview | Report synthesis |
| Chitchat | gemini-flash-latest | Conversational responses |

---

## 2. Directory Structure

```
backend/
├── server.py              # FastAPI entrypoint
├── config.py              # Configuration constants, model settings
├── lifespan.py            # Application lifecycle (startup/shutdown)
├── limiter.py             # Rate limiting configuration
├── __init__.py            # Package marker
├── Dockerfile             # Container build
├── docker-compose.yml     # Multi-container orchestration
├── requirements.txt       # Python dependencies
├── dependencies/
│   ├── __init__.py
│   └── auth.py            # FastAPI auth dependencies
├── models/
│   ├── __init__.py
│   ├── schemas.py         # Pydantic output schemas
│   └── state.py           # ResearchState TypedDict
├── nodes/
│   ├── __init__.py
│   ├── classifier.py      # Intent classification
│   ├── research.py        # Web search execution
│   ├── reranker_parallel.py # Parallel document scoring
│   ├── content_enricher.py  # URL content fetching
│   ├── compressor.py      # Document summarization
│   ├── generator.py       # Report generation
│   ├── auxiliary.py       # Chitchat, clarification, refusal
│   └── abort_response.py  # Zero-source failure handler
├── routers/
│   ├── __init__.py
│   ├── research.py        # SSE streaming endpoint
│   ├── auth.py            # Authentication endpoints
│   └── history.py         # Query history endpoints
├── services/
│   ├── __init__.py
│   ├── research_graph.py  # LangGraph workflow definition
│   ├── web_search.py      # Google CSE integration
│   ├── pipeline_runner.py # Background pipeline execution
│   ├── routing.py         # Conditional edge functions
│   ├── firebase_service.py # Firebase Admin SDK
│   ├── jwt_service.py     # JWT token management
│   └── user_session_service.py # Redis session management
├── utils/
│   ├── __init__.py
│   ├── model_factory.py   # LLM instance factories
│   ├── prompts.py         # Prompt templates
│   ├── streaming.py       # SSE utilities, error codes
│   ├── json_validation.py # Tiered JSON repair
│   ├── circuit_breaker.py # Failure isolation
│   ├── context.py         # Context variables
│   ├── sanitization.py    # Input sanitization
│   └── [other utilities]
├── tests/                 # Test modules
└── scripts/               # Validation scripts
```

---

## 3. Configuration (`config.py`)

### Environment Variables (Required)
| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID |
| `GOOGLE_CSE_API_KEY` | CSE API key (defaults to GOOGLE_API_KEY) |

### ModelConfig Dataclass
```python
@dataclass(frozen=True)
class ModelConfig:
    CLASSIFIER_MODEL: str = "gemini-3-pro-preview"
    CLASSIFIER_TEMPERATURE: float = 0.0
    RERANKER_MODEL: str = "gemini-flash-latest"
    RERANKER_MAX_CONCURRENT: int = 8
    COMPRESSOR_MODEL: str = "gemini-3-pro-preview"
    GENERATOR_MODEL: str = "gemini-3-pro-preview"
    
    # Thresholds
    MAX_CONTEXT_TOKENS: int = 100_000
    COMPRESSION_THRESHOLD: int = 50_000
    RELEVANCE_THRESHOLD: float = 0.60
    MAX_TOP_SOURCES: int = 5
    
    # Timeouts
    LLM_SCORING_TIMEOUT: int = 30
    LLM_SUMMARY_TIMEOUT: int = 45
    FETCH_TIMEOUT: int = 10
    CSE_SEARCH_TIMEOUT: int = 8
```

### Source Quality Configuration
Domain sets defined for source classification: `VIDEO_DOMAINS`, `SOCIAL_MEDIA_DOMAINS`, `WIKI_DOMAINS`, `FORUM_DOMAINS`, `ACADEMIC_DOMAINS`, `NEWS_DOMAINS`

Extractability multipliers applied post-scoring:
| Source Type | Multiplier |
|-------------|------------|
| VIDEO | 0.20 |
| SOCIAL_MEDIA | 0.50 |
| WIKI | 1.10 |
| ACADEMIC | 1.08 |
| FORUM | 1.00 |
| NEWS | 0.85 |

### Key Functions
| Function | Signature | Purpose |
|----------|-----------|---------|
| `get_generator_config` | `(mode: str = "deep") -> Dict[str, Any]` | Returns generator config (mode ignored, DEEP ONLY) |
| `get_adaptive_threshold` | `(query, raw_results_count, social_media_ratio) -> float` | Dynamic threshold (0.45-0.65) based on query characteristics |
| `get_env` | `(key: str, default: Optional[str] = None) -> str` | Environment variable with optional default |

---

## 4. Data Models

### ResearchState (`models/state.py`)
Central TypedDict flowing through LangGraph nodes.

**Key Fields with Reducers:**
| Field | Type | Reducer | Purpose |
|-------|------|---------|---------|
| `messages` | `Annotated[list, add_messages]` | Append | Conversation history |
| `raw_search_results` | `Annotated[List[Dict], operator.add]` | Accumulate | Search results across iterations |
| `iteration_count` | `Annotated[int, operator.add]` | Increment | Thread-safe counter |

**State Categories:**
- **Conversation**: `messages`, `session_id`, `user_query`
- **Classifier**: `intent`, `safety_passed`, `research_query`, `expanded_queries`
- **Research**: `raw_search_results`, `reranked_documents`, `top_sources`, `confidence_scores`
- **Enrichment**: `enriched_sources`, `content_fetch_errors`, `image_token_lookup`
- **Compression**: `compressed_facts`, `entity_map`, `fact_relationships`
- **Generation**: `ui_layout`, `final_report`, `streaming_chunks`
- **Control**: `iteration_count`, `max_iterations`, `is_sufficient`, `should_abort`

**Factory Function:**
```python
def create_initial_state(session_id: str, user_query: str, max_iterations: int = 5) -> ResearchState
```

### Output Schemas (`models/schemas.py`)

**ClassifierOutput**
```python
class ClassifierOutput(BaseModel):
    intent: Literal["RESEARCH_REQUIRED", "CHITCHAT", "CLARIFICATION_NEEDED", "MALICIOUS"]
    reasoning: str
    expanded_queries: Optional[List[str]] = None  # 3-5 queries for RESEARCH_REQUIRED
```

**SingleDocumentScore** (3-dimension scoring)
```python
class SingleDocumentScore(BaseModel):
    document_id: str
    relevance_score: float  # 0.0-1.0, weight: 0.50
    quality_score: float    # 0.0-1.0, weight: 0.30
    usefulness_score: float # 0.0-1.0, weight: 0.20
    composite_score: float  # Weighted aggregate
    scoring_rationale: str
```

**Panel Types** (Discriminated Union)
| Type | Fields |
|------|--------|
| `BodyPanel` | `type="body"`, `title`, `text` |
| `ImagePanel` | `type="image"`, `data: ImagePanelData` |
| `TablePanel` | `type="table"`, `data: TableData` |
| `BodyListfulPanel` | `type="body_listful"`, `title`, `text`, `list_sections: List[Panel]` |

**ResearchReport**
```python
class ResearchReport(BaseModel):
    title: str
    executive_summary: str
    confidence_score: float  # 0.0-1.0
    panels: List[Panel]
    citations: List[Dict[str, str]]
    generation_timestamp: str
```

---

## 5. API Endpoints (Routers)

### Research Router (`/api/research`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/stream` | Optional | SSE streaming research (primary) |
| POST | `/query` | Optional | Non-streaming research |

**GET `/api/research/stream`**
- **Query Params**: `query` (1-2000 chars), `session_id?`, `mode?`, `token?`
- **Response**: `EventSourceResponse` with SSE events
- **Events**: `status`, `mode_selected`, `search_results`, `rerank_update`, `thinking`, `panel_stream`, `panel_complete`, `report_complete`, `error`

**Pipeline Decoupling**: Pipeline runs as background asyncio task. SSE consumer reads from Redis. Client disconnect does NOT stop pipeline.

### Auth Router (`/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/firebase-login` | Exchange Firebase token for backend JWT |
| POST | `/guest-token` | Get guest access token (24h TTL) |
| GET | `/me` | Current user info |
| GET | `/settings` | User settings (authenticated) |
| PUT | `/settings` | Update user settings (authenticated) |

### History Router (`/history`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/active` | Get active query (if processing) |
| DELETE | `/active` | Clear active query |
| POST | `/active/cancel` | Cancel processing query |
| GET | `` | List query history (paginated) |
| DELETE | `` | Clear all history |
| GET | `/{query_id}` | Query details |
| GET | `/{query_id}/report` | Full report |
| DELETE | `/{query_id}` | Delete from history |

---

## 6. LangGraph Workflow

### Graph Topology (9 Nodes)
```
START → classifier → [conditional routing]
    RESEARCH_REQUIRED → research → reranker → content_enricher → [sufficiency check]
        sufficient → compressor → generator → END
        insufficient → research (loop)
        abort → abort_response → END
    CHITCHAT → chitchat_response → END
    CLARIFICATION_NEEDED → classifier (loop)
    MALICIOUS → refusal_response → END
```

### Nodes

**classifier_node** (`nodes/classifier.py`)
- **Model**: gemini-3-pro-preview
- **Input**: User message from state
- **Output**: `intent`, `safety_passed`, `expanded_queries` (3-5 CSE-optimized queries)
- **Routing**: Returns intent string for conditional edge

**deep_research_node** (`nodes/research.py`)
- **Model**: None (tool execution)
- **Tool**: Google CSE via `execute_batch_search()`
- **Behavior**: 
  - Executes expanded queries with concurrency control
  - Query reformulation on iteration >0 if results < threshold
  - Strategies: BROADEN (iter 1) → NARROW (iter 2) → SYNONYMS (iter 3+)

**parallel_reranker_node** (`nodes/reranker_parallel.py`)
- **Model**: gemini-flash-latest
- **Strategy**: Score documents concurrently with `asyncio.gather()`
- **3-Dimension Scoring**: relevance (0.50), quality (0.30), usefulness (0.20)
- **Post-processing**: Extractability multiplier, query relevance multiplier
- **Adaptive Threshold**: Calculated based on result count and social media ratio

**content_enricher_node** (`nodes/content_enricher.py`)
- **Purpose**: Fetch full content from top sources
- **Parallel**: Uses aiohttp with semaphore-controlled concurrency
- **Image Extraction**: Parses HTML for images, builds token lookup
- **Fallback**: Snippet used if fetch fails

**fact_compresser_node** (`nodes/compressor.py`)
- **Model**: gemini-flash-latest (parallel summarization)
- **Strategy**: Summarize each document concurrently, concatenate
- **Abort Signals**: Sets `should_abort=True` if no sources or all summarizations fail

**generator_node** (`nodes/generator.py`)
- **Model**: gemini-3-pro-preview
- **3-Phase Generation**:
  1. UI Planning (lightweight model decides panel layout)
  2. Panel Generation (per-panel with isolated context)
  3. Assembly + Tiered Validation (heuristic repair → Pydantic → reflector)
- **Output**: ResearchReport with progressive streaming support

**Auxiliary Nodes** (`nodes/auxiliary.py`)
- `chitchat_node`: Conversational response (gemini-flash-latest)
- `clarification_node`: Asks for clarification (loops back to classifier)
- `refusal_node`: Static policy refusal for MALICIOUS intent

**abort_response_node** (`nodes/abort_response.py`)
- **Trigger**: Max iterations with 0 quality sources, or early exit detection
- **Output**: Structured error report explaining research limitations

### Routing Functions (`services/routing.py`)

**route_by_intent**
```python
def route_by_intent(state: ResearchState) -> str:
    # Returns: "RESEARCH_REQUIRED" | "CHITCHAT" | "CLARIFICATION_NEEDED" | "MALICIOUS"
```

**check_source_sufficiency**
```python
def check_source_sufficiency(state: ResearchState) -> Literal["sufficient", "insufficient", "abort"]:
    # Decision logic:
    # - iter 2 + 0 sources → abort (early exit)
    # - max_iterations + 0 sources → abort
    # - max_iterations + >0 sources → sufficient
    # - >= min_sources above threshold → sufficient
    # - else → insufficient (loop)
```

---

## 7. Services

### research_graph.py
- **Graph Construction**: `build_research_graph() -> StateGraph`
- **Checkpointer Management**: `initialize_checkpointer()`, `cleanup_checkpointer()`
- **Lazy Singleton**: `research_app` proxy delays compilation until first use

### web_search.py
- **Primary Function**: `execute_batch_search(queries, num_results_per_query, max_concurrent, executor)`
- **Retry Strategy**: Exponential backoff (4 retries, 0.5s base, 4s max)
- **Circuit Breaker**: `search_breaker` for failure isolation
- **Domain Diversity**: Max 3 results per domain

### pipeline_runner.py
- **Background Execution**: `run_pipeline_background()` runs independently of SSE
- **Event Publishing**: Events published to Redis via `publish_sse_event()`
- **Heartbeat**: 10s interval heartbeats prevent SSE timeout
- **Cancellation**: Checks `is_query_cancelled()` between iterations

### user_session_service.py
- **Redis Keys**: `user:{uid}:queries`, `user:{uid}:active_query`, `user:{uid}:report:{qid}`
- **Session Types**: Guest (24h TTL), Authenticated (30d TTL)
- **Active Query**: One per user, status: processing → completed/failed/cancelled
- **SSE Events**: Stored in Redis lists, consumed by SSE endpoint

### firebase_service.py
- **Initialization**: `initialize_firebase()` loads credentials from path or base64 env
- **Token Verification**: `verify_firebase_token(id_token)` with 10s clock skew tolerance

### jwt_service.py
- **Token Creation**: `create_access_token(data, expires_delta)` - 7 day default
- **Guest Tokens**: `create_guest_token()` - 24h TTL

---

## 8. Utilities

### model_factory.py
| Function | Returns | Model |
|----------|---------|-------|
| `get_classifier_llm()` | ChatGoogleGenerativeAI | gemini-3-pro-preview |
| `get_utility_llm()` | ChatGoogleGenerativeAI | gemini-flash-latest |
| `get_compressor_llm()` | ChatGoogleGenerativeAI | gemini-3-pro-preview |
| `get_chitchat_llm()` | ChatGoogleGenerativeAI | gemini-flash-latest |
| `get_generator_llm()` | ChatGoogleGenerativeAI | gemini-3-pro-preview |
| `get_structured_generator(schema)` | Bound LLM | gemini-3-pro-preview |

### prompts.py
- **Classifier**: XML-structured with CSE query optimization guidance
- **ReRanker**: Single document scoring with 3-dimension criteria
- **Generator**: Criteria-based (NO "think step by step" for Gemini 3 Pro)
- **Security**: User input sanitized via `sanitize_query()` before interpolation

### streaming.py
- **PipelineErrorCode**: Enum of all failure types (CLASSIFIER_FAILED, NO_RESULTS, etc.)
- **Error Messages**: User-friendly message mapping
- **Recoverable Errors**: Set of codes that allow retry
- **JSON Utilities**: `is_valid_json()`, `find_matching_brace()`, `extract_panel_at_index()`
- **SSE Formatters**: `format_sse_event()`, `create_error_event()`, etc.

### json_validation.py
- **Tiered Defense**: Heuristic repair → Pydantic validation
- **Error Extraction**: `extract_validation_errors_detailed()` for reflector feedback
- **JSON Extraction**: `extract_json_from_response()` handles markdown, partial JSON

### circuit_breaker.py
```python
class CircuitBreaker:
    # States: CLOSED → OPEN → HALF_OPEN → CLOSED
    # Config: failure_threshold=5, success_threshold=2, timeout=60s
```
- **Usage**: `@breaker.protect` decorator or `async with breaker.call()`
- **Instance**: `search_breaker` for CSE API protection

### context.py
Context variables for cross-node resource access:
- `set_search_executor(executor)` / `get_search_executor()` - ThreadPoolExecutor access without state serialization

### sanitization.py
- **XML Escaping**: `escape_xml_content()` - prevents prompt structure breakout
- **Injection Detection**: `detect_injection_attempt()` - regex patterns for jailbreak attempts
- **Combined**: `sanitize_query()` - escapes and warns on injection patterns

---

## 9. Authentication & Authorization

### Dependency Functions (`dependencies/auth.py`)

**AuthenticatedUser Class**
```python
class AuthenticatedUser:
    user_id: str
    user_type: str  # "firebase" | "guest"
    email: Optional[str]
    display_name: Optional[str]
    firebase_uid: Optional[str]
    
    @property
    def is_authenticated(self) -> bool
    
    @property
    def is_guest(self) -> bool
```

**Dependency Functions**
| Function | Auth Required | Description |
|----------|--------------|-------------|
| `get_user_or_guest` | No | Returns user from token or guest |
| `get_user_or_guest_from_token_param` | No | For SSE (token in query param) |
| `require_authenticated_user` | Yes | Raises 401 if not authenticated |

### Token Flow
1. Client signs in with Firebase (Google/Email)
2. Client sends Firebase ID token to `/auth/firebase-login`
3. Backend verifies with Firebase Admin SDK
4. Backend issues its own JWT (7 day TTL)
5. Client uses backend JWT for subsequent requests

---

## 10. Application Lifecycle

### Lifespan Manager (`lifespan.py`)

**Startup**
1. Validate environment variables (GOOGLE_API_KEY, GOOGLE_CSE_ID)
2. Create asyncio.Semaphore instances (scoring, fetch) bound to current loop
3. Initialize ThreadPoolExecutor for web searches
4. Initialize Firebase Admin SDK
5. Initialize Redis checkpointer (or MemorySaver fallback)
6. Pre-compile research graph

**Shutdown**
1. Shutdown ThreadPoolExecutor with timeout
2. Clear semaphore references
3. Cleanup Redis checkpointer connection
4. Cleanup user session Redis pool

### Rate Limiting (`limiter.py`)
- **Global Switch**: `RATE_LIMIT_ENABLED` env var (default: false)
- **Limits**: `/stream` 10/min, `/query` 20/min, authenticated users effectively unlimited
- **Backend**: Redis (production) or memory (development)
- **Handler**: Custom 429 response with retry-after

---

## 11. Infrastructure

### Docker Configuration

**Dockerfile**
- Base: `python:3.12-slim`
- Working dir: `/app`
- Installs from `requirements.txt`
- Runs: `uvicorn server:app --host 0.0.0.0 --port 8000`

**docker-compose.yml** (inferred services)
- `backend`: FastAPI application
- `redis`: Session persistence, rate limiting, SSE event queue

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key |
| `GOOGLE_CSE_ID` | Yes | Custom Search Engine ID |
| `REDIS_URL` | No | Redis connection (default: memory) |
| `FIREBASE_CREDENTIALS_PATH` | No | Path to serviceAccountKey.json |
| `FIREBASE_CREDENTIALS_JSON` | No | Base64-encoded credentials |
| `JWT_SECRET_KEY` | No | JWT signing key (change in prod) |
| `RATE_LIMIT_ENABLED` | No | Enable rate limiting (default: false) |
| `LOG_LEVEL` | No | Logging level (default: DEBUG) |

---

## 12. Error Handling

### Pipeline Error Codes
| Code | Description | Recoverable |
|------|-------------|-------------|
| `CLASSIFIER_FAILED` | Intent detection failed | Yes |
| `SEARCH_FAILED` | Web search failed | Yes |
| `NO_RESULTS` | No search results | No |
| `NO_QUALITY_SOURCES` | Sources below threshold | No |
| `GENERATOR_FAILED` | Report generation failed | Yes |
| `GENERATION_TIMEOUT` | Generation timed out | Yes |
| `RATE_LIMITED` | Too many requests | Yes |

### Graceful Degradation
1. **Content Fetch Failure**: Falls back to snippet
2. **Scoring Failure**: Returns default low-confidence score
3. **Summarization Failure**: Uses raw content
4. **Generator Failure**: Returns error report with diagnostic info
5. **Zero Sources**: Abort path generates structured error response

---

## 13. Testing

### Test Directory Structure
```
tests/
├── conftest.py              # Pytest fixtures
├── test_classifier.py       # Classifier node tests
├── test_generator_integration.py
├── test_image_tokens.py
├── test_json_validation.py
├── test_pipeline_complete.py
├── test_reranker_*.py
├── test_research_node.py
├── test_sse_endpoint.py
├── test_streaming.py
├── test_web_search.py
└── pipeline_integration/
```

### Key Fixtures (conftest.py)
- `mock_llm`: Mocked LLM for unit tests
- `research_state`: Pre-populated ResearchState
- `client`: TestClient for API tests

---

## 14. Symbol Index

### Classes
| Class | Module | Purpose |
|-------|--------|---------|
| `ModelConfig` | config | Immutable configuration dataclass |
| `ResearchState` | models.state | TypedDict for graph state |
| `ClassifierOutput` | models.schemas | Classifier response schema |
| `SingleDocumentScore` | models.schemas | 3-dimension document score |
| `ResearchReport` | models.schemas | Final output schema |
| `Panel` | models.schemas | Discriminated union of panel types |
| `AuthenticatedUser` | dependencies.auth | User identity wrapper |
| `CircuitBreaker` | utils.circuit_breaker | Failure isolation pattern |
| `PipelineErrorCode` | utils.streaming | Error code enum |

### Key Functions
| Function | Module | Signature |
|----------|--------|-----------|
| `classifier_node` | nodes.classifier | `(state) -> Dict[str, Any]` |
| `deep_research_node` | nodes.research | `(state) -> Dict[str, Any]` |
| `parallel_reranker_node` | nodes.reranker_parallel | `(state) -> Dict[str, Any]` |
| `content_enricher_node` | nodes.content_enricher | `(state) -> Dict[str, Any]` |
| `fact_compresser_node` | nodes.compressor | `(state) -> Dict[str, Any]` |
| `generator_node` | nodes.generator | `(state) -> Dict[str, Any]` |
| `route_by_intent` | services.routing | `(state) -> str` |
| `check_source_sufficiency` | services.routing | `(state) -> Literal[...]` |
| `execute_batch_search` | services.web_search | `(queries, ...) -> List[Dict]` |
| `run_pipeline_background` | services.pipeline_runner | `async (query, session_id, ...)` |
| `sanitize_query` | utils.sanitization | `(query) -> str` |

---

*End of Backend Technical Reference*
