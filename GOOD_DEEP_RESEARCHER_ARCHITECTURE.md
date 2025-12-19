# Deep Researcher Architecture Guide

> A comprehensive explanation of the AI Deep Researcher system architecture, component interactions, and data flow patterns.

---

## Table of Contents

1. [System Purpose & Goals](#1-system-purpose--goals)
2. [High-Level Architecture](#2-high-level-architecture)
3. [The Research Pipeline Flow](#3-the-research-pipeline-flow)
4. [Component Deep Dives](#4-component-deep-dives)
5. [State Management & Data Flow](#5-state-management--data-flow)
6. [Concurrency & Resilience Patterns](#6-concurrency--resilience-patterns)
7. [Session Persistence & Reconnection](#7-session-persistence--reconnection)
8. [Key Architectural Decisions](#8-key-architectural-decisions)

---

## 1. System Purpose & Goals

### What is the Deep Researcher?

The AI Deep Researcher is an **autonomous research agent** that transforms user queries into comprehensive, well-cited research reports. It operates as a multi-agent pipeline that:

1. **Understands** user intent through classification
2. **Searches** the web using Google Custom Search Engine
3. **Evaluates** sources using AI-powered quality scoring
4. **Enriches** content by fetching full web pages
5. **Synthesizes** information into structured UI panels
6. **Streams** results progressively to the frontend

### Core Design Goals

| Goal | Implementation |
|------|----------------|
| **Accuracy** | Multi-dimensional source scoring, adaptive thresholds, fact verification |
| **Speed** | Parallel processing, progressive streaming, concurrent LLM calls |
| **Resilience** | Circuit breakers, graceful degradation, retry strategies |
| **Transparency** | Source citations, confidence scores, reasoning traces |
| **Scalability** | Stateless pipeline, Redis persistence, background execution |

### The "Deep" Philosophy

Unlike simple search aggregators, Deep Researcher implements **iterative refinement**:

```
Query → Search → Score → [Not Enough Quality?] → Reformulate → Search Again
                              ↓
                        [Quality Met] → Enrich → Compress → Generate Report
```

The system will loop up to 5 times, reformulating queries each iteration until it finds sufficient high-quality sources or exhausts attempts.

---

## 2. High-Level Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                             │
│                     EventSource SSE Connection                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI SERVER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   /stream   │  │   /auth     │  │  /history   │  │   Rate Limiter      │ │
│  │   Router    │  │   Router    │  │   Router    │  │   (SlowAPI/Redis)   │ │
│  └──────┬──────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      PIPELINE RUNNER (Background Task)                  ││
│  │                                                                         ││
│  │   ┌───────────────────────────────────────────────────────────────────┐ ││
│  │   │                    LANGGRAPH STATE MACHINE                        │ ││
│  │   │                                                                   │ ││
│  │   │  classifier → research → reranker → enricher → compressor →      │ ││
│  │   │                    ↑          │                    generator      │ ││
│  │   │                    └──────────┘ (loop if insufficient)            │ ││
│  │   └───────────────────────────────────────────────────────────────────┘ ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  Google CSE │   │ Gemini API  │   │    Redis    │
            │  (Search)   │   │   (LLMs)    │   │ (Sessions)  │
            └─────────────┘   └─────────────┘   └─────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Web Server | FastAPI + Uvicorn | Async HTTP, SSE streaming |
| Agent Orchestration | LangGraph StateGraph | Cyclic workflow, state management |
| LLM Provider | Google Gemini | Classification, scoring, generation |
| Web Search | Google CSE API | External information retrieval |
| Session Store | Redis | Checkpoints, event queue, history |
| Authentication | Firebase Admin + JWT | User identity, token verification |

---

## 3. The Research Pipeline Flow

### Complete Request Lifecycle

```
1. USER SUBMITS QUERY
   │
   ├─► Frontend sends GET /api/research/stream?query=...
   │
   ▼
2. SSE ENDPOINT RECEIVES REQUEST
   │
   ├─► Validate query (length, characters)
   ├─► Resolve session ID (guest or authenticated)
   ├─► Check for existing active query
   │
   ▼
3. PIPELINE STARTS AS BACKGROUND TASK
   │
   ├─► Pipeline runs INDEPENDENTLY of SSE connection
   ├─► Events published to Redis as they occur
   │
   ▼
4. SSE CONSUMER READS FROM REDIS
   │
   ├─► Polls Redis for new events
   ├─► Forwards events to client
   ├─► Client disconnect does NOT stop pipeline
   │
   ▼
5. PIPELINE EXECUTION (LangGraph)
   │
   ├─► [CLASSIFIER] Intent detection, query expansion
   │       │
   │       ├─► RESEARCH_REQUIRED → Continue
   │       ├─► CHITCHAT → Quick response → END
   │       ├─► MALICIOUS → Refusal → END
   │       └─► CLARIFICATION_NEEDED → Loop
   │
   ├─► [RESEARCH] Execute web searches
   │       │
   │       └─► 3-5 expanded queries → Google CSE → Raw results
   │
   ├─► [RERANKER] AI-powered source scoring
   │       │
   │       ├─► Score each document (parallel)
   │       ├─► Apply extractability multipliers
   │       ├─► Filter by adaptive threshold
   │       └─► Select top 5 sources
   │
   ├─► [CONTENT ENRICHER] Fetch full content
   │       │
   │       ├─► Parallel URL fetching (aiohttp)
   │       ├─► HTML parsing, content extraction
   │       └─► Image token extraction
   │
   ├─► [SUFFICIENCY CHECK] Quality gate
   │       │
   │       ├─► sources >= min_required? → Continue
   │       ├─► iteration < max? → Loop back to RESEARCH
   │       └─► max iterations + 0 sources? → ABORT
   │
   ├─► [COMPRESSOR] Document summarization
   │       │
   │       ├─► Summarize each source (parallel)
   │       └─► Concatenate for generator context
   │
   └─► [GENERATOR] Report synthesis
           │
           ├─► Phase 1: UI Planning (panel layout)
           ├─► Phase 2: Panel Generation (per-panel)
           ├─► Phase 3: Validation + Repair
           └─► Output: ResearchReport JSON
   │
   ▼
6. REPORT COMPLETE
   │
   ├─► Final report stored in Redis
   ├─► History entry created (authenticated users)
   └─► SSE stream closes
```

### Intent Routing Decision Tree

```
                    ┌─────────────────┐
                    │   USER QUERY    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   CLASSIFIER    │
                    │  (Gemini Pro)   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  RESEARCH    │  │   CHITCHAT   │  │  MALICIOUS   │
    │  REQUIRED    │  │              │  │              │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                 │
           ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  Research    │  │  Chitchat    │  │   Refusal    │
    │  Pipeline    │  │  Response    │  │   Response   │
    └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 4. Component Deep Dives

### 4.1 Classifier Node

**Purpose**: First gate in the pipeline. Determines what the user wants and whether to proceed with research.

**Model**: `gemini-3-pro-preview` (high accuracy for critical routing)

**Inputs**:
- User query from message history

**Outputs**:
- `intent`: RESEARCH_REQUIRED | CHITCHAT | CLARIFICATION_NEEDED | MALICIOUS
- `safety_passed`: Boolean safety gate
- `expanded_queries`: 3-5 CSE-optimized search queries

**Query Expansion Strategy**:
```
Original: "Winton Ireland Strom and Green vs competitors"

Expanded:
1. "Winton Ireland Strom and Green" insurance company profile
2. intitle:"Winton Ireland" insurance agency review -site:pinterest.com
3. "Winton Ireland Strom" competitors alternatives -site:facebook.com
4. Winton Ireland Strom Green insurance services midwest
5. "WISG" insurance company analysis 2024
```

The classifier uses CSE operators (`intitle:`, `site:`, `-site:`, quotes) to maximize search precision.

---

### 4.2 Research Node

**Purpose**: Execute web searches across expanded queries.

**Model**: None (pure tool execution)

**External Service**: Google Custom Search Engine API

**Key Behaviors**:
1. **First Iteration**: Execute classifier's expanded queries
2. **Subsequent Iterations**: Reformulate queries based on previous results
   - Iteration 1: BROADEN (remove restrictive operators)
   - Iteration 2: NARROW (add precision operators)
   - Iteration 3+: SYNONYMS (alternative phrasings)

**Concurrency**:
- Sequential CSE API calls (prevents SSL pool exhaustion in Docker)
- 0.5s inter-query delay for connection cleanup

**Output**: Raw search results accumulated via `operator.add` reducer

---

### 4.3 Parallel ReRanker Node

**Purpose**: AI-powered quality scoring of each document.

**Model**: `gemini-flash-latest` (fast, parallel-safe)

**Scoring Dimensions** (3-Dimension Composite):
| Dimension | Weight | Question |
|-----------|--------|----------|
| Relevance | 50% | Does this directly answer the query? |
| Quality | 30% | Is this source credible and well-written? |
| Usefulness | 20% | Does this provide actionable information? |

**Post-Processing Pipeline**:
```
LLM Score → Extractability Multiplier → Query Relevance Multiplier → Final Score
```

**Extractability Multipliers** (penalize low-content sources):
| Source Type | Multiplier | Rationale |
|-------------|------------|-----------|
| VIDEO | 0.20 | Cannot extract video content |
| SOCIAL_MEDIA | 0.50 | Limited text, noisy |
| WIKI | 1.10 | Excellent extractability |
| ACADEMIC | 1.08 | High-quality content |
| NEWS | 0.85 | Paywalls, bias concerns |

**Adaptive Threshold**:
The relevance threshold dynamically adjusts based on query characteristics:
- **Low result count** (<15): Use 0.45 (niche query)
- **High social ratio** (>50%): Use 0.45 (limited quality sources)
- **Well-covered topic** (>40 results, <20% social): Use 0.65 (stricter)
- **Default**: Use 0.60

---

### 4.4 Content Enricher Node

**Purpose**: Fetch full content from top-ranked sources.

**Why Needed**: Search snippets (~200 chars) are insufficient for deep synthesis. Full content (~8000 chars per source) provides richer context.

**Parallel Fetching**:
```python
async with aiohttp.ClientSession() as session:
    tasks = [fetch_url(url, semaphore) for url in top_source_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Content Extraction**:
1. Fetch raw HTML
2. Remove scripts, styles, comments
3. Extract text content
4. Parse images for token injection
5. Assess content quality (HIGH/MEDIUM/LOW/INSUFFICIENT)

**Image Token System**:
```
Extracted: {"hero_image_1": {"value": "https://...", "description": "Product photo"}}
Injected into prompt: "Use [IMG:hero_image_1] when referring to the product."
Post-generation: Replace tokens with actual URLs
```

**Graceful Degradation**: If fetch fails, falls back to search snippet.

---

### 4.5 Sufficiency Check (Routing Function)

**Purpose**: Quality gate determining whether to continue or loop.

**Decision Logic**:
```python
def check_source_sufficiency(state) -> "sufficient" | "insufficient" | "abort":
    passing_sources = count(score >= adaptive_threshold for score in confidence_scores)
    
    # Early abort: Iteration 2 with 0 sources (reformulation failed)
    if iteration == 2 and passing_sources == 0:
        return "abort"
    
    # Max iterations with no sources → prevent hallucination
    if iteration >= max_iterations and passing_sources == 0:
        return "abort"
    
    # Max iterations with some sources → proceed with available data
    if iteration >= max_iterations:
        return "sufficient"
    
    # Quality threshold met
    if passing_sources >= min_sources:
        return "sufficient"
    
    # Need more research
    return "insufficient"
```

**The Feedback Loop**:
```
research → reranker → enricher → [insufficient] → research (with reformulated queries)
                                       ↓
                                 [sufficient] → compressor → generator
```

---

### 4.6 Compressor Node

**Purpose**: Parallel document summarization for generator context.

**Model**: `gemini-flash-latest` (fast summarization)

**Strategy**: Instead of Chain-of-Density compression, uses per-document summarization:

```
Source 1 (8000 chars) → Summarize → "Key facts about topic from Source 1..."
Source 2 (8000 chars) → Summarize → "Key facts about topic from Source 2..."
...
Concatenate → compressed_facts (input to generator)
```

**Abort Signals**:
- `NO_SOURCES_TO_COMPRESS`: No sources reached this node
- `ALL_SUMMARIZATIONS_FAILED`: Every LLM call failed (rate limits, timeouts)

---

### 4.7 Generator Node

**Purpose**: Synthesize research into structured UI panels.

**Model**: `gemini-3-pro-preview` (maximum reasoning depth)

**3-Phase Generation**:

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: UI PLANNING                                            │
│                                                                  │
│ Input: Query + Fact Summary (2000 chars)                        │
│ Model: gemini-flash-latest (lightweight)                        │
│ Output: Panel specifications with types and purposes            │
│                                                                  │
│ Example Output:                                                  │
│ [                                                                │
│   {"panel_type": "body", "purpose": "Executive overview"},      │
│   {"panel_type": "table", "purpose": "Technical specs"},        │
│   {"panel_type": "body_listful", "purpose": "Key features"},    │
│   {"panel_type": "body", "purpose": "Analysis"},                │
│   {"panel_type": "body", "purpose": "Conclusion"}               │
│ ]                                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: PANEL GENERATION                                       │
│                                                                  │
│ For each panel in plan:                                         │
│   - Isolated context (prevents cross-panel confusion)           │
│   - Type-specific prompting (table vs body vs body_listful)     │
│   - Image token injection (for image panels)                    │
│                                                                  │
│ Model: gemini-3-pro-preview (per-panel call)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: ASSEMBLY + TIERED VALIDATION                           │
│                                                                  │
│ 1. Assemble panels into ResearchReport                          │
│ 2. Tier 1: Heuristic JSON repair (json-repair library)          │
│ 3. Tier 2: Pydantic schema validation                           │
│ 4. Tier 3: Reflector LLM (fix specific validation errors)       │
│                                                                  │
│ Output: Validated ResearchReport                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Panel Types**:
| Type | Structure | Use Case |
|------|-----------|----------|
| `body` | title + text | Prose sections |
| `table` | title + 2D array | Comparisons, specs |
| `body_listful` | title + text + nested panels | Hierarchical info |
| `image` | image_url + title + caption | Visual content |

---

### 4.8 Abort Response Node

**Purpose**: Generate graceful failure response when research cannot succeed.

**Trigger Conditions**:
- Max iterations reached with 0 quality sources
- Early exit: Iteration 2 with 0 sources (reformulation failed)

**Why This Matters**: Without abort handling, the generator would receive empty input and **hallucinate** content. This node prevents that by generating an honest "unable to research" response.

**Output Structure**:
```json
{
  "title": "Unable to Research: [query]",
  "executive_summary": "After N iterations, we could not find sufficient sources...",
  "confidence_score": 0.0,
  "panels": [
    {"type": "body", "title": "Research Limitations", "text": "..."},
    {"type": "body", "title": "What This Means", "text": "..."},
    {"type": "body", "title": "Suggestions", "text": "..."}
  ]
}
```

---

## 5. State Management & Data Flow

### ResearchState Structure

The `ResearchState` TypedDict is the **single source of truth** across all nodes:

```python
class ResearchState(TypedDict):
    # ═══ CONVERSATION ═══
    messages: Annotated[list, add_messages]  # Appends, never overwrites
    session_id: str
    user_query: str
    
    # ═══ CLASSIFIER OUTPUT ═══
    intent: Literal["RESEARCH_REQUIRED", "CHITCHAT", ...]
    safety_passed: bool
    research_query: str
    expanded_queries: List[str]
    
    # ═══ RESEARCH ARTIFACTS ═══
    raw_search_results: Annotated[List[Dict], operator.add]  # Accumulates
    reranked_documents: List[Dict]
    top_sources: List[Dict]
    confidence_scores: List[Dict[str, float]]
    
    # ═══ ENRICHMENT ═══
    enriched_sources: List[Dict]
    image_token_lookup: Dict[str, Dict[str, str]]
    
    # ═══ COMPRESSION ═══
    compressed_facts: str
    
    # ═══ GENERATION ═══
    final_report: Optional[Dict]
    
    # ═══ CONTROL FLOW ═══
    iteration_count: Annotated[int, operator.add]  # Thread-safe increment
    max_iterations: int
    is_sufficient: bool
    should_abort: bool
    abort_reason: Optional[str]
```

### Reducer Patterns

**Append Reducer** (`add_messages`):
```python
# Each node's message output is APPENDED to existing messages
return {"messages": [AIMessage(content="Found 10 sources")]}
# Result: messages = [...existing..., AIMessage("Found 10 sources")]
```

**Accumulate Reducer** (`operator.add`):
```python
# Search results from each iteration are COMBINED
return {"raw_search_results": new_results}
# Result: raw_search_results = [...iteration1..., ...iteration2..., ...new...]
```

**Overwrite** (default):
```python
# Most fields simply replace previous value
return {"top_sources": filtered_top_5}
# Result: top_sources = filtered_top_5
```

### Data Flow Diagram

```
┌──────────────┐
│  Classifier  │──┐
└──────────────┘  │
                  │ expanded_queries
                  ▼
┌──────────────┐
│   Research   │──┐
└──────────────┘  │
                  │ raw_search_results (accumulates)
                  ▼
┌──────────────┐
│   ReRanker   │──┐
└──────────────┘  │
                  │ top_sources, confidence_scores
                  ▼
┌──────────────┐
│   Enricher   │──┐
└──────────────┘  │
                  │ enriched_sources, image_token_lookup
                  │
                  ├──[insufficient]──→ Back to Research
                  │
                  ▼ [sufficient]
┌──────────────┐
│  Compressor  │──┐
└──────────────┘  │
                  │ compressed_facts
                  ▼
┌──────────────┐
│  Generator   │──┐
└──────────────┘  │
                  │ final_report
                  ▼
              ┌───────┐
              │  END  │
              └───────┘
```

---

## 6. Concurrency & Resilience Patterns

### Parallel Processing Points

| Node | Parallelism | Control Mechanism |
|------|-------------|-------------------|
| ReRanker | Score 8 docs simultaneously | asyncio.Semaphore(8) |
| Enricher | Fetch 5 URLs simultaneously | asyncio.Semaphore(5) |
| Compressor | Summarize 5 docs simultaneously | asyncio.Semaphore(5) |

### Circuit Breaker Pattern

Protects against cascade failures when external services fail:

```python
class CircuitBreaker:
    States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)
    
    CLOSED: Requests pass through, failures counted
    OPEN: Requests immediately rejected (fail fast)
    HALF_OPEN: Limited requests allowed to test recovery
    
    Thresholds:
    - 5 failures → OPEN
    - 60s timeout → HALF_OPEN
    - 2 successes → CLOSED
```

**Applied to**: Google CSE API calls (`search_breaker`)

### Retry Strategy (CSE API)

```python
CSE_MAX_RETRIES = 4           # 5 total attempts
CSE_BASE_DELAY = 0.5          # Initial backoff
CSE_MAX_DELAY = 4.0           # Maximum backoff

Retryable errors:
- SSL handshake failures
- Connection reset/timeout
- HTTP 429, 502, 503, 504
```

### Timeout Protection

| Operation | Timeout | Fallback |
|-----------|---------|----------|
| LLM Scoring | 30s | Default low-confidence score |
| LLM Summarization | 45s | Raw content passthrough |
| URL Fetch | 10s | Use search snippet |
| CSE API | 8s | Skip query, try next |

### Graceful Degradation Cascade

```
Content fetch fails → Use snippet instead
Scoring fails → Assign default score (0.5)
Summarization fails → Pass raw content
All summaries fail → Set abort flag
Generator fails → Return error report
```

---

## 7. Session Persistence & Reconnection

### The Decoupled Architecture

**Problem**: Browser refresh or network hiccup kills SSE connection, losing research progress.

**Solution**: Complete separation between pipeline execution and event delivery.

```
┌─────────────────────────────────────────────────────────────────┐
│                     BACKGROUND PIPELINE                         │
│                                                                 │
│   Runs as asyncio.Task, completely independent of HTTP request │
│   Publishes events to Redis as they occur                      │
│   Client disconnect has NO effect on execution                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ publish_sse_event(query_id, event_type, data)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          REDIS                                  │
│                                                                 │
│   Key: sse_events:{query_id}                                   │
│   Value: List of event JSON objects                            │
│   TTL: 1 hour                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ get_sse_events(query_id, from_index)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SSE CONSUMER                              │
│                                                                 │
│   Polls Redis for new events (0.3s interval)                   │
│   Yields events to client                                       │
│   Timeout after 180s of no events                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Heartbeat Mechanism

Long operations (CSE search with retries) can take 30+ seconds without producing events. The SSE consumer would timeout.

**Solution**: Background heartbeat task emits internal keepalive events:

```python
async def _emit_heartbeat(query_id, stop_event, interval=10.0):
    while not stop_event.is_set():
        await asyncio.sleep(interval)
        await publish_sse_event(query_id, "heartbeat", {"message": "Processing..."})
```

SSE consumer receives heartbeats to reset idle counter but does NOT forward to client.

### Active Query Tracking

For authenticated users, only ONE active query allowed:

```
User submits query
    │
    ├─► Check for existing active query
    │       │
    │       ├─► status=processing + pipeline running → Reconnect to stream
    │       ├─► status=processing + pipeline dead → Force replace (stale)
    │       └─► status=completed/failed → Auto-clear, allow new
    │
    └─► Save new active query (status=processing)
```

### Reconnection Flow

```
1. Client disconnects (browser refresh, network issue)
2. Pipeline continues running in background
3. Client reconnects, hits /history/active
4. Backend returns active query with:
   - status: processing | completed | failed
   - If completed: full final_report included
5. Client either:
   - Reconnects to SSE stream (if still processing)
   - Displays cached result (if completed)
```

---

## 8. Key Architectural Decisions

### Decision 1: LangGraph over Custom Orchestration

**Why LangGraph?**
- Native cyclic graph support (research feedback loop)
- Built-in checkpointing (session persistence)
- State management with reducers
- Streaming support (astream_events)

**Trade-off**: LangGraph's msgpack serialization limits what can be stored in state (no Request objects, no Executors).

**Solution**: Context variables (`contextvars`) for non-serializable resources.

---

### Decision 2: Strict Two-Model Stack

**Models Used**:
- `gemini-3-pro-preview`: High-accuracy tasks (classifier, compressor, generator)
- `gemini-flash-latest`: Fast tasks (reranker, chitchat)

**Why Not More Models?**
- Simplifies API compatibility
- Reduces testing surface
- Consistent behavior expectations

---

### Decision 3: 3-Dimension Scoring over Binary Relevance

**Traditional**: Binary relevant/not-relevant

**Deep Researcher**: Multi-dimensional scoring
- Relevance (50%): Query match
- Quality (30%): Source credibility
- Usefulness (20%): Actionable information

**Benefit**: A highly relevant but low-quality source (e.g., social media post) gets appropriately downranked.

---

### Decision 4: Adaptive Thresholds

**Problem**: Fixed 0.60 threshold fails for niche queries with limited web presence.

**Solution**: Dynamic threshold based on:
- Result count (fewer results → lower threshold)
- Social media ratio (more social → lower threshold)
- Query type (entity comparison → lower threshold)

**Benefit**: Prevents over-filtering for niche topics while maintaining standards for well-covered topics.

---

### Decision 5: Pipeline Decoupling

**Problem**: SSE connection tied to pipeline execution. Browser refresh = lost research.

**Solution**: 
- Pipeline runs as independent background task
- Events published to Redis
- SSE consumer reads from Redis

**Trade-off**: Added complexity, Redis dependency.

**Benefit**: True resilience. Client can disconnect/reconnect freely.

---

### Decision 6: Abort Path for Zero Sources

**Problem**: Generator receiving empty input hallucinates content.

**Solution**: Dedicated abort path that:
- Detects zero-source scenarios
- Generates honest "unable to research" response
- Provides helpful suggestions to user

**Benefit**: Maintains user trust by being transparent about limitations.

---

### Decision 7: Per-Document Summarization over Global Compression

**Original Design**: Chain of Density compression of all sources into single compressed output.

**Current Design**: Summarize each document independently, then concatenate.

**Why Changed?**
- Better source attribution (each summary tagged with source)
- Parallel processing (multiple LLM calls simultaneously)
- Graceful degradation (one failed summary doesn't break everything)

---

## Summary

The AI Deep Researcher is a **resilient, multi-agent research pipeline** that:

1. **Classifies** user intent with high-accuracy LLM
2. **Searches** using CSE-optimized queries with iterative refinement
3. **Scores** sources on three dimensions with adaptive thresholds
4. **Enriches** top sources with full content fetching
5. **Compresses** via parallel per-document summarization
6. **Generates** structured reports with tiered validation
7. **Streams** results progressively via decoupled SSE architecture

The system is designed to be **accurate** (multi-dimensional scoring, fact verification), **fast** (parallel processing, progressive streaming), and **resilient** (circuit breakers, graceful degradation, session persistence).

---

*End of Architecture Guide*
