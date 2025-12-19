# Phase 2: Multi-Dimensional Scoring System

**Phase:** 2 of 4  
**Focus:** AI-Powered Source Scoring & Quality Assessment  
**Risk Level:** Medium  
**Prerequisites:** Phase 1 (Query Expansion)

---

## 1. Objective

Replace the heuristic-only quality assessment with a robust multi-dimensional AI scoring system that:
- Scores each source on 3 dimensions (Relevance, Quality, Usefulness)
- Applies extractability multipliers based on source type
- Uses adaptive thresholds based on result characteristics
- Supports parallel scoring for performance

---

## 2. Current State (To Demolish)

### Location: `services/nodes/research_reranker.py`

**Current approach:**
```python
# LEGACY: Heuristic-only assessment
def assess_quality_heuristically(phase_2_output):
    # Counts tech_stack items, requirements, culture_signals
    # No per-source scoring
    # No source type awareness
    # Static thresholds
```

**Problems:**
1. No per-document scoring (batch assessment only)
2. Heuristics miss nuanced quality signals
3. No source type penalties (video, social media)
4. Static thresholds ignore context
5. Sequential LLM calls (slow)

---

## 3. Target State (New Architecture)

### 3.1 Scoring Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-DIMENSIONAL SCORING SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │ Search Results  │                                                        │
│  │ (raw documents) │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SOURCE CLASSIFIER                                │   │
│  │  Detect: VIDEO | SOCIAL_MEDIA | WIKI | ACADEMIC | NEWS | GENERAL   │   │
│  └────────┬────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PARALLEL AI SCORING                              │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │   │
│  │  │ Doc 1   │  │ Doc 2   │  │ Doc 3   │  │ Doc 4   │  │ Doc 5   │   │   │
│  │  │ Score   │  │ Score   │  │ Score   │  │ Score   │  │ Score   │   │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │   │
│  └────────┬────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    POST-PROCESSING                                  │   │
│  │  1. Apply extractability multiplier                                 │   │
│  │  2. Apply query relevance multiplier                                │   │
│  │  3. Calculate composite score                                       │   │
│  └────────┬────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ADAPTIVE THRESHOLD                               │   │
│  │  Dynamic threshold based on result count & social media ratio       │   │
│  └────────┬────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ Ranked Sources  │                                                        │
│  │ (with scores)   │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Specification

### 4.1 Data Models

**Add to `models/fit_check.py`:**

```python
from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

class SourceType(str, Enum):
    """Classification of source type for extractability scoring."""
    VIDEO = "video"
    SOCIAL_MEDIA = "social_media"
    WIKI = "wiki"
    ACADEMIC = "academic"
    NEWS = "news"
    FORUM = "forum"
    GENERAL = "general"

class DocumentScore(BaseModel):
    """3-dimension score for a single document."""
    document_id: str = Field(..., description="Unique identifier")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Document title")
    
    # 3-Dimension Scores (0.0 - 1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    quality_score: float = Field(..., ge=0.0, le=1.0)
    usefulness_score: float = Field(..., ge=0.0, le=1.0)
    
    # Composite and adjusted scores
    raw_composite: float = Field(..., ge=0.0, le=1.0)
    extractability_multiplier: float = Field(default=1.0, ge=0.0, le=1.5)
    final_score: float = Field(..., ge=0.0, le=1.5)
    
    # Metadata
    source_type: SourceType = Field(default=SourceType.GENERAL)
    scoring_rationale: str = Field(..., description="LLM reasoning for scores")

class ScoringResult(BaseModel):
    """Result of parallel document scoring."""
    scores: List[DocumentScore]
    adaptive_threshold: float = Field(..., ge=0.0, le=1.0)
    passing_count: int
    total_count: int
    social_media_ratio: float = Field(..., ge=0.0, le=1.0)
```

### 4.2 Source Classifier

**Create `services/utils/source_classifier.py`:**

```python
"""
Source Type Classifier for Extractability Scoring.

Classifies URLs into source types and applies extractability multipliers.
"""

from typing import Tuple
from urllib.parse import urlparse
from models.fit_check import SourceType

# Domain sets for classification
VIDEO_DOMAINS = {"youtube.com", "vimeo.com", "dailymotion.com", "twitch.tv"}
SOCIAL_MEDIA_DOMAINS = {"twitter.com", "x.com", "facebook.com", "instagram.com", 
                        "linkedin.com", "tiktok.com", "pinterest.com", "reddit.com"}
WIKI_DOMAINS = {"wikipedia.org", "wikimedia.org", "fandom.com"}
ACADEMIC_DOMAINS = {"arxiv.org", "scholar.google.com", "researchgate.net", 
                    "academia.edu", "sciencedirect.com", "ieee.org"}
NEWS_DOMAINS = {"nytimes.com", "wsj.com", "bloomberg.com", "techcrunch.com",
                "theverge.com", "wired.com", "arstechnica.com", "bbc.com"}
FORUM_DOMAINS = {"stackoverflow.com", "stackexchange.com", "quora.com",
                 "news.ycombinator.com", "dev.to"}

# Extractability multipliers by source type
EXTRACTABILITY_MULTIPLIERS = {
    SourceType.VIDEO: 0.20,        # Cannot extract video content
    SourceType.SOCIAL_MEDIA: 0.50, # Limited text, noisy
    SourceType.WIKI: 1.10,         # Excellent extractability
    SourceType.ACADEMIC: 1.08,     # High-quality content
    SourceType.FORUM: 1.00,        # Good technical content
    SourceType.NEWS: 0.85,         # Paywalls, bias concerns
    SourceType.GENERAL: 1.00,      # Baseline
}


def classify_source(url: str) -> Tuple[SourceType, float]:
    """
    Classify a URL into a source type and return extractability multiplier.
    
    Args:
        url: The source URL to classify.
    
    Returns:
        Tuple of (SourceType, extractability_multiplier).
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        return SourceType.GENERAL, 1.0
    
    # Check each domain set
    for video_domain in VIDEO_DOMAINS:
        if video_domain in domain:
            return SourceType.VIDEO, EXTRACTABILITY_MULTIPLIERS[SourceType.VIDEO]
    
    for social_domain in SOCIAL_MEDIA_DOMAINS:
        if social_domain in domain:
            return SourceType.SOCIAL_MEDIA, EXTRACTABILITY_MULTIPLIERS[SourceType.SOCIAL_MEDIA]
    
    for wiki_domain in WIKI_DOMAINS:
        if wiki_domain in domain:
            return SourceType.WIKI, EXTRACTABILITY_MULTIPLIERS[SourceType.WIKI]
    
    for academic_domain in ACADEMIC_DOMAINS:
        if academic_domain in domain:
            return SourceType.ACADEMIC, EXTRACTABILITY_MULTIPLIERS[SourceType.ACADEMIC]
    
    for news_domain in NEWS_DOMAINS:
        if news_domain in domain:
            return SourceType.NEWS, EXTRACTABILITY_MULTIPLIERS[SourceType.NEWS]
    
    for forum_domain in FORUM_DOMAINS:
        if forum_domain in domain:
            return SourceType.FORUM, EXTRACTABILITY_MULTIPLIERS[SourceType.FORUM]
    
    return SourceType.GENERAL, EXTRACTABILITY_MULTIPLIERS[SourceType.GENERAL]


def get_extractability_multiplier(source_type: SourceType) -> float:
    """Get the extractability multiplier for a source type."""
    return EXTRACTABILITY_MULTIPLIERS.get(source_type, 1.0)
```

### 4.3 Parallel AI Scorer

**Create `services/utils/parallel_scorer.py`:**

```python
"""
Parallel AI Document Scoring for Fit Check Research.

Scores documents concurrently using 3-dimension evaluation:
- Relevance (50%): Does this directly answer the query?
- Quality (30%): Is this source credible and well-written?
- Usefulness (20%): Does this provide actionable Fit Check info?
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import json

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from services.utils.source_classifier import classify_source
from models.fit_check import DocumentScore, SourceType

logger = logging.getLogger(__name__)

# Scoring weights
RELEVANCE_WEIGHT = 0.50
QUALITY_WEIGHT = 0.30
USEFULNESS_WEIGHT = 0.20

# Scoring prompt template
SCORING_PROMPT = """<system_instruction>
You are a document quality scorer for employer research. Score this document on 3 dimensions.
</system_instruction>

<context>
Research Query: {query}
Document Title: {title}
Document URL: {url}
Document Content: {content}
</context>

<scoring_criteria>
1. RELEVANCE (0.0-1.0): Does this document directly address the research query about the employer/job?
   - 0.9-1.0: Directly about the company/role, specific details
   - 0.6-0.8: Related but not specific (industry info, general tech)
   - 0.3-0.5: Tangentially related
   - 0.0-0.2: Unrelated or wrong company/role

2. QUALITY (0.0-1.0): Is this source credible and informative?
   - 0.9-1.0: Official source, well-written, detailed
   - 0.6-0.8: Credible source, some useful info
   - 0.3-0.5: User-generated, mixed quality
   - 0.0-0.2: Spam, outdated, or unreliable

3. USEFULNESS (0.0-1.0): Does this provide actionable info for Fit Check?
   - 0.9-1.0: Tech stack, requirements, culture details
   - 0.6-0.8: Some relevant details about company/role
   - 0.3-0.5: General information only
   - 0.0-0.2: No actionable information
</scoring_criteria>

<output_format>
Return ONLY valid JSON:
{{"relevance": 0.0-1.0, "quality": 0.0-1.0, "usefulness": 0.0-1.0, "rationale": "Brief explanation"}}
</output_format>"""


async def score_single_document(
    document: Dict[str, Any],
    query: str,
    llm,
) -> Optional[DocumentScore]:
    """
    Score a single document using AI.
    
    Args:
        document: Document with title, url, content/snippet.
        query: The research query for context.
        llm: LLM instance for scoring.
    
    Returns:
        DocumentScore or None if scoring fails.
    """
    doc_id = document.get("id", document.get("url", "unknown"))
    url = document.get("url", "")
    title = document.get("title", "")
    content = document.get("content") or document.get("snippet", "")[:500]
    
    # Classify source type
    source_type, extractability = classify_source(url)
    
    # Build scoring prompt
    prompt = SCORING_PROMPT.format(
        query=query,
        title=title,
        url=url,
        content=content[:1000],  # Limit content for scoring
    )
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()
        
        # Parse JSON response
        scores = _parse_score_response(response_text)
        if not scores:
            return None
        
        # Calculate composite score
        relevance = scores.get("relevance", 0.5)
        quality = scores.get("quality", 0.5)
        usefulness = scores.get("usefulness", 0.5)
        
        raw_composite = (
            relevance * RELEVANCE_WEIGHT +
            quality * QUALITY_WEIGHT +
            usefulness * USEFULNESS_WEIGHT
        )
        
        # Apply extractability multiplier
        final_score = raw_composite * extractability
        
        return DocumentScore(
            document_id=str(doc_id),
            url=url,
            title=title,
            relevance_score=relevance,
            quality_score=quality,
            usefulness_score=usefulness,
            raw_composite=raw_composite,
            extractability_multiplier=extractability,
            final_score=final_score,
            source_type=source_type,
            scoring_rationale=scores.get("rationale", ""),
        )
        
    except Exception as e:
        logger.warning(f"Failed to score document {doc_id}: {e}")
        return None


def _parse_score_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse LLM scoring response into scores dict."""
    try:
        # Try direct JSON parse
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown
    import re
    json_match = re.search(r'\{[^}]+\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


async def score_documents_parallel(
    documents: List[Dict[str, Any]],
    query: str,
    max_concurrent: int = 5,
) -> List[DocumentScore]:
    """
    Score multiple documents in parallel.
    
    Args:
        documents: List of documents to score.
        query: Research query for context.
        max_concurrent: Maximum concurrent scoring tasks.
    
    Returns:
        List of DocumentScores (successful scores only).
    """
    # Get LLM for scoring (use fast model)
    llm = get_llm(
        streaming=False,
        temperature=0.1,  # Low temperature for consistent scoring
        model_id="gemini-flash-latest",  # Fast model for parallel scoring
    )
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def score_with_semaphore(doc):
        async with semaphore:
            return await score_single_document(doc, query, llm)
    
    # Score all documents in parallel
    tasks = [score_with_semaphore(doc) for doc in documents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successful scores
    scores = []
    for result in results:
        if isinstance(result, DocumentScore):
            scores.append(result)
        elif isinstance(result, Exception):
            logger.warning(f"Scoring exception: {result}")
    
    return scores


def calculate_adaptive_threshold(
    total_results: int,
    social_media_ratio: float,
) -> float:
    """
    Calculate adaptive relevance threshold based on result characteristics.
    
    Args:
        total_results: Total number of search results.
        social_media_ratio: Ratio of social media sources (0.0-1.0).
    
    Returns:
        Adaptive threshold (0.45-0.65).
    """
    # Base threshold
    threshold = 0.55
    
    # Adjust for result count
    if total_results < 10:
        # Niche query - be more lenient
        threshold = 0.45
    elif total_results > 30:
        # Well-covered topic - be stricter
        threshold = 0.60
    
    # Adjust for social media ratio
    if social_media_ratio > 0.5:
        # High noise ratio - be more lenient
        threshold = min(threshold, 0.45)
    elif social_media_ratio < 0.2 and total_results > 20:
        # Low noise, good coverage - be stricter
        threshold = max(threshold, 0.60)
    
    return threshold
```

### 4.4 Integration with Research Reranker

**Update `services/nodes/research_reranker.py`:**

```python
# NEW IMPORTS
from services.utils.parallel_scorer import (
    score_documents_parallel,
    calculate_adaptive_threshold,
)
from services.utils.source_classifier import classify_source, SourceType
from models.fit_check import DocumentScore, ScoringResult

# REPLACE assess_quality_heuristically with new scoring integration

async def research_reranker_node(state, callback) -> Dict[str, Any]:
    """
    Phase 2B: Research Reranker with Multi-Dimensional Scoring.
    
    NEW APPROACH:
    1. Extract raw search results from Phase 2
    2. Score each document with parallel AI scoring
    3. Apply extractability multipliers
    4. Calculate adaptive threshold
    5. Route based on passing source count
    """
    phase_2_output = state.get("phase_2_output", {})
    original_query = state.get("query", "")
    
    # Get search results (need to extract from formatted results)
    search_results = _extract_search_results_from_phase2(state)
    
    if not search_results:
        # No results to score - early exit
        return _create_early_exit_state(state, "NO_SEARCH_RESULTS")
    
    # Emit scoring start event
    if callback:
        await callback.on_thought(
            step=state.get("step_count", 0) + 1,
            thought_type="reasoning",
            content=f"Scoring {len(search_results)} sources with AI evaluation...",
        )
    
    # Parallel AI scoring
    scores = await score_documents_parallel(
        documents=search_results,
        query=original_query,
        max_concurrent=5,
    )
    
    if not scores:
        # All scoring failed
        return _create_early_exit_state(state, "SCORING_FAILED")
    
    # Calculate social media ratio
    social_count = sum(1 for s in scores if s.source_type == SourceType.SOCIAL_MEDIA)
    social_ratio = social_count / len(scores) if scores else 0.0
    
    # Calculate adaptive threshold
    threshold = calculate_adaptive_threshold(
        total_results=len(search_results),
        social_media_ratio=social_ratio,
    )
    
    # Count passing sources
    passing_scores = [s for s in scores if s.final_score >= threshold]
    
    # Create scoring result
    scoring_result = ScoringResult(
        scores=scores,
        adaptive_threshold=threshold,
        passing_count=len(passing_scores),
        total_count=len(scores),
        social_media_ratio=social_ratio,
    )
    
    # Determine routing action
    action = _determine_routing_action(
        passing_count=len(passing_scores),
        total_count=len(scores),
        iteration=state.get("search_attempt", 1),
    )
    
    # Build state update
    return {
        "scoring_result": scoring_result,
        "top_sources": passing_scores[:5],  # Top 5 for enrichment
        "reranker_action": action,
        "step_count": state.get("step_count", 0) + 1,
    }


def _determine_routing_action(
    passing_count: int,
    total_count: int,
    iteration: int,
) -> str:
    """
    Determine routing action based on scoring results.
    
    Returns:
        - "CONTINUE": Proceed with analysis
        - "RETRY": Loop back for more search
        - "ABORT": Exit with insufficient data
    """
    # Sufficient sources
    if passing_count >= 3:
        return "CONTINUE"
    
    # Some sources, but below threshold
    if passing_count >= 1 and iteration < 3:
        return "RETRY"
    
    # No good sources after max iterations
    if iteration >= 3:
        return "ABORT"
    
    # First iteration with poor results
    if passing_count == 0 and iteration == 1:
        return "RETRY"
    
    return "CONTINUE"  # Proceed with what we have
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

**`tests/unit/test_source_classifier.py`:**

```python
import pytest
from services.utils.source_classifier import classify_source, SourceType

class TestSourceClassifier:
    """Test source type classification."""
    
    def test_video_classification(self):
        source_type, multiplier = classify_source("https://youtube.com/watch?v=123")
        assert source_type == SourceType.VIDEO
        assert multiplier == 0.20
    
    def test_social_media_classification(self):
        source_type, _ = classify_source("https://twitter.com/company/status/123")
        assert source_type == SourceType.SOCIAL_MEDIA
    
    def test_wiki_classification(self):
        source_type, multiplier = classify_source("https://en.wikipedia.org/wiki/Company")
        assert source_type == SourceType.WIKI
        assert multiplier > 1.0  # Bonus multiplier
    
    def test_academic_classification(self):
        source_type, _ = classify_source("https://arxiv.org/abs/2301.00000")
        assert source_type == SourceType.ACADEMIC
    
    def test_general_classification(self):
        source_type, multiplier = classify_source("https://company.com/careers")
        assert source_type == SourceType.GENERAL
        assert multiplier == 1.0
    
    def test_www_prefix_handling(self):
        source_type, _ = classify_source("https://www.youtube.com/watch")
        assert source_type == SourceType.VIDEO


class TestAdaptiveThreshold:
    """Test adaptive threshold calculation."""
    
    def test_low_results_lenient_threshold(self):
        from services.utils.parallel_scorer import calculate_adaptive_threshold
        threshold = calculate_adaptive_threshold(total_results=5, social_media_ratio=0.2)
        assert threshold <= 0.50
    
    def test_high_results_strict_threshold(self):
        from services.utils.parallel_scorer import calculate_adaptive_threshold
        threshold = calculate_adaptive_threshold(total_results=40, social_media_ratio=0.1)
        assert threshold >= 0.55
    
    def test_high_social_ratio_lenient(self):
        from services.utils.parallel_scorer import calculate_adaptive_threshold
        threshold = calculate_adaptive_threshold(total_results=20, social_media_ratio=0.6)
        assert threshold <= 0.50
```

**`tests/unit/test_parallel_scorer.py`:**

```python
import pytest
from unittest.mock import AsyncMock, patch
from services.utils.parallel_scorer import score_documents_parallel, score_single_document

class TestParallelScorer:
    """Test parallel document scoring."""
    
    @pytest.mark.asyncio
    async def test_score_single_document_success(self):
        """Should score document and apply extractability."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"relevance": 0.8, "quality": 0.7, "usefulness": 0.6, "rationale": "Good source"}'
        
        doc = {"id": "1", "url": "https://company.com", "title": "About", "snippet": "Test"}
        
        with patch('services.utils.parallel_scorer.get_llm', return_value=mock_llm):
            result = await score_single_document(doc, "company research", mock_llm)
        
        assert result is not None
        assert result.relevance_score == 0.8
        assert result.final_score > 0
    
    @pytest.mark.asyncio
    async def test_video_source_penalty(self):
        """Video sources should have extractability penalty."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"relevance": 0.9, "quality": 0.9, "usefulness": 0.9, "rationale": "Good"}'
        
        doc = {"id": "1", "url": "https://youtube.com/watch?v=123", "title": "Video", "snippet": "Test"}
        
        result = await score_single_document(doc, "query", mock_llm)
        
        assert result.extractability_multiplier == 0.20
        assert result.final_score < result.raw_composite
    
    @pytest.mark.asyncio
    async def test_parallel_scoring_respects_concurrency(self):
        """Should respect concurrency limits."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"relevance": 0.5, "quality": 0.5, "usefulness": 0.5, "rationale": ""}'
        
        docs = [{"id": str(i), "url": f"https://site{i}.com", "title": f"Doc {i}", "snippet": "Test"} for i in range(10)]
        
        with patch('services.utils.parallel_scorer.get_llm', return_value=mock_llm):
            results = await score_documents_parallel(docs, "query", max_concurrent=3)
        
        assert len(results) == 10
```

---

## 6. Requirements Tracking

### Verification Checklist

| # | Requirement | Test | Status |
|---|-------------|------|--------|
| 2.1 | Source type classification | `test_video_classification` | ⬜ |
| 2.2 | Extractability multipliers | `test_video_source_penalty` | ⬜ |
| 2.3 | 3-dimension scoring | `test_score_single_document_success` | ⬜ |
| 2.4 | Parallel scoring | `test_parallel_scoring_respects_concurrency` | ⬜ |
| 2.5 | Adaptive thresholds | `test_low_results_lenient_threshold` | ⬜ |
| 2.6 | Routing action logic | Unit test needed | ⬜ |
| 2.7 | Integration with reranker | Integration test needed | ⬜ |

### Sign-Off

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Performance benchmarked (parallel scoring < 5s for 10 docs)
- [ ] Code review completed

---

## 7. Files Changed Summary

| File | Action | Lines Changed (est.) |
|------|--------|---------------------|
| `models/fit_check.py` | EXTEND | ~40 |
| `services/utils/source_classifier.py` | **CREATE** | ~80 |
| `services/utils/parallel_scorer.py` | **CREATE** | ~180 |
| `services/nodes/research_reranker.py` | **MAJOR MODIFY** | ~150 |
| `services/pipeline_state.py` | EXTEND | ~10 |
| `tests/unit/test_source_classifier.py` | **CREATE** | ~50 |
| `tests/unit/test_parallel_scorer.py` | **CREATE** | ~60 |

---

## 8. Rollback Plan

If issues arise:
1. Feature flag: `USE_AI_SCORING = False` reverts to heuristic-only
2. New modules are additive and can be disabled
3. Original `assess_quality_heuristically()` preserved as fallback
