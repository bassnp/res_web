# Fit Check Agent Upgrade - Architecture Overview

**Version:** 2.0.0  
**Target:** Enhanced Research Intelligence System  
**Date:** 2024-12-18

---

## Executive Summary

This document outlines the architectural upgrade path from the current Fit Check Agent to an enhanced research intelligence system. The upgrade adopts proven patterns from the Deep Researcher architecture while preserving the core Fit Check goals.

---

## 1. Current State Analysis

### Current Architecture (v1.0)

```
START → connecting → deep_research → research_reranker → (conditional)
      ↓                                                    ↓
      END (irrelevant)                     CONTINUE / ENHANCE_SEARCH / EARLY_EXIT
                                                          ↓
skeptical_comparison → skills_matching → confidence_reranker → generate_results → END
```

### Current Limitations

| Area | Limitation | Impact |
|------|------------|--------|
| **Query Construction** | Only 2 basic queries, no CSE operators | Misses relevant results |
| **Scoring** | Heuristic-only quality assessment | Inconsistent source selection |
| **Iteration** | Single retry (enhanced search) | Insufficient for obscure companies |
| **Content** | Uses snippets only (~200 chars) | Shallow context for synthesis |
| **Resilience** | No circuit breakers | Cascading failures possible |
| **Concurrency** | Sequential LLM calls | Suboptimal latency |

---

## 2. Ideal Architecture Patterns (from Deep Researcher)

### Key Patterns to Adopt

| Pattern | Description | Benefit |
|---------|-------------|---------|
| **Query Expansion** | 3-5 CSE-optimized queries with operators | Higher precision search |
| **Multi-Dimensional Scoring** | Relevance + Quality + Usefulness | Better source selection |
| **Extractability Multipliers** | Source-type penalties (video, social) | Realistic content expectations |
| **Adaptive Thresholds** | Dynamic based on result characteristics | Context-aware filtering |
| **Iterative Loop** | Up to N iterations with reformulation | Comprehensive coverage |
| **Content Enrichment** | Full page fetching for top sources | Rich synthesis context |
| **Parallel Processing** | Concurrent scoring/compression | Reduced latency |
| **Circuit Breakers** | Failure isolation for external calls | System stability |

---

## 3. Upgrade Goals

### Primary Objectives

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FIT CHECK v2.0 GOALS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. INTELLIGENT QUERYING                                            │
│     └─► CSE operator-enriched query expansion                       │
│     └─► Query reformulation strategies per iteration                │
│     └─► Fit Check context-aware query generation                    │
│                                                                     │
│  2. ROBUST SOURCE SCORING                                           │
│     └─► 3-dimension AI scoring (relevance, quality, usefulness)     │
│     └─► Extractability multipliers for source types                 │
│     └─► Adaptive thresholds based on result distribution            │
│                                                                     │
│  3. ITERATIVE REFINEMENT                                            │
│     └─► Up to 3 search iterations with progressive strategies       │
│     └─► Sufficiency check routing between iterations                │
│     └─► Early abort for unreliable data                             │
│                                                                     │
│  4. CONTENT ENRICHMENT                                              │
│     └─► Full content fetching for top sources                       │
│     └─► Quality-gated content extraction                            │
│     └─► Graceful fallback to snippets                               │
│                                                                     │
│  5. SYSTEM RESILIENCE                                               │
│     └─► Circuit breakers for external API calls                     │
│     └─► Parallel processing where safe                              │
│     └─► Comprehensive error handling                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Relevant results per search | ~2 | ≥4 | Manual audit |
| Source quality score accuracy | N/A | >80% | LLM evaluation |
| Research iterations (avg) | 1.5 | 2.0 | Pipeline logs |
| Content extraction success | 0% | >70% | Enrichment stats |
| API failure recovery | 0% | 100% | Circuit breaker logs |

---

## 4. Architecture Comparison

### Before vs After

```
CURRENT (v1.0):
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  2 queries  │──►│  Snippets   │──►│  Heuristic  │──► Continue/Exit
│  (basic)    │   │  only       │   │  quality    │
└─────────────┘   └─────────────┘   └─────────────┘

UPGRADED (v2.0):
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  3-5 CSE    │──►│  Parallel   │──►│  3-Dimension│──►│  Sufficiency│
│  queries    │   │  AI Scoring │   │  Scoring    │   │  Check      │
└─────────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘
                                                             │
                  ┌──────────────────────────────────────────┤
                  │                                          │
                  ▼                                          ▼
         [Insufficient]                              [Sufficient]
         ┌─────────────┐                             ┌─────────────┐
         │ Reformulate │──► Loop (max 3)             │  Content    │
         │ Queries     │                             │  Enrichment │
         └─────────────┘                             └─────────────┘
                                                            │
                                                            ▼
                                                     ┌─────────────┐
                                                     │  Continue   │
                                                     │  Pipeline   │
                                                     └─────────────┘
```

---

## 5. Module Impact Analysis

### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `services/tools/web_search.py` | **Major Rewrite** | Batch search, circuit breaker, domain diversity |
| `services/nodes/deep_research.py` | **Major Rewrite** | Query expansion, iteration loop |
| `services/nodes/research_reranker.py` | **Major Rewrite** | AI scoring, extractability, adaptive thresholds |
| `services/pipeline_state.py` | **Extend** | New state fields for iteration, scoring |
| `services/fit_check_agent.py` | **Modify** | Updated routing logic, loop handling |
| `models/fit_check.py` | **Extend** | New scoring models, source types |

### New Modules to Create

| File | Purpose |
|------|---------|
| `services/nodes/content_enricher.py` | Full content fetching and extraction |
| `services/utils/circuit_breaker.py` | Failure isolation for external calls |
| `services/utils/source_classifier.py` | Source type detection and multipliers |
| `services/utils/query_reformulator.py` | Iteration-specific query strategies |

---

## 6. Implementation Phases

### Phase Overview

| Phase | Focus | Duration | Risk |
|-------|-------|----------|------|
| **Phase 1** | Query Intelligence & Expansion | 1 day | Low |
| **Phase 2** | Multi-Dimensional Scoring System | 1-2 days | Medium |
| **Phase 3** | Iterative Research Loop & Enrichment | 1-2 days | Medium |
| **Phase 4** | Resilience, Integration & Testing | 1 day | Low |

### Dependency Graph

```
Phase 1 ─────────────────────────────────────────────────┐
   │                                                     │
   ▼                                                     │
Phase 2 ──────────────────────────────────┐              │
   │                                      │              │
   ▼                                      ▼              ▼
Phase 3 ─────────────────────────────► Phase 4 (Integration)
```

---

## 7. Risk Mitigation

### Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Search API rate limits | Medium | High | Circuit breaker, exponential backoff |
| Content fetch timeouts | High | Medium | Timeout limits, fallback to snippet |
| LLM scoring latency | Medium | Medium | Parallel execution, caching |
| Breaking existing pipeline | Low | High | Incremental migration, feature flags |

### Rollback Strategy

Each phase maintains backward compatibility:
1. New modules are additive (don't remove old code until verified)
2. Feature flags control new behavior activation
3. State schema changes are backward-compatible (optional fields)

---

## 8. Fit Check Context Preservation

### Core Goals Retained

The upgrade **preserves** these Fit Check fundamentals:

| Goal | How Preserved |
|------|---------------|
| **Anti-Sycophancy** | Minimum 2 gaps enforced (unchanged) |
| **Employer Fit Focus** | Query expansion tailored to job/company research |
| **Skills Matching** | Enhanced by better source quality |
| **Confidence Calibration** | Improved by multi-dimensional scoring input |
| **Streaming UX** | SSE events maintained with new event types |

### New Capabilities for Fit Check

| Capability | Fit Check Benefit |
|------------|-------------------|
| Better tech stack detection | More accurate skills matching |
| Culture signal extraction | Improved gap analysis |
| Requirement confidence scores | Calibrated fit percentages |
| Source citations | Transparent reasoning |

---

## Next Steps

Proceed to the individual phase implementation guides:

1. [PHASE_1_QUERY_INTELLIGENCE.md](PHASE_1_QUERY_INTELLIGENCE.md)
2. [PHASE_2_SCORING_SYSTEM.md](PHASE_2_SCORING_SYSTEM.md)
3. [PHASE_3_ITERATIVE_RESEARCH.md](PHASE_3_ITERATIVE_RESEARCH.md)
4. [PHASE_4_RESILIENCE_INTEGRATION.md](PHASE_4_RESILIENCE_INTEGRATION.md)
