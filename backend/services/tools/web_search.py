"""
Web Search Tool for the Fit Check Agent.

This module provides web search functionality using Google Custom Search Engine (CSE)
to research companies, job positions, and industry information.
"""

import os
import logging
from typing import Optional

from langchain_core.tools import tool
from services.utils.circuit_breaker import search_breaker, CircuitOpenError

logger = logging.getLogger(__name__)


# =============================================================================
# Google CSE Configuration
# =============================================================================

def _get_search_wrapper():
    """
    Lazily initialize the Google Search API wrapper.
    
    Returns:
        GoogleSearchAPIWrapper or None if not configured.
    """
    cse_api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not cse_api_key or not cse_id:
        logger.warning(
            "Google CSE not configured. Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID "
            "in your .env file for web search functionality."
        )
        return None
    
    try:
        from langchain_google_community import GoogleSearchAPIWrapper
        
        return GoogleSearchAPIWrapper(
            google_api_key=cse_api_key,
            google_cse_id=cse_id,
            k=5,  # Return top 5 results
        )
    except ImportError:
        logger.error(
            "langchain-google-community not installed. "
            "Run: pip install langchain-google-community"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Google Search wrapper: {e}")
        return None


# =============================================================================
# Web Search Tool
# =============================================================================

@tool
async def web_search(query: str) -> str:
    """
    Search the web for information about companies, job positions, or industry topics.
    
    Use this tool to research:
    - Company culture, values, and tech stack
    - Job requirements and responsibilities
    - Industry trends and news
    - Technology information relevant to the employer
    
    Args:
        query: The search query. Be specific and include relevant keywords
               like company name, technology, or job-related terms.
    
    Returns:
        str: Search results as formatted text, or an error message if search fails.
    
    Example queries:
        - "Google engineering culture and values"
        - "Stripe software engineer requirements tech stack"
        - "OpenAI Python developer job responsibilities"
    """
    logger.info(f"Web search tool called with query: {query}")
    
    # Validate input
    if not query or not query.strip():
        return "Error: Search query cannot be empty."
    
    query = query.strip()
    
    # Get search wrapper
    search_wrapper = _get_search_wrapper()
    
    if search_wrapper is None:
        # Fallback: Return a message indicating search is unavailable
        logger.warning("Web search unavailable, returning fallback response")
        return _get_fallback_response(query)
    
    try:
        async with search_breaker.call():
            # Perform the search
            results = search_wrapper.run(query)
            
            if not results or results.strip() == "":
                logger.info(f"No results found for query: {query}")
                return f"No search results found for: {query}. Try a different search query."
            
            # Truncate results if too long (keep under 1500 chars for context efficiency)
            if len(results) > 1500:
                results = results[:1500] + "..."
                logger.debug("Search results truncated to 1500 characters")
            
            logger.info(f"Web search successful, returned {len(results)} characters")
            return results
            
    except CircuitOpenError:
        logger.warning(f"Search circuit is OPEN for query: {query}, using fallback")
        return _get_fallback_response(query)
    except Exception as e:
        error_msg = f"Web search failed: {str(e)}"
        logger.error(error_msg)
        return f"Error performing web search: {str(e)}. Please try a different query."


async def web_search_structured(query: str, num_results: int = 5) -> list:
    """
    Perform a web search and return structured results.
    
    Args:
        query: The search query.
        num_results: Number of results to return.
        
    Returns:
        list: List of dicts with 'title', 'link', 'snippet'.
    """
    logger.info(f"Structured web search called with query: {query}")
    
    search_wrapper = _get_search_wrapper()
    if search_wrapper is None:
        return []
        
    try:
        async with search_breaker.call():
            # GoogleSearchAPIWrapper.results returns a list of dicts
            return search_wrapper.results(query, num_results)
    except CircuitOpenError:
        logger.warning(f"Search circuit is OPEN for structured query: {query}")
        return []
    except Exception as e:
        logger.error(f"Structured web search failed: {e}")
        return []


def _get_fallback_response(query: str) -> str:
    """
    Provide a fallback response when web search is unavailable.
    
    Args:
        query: The original search query.
    
    Returns:
        str: A helpful fallback message.
    """
    # Extract potential company name from query
    query_lower = query.lower()
    
    # Common tech companies with known info
    company_info = {
        "google": (
            "Google is a leading technology company known for search, cloud computing, "
            "and AI/ML. They value innovation, technical excellence, and data-driven "
            "decision making. Tech stack includes Python, Go, Java, and cutting-edge ML."
        ),
        "meta": (
            "Meta (formerly Facebook) focuses on social media and metaverse technologies. "
            "They value move fast, be bold, and building community. Tech stack includes "
            "React, Python, Hack/PHP, and PyTorch for AI."
        ),
        "amazon": (
            "Amazon is an e-commerce and cloud computing leader (AWS). They follow "
            "leadership principles like customer obsession and bias for action. "
            "Tech stack includes Java, Python, AWS services, and microservices architecture."
        ),
        "microsoft": (
            "Microsoft is a software and cloud computing giant (Azure). They value "
            "growth mindset, diversity, and innovation. Tech stack includes C#, .NET, "
            "TypeScript, Python, and Azure services."
        ),
        "apple": (
            "Apple focuses on consumer electronics and software with emphasis on "
            "design excellence and user experience. Tech stack includes Swift, "
            "Objective-C, Python, and proprietary frameworks."
        ),
        "netflix": (
            "Netflix is a streaming entertainment company known for engineering culture "
            "of freedom and responsibility. Tech stack includes Java, Python, Node.js, "
            "and microservices on AWS."
        ),
        "stripe": (
            "Stripe provides payment infrastructure for the internet. They value "
            "meticulous craftsmanship and user-centric design. Tech stack includes "
            "Ruby, Go, Python, React, and strong API design."
        ),
        "openai": (
            "OpenAI is an AI research company building advanced AI systems. They value "
            "safety, beneficial AI, and research excellence. Tech stack includes Python, "
            "PyTorch, distributed systems, and cutting-edge ML infrastructure."
        ),
    }
    
    for company, info in company_info.items():
        if company in query_lower:
            return (
                f"[Note: Live web search unavailable. Using cached information]\n\n"
                f"{info}"
            )
    
    return (
        f"[Note: Web search is currently unavailable. Please ensure GOOGLE_CSE_API_KEY "
        f"and GOOGLE_CSE_ID are configured in your .env file.]\n\n"
        f"Unable to search for: {query}\n\n"
        f"The AI agent will proceed with general knowledge about the topic."
    )


# =============================================================================
# Utility Functions
# =============================================================================

def validate_search_config() -> dict:
    """
    Validate that web search is properly configured.
    
    Returns:
        dict: Configuration status information.
    """
    cse_api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    return {
        "cse_api_key_configured": bool(cse_api_key and len(cse_api_key) > 10),
        "cse_id_configured": bool(cse_id and len(cse_id) > 5),
        "ready": bool(cse_api_key and cse_id),
    }
