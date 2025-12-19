# Deep Research Flow Architecture

**System:** Portfolio Backend API - Fit Check Agent  
**Subsystem:** Employer Intelligence Gathering & Quality Assurance  
**Components:** Phase 2 (Deep Research) + Phase 2B (Research Reranker)  
**Version:** 1.0.0

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Design Philosophy](#2-design-philosophy)
3. [System Goals](#3-system-goals)
4. [Component Architecture](#4-component-architecture)
5. [Data Flow Diagram](#5-data-flow-diagram)
6. [Phase 2: Deep Research Node](#6-phase-2-deep-research-node)
7. [Phase 2B: Research Reranker Node](#7-phase-2b-research-reranker-node)
8. [Conditional Routing Logic](#8-conditional-routing-logic)
9. [Data Quality Framework](#9-data-quality-framework)
10. [Industry Inference Engine](#10-industry-inference-engine)
11. [Bad Data Detection System](#11-bad-data-detection-system)
12. [Enhancement Query Generation](#12-enhancement-query-generation)
13. [State Management](#13-state-management)
14. [Error Handling & Graceful Degradation](#14-error-handling--graceful-degradation)
15. [SSE Event Emission](#15-sse-event-emission)

---

## 1. Executive Overview

The Deep Research Flow is a **two-phase intelligence gathering and quality assurance subsystem** within the Fit Check Agent pipeline. It is responsible for:

1. **Gathering external employer intelligence** via web search
2. **Synthesizing raw data** into structured employer profiles
3. **Validating data quality** before downstream processing
4. **Pruning unreliable data** to prevent contamination
5. **Making routing decisions** (continue, retry, or early exit)

### Critical Insight

> **"Bad data is worse than no data."**

The Research Reranker exists because LLM synthesis can produce confident-sounding but unreliable outputs. Without quality validation, garbage data would flow downstream, causing:
- Inflated match scores based on hallucinated requirements
- False confidence in non-existent tech stacks
- Wasted compute on analyzing fabricated information

---

## 2. Design Philosophy

### 2.1 Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Totality of Evidence** | Gather comprehensive external data before analysis |
| **Garbage-In Prevention** | Aggressive data pruning before downstream processing |
| **Fail-Fast for Bad Data** | Early exit saves compute and prevents false confidence |
| **Explicit Uncertainty** | Flag unknown data rather than interpolate |
| **Retry with Enhancement** | Obscure companies get a second chance with alternative queries |

### 2.2 Gemini Optimization

Both nodes are optimized for Google Gemini models:

| Optimization | Rationale |
|--------------|-----------|
| XML-structured prompts | Better instruction following |
| Criteria-based constraints | More reliable than "think step-by-step" |
| Post-hoc reasoning trace | Avoids redundant thinking in reasoning models |
| Low temperature (0.1-0.3) | Deterministic, reproducible outputs |
| Concise prompts for reasoning models | Prevents "double-think" timeouts |

---

## 3. System Goals

### 3.1 Primary Goals

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEEP RESEARCH FLOW GOALS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. GATHER INTELLIGENCE                                             │
│     └─► Execute targeted web searches based on query classification │
│     └─► Extract tech stack, requirements, culture signals           │
│     └─► Synthesize findings into structured employer profile        │
│                                                                     │
│  2. ENSURE DATA QUALITY                                             │
│     └─► Detect fabricated/hallucinated content                      │
│     └─► Prune generic phrases and platitudes                        │
│     └─► Verify company existence and legitimacy                     │
│                                                                     │
│  3. ROUTE INTELLIGENTLY                                             │
│     └─► Continue with clean/partial data                            │
│     └─► Retry with enhanced queries for sparse data                 │
│     └─► Early exit for garbage/suspicious data                      │
│                                                                     │
│  4. PRESERVE TRANSPARENCY                                           │
│     └─► Track which queries were executed                           │
│     └─► Log what data was pruned and why                            │
│     └─► Flag quality concerns for downstream awareness              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Data extraction rate | ≥2 tech items, ≥2 requirements | Per-search average |
| Hallucination prevention | 0 fabricated company claims | Manual audit |
| Early exit accuracy | 100% for injection attempts | Security testing |
| Retry success rate | >50% improvement on retry | A/B comparison |

---

## 4. Component Architecture

### 4.1 Component Relationship

```
                    ┌──────────────────────────────────────────────────────────────┐
                    │                    DEEP RESEARCH FLOW                        │
                    └──────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│   ┌─────────────┐     ┌───────────────────┐     ┌──────────────────────────────┐   │
│   │  Phase 1    │     │    Phase 2        │     │       Phase 2B               │   │
│   │ CONNECTING  │────►│  DEEP_RESEARCH    │────►│   RESEARCH_RERANKER          │   │
│   └─────────────┘     └───────────────────┘     └──────────────────────────────┘   │
│         │                     │                           │                         │
│         │                     │                           ├─── CONTINUE ──────────► │
│         │                     │                           │                         │
│         ▼                     ▼                           ├─── ENHANCE_SEARCH ──┐   │
│   • query_type          • web_search tool                 │                     │   │
│   • company_name        • LLM synthesis                   │     ┌───────────────┘   │
│   • job_title           • Phase2Output                    │     │ (retry)           │
│   • extracted_skills                                      │     ▼                   │
│                                                           │ ┌───────────────────┐   │
│                                                           │ │  DEEP_RESEARCH    │   │
│                                                           │ │ (enhanced queries)│   │
│                                                           │ └───────────────────┘   │
│                                                           │                         │
│                                                           ├─── EARLY_EXIT ────────► │
│                                                           │    (skip to Phase 5)    │
│                                                           │                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Module Dependencies

```
services/nodes/deep_research.py
├── imports
│   ├── config.llm.get_llm
│   ├── services.pipeline_state.FitCheckPipelineState, Phase2Output
│   ├── services.callbacks.ThoughtCallback
│   ├── services.tools.web_search.web_search
│   ├── services.utils.get_response_text
│   └── services.prompt_loader.load_prompt, PHASE_DEEP_RESEARCH

services/nodes/research_reranker.py
├── imports
│   ├── config.llm.get_llm
│   ├── services.pipeline_state.FitCheckPipelineState
│   ├── services.callbacks.ThoughtCallback
│   ├── services.utils.get_response_text
│   └── services.prompt_loader.load_prompt, PHASE_RESEARCH_RERANKER
```

---

## 5. Data Flow Diagram

```
                              PHASE 1 OUTPUT
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              PHASE 2: DEEP RESEARCH                                   │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌─────────────────┐                                                                │
│   │ Query Strategy  │ ◄── company vs job_description determines search approach     │
│   │ Selection       │                                                                │
│   └────────┬────────┘                                                                │
│            │                                                                         │
│            ▼                                                                         │
│   ┌─────────────────┐     ┌─────────────────┐                                        │
│   │ Search Query 1  │────►│   web_search    │────► Result 1 (max 1500 chars)         │
│   └─────────────────┘     │      tool       │                                        │
│                           └─────────────────┘                                        │
│   ┌─────────────────┐     ┌─────────────────┐                                        │
│   │ Search Query 2  │────►│   web_search    │────► Result 2 (max 1500 chars)         │
│   └─────────────────┘     │      tool       │                                        │
│                           └─────────────────┘                                        │
│            │                                                                         │
│            ▼                                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │              FORMATTED SEARCH RESULTS               │                            │
│   │  --- Search Result 1 ---                            │                            │
│   │  Query: "..."                                       │                            │
│   │  Findings: ...                                      │                            │
│   │                                                     │                            │
│   │  --- Search Result 2 ---                            │                            │
│   │  Query: "..."                                       │                            │
│   │  Findings: ...                                      │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
│                            ▼                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │           LLM SYNTHESIS (Gemini)                    │                            │
│   │   Temperature: 0.3                                  │                            │
│   │   Prompt: XML-structured with constraints           │                            │
│   │   Output: JSON with employer profile                │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
│                            ▼                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │                 PHASE 2 OUTPUT                      │                            │
│   │  • employer_summary: string                         │                            │
│   │  • identified_requirements: List[str]               │                            │
│   │  • tech_stack: List[str]                            │                            │
│   │  • culture_signals: List[str]                       │                            │
│   │  • search_queries_used: List[str]                   │                            │
│   │  • reasoning_trace: string                          │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
└────────────────────────────┼─────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 2B: RESEARCH RERANKER                                  │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │         HEURISTIC PRE-ASSESSMENT                    │                            │
│   │  • Count tech_stack, requirements, culture_signals  │                            │
│   │  • Check summary word count                         │                            │
│   │  • Determine preliminary tier                       │                            │
│   │  • Pre-prune generic/platitude data                 │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
│                            ▼                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │         BAD DATA PATTERN DETECTION                  │                            │
│   │  • Generic tech terms check                         │                            │
│   │  • Generic requirement patterns                     │                            │
│   │  • Platitude culture signals                        │                            │
│   │  • Suspicious company name patterns                 │                            │
│   │  • Hallucination signals                            │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
│                            ▼                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │          INDUSTRY INFERENCE (if sparse)             │                            │
│   │  If tech_stack < 2:                                 │                            │
│   │    • Detect industry from context keywords          │                            │
│   │    • Provide fallback tech assumptions              │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
│                            ▼                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │          LLM-AS-JUDGE EVALUATION                    │                            │
│   │  Temperature: 0.1 (deterministic)                   │                            │
│   │  Inputs: heuristics + phase_2_output                │                            │
│   │  Evaluates: quality tier, confidence, action        │                            │
│   └────────────────────────┬────────────────────────────┘                            │
│                            │                                                         │
│                            ▼                                                         │
│   ┌─────────────────────────────────────────────────────┐                            │
│   │              ROUTING DECISION                       │                            │
│   │                                                     │                            │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │                            │
│   │  │  CONTINUE   │  │  ENHANCE    │  │ EARLY_EXIT  │  │                            │
│   │  │             │  │  SEARCH     │  │             │  │                            │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │                            │
│   │         │                │                │         │                            │
│   │         ▼                ▼                ▼         │                            │
│   │   skeptical_       deep_research    generate_       │                            │
│   │   comparison       (retry)          results         │                            │
│   │                                                     │                            │
│   └─────────────────────────────────────────────────────┘                            │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Phase 2: Deep Research Node

### 6.1 Purpose

The Deep Research node is the **intelligence gathering engine**. It executes targeted web searches and synthesizes raw search results into a structured employer profile.

### 6.2 Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `SYNTHESIS_TEMPERATURE` | 0.3 | Balance accuracy with synthesis creativity |
| `MAX_SEARCH_QUERIES` | 2 | Latency control |
| `MAX_RESULT_LENGTH` | 1500 chars | Prevent context overflow |

### 6.3 Search Query Construction

The search strategy varies based on Phase 1 classification:

#### Company-Type Query

```python
# For query_type == "company"
queries = [
    f"{company} software engineer tech stack engineering culture",
    f"{company} careers jobs software developer requirements"
]
```

**Goal:** Discover company-specific tech stack, culture, and job requirements.

#### Job Description Query

```python
# For query_type == "job_description"
title = job_title or "software engineer"
skills = extracted_skills[:3]

queries = [
    f"{title} {skills} requirements tech stack",
    f"{company_name} engineering team culture values"  # if company known
    # OR
    f"{skills[0]} engineer job requirements industry trends"  # if no company
]
```

**Goal:** Understand role requirements and industry context.

### 6.4 Search Result Formatting

```python
def format_search_results(results: List[Dict]) -> str:
    """
    Format:
    --- Search Result 1 ---
    Query: "{query}"
    Findings:
    {result_text}
    
    --- Search Result 2 ---
    ...
    """
```

### 6.5 LLM Synthesis

The LLM receives:
- Query type and extracted entities from Phase 1
- Formatted search results
- XML-structured prompt with behavioral constraints

**Output Schema (Phase2Output):**

```python
{
    "employer_summary": str,           # 50-200 word synthesis
    "identified_requirements": List[str],  # Explicit job requirements
    "tech_stack": List[str],           # Technologies mentioned
    "culture_signals": List[str],      # Cultural indicators
    "search_queries_used": List[str],  # Audit trail
    "reasoning_trace": str             # Post-hoc explanation
}
```

### 6.6 Graceful Degradation

On error, the node returns a minimal fallback:

```python
fallback_output = Phase2Output(
    employer_summary="Unable to gather complete employer information...",
    identified_requirements=[],
    tech_stack=[],
    culture_signals=[],
    search_queries_used=queries_executed,
    reasoning_trace=f"Research phase encountered an error: {error}"
)
```

The pipeline continues with `low_data_flag=True`.

---

## 7. Phase 2B: Research Reranker Node

### 7.1 Purpose

The Research Reranker is the **data quality firewall**. It prevents bad data from contaminating downstream analysis by:

1. Validating Phase 2 output quality
2. Pruning unreliable data elements
3. Making routing decisions
4. Flagging concerns for transparency

### 7.2 Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `RERANKER_TEMPERATURE` | 0.1 | Maximum determinism for consistent judgments |
| `MIN_TECH_STACK_HIGH` | 3 | Threshold for HIGH tier |
| `MIN_TECH_STACK_MEDIUM` | 1 | Threshold for MEDIUM tier |
| `MIN_REQUIREMENTS_HIGH` | 3 | Threshold for HIGH tier |
| `MIN_REQUIREMENTS_MEDIUM` | 2 | Threshold for MEDIUM tier |
| `MIN_EMPLOYER_SUMMARY_WORDS` | 15 | Minimum for valid summary |

### 7.3 Processing Pipeline

```
Phase 2 Output
      │
      ▼
┌─────────────────────────────────────────┐
│   1. HEURISTIC PRE-ASSESSMENT           │
│      assess_quality_heuristically()     │
│      • Count tech/requirements/culture  │
│      • Determine preliminary tier       │
│      • Pre-prune low-quality data       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   2. BAD DATA PATTERN DETECTION         │
│      detect_bad_data_patterns()         │
│      • Check for generic terms          │
│      • Check for suspicious patterns    │
│      • Assess risk level                │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   3. INDUSTRY INFERENCE (if sparse)     │
│      infer_industry_from_context()      │
│      • Match keywords to industries     │
│      • Provide fallback tech stack      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   4. LLM-AS-JUDGE EVALUATION            │
│      • Evaluate quality with rubric     │
│      • Determine confidence score       │
│      • Recommend routing action         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   5. ROUTING DECISION                   │
│      • CONTINUE → skeptical_comparison  │
│      • ENHANCE_SEARCH → deep_research   │
│      • EARLY_EXIT → generate_results    │
└─────────────────────────────────────────┘
```

### 7.4 Output Schema (ResearchRerankerOutput)

```python
{
    # Data Quality Assessment
    "data_quality_tier": Literal["CLEAN", "PARTIAL", "SPARSE", "UNRELIABLE", "GARBAGE"],
    "research_quality_tier": Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"],
    "data_confidence_score": int,  # 0-100
    
    # Quality Issues
    "quality_flags": List[str],
    "missing_data_categories": List[str],
    
    # Routing Decision
    "recommended_action": Literal["CONTINUE", "CONTINUE_WITH_FLAGS", "ENHANCE_SEARCH", "EARLY_EXIT"],
    "enhancement_queries": List[str],  # For retry
    
    # Company Verification
    "company_verifiability": Literal["VERIFIED", "PARTIAL", "UNVERIFIED", "SUSPICIOUS"],
    "company_verification": Dict[str, Any],
    
    # Data Pruning
    "pruned_data": Dict[str, List[str]],  # What was removed
    "cleaned_data": Dict[str, Any],       # What was kept
    
    # Exit Handling
    "early_exit_reason": str,
    "reasoning_trace": str
}
```

---

## 8. Conditional Routing Logic

### 8.1 Routing Decision Tree

```
                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Is action EARLY_EXIT? │
                    │ OR data_tier GARBAGE? │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │ YES                               │ NO
              ▼                                   ▼
    ┌─────────────────┐              ┌───────────────────────┐
    │ EARLY EXIT      │              │ Is action ENHANCE_    │
    │ → generate_     │              │ SEARCH AND attempt<2? │
    │   results       │              └───────────┬───────────┘
    │ early_exit=True │                          │
    │ low_data=True   │            ┌─────────────┴─────────────┐
    └─────────────────┘            │ YES                       │ NO
                                   ▼                           ▼
                       ┌─────────────────┐        ┌───────────────────────┐
                       │ ENHANCED RETRY  │        │ Is tier HIGH/MEDIUM   │
                       │ → deep_research │        │ AND action CONTINUE?  │
                       │ search_attempt++│        └───────────┬───────────┘
                       │ (different      │                    │
                       │  queries used)  │      ┌─────────────┴─────────────┐
                       └─────────────────┘      │ YES                       │ NO
                                                ▼                           ▼
                                   ┌─────────────────┐        ┌─────────────────┐
                                   │ CONTINUE        │        │ PROCEED WITH    │
                                   │ → skeptical_    │        │ FLAGS           │
                                   │   comparison    │        │ → skeptical_    │
                                   │ low_data=False  │        │   comparison    │
                                   └─────────────────┘        │ low_data=True   │
                                                              └─────────────────┘
```

### 8.2 Routing Implementation (fit_check_agent.py)

```python
def route_after_research_reranker(state: FitCheckPipelineState) -> str:
    reranker_output = state.get("research_reranker_output") or {}
    search_attempt = state.get("search_attempt", 1)
    early_exit = state.get("early_exit", False)
    
    data_tier = reranker_output.get("data_quality_tier", "PARTIAL")
    action = reranker_output.get("recommended_action", "CONTINUE")
    
    # CRITICAL: Early exit for garbage/suspicious data
    if early_exit or action == "EARLY_EXIT" or data_tier == "GARBAGE":
        return "generate_results"
    
    # ENHANCE: Retry search for sparse data (first attempt only)
    if action == "ENHANCE_SEARCH" and search_attempt < 2:
        return "deep_research"
    
    # CONTINUE: Good or acceptable data proceeds
    if action in ["CONTINUE", "CONTINUE_WITH_FLAGS"]:
        return "skeptical_comparison"
    
    return "skeptical_comparison"  # Default: proceed with caution
```

### 8.3 State Updates per Route

| Route | State Changes |
|-------|---------------|
| CONTINUE | `current_phase="skeptical_comparison"`, `low_data_flag=False` |
| CONTINUE_WITH_FLAGS | `current_phase="skeptical_comparison"`, `low_data_flag=True` |
| ENHANCE_SEARCH | `current_phase="deep_research"`, `search_attempt+=1` |
| EARLY_EXIT | `current_phase="generate_results"`, `early_exit=True`, `low_data_flag=True` |

---

## 9. Data Quality Framework

### 9.1 Quality Tier Definitions

#### Data Quality Tiers (Triage)

| Tier | Definition | Criteria |
|------|------------|----------|
| **CLEAN** | High-quality, verified data | tech≥3, requirements≥3, no flags |
| **PARTIAL** | Acceptable with minor gaps | tech≥1, requirements≥2 |
| **SPARSE** | Limited but usable data | some data but below thresholds |
| **UNRELIABLE** | Contradictory or suspicious | mixed quality signals |
| **GARBAGE** | Unusable, possibly fabricated | no real data, injection attempt |

#### Research Quality Tiers (Overall)

| Tier | Confidence Range | Routing |
|------|------------------|---------|
| **HIGH** | 75-100 | CONTINUE |
| **MEDIUM** | 40-74 | CONTINUE or CONTINUE_WITH_FLAGS |
| **LOW** | 15-39 | ENHANCE_SEARCH or CONTINUE_WITH_FLAGS |
| **INSUFFICIENT** | 0-14 | EARLY_EXIT |

### 9.2 Heuristic Scoring

```python
def assess_quality_heuristically(phase_2_output) -> Dict:
    # Count AFTER pruning for accurate assessment
    pruned = prune_low_quality_data(phase_2_output)
    
    tech_count = len(pruned["retained_tech"])
    req_count = len(pruned["retained_requirements"])
    
    # Tier determination
    if tech_count >= 3 and req_count >= 3:
        preliminary_tier = "HIGH"
        data_quality_tier = "CLEAN"
    elif tech_count >= 1 and req_count >= 2:
        preliminary_tier = "MEDIUM"
        data_quality_tier = "PARTIAL"
    elif tech_count == 0 and req_count == 0:
        preliminary_tier = "INSUFFICIENT"
        data_quality_tier = "GARBAGE" if summary_words < 10 else "SPARSE"
    else:
        preliminary_tier = "LOW"
        data_quality_tier = "SPARSE"
```

---

## 10. Industry Inference Engine

### 10.1 Purpose

When tech stack data is sparse (< 2 items), the system attempts to **infer the industry** from available context to provide fallback technology assumptions.

### 10.2 Supported Industries

| Industry | Signal Keywords | Representative Technologies |
|----------|-----------------|----------------------------|
| **fintech** | fintech, financial, payments, banking | Python, Java, Go, PostgreSQL, Kafka |
| **ai_ml** | ai, ml, machine learning, deep learning | Python, PyTorch, TensorFlow, CUDA |
| **saas_b2b** | saas, enterprise, b2b, subscription | TypeScript, Python, React, AWS |
| **e_commerce** | e-commerce, marketplace, retail | Python, Node.js, PostgreSQL, Redis |
| **streaming_media** | streaming, media, video, content | Java, Scala, Go, Kafka, Spark |
| **healthcare** | healthcare, medical, patient, HIPAA | Python, Java, PostgreSQL, FHIR |
| **gaming** | gaming, esports, unity, unreal | C++, C#, Unity, Go, Redis |
| **cybersecurity** | security, infosec, threat, vulnerability | Python, Go, Rust, Linux, Splunk |

### 10.3 Inference Algorithm

```python
def infer_industry_from_context(company_name, employer_summary, job_title):
    context_text = f"{company_name} {employer_summary} {job_title}".lower()
    
    # Score each industry by signal matches
    industry_scores = {}
    for industry, config in INDUSTRY_TECH_DEFAULTS.items():
        signals = config.get("signals", [])
        score = sum(1 for signal in signals if signal in context_text)
        if score > 0:
            industry_scores[industry] = score
    
    # Return highest scoring industry + top 5 representative technologies
    best_industry = max(industry_scores, key=industry_scores.get)
    return best_industry, inferred_technologies[:5]
```

---

## 11. Bad Data Detection System

### 11.1 Detection Categories

#### Generic Tech Terms (Pruned)

```python
GENERIC_TECH_TERMS = {
    "modern stack", "cloud", "databases", "web technologies",
    "modern technologies", "cutting-edge", "best practices",
    "agile", "devops", "full stack", "backend", "frontend",
    "microservices", "api", "rest", "scalable", "distributed"
}
```

**Action:** Removed from tech_stack before downstream processing.

#### Generic Requirement Patterns (Pruned)

```python
GENERIC_REQUIREMENT_PATTERNS = [
    r"must have experience",
    r"strong (communication|skills|background)",
    r"team player",
    r"fast-paced environment",
    r"passion for",
    r"self-starter",
    r"excellent (written|verbal)",
    r"ability to (work|learn|adapt)",
    r"problem.?solving",
    r"detail.?oriented",
]
```

**Action:** Removed if short (< 10 words).

#### Platitude Culture Signals (Pruned)

```python
PLATITUDE_CULTURE_SIGNALS = {
    "innovative culture", "great benefits", "competitive salary",
    "work-life balance", "collaborative environment", "fast-growing",
    "exciting opportunity", "dynamic team", "cutting-edge",
    "industry leader", "passionate team", "make an impact"
}
```

**Action:** Removed as uninformative.

#### Suspicious Name Patterns (CRITICAL)

```python
SUSPICIOUS_NAME_PATTERNS = [
    r"ignore\s*ai",
    r"test\s*corp",
    r"fake\s*company",
    r"<[^>]+>",           # HTML/XML tags
    r"\{[^}]+\}",         # Template variables
    r"prompt|inject|ignore|bypass|override"
]
```

**Action:** IMMEDIATE EARLY_EXIT with `company_verifiability=SUSPICIOUS`.

### 11.2 Risk Level Assessment

```python
def detect_bad_data_patterns(phase_2_output, company_name) -> Dict:
    patterns_detected = []
    risk_level = "LOW"
    
    # Check each category...
    
    # Escalation logic
    if len(patterns_detected) >= 3:
        risk_level = "HIGH"
    elif suspicious_name_detected:
        risk_level = "CRITICAL"
    elif len(patterns_detected) >= 1:
        risk_level = "MEDIUM"
    
    return {
        "patterns_detected": patterns_detected,
        "risk_level": risk_level
    }
```

---

## 12. Enhancement Query Generation

### 12.1 Purpose

When initial research returns sparse data, the system generates **alternative search queries** targeting different data sources.

### 12.2 Query Types

```python
def generate_enhancement_queries(company_name, job_title, inferred_industry):
    queries = []
    
    if company_name:
        # Alternative source queries
        queries.extend([
            f"{company_name} github engineering open source",
            f"{company_name} engineering blog technology",
            f"{company_name} linkedin engineering team",
            f"{company_name} crunchbase funding technology stack",
            f"{company_name} glassdoor engineer interview",
        ])
    
    if job_title and inferred_industry:
        # Industry-specific queries
        queries.append(f"{inferred_industry} {job_title} typical tech stack 2024")
    
    return queries[:4]  # Limit to 4
```

### 12.3 Retry Behavior

On enhanced search retry:
1. `search_attempt` is incremented (1 → 2)
2. New queries are used instead of original
3. If still sparse after retry, pipeline continues with `low_data_flag=True`
4. Maximum 1 retry (prevents infinite loops)

---

## 13. State Management

### 13.1 Research-Related State Fields

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `phase_2_output` | Phase2Output | deep_research | Synthesized employer intelligence |
| `research_reranker_output` | ResearchRerankerOutput | research_reranker | Quality assessment |
| `search_attempt` | int | research_reranker | Current attempt (1 or 2) |
| `low_data_flag` | bool | research_reranker | Downstream awareness flag |
| `early_exit` | bool | research_reranker | Skip to generate_results |

### 13.2 State Flow Example

```python
# After Phase 2 (first attempt)
state = {
    "phase_2_output": {
        "employer_summary": "...",
        "tech_stack": ["Python"],  # Sparse!
        "identified_requirements": [],
        ...
    },
    "search_attempt": 1,
}

# After Phase 2B (triggers retry)
state = {
    "research_reranker_output": {
        "data_quality_tier": "SPARSE",
        "recommended_action": "ENHANCE_SEARCH",
        ...
    },
    "search_attempt": 2,  # Incremented
    "current_phase": "deep_research",  # Retry
}

# After Phase 2 (retry with enhanced queries)
state = {
    "phase_2_output": {
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],  # Better!
        ...
    },
    "search_attempt": 2,
}

# After Phase 2B (now acceptable)
state = {
    "research_reranker_output": {
        "data_quality_tier": "PARTIAL",
        "recommended_action": "CONTINUE_WITH_FLAGS",
        ...
    },
    "low_data_flag": True,
    "current_phase": "skeptical_comparison",  # Continue
}
```

---

## 14. Error Handling & Graceful Degradation

### 14.1 Deep Research Error Handling

```python
try:
    # Execute searches and synthesis...
    return {"phase_2_output": validated_output, ...}
except Exception as e:
    # Return fallback with empty data
    fallback_output = Phase2Output(
        employer_summary="Unable to gather complete employer information...",
        identified_requirements=[],
        tech_stack=[],
        culture_signals=[],
        search_queries_used=queries_executed,
        reasoning_trace=f"Research phase encountered an error: {str(e)[:100]}"
    )
    return {
        "phase_2_output": fallback_output,
        "current_phase": "skeptical_comparison",  # Continue anyway
        "processing_errors": [f"Phase 2 error: {str(e)}"]
    }
```

### 14.2 Research Reranker Error Handling

```python
try:
    # LLM evaluation...
except Exception as e:
    # Use heuristic-based decision
    heuristics = assess_quality_heuristically(phase_2)
    bad_data = detect_bad_data_patterns(phase_2, company_name)
    
    is_garbage = heuristics["data_quality_tier"] == "GARBAGE"
    is_critical = bad_data["risk_level"] == "CRITICAL"
    
    fallback_output = {
        "data_quality_tier": heuristics["data_quality_tier"],
        "recommended_action": "EARLY_EXIT" if (is_garbage or is_critical) else "CONTINUE_WITH_FLAGS",
        "quality_flags": heuristics["quality_flags"] + ["EVALUATION_ERROR"],
        ...
    }
    
    return {
        "research_reranker_output": fallback_output,
        "current_phase": "generate_results" if (is_garbage or is_critical) else "skeptical_comparison",
        "early_exit": is_garbage or is_critical,
        "search_attempt": search_attempt + 1,  # Prevent retry loops
    }
```

---

## 15. SSE Event Emission

### 15.1 Deep Research Events

| Event Type | When | Content |
|------------|------|---------|
| `phase` | Node start | `"Researching for info..."` |
| `thought (tool_call)` | Before each search | `tool="web_search"`, `input={query}` |
| `thought (observation)` | After each search | `"Found relevant employer information."` |
| `thought (reasoning)` | Before synthesis | `"Synthesizing search results..."` |
| `phase_complete` | Node end | `"Identified X technologies, Y requirements, Z culture signals"` |

### 15.2 Research Reranker Events

| Event Type | When | Content |
|------------|------|---------|
| `phase` | Node start | `"Validating research quality..."` |
| `thought (reasoning)` | After heuristics | `"Assessing research quality: {tier} tier detected"` |
| `phase_complete` | Node end | `"Data: {tier} | Quality: {tier} | Confidence: {score}% | Action: {action}"` |

---

## Summary

The Deep Research Flow is a **sophisticated intelligence gathering and quality assurance subsystem** that ensures only reliable employer data reaches downstream analysis phases. Its key innovations are:

1. **Two-Phase Architecture** — Separation of gathering (Phase 2) and validation (Phase 2B)
2. **Aggressive Data Pruning** — Generic terms and platitudes are removed
3. **Industry Inference** — Fallback tech assumptions for obscure companies
4. **Conditional Routing** — Retry, continue, or early exit based on data quality
5. **Transparent Flagging** — Quality concerns are tracked for downstream awareness

This design ensures the Fit Check Agent produces honest, evidence-based analysis rather than confident-sounding hallucinations.
