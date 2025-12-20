"""
Content Enrichment Node - Phase 2C of the Fit Check Pipeline.

This module implements the full content extraction layer that:
1. Takes top-scored sources from Phase 2B
2. Fetches full HTML/text content in parallel
3. Cleans and truncates content for downstream synthesis
4. Provides rich context for skeptical comparison and skills matching

Key Design Principles:
- Parallel fetching with semaphore-controlled concurrency
- Graceful degradation (fallback to snippet if fetch fails)
- Content cleaning to remove boilerplate/nav
- Context-aware truncation to stay within token limits
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List

import httpx
from services.pipeline_state import FitCheckPipelineState
from services.callbacks import ThoughtCallback
from models.fit_check import DocumentScore
from services.utils.circuit_breaker import fetch_breaker, CircuitOpenError

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

PHASE_NAME = "content_enrich"
PHASE_DISPLAY = "Content Enrichment"

# Maximum concurrent fetches
MAX_CONCURRENT_FETCHES = 5

# Fetch timeout in seconds
FETCH_TIMEOUT = 10

# Maximum characters per enriched document
MAX_ENRICHED_LENGTH = 8000

# User agent for fetching
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# =============================================================================
# Content Extraction Utilities
# =============================================================================

async def fetch_full_content(url: str, client: httpx.AsyncClient) -> Optional[str]:
    """
    Fetch full content from a URL.
    
    Args:
        url: The URL to fetch.
        client: Async HTTP client.
        
    Returns:
        str: Extracted text content or None if fetch fails.
    """
    try:
        response = await client.get(url, timeout=FETCH_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
        
        # Basic HTML cleaning
        html = response.text
        
        # Remove script and style elements
        text = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove all other tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    except Exception as e:
        logger.warning(f"Failed to fetch content from {url}: {e}")
        return None

async def enrich_source(
    source: DocumentScore,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    """
    Enrich a single source with full content.
    
    Args:
        source: The document score object.
        client: Async HTTP client.
        semaphore: Concurrency control.
        
    Returns:
        Dict with enriched content.
    """
    async with semaphore:
        url = source.url
        logger.info(f"Enriching source: {url}")
        
        full_content = None
        try:
            async with fetch_breaker.call():
                full_content = await fetch_full_content(url, client)
        except CircuitOpenError:
            logger.warning(f"Fetch circuit is OPEN for URL: {url}, using fallback")
        except Exception as e:
            logger.warning(f"Error fetching {url} within circuit breaker: {e}")
        
        if full_content:
            # Truncate to limit
            if len(full_content) > MAX_ENRICHED_LENGTH:
                full_content = full_content[:MAX_ENRICHED_LENGTH] + "... [truncated]"
            
            return {
                "url": url,
                "title": source.title,
                "content": full_content,
                "is_enriched": True,
                "score": source.final_score,
            }
        else:
            # Fallback to snippet
            return {
                "url": url,
                "title": source.title,
                "content": source.snippet or "No content available.",
                "is_enriched": False,
                "score": source.final_score,
            }

# =============================================================================
# Main Node Function
# =============================================================================

async def content_enrich_node(
    state: FitCheckPipelineState,
    callback: Optional[ThoughtCallback] = None,
) -> Dict[str, Any]:
    """
    Phase 2C: CONTENT_ENRICH - Full Content Extraction Node.
    
    Fetches full content for the top-scored sources identified in Phase 2B.
    This provides deeper context for the subsequent analysis phases.
    """
    logger.info("[CONTENT_ENRICH] Starting phase 2C")
    step = state.get("step_count", 0)
    top_sources = state.get("top_sources") or []
    
    if not top_sources:
        logger.warning("[CONTENT_ENRICH] No top sources found to enrich")
        return {
            "current_phase": "skeptical_comparison",
            "step_count": step,
        }

    # Emit phase start event
    if callback and hasattr(callback, 'on_phase'):
        await callback.on_phase(
            PHASE_NAME,
            f"Enriching top {len(top_sources)} sources..."
        )
    
    step += 1
    if callback:
        await callback.on_thought(
            step=step,
            thought_type="reasoning",
            content=f"Fetching full content for {len(top_sources)} high-quality sources to deepen analysis...",
            phase=PHASE_NAME,
        )

    enriched_results = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
    
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
        tasks = [enrich_source(source, client, semaphore) for source in top_sources]
        enriched_results = await asyncio.gather(*tasks)

    enriched_count = sum(1 for r in enriched_results if r.get("is_enriched"))
    total_kb = sum(len(r.get("content", "")) for r in enriched_results) / 1024
    summary = f"Enriched {enriched_count}/{len(enriched_results)} sources with full content ({total_kb:.1f} KB)"
    
    # Emit phase complete event with enriched metadata
    if callback and hasattr(callback, 'on_phase_complete'):
        # Build rich source details for frontend transparency
        source_details = []
        for r in enriched_results:
            source_details.append({
                "title": r.get("title", "Unknown")[:60],
                "url": r.get("url", ""),
                "size_kb": round(len(r.get("content", "")) / 1024, 1),
                "is_enriched": r.get("is_enriched", False),
                "score": r.get("score", 0),
            })
        
        enriched_data = {
            "enriched_count": enriched_count,
            "total_count": len(enriched_results),
            "total_kb": round(total_kb, 1),
            # Detailed source breakdown
            "sources": source_details,
            "success_rate": f"{int(enriched_count / max(len(enriched_results), 1) * 100)}%",
        }
        await callback.on_phase_complete(
            PHASE_NAME, 
            summary,
            data=enriched_data
        )
    
    logger.info(f"[CONTENT_ENRICH] Phase 2C complete: {summary}")
    
    return {
        "enriched_content": enriched_results,
        "current_phase": "skeptical_comparison",
        "step_count": step,
    }
