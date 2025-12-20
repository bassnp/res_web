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
from services.utils.circuit_breaker import llm_breaker, CircuitOpenError

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
    url = document.get("url", document.get("link", ""))
    title = document.get("title", "")
    snippet = document.get("snippet", "")
    content = document.get("content") or snippet[:500]
    doc_id = document.get("id", url or "unknown")
    
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
        async with llm_breaker.call():
            response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        # Handle Gemini's response format - content can be string or list of parts
        raw_content = response.content
        if isinstance(raw_content, list):
            # Gemini returns list of content parts
            response_text = "".join(
                part.text if hasattr(part, 'text') else str(part)
                for part in raw_content
            ).strip()
        else:
            response_text = str(raw_content).strip()
        
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
            snippet=snippet,
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
        model_id="gemini-3-flash-preview",  # Fast model for parallel scoring
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
