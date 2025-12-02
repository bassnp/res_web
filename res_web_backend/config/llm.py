"""
LLM Configuration for the Fit Check Agent.

This module provides configuration and factory functions for the
Google Gemini LLM used by the AI agent.
"""

import os
import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


# =============================================================================
# Model Configuration
# =============================================================================

# Default model - Using Gemini Flash for fast, capable responses
DEFAULT_MODEL = "gemini-flash-latest"

# Get model from environment or use default
MODEL_NAME = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

# Temperature settings
DEFAULT_TEMPERATURE = 0.7

# Token limits
MAX_OUTPUT_TOKENS = 2048


# =============================================================================
# LLM Factory Functions
# =============================================================================

def get_llm(
    streaming: bool = False,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> ChatGoogleGenerativeAI:
    """
    Get a configured LLM instance for the Fit Check Agent.
    
    Args:
        streaming: Whether to enable streaming mode for token-by-token output.
        temperature: Override default temperature (0.0-1.0).
        max_output_tokens: Override default max output tokens.
    
    Returns:
        ChatGoogleGenerativeAI: Configured LLM instance.
    
    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it in your .env file."
        )
    
    # Use provided values or defaults
    temp = temperature if temperature is not None else DEFAULT_TEMPERATURE
    max_tokens = max_output_tokens if max_output_tokens is not None else MAX_OUTPUT_TOKENS
    
    logger.debug(
        f"Creating LLM instance: model={MODEL_NAME}, "
        f"streaming={streaming}, temperature={temp}"
    )
    
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=temp,
        max_output_tokens=max_tokens,
        streaming=streaming,
        convert_system_message_to_human=True,
    )
