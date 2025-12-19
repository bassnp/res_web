# Phase 3: Iterative Research Loop & Content Enrichment

**Phase:** 3 of 4  
**Focus:** Research Iteration & Full Content Extraction  
**Risk Level:** Medium  
**Prerequisites:** Phase 1 (Query Expansion), Phase 2 (Scoring System)

---

## 1. Objective

Implement an iterative research loop that:
- Loops up to N iterations with reformulated queries when insufficient sources found
- Enriches top sources with full content extraction
- Implements sufficiency check routing between iterations
- Provides graceful degradation and early abort for unsalvageable research

---

## 2. Current State (To Demolish)

### Location: `services/fit_check_agent.py` & `services/nodes/deep_research.py`

**Current approach:**
```python
# LEGACY: Single retry with "enhanced search"
# Only 1 retry attempt (search_attempt = 1 or 2)
# No content enrichment (uses snippets only)
# Static routing after research_reranker
```

**Problems:**
1. Only 1 retry is insufficient for obscure companies
2. No reformulation strategy per iteration
3. Snippets (~200 chars) lack depth for synthesis
4. No structured sufficiency check loop

---

## 3. Target State (New Architecture)

### 3.1 Iterative Research Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ITERATIVE RESEARCH LOOP                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   START                                                                     │
│     │                                                                       │
│     ▼                                                                       │
│  ┌─────────────────┐                                                        │
│  │  deep_research  │◄──────────────────────────────────┐                    │
│  │  (iteration N)  │                                   │                    │
│  └────────┬────────┘                                   │                    │
│           │                                            │                    │
│           ▼                                            │                    │
│  ┌─────────────────┐                                   │                    │
│  │  score_sources  │                                   │                    │
│  │  (parallel AI)  │                                   │                    │
│  └────────┬────────┘                                   │                    │
│           │                                            │                    │
│           ▼                                            │                    │
│  ┌─────────────────┐     ┌──────────────┐              │                    │
│  │ sufficiency     │────►│ INSUFFICIENT │──► reformulate ─┘                 │
│  │ check           │     │ (< 3 good)   │     queries                       │
│  └────────┬────────┘     └──────────────┘     (if iteration < MAX)          │
│           │                                                                 │
│           ▼                                                                 │
│     ┌──────────────┐     ┌──────────────┐                                   │
│     │ SUFFICIENT   │     │    ABORT     │                                   │
│     │ (≥ 3 good)   │     │ (max iter)   │                                   │
│     └──────┬───────┘     └──────┬───────┘                                   │
│            │                    │                                           │
│            ▼                    ▼                                           │
│  ┌─────────────────┐   ┌─────────────────┐                                  │
│  │ content_enrich  │   │ abort_response  │                                  │
│  │ (full content)  │   │ (graceful exit) │                                  │
│  └────────┬────────┘   └─────────────────┘                                  │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ Continue to     │                                                        │
│  │ skeptical_comp  │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Max 3 iterations** | Balances coverage with latency (each iter ~2s) |
| **Reformulation per iteration** | BROADEN → NARROW → SYNONYMS strategy |
| **3 source minimum** | Ensures diverse perspectives |
| **Full content fetch** | Rich context for synthesis (~8000 chars vs 200) |
| **Parallel enrichment** | Reduces latency with semaphore-controlled concurrency |

---

## 4. Implementation Specification

### 4.1 Pipeline State Extensions

**Update `services/pipeline_state.py`:**

```python
from typing import TypedDict, Optional, List, Dict, Any, Literal

class FitCheckPipelineState(TypedDict):
    # ... existing fields ...
    
    # NEW: Iteration control
    iteration_count: int  # Current iteration (1-3)
    max_iterations: int   # Maximum allowed (default: 3)
    
    # NEW: Sufficiency tracking
    is_sufficient: bool           # True if enough quality sources
    sufficiency_reason: Optional[str]  # Why sufficient/insufficient
    
    # NEW: Content enrichment
    enriched_sources: Optional[List[Dict[str, Any]]]  # Full content
    content_fetch_errors: Optional[List[str]]  # Failed fetches
    
    # NEW: Abort handling
    should_abort: bool            # True if research failed
    abort_reason: Optional[str]   # Why aborting


def create_initial_state(
    query: str,
    model_id: Optional[str] = None,
    config_type: Optional[str] = None,
) -> FitCheckPipelineState:
    """Create initial pipeline state with new iteration fields."""
    return FitCheckPipelineState(
        query=query,
        current_phase="connecting",
        step_count=0,
        # ... existing fields ...
        
        # NEW: Iteration control
        iteration_count=1,
        max_iterations=3,
        
        # NEW: Sufficiency tracking
        is_sufficient=False,
        sufficiency_reason=None,
        
        # NEW: Content enrichment
        enriched_sources=None,
        content_fetch_errors=None,
        
        # NEW: Abort handling
        should_abort=False,
        abort_reason=None,
        
        # ... rest of existing fields ...
    )
```

### 4.2 Sufficiency Check Function

**Add to `services/utils/sufficiency_check.py`:**

```python
"""
Sufficiency Check for Iterative Research Loop.

Determines whether research has gathered enough quality sources,
or if another iteration is needed, or if research should abort.
"""

from typing import Literal, Tuple
from models.fit_check import ScoringResult

# Minimum passing sources for sufficiency
MIN_SUFFICIENT_SOURCES = 3

# Minimum sources to attempt enrichment (even if below threshold)
MIN_ENRICHMENT_SOURCES = 1


def check_source_sufficiency(
    scoring_result: ScoringResult,
    iteration: int,
    max_iterations: int = 3,
) -> Tuple[Literal["sufficient", "insufficient", "abort"], str]:
    """
    Determine research sufficiency based on scoring results.
    
    Decision logic:
        - ≥3 passing sources → sufficient (proceed to enrichment)
        - <3 sources AND iteration < max → insufficient (retry)
        - <3 sources AND iteration >= max → abort (graceful exit)
        - 0 sources AND iteration = 2 → abort (early exit, reformulation failed)
    
    Args:
        scoring_result: Result from parallel scoring.
        iteration: Current iteration number (1-based).
        max_iterations: Maximum allowed iterations.
    
    Returns:
        Tuple of (decision, reason).
    """
    passing = scoring_result.passing_count
    total = scoring_result.total_count
    threshold = scoring_result.adaptive_threshold
    
    # Sufficient: Have enough quality sources
    if passing >= MIN_SUFFICIENT_SOURCES:
        return (
            "sufficient",
            f"Found {passing} quality sources (threshold: {threshold:.2f})"
        )
    
    # Early abort: No sources after retry
    if passing == 0 and iteration >= 2:
        return (
            "abort",
            f"No quality sources after {iteration} iterations. Research exhausted."
        )
    
    # Max iterations reached
    if iteration >= max_iterations:
        if passing >= MIN_ENRICHMENT_SOURCES:
            # Proceed with limited data
            return (
                "sufficient",
                f"Max iterations reached. Proceeding with {passing} source(s)."
            )
        else:
            return (
                "abort",
                f"Max iterations ({max_iterations}) reached with insufficient sources."
            )
    
    # Can retry
    return (
        "insufficient",
        f"Only {passing}/{total} sources passed (need {MIN_SUFFICIENT_SOURCES}). "
        f"Retrying with reformulated queries (iteration {iteration + 1})."
    )
```

### 4.3 Content Enricher Node

**Create `services/nodes/content_enricher.py`:**

```python
"""
Content Enricher Node for Fit Check Research.

Fetches full page content from top-ranked sources to provide
rich context for downstream synthesis. Uses parallel fetching
with graceful fallback to snippets.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import aiohttp

from services.pipeline_state import FitCheckPipelineState
from services.callbacks import ThoughtCallback

logger = logging.getLogger(__name__)

# Configuration
MAX_CONTENT_LENGTH = 8000  # Max chars per source
FETCH_TIMEOUT = 10  # Seconds per fetch
MAX_CONCURRENT_FETCHES = 3  # Parallel fetch limit


async def content_enricher_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Fetch full content from top-ranked sources.
    
    Args:
        state: Pipeline state with top_sources from scoring.
        callback: Optional callback for SSE events.
    
    Returns:
        State update with enriched_sources and content_fetch_errors.
    """
    top_sources = state.get("top_sources", [])
    
    if not top_sources:
        return {
            "enriched_sources": [],
            "content_fetch_errors": ["No sources to enrich"],
            "step_count": state.get("step_count", 0) + 1,
        }
    
    # Emit enrichment start
    if callback:
        await callback.on_thought(
            step=state.get("step_count", 0) + 1,
            thought_type="tool_call",
            tool="content_fetcher",
            input=f"Fetching full content from {len(top_sources)} sources",
        )
    
    # Parallel fetch with semaphore
    enriched = []
    errors = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
    
    async def fetch_with_semaphore(source):
        async with semaphore:
            return await _fetch_source_content(source)
    
    # Gather all fetch tasks
    tasks = [fetch_with_semaphore(source) for source in top_sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for source, result in zip(top_sources, results):
        if isinstance(result, Exception):
            errors.append(f"Failed to fetch {source.url}: {str(result)}")
            # Fallback to snippet
            enriched.append(_create_fallback_enrichment(source))
        elif result:
            enriched.append(result)
        else:
            errors.append(f"Empty content from {source.url}")
            enriched.append(_create_fallback_enrichment(source))
    
    # Emit enrichment complete
    if callback:
        success_count = len([e for e in enriched if e.get("fetch_status") == "success"])
        await callback.on_thought(
            step=state.get("step_count", 0) + 1,
            thought_type="observation",
            content=f"Enriched {success_count}/{len(top_sources)} sources with full content",
        )
    
    return {
        "enriched_sources": enriched,
        "content_fetch_errors": errors if errors else None,
        "step_count": state.get("step_count", 0) + 1,
    }


async def _fetch_source_content(source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch and extract content from a single source.
    
    Args:
        source: Source dict with url, title, snippet.
    
    Returns:
        Enriched source dict with full content, or None on failure.
    """
    url = source.get("url", "")
    
    if not url:
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
                headers={"User-Agent": "FitCheckBot/1.0"},
            ) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                content = _extract_text_content(html)
                
                if not content or len(content) < 50:
                    return None
                
                # Truncate to max length
                if len(content) > MAX_CONTENT_LENGTH:
                    content = content[:MAX_CONTENT_LENGTH] + "... [truncated]"
                
                return {
                    **source,
                    "full_content": content,
                    "content_length": len(content),
                    "fetch_status": "success",
                }
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None


def _extract_text_content(html: str) -> str:
    """
    Extract clean text content from HTML.
    
    Removes scripts, styles, and extracts main text.
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines)
        
        return content
        
    except ImportError:
        # Fallback: basic regex extraction
        import re
        # Remove script/style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception:
        return ""


def _create_fallback_enrichment(source: Dict[str, Any]) -> Dict[str, Any]:
    """Create enrichment entry using snippet as fallback."""
    return {
        **source,
        "full_content": source.get("snippet", ""),
        "content_length": len(source.get("snippet", "")),
        "fetch_status": "fallback",
    }
```

### 4.4 Abort Response Node

**Create `services/nodes/abort_response.py`:**

```python
"""
Abort Response Node for Graceful Research Failure.

Generates a structured response explaining why research could not
be completed, preventing hallucination when data is insufficient.
"""

import logging
from typing import Dict, Any, Optional

from services.pipeline_state import FitCheckPipelineState
from services.callbacks import ThoughtCallback

logger = logging.getLogger(__name__)


async def abort_response_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Generate graceful failure response when research fails.
    
    Args:
        state: Pipeline state with abort_reason.
        callback: Optional callback for SSE events.
    
    Returns:
        State update with final_response containing abort message.
    """
    query = state.get("query", "your query")
    abort_reason = state.get("abort_reason", "Insufficient research data")
    iteration = state.get("iteration_count", 1)
    
    # Build structured abort response
    response = _build_abort_response(query, abort_reason, iteration)
    
    # Emit abort event
    if callback:
        await callback.on_thought(
            step=state.get("step_count", 0) + 1,
            thought_type="reasoning",
            content=f"Research aborted: {abort_reason}",
        )
    
    return {
        "final_response": response,
        "should_abort": True,
        "current_phase": "__end__",
        "step_count": state.get("step_count", 0) + 1,
    }


def _build_abort_response(query: str, reason: str, iterations: int) -> str:
    """Build markdown response for research abort."""
    return f"""## Unable to Complete Research

I wasn't able to gather sufficient reliable information to provide a meaningful fit analysis.

**Query:** {query}

**What Happened:**
{reason}

**Research Attempts:** {iterations} iteration(s) with query reformulation

**Recommendations:**
1. Try providing more specific information (e.g., full company name, job URL)
2. If this is a small or private company, I may have limited public data
3. Try rephrasing your query with additional context

**Why This Matters:**
Rather than guessing or providing potentially inaccurate information, I've chosen to be transparent about the limitations of my research. This ensures you receive reliable insights when I can provide them.

---
*Fit Check Research Engine v2.0*
"""
```

### 4.5 Updated Graph Builder

**Update `services/fit_check_agent.py`:**

```python
from langgraph.graph import StateGraph, END

from services.nodes import (
    connecting_node,
    deep_research_node,
    content_enricher_node,  # NEW
    abort_response_node,     # NEW
    skeptical_comparison_node,
    skills_matching_node,
    confidence_reranker_node,
    generate_results_node,
)
from services.utils.sufficiency_check import check_source_sufficiency
from services.utils.query_expander import reformulate_queries


def build_fit_check_pipeline(callback_holder: Dict = None):
    """
    Build the iterative research pipeline.
    
    NEW STRUCTURE:
        START → connecting → deep_research → score_and_route → (conditional)
            ├─► [sufficient] → content_enricher → skeptical_comparison → ...
            ├─► [insufficient] → deep_research (loop, reformulated queries)
            └─► [abort] → abort_response → END
    """
    if callback_holder is None:
        callback_holder = {}
    
    workflow = StateGraph(FitCheckPipelineState)
    
    # Add nodes
    workflow.add_node("connecting", create_node_wrapper(connecting_node, callback_holder))
    workflow.add_node("deep_research", create_node_wrapper(deep_research_node, callback_holder))
    workflow.add_node("score_and_route", create_node_wrapper(score_and_route_node, callback_holder))  # NEW
    workflow.add_node("content_enricher", create_node_wrapper(content_enricher_node, callback_holder))  # NEW
    workflow.add_node("abort_response", create_node_wrapper(abort_response_node, callback_holder))  # NEW
    workflow.add_node("skeptical_comparison", create_node_wrapper(skeptical_comparison_node, callback_holder))
    workflow.add_node("skills_matching", create_node_wrapper(skills_matching_node, callback_holder))
    workflow.add_node("confidence_reranker", create_node_wrapper(confidence_reranker_node, callback_holder))
    workflow.add_node("generate_results", create_node_wrapper(generate_results_node, callback_holder))
    
    # Entry point
    workflow.set_entry_point("connecting")
    
    # Edges
    workflow.add_conditional_edges(
        "connecting",
        route_after_connecting,
        {
            "deep_research": "deep_research",
            END: END,
        }
    )
    
    workflow.add_edge("deep_research", "score_and_route")
    
    # CRITICAL: Sufficiency routing
    workflow.add_conditional_edges(
        "score_and_route",
        route_by_sufficiency,
        {
            "sufficient": "content_enricher",
            "insufficient": "deep_research",  # LOOP BACK
            "abort": "abort_response",
        }
    )
    
    workflow.add_edge("content_enricher", "skeptical_comparison")
    workflow.add_edge("abort_response", END)
    
    # Rest of pipeline unchanged
    workflow.add_edge("skeptical_comparison", "skills_matching")
    workflow.add_edge("skills_matching", "confidence_reranker")
    workflow.add_edge("confidence_reranker", "generate_results")
    workflow.add_edge("generate_results", END)
    
    return workflow.compile()


async def score_and_route_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Combined scoring and sufficiency check node.
    
    Performs:
    1. Parallel AI scoring of search results
    2. Sufficiency check
    3. Sets routing flags
    """
    from services.utils.parallel_scorer import score_documents_parallel, calculate_adaptive_threshold
    from services.utils.sufficiency_check import check_source_sufficiency
    
    # ... scoring logic from Phase 2 ...
    
    # Check sufficiency
    scoring_result = state.get("scoring_result")
    iteration = state.get("iteration_count", 1)
    max_iter = state.get("max_iterations", 3)
    
    decision, reason = check_source_sufficiency(scoring_result, iteration, max_iter)
    
    # Prepare state update
    update = {
        "is_sufficient": decision == "sufficient",
        "sufficiency_reason": reason,
        "should_abort": decision == "abort",
        "step_count": state.get("step_count", 0) + 1,
    }
    
    # If insufficient and can retry, increment iteration and reformulate
    if decision == "insufficient":
        update["iteration_count"] = iteration + 1
        # Reformulate queries for next iteration
        previous_queries = [q["query"] for q in state.get("expanded_queries", [])]
        update["reformulated_queries"] = reformulate_queries(
            previous_queries,
            iteration=iteration + 1,
        )
    
    if decision == "abort":
        update["abort_reason"] = reason
    
    return update


def route_by_sufficiency(state: FitCheckPipelineState) -> str:
    """Route based on sufficiency check result."""
    if state.get("should_abort"):
        return "abort"
    if state.get("is_sufficient"):
        return "sufficient"
    return "insufficient"
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

**`tests/unit/test_sufficiency_check.py`:**

```python
import pytest
from services.utils.sufficiency_check import check_source_sufficiency
from models.fit_check import ScoringResult

class TestSufficiencyCheck:
    """Test sufficiency determination logic."""
    
    def test_sufficient_with_3_sources(self):
        result = ScoringResult(scores=[], adaptive_threshold=0.5, passing_count=3, total_count=5, social_media_ratio=0.1)
        decision, _ = check_source_sufficiency(result, iteration=1)
        assert decision == "sufficient"
    
    def test_insufficient_can_retry(self):
        result = ScoringResult(scores=[], adaptive_threshold=0.5, passing_count=1, total_count=5, social_media_ratio=0.1)
        decision, _ = check_source_sufficiency(result, iteration=1, max_iterations=3)
        assert decision == "insufficient"
    
    def test_abort_at_max_iterations_zero_sources(self):
        result = ScoringResult(scores=[], adaptive_threshold=0.5, passing_count=0, total_count=5, social_media_ratio=0.1)
        decision, _ = check_source_sufficiency(result, iteration=3, max_iterations=3)
        assert decision == "abort"
    
    def test_proceed_at_max_with_some_sources(self):
        result = ScoringResult(scores=[], adaptive_threshold=0.5, passing_count=1, total_count=5, social_media_ratio=0.1)
        decision, _ = check_source_sufficiency(result, iteration=3, max_iterations=3)
        # Should proceed with limited data
        assert decision == "sufficient"
    
    def test_early_abort_no_sources_after_retry(self):
        result = ScoringResult(scores=[], adaptive_threshold=0.5, passing_count=0, total_count=3, social_media_ratio=0.2)
        decision, _ = check_source_sufficiency(result, iteration=2)
        assert decision == "abort"
```

**`tests/unit/test_content_enricher.py`:**

```python
import pytest
from unittest.mock import patch, AsyncMock
from services.nodes.content_enricher import content_enricher_node, _extract_text_content

class TestContentEnricher:
    """Test content enrichment functionality."""
    
    def test_extract_text_removes_scripts(self):
        html = "<html><script>evil()</script><p>Good content</p></html>"
        text = _extract_text_content(html)
        assert "evil" not in text
        assert "Good content" in text
    
    @pytest.mark.asyncio
    async def test_enricher_handles_empty_sources(self):
        state = {"top_sources": [], "step_count": 0}
        result = await content_enricher_node(state, callback=None)
        assert result["enriched_sources"] == []
    
    @pytest.mark.asyncio
    async def test_enricher_creates_fallback_on_failure(self):
        state = {
            "top_sources": [{"url": "https://example.com", "title": "Test", "snippet": "Fallback text"}],
            "step_count": 0,
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            result = await content_enricher_node(state, callback=None)
        
        # Should have fallback with snippet
        assert len(result["enriched_sources"]) == 1
        assert result["enriched_sources"][0]["fetch_status"] == "fallback"
```

### 5.2 Integration Tests

**`tests/integration/test_iterative_loop.py`:**

```python
import pytest
from services.fit_check_agent import build_fit_check_pipeline
from services.pipeline_state import create_initial_state

@pytest.mark.asyncio
async def test_loop_retries_on_insufficient():
    """Pipeline should loop on insufficient sources."""
    # Mock scoring to return insufficient on first iteration
    state = create_initial_state(query="Obscure Startup XYZ")
    state["phase_1_output"] = {"query_type": "company", "company_name": "Obscure Startup XYZ"}
    
    # ... mock scoring to return 1 source first, then 3 sources ...
    
    # Final iteration count should be > 1
    # (Full integration test would run the graph)

@pytest.mark.asyncio  
async def test_abort_on_max_iterations_no_sources():
    """Pipeline should abort gracefully after max iterations."""
    state = create_initial_state(query="Nonexistent Company ABC")
    
    # ... mock to always return 0 sources ...
    
    # Should have abort response
```

---

## 6. Requirements Tracking

### Verification Checklist

| # | Requirement | Test | Status |
|---|-------------|------|--------|
| 3.1 | Sufficiency check logic | `test_sufficient_with_3_sources` | ⬜ |
| 3.2 | Retry on insufficient | `test_insufficient_can_retry` | ⬜ |
| 3.3 | Abort at max iterations | `test_abort_at_max_iterations_zero_sources` | ⬜ |
| 3.4 | Early abort on failed retry | `test_early_abort_no_sources_after_retry` | ⬜ |
| 3.5 | Content extraction | `test_extract_text_removes_scripts` | ⬜ |
| 3.6 | Fallback to snippet | `test_enricher_creates_fallback_on_failure` | ⬜ |
| 3.7 | Query reformulation per iteration | Unit test needed | ⬜ |
| 3.8 | Loop integration | `test_loop_retries_on_insufficient` | ⬜ |

### Sign-Off

- [ ] All unit tests pass
- [ ] Integration tests pass  
- [ ] Loop latency acceptable (< 10s for 3 iterations)
- [ ] Code review completed

---

## 7. Files Changed Summary

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `services/pipeline_state.py` | EXTEND | ~30 |
| `services/utils/sufficiency_check.py` | **CREATE** | ~60 |
| `services/nodes/content_enricher.py` | **CREATE** | ~150 |
| `services/nodes/abort_response.py` | **CREATE** | ~70 |
| `services/fit_check_agent.py` | **MAJOR MODIFY** | ~100 |
| `services/nodes/__init__.py` | EXTEND | ~5 |
| `requirements.txt` | EXTEND | ~2 (aiohttp, beautifulsoup4) |
| `tests/unit/test_sufficiency_check.py` | **CREATE** | ~50 |
| `tests/unit/test_content_enricher.py` | **CREATE** | ~50 |

---

## 8. Rollback Plan

If issues arise:
1. Remove `content_enricher` node from graph (skip enrichment)
2. Revert routing to direct path (no loop)
3. Set `max_iterations = 1` to disable looping
4. Abort response can be replaced with existing early exit logic
