# Portfolio Backend API - Technical Reference Document

**Version:** 1.0.0  
**Framework:** FastAPI + LangGraph  
**Language:** Python 3.11+  
**Generated:** 2024-12-18

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Directory Structure](#2-directory-structure)
3. [Infrastructure & Dependencies](#3-infrastructure--dependencies)
4. [Configuration](#4-configuration)
5. [Data Models](#5-data-models)
6. [Pipeline State & Orchestration](#6-pipeline-state--orchestration)
7. [API Surface](#7-api-surface)
8. [Pipeline Nodes](#8-pipeline-nodes)
9. [Tools](#9-tools)
10. [Services & Utilities](#10-services--utilities)
11. [Testing](#11-testing)

---

## 1. System Architecture

### Overview

The backend implements a **7-phase LangGraph AI pipeline** for employer fit analysis. It powers a "See if I'm fit for you!" feature that streams real-time AI analysis via Server-Sent Events (SSE).

### Pipeline Flow

```
START → connecting → deep_research → research_reranker → (conditional routing)
      ↓                                                    ↓
      ↓  ←←← GARBAGE/UNRELIABLE ←←←←←←←←←←←←←←←←←←←←←←←←←
      ↓  ←←← SPARSE (retry) ←←←←←←←←←← deep_research ←←←←
      ↓
skeptical_comparison → skills_matching → confidence_reranker → generate_results → END
```

### Key Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Anti-Sycophancy** | Minimum 2 gaps enforced in skeptical_comparison |
| **Data Quality Gates** | research_reranker prunes bad data, triggers early exit |
| **Confidence Calibration** | LLM-as-Judge meta-reasoning in confidence_reranker |
| **Streaming** | SSE events via asyncio.Queue for real-time updates |
| **Gemini Optimization** | XML prompts, criteria-based constraints, no "think step-by-step" |

---

## 2. Directory Structure

```
backend/
├── server.py                    # FastAPI entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Multi-stage production build
├── docker-compose.yml           # Container orchestration
├── pytest.ini                   # Test configuration
├── .env.local                   # Local environment variables
├── .env.deployed                # Production environment variables
│
├── config/
│   ├── __init__.py              # Exports: get_llm, ENGINEER_PROFILE, profile helpers
│   ├── llm.py                   # LLM factory (Gemini configuration)
│   └── engineer_profile.py      # Candidate profile data
│
├── models/
│   ├── __init__.py              # Exports all Pydantic models
│   └── fit_check.py             # Request/response models, SSE event schemas
│
├── routers/
│   ├── __init__.py
│   ├── fit_check.py             # POST /api/fit-check/stream (SSE endpoint)
│   └── prompts.py               # GET /api/prompts (transparency endpoints)
│
├── services/
│   ├── __init__.py
│   ├── fit_check_agent.py       # FitCheckAgent class, pipeline builder
│   ├── pipeline_state.py        # TypedDict state schemas, phase outputs
│   ├── callbacks.py             # ThoughtCallback interface
│   ├── streaming_callback.py    # SSE event formatter and queue
│   ├── prompt_loader.py         # Model-specific prompt selection
│   ├── utils.py                 # LLM response text extraction
│   │
│   ├── nodes/
│   │   ├── __init__.py          # Exports all node functions
│   │   ├── connecting.py        # Phase 1: Query classification
│   │   ├── deep_research.py     # Phase 2: Web research
│   │   ├── research_reranker.py # Phase 2B: Quality validation
│   │   ├── skeptical_comparison.py # Phase 3: Gap analysis
│   │   ├── skills_matching.py   # Phase 4: Skill mapping
│   │   ├── confidence_reranker.py # Phase 5B: Confidence calibration
│   │   └── generate_results.py  # Phase 5: Response generation
│   │
│   └── tools/
│       ├── __init__.py          # Exports tools and utilities
│       ├── web_search.py        # Google CSE integration
│       ├── skill_matcher.py     # Skill alignment analysis
│       └── experience_matcher.py # Experience relevance analysis
│
├── prompts/
│   ├── phase_1_connecting.xml           # Verbose prompt
│   ├── phase_1_connecting_concise.xml   # Reasoning model prompt
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
└── tests/
    ├── conftest.py              # Fixtures and markers
    ├── test_fit_check_agent.py  # Agent tests
    ├── test_integration.py      # Integration tests
    ├── unit/                    # Unit tests per node
    └── simulation/              # Pipeline simulation tests
```

---

## 3. Infrastructure & Dependencies

### requirements.txt

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | ≥0.110.0 | Web framework |
| uvicorn[standard] | ≥0.27.0 | ASGI server |
| python-dotenv | ≥1.0.0 | Environment loading |
| pydantic | ≥2.6.0 | Data validation |
| langchain | ≥0.3.0 | LLM orchestration |
| langchain-core | ≥0.3.0 | Core abstractions |
| langchain-google-genai | ≥2.1.0 | Gemini integration |
| langgraph | ≥0.2.0 | Graph-based workflows |
| langchain-google-community | ≥2.0.0 | Google CSE |
| pytest | ≥8.0.0 | Testing |
| pytest-asyncio | ≥0.23.0 | Async test support |
| httpx | ≥0.27.0 | HTTP client for tests |

### Dockerfile (Multi-Stage)

| Stage | Base Image | Purpose |
|-------|-----------|---------|
| builder | python:3.11-slim-bookworm | Compile dependencies |
| production | python:3.11-slim-bookworm | Runtime (non-root user) |

**Security Features:**
- Non-root user (UID/GID 1000)
- `PYTHONDONTWRITEBYTECODE=1`
- `PYTHONUNBUFFERED=1`
- No pip cache

### docker-compose.yml

| Service | Image | Ports | Health Check |
|---------|-------|-------|--------------|
| backend | res_web:latest | 8000:8000 | HTTP GET /health |

**Environment Variables:**
- `HOST`, `PORT`, `LOG_LEVEL`, `ALLOWED_ORIGINS` (from .env.local)

---

## 4. Configuration

### config/llm.py

**Constants:**

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_MODEL` | `"gemini-3-pro-preview"` | Default LLM model |
| `DEFAULT_TEMPERATURE` | `0.3` | Standard model temperature |
| `DEFAULT_TOP_K` | `40` | Sampling diversity |
| `MAX_OUTPUT_TOKENS` | `2048` | Token limit |

**Supported Models:**

| Model ID | Config Type | Description |
|----------|-------------|-------------|
| `gemini-3-pro-preview` | reasoning | Uses `thinking_budget=1024` |
| `gemini-flash-latest` | standard | Uses temperature/topK |

**Function: `get_llm`**

```python
def get_llm(
    streaming: bool = False,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    model_id: Optional[str] = None,
    config_type: Optional[Literal["reasoning", "standard"]] = None,
) -> ChatGoogleGenerativeAI
```

Returns configured `ChatGoogleGenerativeAI` instance. Raises `ValueError` if `GOOGLE_API_KEY` not set.

---

### config/engineer_profile.py

**`ENGINEER_PROFILE: Dict[str, Any]`** — Static profile data for the candidate.

| Key | Type | Description |
|-----|------|-------------|
| `name` | str | "Software Engineer" |
| `education` | str | "B.S. in Computer Science" |
| `skills` | Dict[str, List[str]] | Categorized skills (languages, frameworks, cloud_devops, ai_ml, tools) |
| `experience_summary` | str | Multi-line experience description |
| `notable_projects` | List[Dict] | Project entries with name, description, tech |
| `strengths` | List[str] | Key professional strengths |
| `career_interests` | List[str] | Target career areas |

**Utility Functions:**

| Function | Returns | Description |
|----------|---------|-------------|
| `get_formatted_profile()` | str | Profile formatted for prompt injection |
| `get_skills_list()` | List[str] | Flat list of all skills |
| `get_skills_by_category()` | Dict[str, List[str]] | Skills organized by category |
| `get_experience_summary()` | str | Experience summary text |

---

## 5. Data Models

### models/fit_check.py

#### Request Models

**`FitCheckRequest(BaseModel)`**

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `query` | str | min=3, max=2000 | required |
| `include_thoughts` | bool | — | `True` |
| `model_id` | Optional[str] | — | `"gemini-3-pro-preview"` |
| `config_type` | Optional[Literal["reasoning", "standard"]] | — | `"reasoning"` |

#### SSE Event Models

| Model | Event Type | Key Fields |
|-------|------------|------------|
| `StatusEvent` | status | `status` (connecting\|researching\|analyzing\|generating), `message` |
| `ThoughtEvent` | thought | `step`, `type` (tool_call\|observation\|reasoning), `tool?`, `input?`, `content?` |
| `ResponseEvent` | response | `chunk` |
| `CompleteEvent` | complete | `duration_ms` |
| `ErrorEvent` | error | `code`, `message` |

**Error Codes:**
- `INVALID_QUERY` (400)
- `RATE_LIMITED` (429)
- `AGENT_ERROR` (500)
- `SEARCH_ERROR` (502)
- `LLM_ERROR` (503)
- `TIMEOUT` (504)

---

## 6. Pipeline State & Orchestration

### services/pipeline_state.py

#### Phase Output TypedDicts

**`Phase1Output`** (Connecting)

| Field | Type | Description |
|-------|------|-------------|
| `query_type` | Literal["company", "job_description", "irrelevant"] | Classification result |
| `company_name` | Optional[str] | Extracted company |
| `job_title` | Optional[str] | Extracted role |
| `extracted_skills` | List[str] | Skills from query |
| `reasoning_trace` | str | Post-hoc explanation |

**`Phase2Output`** (Deep Research)

| Field | Type | Description |
|-------|------|-------------|
| `employer_summary` | str | Synthesized employer info |
| `identified_requirements` | List[str] | Job requirements |
| `tech_stack` | List[str] | Technologies used |
| `culture_signals` | List[str] | Cultural indicators |
| `search_queries_used` | List[str] | Queries executed |
| `reasoning_trace` | str | Synthesis explanation |

**`ResearchRerankerOutput`** (Phase 2B)

| Field | Type | Description |
|-------|------|-------------|
| `data_quality_tier` | Literal["CLEAN", "PARTIAL", "SPARSE", "UNRELIABLE", "GARBAGE"] | Data triage |
| `research_quality_tier` | Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"] | Overall quality |
| `data_confidence_score` | int | 0-100 confidence |
| `quality_flags` | List[str] | Quality issues |
| `recommended_action` | Literal["CONTINUE", "CONTINUE_WITH_FLAGS", "ENHANCE_SEARCH", "EARLY_EXIT"] | Routing decision |
| `pruned_data` | Dict[str, List[str]] | Removed unreliable data |
| `cleaned_data` | Dict[str, Any] | Verified data |
| `early_exit_reason` | str | Exit explanation if applicable |

**`Phase3Output`** (Skeptical Comparison)

| Field | Type | Description |
|-------|------|-------------|
| `genuine_strengths` | List[str] | Verified alignment points |
| `genuine_gaps` | List[str] | Honest gaps (min 2 enforced) |
| `unverified_claims` | List[str] | Claims lacking evidence |
| `transferable_skills` | List[str] | Gap-bridging skills |
| `risk_assessment` | Literal["low", "medium", "high"] | Fit risk level |
| `risk_justification` | str | Risk explanation |

**`Phase4Output`** (Skills Matching)

| Field | Type | Description |
|-------|------|-------------|
| `matched_requirements` | List[Dict] | `{requirement, matched_skill, confidence, evidence}` |
| `unmatched_requirements` | List[str] | No-match requirements |
| `overall_match_score` | float | 0.0-1.0 calculated score |
| `reasoning_trace` | str | Score breakdown |

**`RerankerOutput`** (Confidence Reranker)

| Field | Type | Description |
|-------|------|-------------|
| `calibrated_score` | int | 0-100 adjusted score |
| `tier` | Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"] | Confidence tier |
| `justification` | str | Tier explanation |
| `quality_flags` | List[str] | Quality concerns |
| `data_quality` | Dict[str, str] | Per-phase quality |
| `adjustment_rationale` | str | Score adjustment reason |

---

#### `FitCheckPipelineState(TypedDict)`

Main pipeline state passed through all nodes.

| Field | Type | Description |
|-------|------|-------------|
| `query` | str | Original user input |
| `current_phase` | str | Active phase |
| `step_count` | int | SSE step counter |
| `phase_1_output` | Optional[Phase1Output] | Connecting output |
| `phase_2_output` | Optional[Phase2Output] | Deep research output |
| `research_reranker_output` | Optional[ResearchRerankerOutput] | Quality gate output |
| `phase_3_output` | Optional[Phase3Output] | Skeptical comparison output |
| `phase_4_output` | Optional[Phase4Output] | Skills matching output |
| `reranker_output` | Optional[RerankerOutput] | Confidence calibration |
| `search_attempt` | int | 1=primary, 2=enhanced retry |
| `low_data_flag` | bool | Insufficient data flag |
| `early_exit` | bool | Skip to generate_results |
| `final_response` | Optional[str] | Generated markdown |
| `messages` | Annotated[List[BaseMessage], add_messages] | LangGraph compatibility |
| `processing_errors` | List[str] | Non-fatal errors |
| `error` | Optional[str] | Fatal error |
| `rejection_reason` | Optional[str] | Query rejection reason |
| `model_id` | Optional[str] | Selected model |
| `config_type` | Optional[str] | Model configuration |

**Factory Function:**

```python
def create_initial_state(
    query: str,
    model_id: Optional[str] = None,
    config_type: Optional[str] = None,
) -> FitCheckPipelineState
```

**Phase Helpers:**

| Function | Returns | Description |
|----------|---------|-------------|
| `get_phase_display_name(phase)` | str | Human-readable name |
| `get_next_phase(current)` | Optional[str] | Next in sequence |
| `is_terminal_phase(phase)` | bool | True if generate_results |

**`PHASE_ORDER`:** `["connecting", "deep_research", "research_reranker", "skeptical_comparison", "skills_matching", "confidence_reranker", "generate_results"]`

---

### services/fit_check_agent.py

**`FitCheckAgent` Class**

| Method | Signature | Description |
|--------|-----------|-------------|
| `analyze` | `async (query, model_id?, config_type?) → str` | Non-streaming analysis |
| `stream_analysis` | `async (query, callback, model_id?, config_type?) → AsyncGenerator[str, None]` | Streaming with SSE events |

**Singleton:** `get_agent() → FitCheckAgent`

**Pipeline Builder:**

```python
def build_fit_check_pipeline(callback_holder: Dict = None) → CompiledGraph
```

Builds LangGraph with conditional routing:
1. After `connecting`: → `deep_research` OR → END (irrelevant)
2. After `research_reranker`: → `skeptical_comparison` OR → `deep_research` (retry) OR → `generate_results` (early exit)

---

## 7. API Surface

### routers/fit_check.py

#### `POST /api/fit-check/stream`

**Request:** `FitCheckRequest` (JSON body)

**Response:** `StreamingResponse` (text/event-stream)

**SSE Event Sequence:**
1. `status` — connecting, researching, analyzing, generating
2. `phase` — Phase transitions
3. `thought` — Tool calls, observations, reasoning steps
4. `response` — Streamed markdown chunks
5. `complete` — Duration in ms
6. `error` — If failure

**Headers:**
- `Cache-Control: no-cache`
- `Connection: keep-alive`
- `X-Accel-Buffering: no`

#### `GET /api/fit-check/health`

Returns: `{"status": "healthy", "service": "fit-check", "agent_ready": bool}`

---

### routers/prompts.py

#### `GET /api/prompts`

Returns `PromptListResponse` with all phase metadata.

#### `GET /api/prompts/{phase}`

Returns `PromptContentResponse` with prompt content.

**Available Phases:**
| Phase | Display Name | Order |
|-------|-------------|-------|
| `connecting` | Query Classification | 1 |
| `deep_research` | Deep Research | 2 |
| `research_reranker` | Research Quality Gate | 3 |
| `skeptical_comparison` | Skeptical Comparison | 4 |
| `skills_matching` | Skills Matching | 5 |
| `confidence_reranker` | Confidence Calibration | 6 |
| `generate_results` | Response Generation | 7 |

---

### server.py

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI docs |
| GET | `/redoc` | ReDoc |

**CORS:** Configured via `ALLOWED_ORIGINS` env var (comma-separated).

---

## 8. Pipeline Nodes

### nodes/connecting.py (Phase 1)

**Purpose:** Query classification, entity extraction, security validation.

**Temperature:** 0.1 (deterministic)

**Security Patterns:**
- `PROMPT_INJECTION_PATTERNS` — 15+ regex patterns
- `HARMFUL_CONTENT_PATTERNS` — Dangerous content detection
- `IRRELEVANT_QUERY_PATTERNS` — Off-topic detection

**Function: `validate_input_security(query) → Tuple[bool, Optional[str]]`**

Pre-LLM pattern matching. Returns `(is_valid, rejection_reason)`.

**Function: `connecting_node(state, callback) → Dict[str, Any]`**

Returns:
- `phase_1_output`: Phase1Output
- `current_phase`: "deep_research" OR "__end__"
- `rejection_reason`: Set if irrelevant/malicious

---

### nodes/deep_research.py (Phase 2)

**Purpose:** Web search and employer intelligence synthesis.

**Temperature:** 0.3

**Constants:** `MAX_SEARCH_QUERIES=2`, `MAX_RESULT_LENGTH=1500`

**Function: `construct_search_queries(phase_1, query) → List[str]`**

Strategy varies by query_type:
- `company`: `"{name} software engineer tech stack"`, `"{name} careers jobs"`
- `job_description`: `"{title} {skills} requirements"`

**Function: `deep_research_node(state, callback) → Dict[str, Any]`**

Executes web_search tool, synthesizes via LLM, returns Phase2Output.

---

### nodes/research_reranker.py (Phase 2B)

**Purpose:** Data quality validation, pruning, routing decisions.

**Temperature:** 0.1

**Industry Inference:** `INDUSTRY_TECH_DEFAULTS` maps 8 industries (fintech, ai_ml, saas_b2b, etc.) to expected tech stacks.

**Bad Data Detection:**
- `GENERIC_TECH_TERMS` — Vague terms to prune
- `GENERIC_REQUIREMENT_PATTERNS` — Soft skill phrases
- `PLATITUDE_CULTURE_SIGNALS` — Empty buzzwords
- `SUSPICIOUS_NAME_PATTERNS` — Injection indicators

**Functions:**

| Function | Returns | Description |
|----------|---------|-------------|
| `detect_bad_data_patterns(phase_2, company)` | Dict | Risk assessment |
| `prune_low_quality_data(phase_2)` | Dict | Separated clean/pruned |
| `assess_quality_heuristically(phase_2)` | Dict | Tier determination |

**Routing Logic:**
- `CLEAN/PARTIAL` → Continue
- `SPARSE` (attempt 1) → Enhanced retry
- `GARBAGE/UNRELIABLE` → Early exit

---

### nodes/skeptical_comparison.py (Phase 3)

**Purpose:** Anti-sycophancy gap analysis.

**Temperature:** 0.4 (higher for creative skepticism)

**Anti-Sycophancy Enforcement:**
- `MIN_REQUIRED_GAPS = 2` — Default gaps added if LLM returns fewer
- `MAX_ALLOWED_STRENGTHS = 4` — Prevents padding
- `SYCOPHANTIC_PHRASES` — Phrases to detect/log

**Function: `validate_phase3_output(data) → Phase3Output`**

Enforces minimum gaps. Validates risk-gap consistency.

**Function: `detect_sycophantic_content(output) → List[str]`**

Post-validation quality check for logging.

---

### nodes/skills_matching.py (Phase 4)

**Purpose:** Skill-to-requirement mapping with quantification.

**Temperature:** 0.2 (precision)

**Score Calculation:**

```python
def calculate_overall_score(matched, unmatched) → Tuple[float, str]
```

Algorithm:
1. `avg_confidence = mean(matched.confidence)`
2. `coverage = len(matched) / total`
3. `base_score = avg_confidence × coverage`
4. Penalty if gap_ratio > 30%

**Tools Invoked:**
- `analyze_skill_match` with requirements
- `analyze_experience_relevance` with employer context

**Validation:** Score recalculated server-side to prevent LLM gaming.

---

### nodes/confidence_reranker.py (Phase 5B)

**Purpose:** LLM-as-Judge confidence calibration.

**Temperature:** 0.1

**Penalties Applied (Fallback Logic):**
- Sparse tech stack (< 2): -15
- No requirements: -10
- Insufficient gaps (< 2): -10
- Default score suspected: -20

**Function: `prepare_context_data(state) → Dict`**

Aggregates metrics from all prior phases.

**Function: `validate_reranker_output(data) → RerankerOutput`**

Infers tier from score if invalid:
- ≥75 → HIGH
- ≥40 → MEDIUM
- ≥15 → LOW
- <15 → INSUFFICIENT_DATA

---

### nodes/generate_results.py (Phase 5)

**Purpose:** Final markdown response generation with streaming.

**Temperature:** 0.7 (creative narrative)

**Constants:** `MAX_RESPONSE_WORDS = 400`

**Context Detection:**

```python
def detect_employer_context(phase_2, phase_1) → Literal["ai_ml", "fintech", "startup", "enterprise", "default"]
```

**Quality Validation:**

```python
def validate_response_quality(response, phase_3) → List[str]
```

Checks:
- Word count limit
- Gap acknowledgment
- Generic phrase detection

**Streaming:** Chunks emitted via `callback.on_response_chunk()`.

**Fallback:** `generate_fallback_response()` if LLM fails.

---

## 9. Tools

### tools/web_search.py

**`@tool web_search(query: str) → str`**

Uses `GoogleSearchAPIWrapper` (langchain-google-community).

**Configuration:**
- `GOOGLE_CSE_API_KEY` (env)
- `GOOGLE_CSE_ID` (env)
- `k=5` (top 5 results)

**Fallback:** Returns cached info for major companies (Google, Meta, Amazon, etc.) if CSE not configured.

**Utility:** `validate_search_config() → dict`

---

### tools/skill_matcher.py

**`@tool analyze_skill_match(requirements: str) → str`**

Matches engineer skills against requirements using:
- Direct matching
- Alias mapping (`skill_aliases` dict for 14 skill categories)
- Partial match detection for soft skills

**Output Format:**
- `## STRONG SKILL MATCHES`
- `## ADDITIONAL QUALIFICATIONS MET`
- `## KEY TECHNICAL STRENGTHS`
- Overall Match Quality rating

**Utility:** `get_skill_summary() → str`

---

### tools/experience_matcher.py

**`@tool analyze_experience_relevance(context: str) → str`**

Matches experience against employer context.

**Domain Patterns:** 8 domains (ai, fintech, saas, startup, e-commerce, cloud, developer_tools, healthcare)

**Project Contexts:** 5 project types (ai_agent, web_platform, rag_system, api_development, real_time)

**Output Format:**
- `## EXPERIENCE RELEVANCE ANALYSIS`
- `### Domain Alignment`
- `### Relevant Project Experience`
- `### Core Experience Highlights`
- Fit Assessment (STRONG/GOOD)

**Utility:** `get_project_highlights() → str`

---

## 10. Services & Utilities

### services/callbacks.py

**`ThoughtCallback` (Abstract Base)**

| Method | Parameters | Description |
|--------|------------|-------------|
| `on_status` | status, message | Status change |
| `on_phase` | phase, message | Phase start |
| `on_phase_complete` | phase, summary | Phase end |
| `on_thought` | step, type, content, tool?, input?, phase? | Reasoning step |
| `on_response_chunk` | chunk | Response streaming |
| `on_complete` | duration_ms | Pipeline done |
| `on_error` | code, message | Error occurred |

---

### services/streaming_callback.py

**`StreamingCallbackHandler(ThoughtCallback)`**

Queues SSE events for async streaming.

| Property | Type | Description |
|----------|------|-------------|
| `_queue` | asyncio.Queue | Event queue |
| `_include_thoughts` | bool | Emit thought events |
| `_completed` | bool | Stream finished |
| `_error_occurred` | bool | Error flag |

**Methods:**
- `events() → AsyncGenerator[str, None]`: Yields SSE strings
- `is_completed`, `has_error`: Status properties

**`format_sse(event_type, data) → str`**

Formats `event: {type}\ndata: {json}\n\n`

---

### services/prompt_loader.py

**Prompt Selection Logic:**
- `reasoning` config → `*_concise.xml`
- `standard` config → `*.xml` (verbose)

**Functions:**

| Function | Returns | Description |
|----------|---------|-------------|
| `get_prompt_path(phase, config_type?, prefer_concise?)` | Path | Prompt file path |
| `load_prompt(phase, config_type?, prefer_concise?)` | str | Prompt content |
| `get_prompt_variant_info(config_type)` | dict | Variant rationale |

**Phase Constants:**
`PHASE_CONNECTING`, `PHASE_DEEP_RESEARCH`, `PHASE_RESEARCH_RERANKER`, `PHASE_SKEPTICAL_COMPARISON`, `PHASE_SKILLS_MATCHING`, `PHASE_GENERATE_RESULTS`, `PHASE_CONFIDENCE_RERANKER`

---

### services/utils.py

**`extract_text_from_content(content: Any) → str`**

Handles:
- Plain strings
- List[str]
- List[Dict] with `{"type": "text", "text": "..."}` (Gemini format)
- Filters out `{"type": "thinking"}` blocks

**`get_response_text(response: Any) → str`**

Safely extracts text from LLM response objects.

---

## 11. Testing

### pytest.ini

| Setting | Value |
|---------|-------|
| `testpaths` | tests |
| `asyncio_mode` | auto |
| `log_cli_level` | INFO |

**Markers:** `slow`, `integration`, `unit`

### tests/conftest.py

**Fixtures:**

| Fixture | Scope | Returns |
|---------|-------|---------|
| `event_loop_policy` | session | Windows compatibility |
| `mock_env` | function | Mocked env vars |
| `sample_query` | function | "Google" |
| `sample_job_description` | function | Multi-line job posting |
| `sample_thoughts` | function | List of thought events |

### Test Structure

```
tests/
├── conftest.py
├── test_fit_check_agent.py      # Agent-level tests
├── test_integration.py          # Full pipeline tests
├── unit/
│   ├── test_connecting_node.py
│   ├── test_deep_research_node.py
│   ├── test_skeptical_comparison_node.py
│   ├── test_skills_matching_node.py
│   └── test_generate_results_node.py
└── simulation/
    ├── simulate_full_pipeline.py
    ├── test_phase_outputs.py
    ├── test_sse_event_flow.py
    └── analyze_ai_outputs.py
```

---

## Symbol Index

### Classes

| Class | Module | Description |
|-------|--------|-------------|
| `FitCheckAgent` | services.fit_check_agent | Pipeline executor |
| `StreamingCallbackHandler` | services.streaming_callback | SSE event handler |
| `ThoughtCallback` | services.callbacks | Callback interface |
| `RerankerOutput` | services.nodes.confidence_reranker | Reranker output container |
| `FitCheckRequest` | models.fit_check | Request model |
| `StatusEvent` | models.fit_check | SSE status event |
| `ThoughtEvent` | models.fit_check | SSE thought event |
| `ResponseEvent` | models.fit_check | SSE response event |
| `CompleteEvent` | models.fit_check | SSE complete event |
| `ErrorEvent` | models.fit_check | SSE error event |

### Node Functions

| Function | Module | Phase |
|----------|--------|-------|
| `connecting_node` | services.nodes.connecting | 1 |
| `deep_research_node` | services.nodes.deep_research | 2 |
| `research_reranker_node` | services.nodes.research_reranker | 2B |
| `skeptical_comparison_node` | services.nodes.skeptical_comparison | 3 |
| `skills_matching_node` | services.nodes.skills_matching | 4 |
| `confidence_reranker_node` | services.nodes.confidence_reranker | 5B |
| `generate_results_node` | services.nodes.generate_results | 5 |

### Tools

| Tool | Module | Purpose |
|------|--------|---------|
| `web_search` | services.tools.web_search | Google CSE search |
| `analyze_skill_match` | services.tools.skill_matcher | Skill alignment |
| `analyze_experience_relevance` | services.tools.experience_matcher | Experience matching |

### Key Configuration Functions

| Function | Module | Returns |
|----------|--------|---------|
| `get_llm` | config.llm | ChatGoogleGenerativeAI |
| `get_formatted_profile` | config.engineer_profile | str |
| `get_skills_list` | config.engineer_profile | List[str] |
| `get_agent` | services.fit_check_agent | FitCheckAgent |
| `build_fit_check_pipeline` | services.fit_check_agent | CompiledGraph |
| `create_initial_state` | services.pipeline_state | FitCheckPipelineState |
| `load_prompt` | services.prompt_loader | str |

---

*Document generated with surgical precision per Backend Documentation Directive. Line count: ~1200 lines.*
