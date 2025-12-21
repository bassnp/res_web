"""
LLM Configuration for the Fit Check Agent.

This module provides configuration and factory functions for the
Google Gemini LLM used by the AI agent.

Model Configuration Types:
- reasoning: Uses thinking_config for high reasoning (Gemini 3 Pro)
- standard: Uses temperature and topK for accuracy (Gemini Flash)
"""

import os
import logging
import asyncio
from typing import Optional, Literal

from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


# =============================================================================
# Model Configuration
# =============================================================================

# Supported models with their configuration requirements
SUPPORTED_MODELS = {
    "gemini-3-pro-preview": {
        "config_type": "reasoning",
        "description": "Advanced reasoning with deep analysis",
    },
    "gemini-3-flash-preview": {
        "config_type": "reasoning",
        "description": "Fast reasoning with good accuracy",
    },
    "gemini-3-flash-preview": {
        "config_type": "standard", 
        "description": "Fast responses with balanced accuracy",
    },
}

# Default model - Using Gemini 3 Flash for faster responses
# Native reasoning model - no need for "think step-by-step" instructions
# Supports criteria-based prompting and good accuracy for complex analysis
DEFAULT_MODEL = "gemini-3-flash-preview"

# Get model from environment or use default
MODEL_NAME = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

# Temperature settings for standard models
DEFAULT_TEMPERATURE = 0.3  # Lower for more deterministic outputs
DEFAULT_TOP_K = 40  # Higher accuracy with diverse sampling

# Token limits
MAX_OUTPUT_TOKENS = 2048


# =============================================================================
# LLM Concurrency Throttling
# =============================================================================

# Maximum concurrent LLM requests (adjust based on Gemini rate limits)
MAX_CONCURRENT_LLM_REQUESTS = 10

# Global semaphore for LLM rate limiting
_llm_semaphore: Optional[asyncio.Semaphore] = None

def get_llm_semaphore() -> asyncio.Semaphore:
    """
    Get or create the global LLM concurrency semaphore.
    
    This limits concurrent requests to the Gemini API to prevent
    rate limiting errors under high load.
    
    Returns:
        asyncio.Semaphore with MAX_CONCURRENT_LLM_REQUESTS permits.
    """
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_REQUESTS)
    return _llm_semaphore


async def with_llm_throttle(coro):
    """
    Execute a coroutine with LLM rate limiting.
    
    Usage:
        result = await with_llm_throttle(llm.ainvoke(prompt))
    
    Args:
        coro: Coroutine to execute.
    
    Returns:
        Result of the coroutine.
    """
    async with get_llm_semaphore():
        return await coro


async def with_llm_throttle_stream(async_iterator):
    """
    Execute an async iterator with LLM rate limiting.
    
    Usage:
        async for chunk in with_llm_throttle_stream(llm.astream(prompt)):
            ...
    """
    async with get_llm_semaphore():
        async for item in async_iterator:
            yield item


# =============================================================================
# LLM Factory Functions
# =============================================================================

def get_llm(
    streaming: bool = False,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    model_id: Optional[str] = None,
    config_type: Optional[Literal["reasoning", "standard"]] = None,
) -> ChatGoogleGenerativeAI:
    """
    Get a configured LLM instance for the Fit Check Agent.
    
    Args:
        streaming: Whether to enable streaming mode for token-by-token output.
        temperature: Override default temperature (0.0-1.0). Only used for standard config.
        max_output_tokens: Override default max output tokens.
        model_id: Model ID to use. Defaults to environment variable or DEFAULT_MODEL.
        config_type: Configuration type ('reasoning' or 'standard').
                    If not specified, will be inferred from model_id.
    
    Returns:
        ChatGoogleGenerativeAI: Configured LLM instance.
    
    Raises:
        ValueError: If GOOGLE_API_KEY is not set or model is not supported.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it in your .env file."
        )
    
    # Determine which model to use
    selected_model = model_id if model_id else MODEL_NAME
    
    # Validate model is supported
    if selected_model not in SUPPORTED_MODELS:
        logger.warning(f"Model {selected_model} not in supported list, using default")
        selected_model = DEFAULT_MODEL
    
    # Determine config type from model if not specified
    if config_type is None:
        config_type = SUPPORTED_MODELS.get(selected_model, {}).get("config_type", "reasoning")
    
    # Use provided values or defaults
    max_tokens = max_output_tokens if max_output_tokens is not None else MAX_OUTPUT_TOKENS
    
    logger.info(
        f"Creating LLM instance: model={selected_model}, "
        f"config_type={config_type}, streaming={streaming}"
    )
    
    # Build configuration based on config type
    thinking_budget = None
    top_k = None
    
    if config_type == "reasoning":
        # Gemini 3 Pro uses thinking_budget for extended reasoning
        # Minimal thinking_budget (1024) for fastest responses
        # Tasks are simple enough that deep reasoning isn't needed
        thinking_budget = 1024
        temp = 1.0  # Gemini 3 reasoning works best with temperature 1.0
        logger.debug("Using reasoning config with thinking_budget=1024")
    else:
        # Standard models use temperature and topK for accuracy
        temp = temperature if temperature is not None else DEFAULT_TEMPERATURE
        top_k = DEFAULT_TOP_K
        logger.debug(f"Using standard config with temperature={temp}, top_k={top_k}")
    
    # Build kwargs dict, only including non-None values
    kwargs = {
        "model": selected_model,
        "google_api_key": api_key,
        "temperature": temp,
        "max_output_tokens": max_tokens,
        "streaming": streaming,
        "convert_system_message_to_human": True,
    }
    
    if thinking_budget is not None:
        kwargs["thinking_budget"] = thinking_budget
    if top_k is not None:
        kwargs["top_k"] = top_k
    
    return ChatGoogleGenerativeAI(**kwargs)
