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
    "gemini-flash-latest": {
        "config_type": "standard", 
        "description": "Fast responses with balanced accuracy",
    },
}

# Default model - Using Gemini 3 Pro for enhanced reasoning capabilities
# Native reasoning model - no need for "think step-by-step" instructions
# Supports criteria-based prompting and higher accuracy for complex analysis
DEFAULT_MODEL = "gemini-3-pro-preview"

# Get model from environment or use default
MODEL_NAME = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

# Temperature settings for standard models
DEFAULT_TEMPERATURE = 0.3  # Lower for more deterministic outputs
DEFAULT_TOP_K = 40  # Higher accuracy with diverse sampling

# Token limits
MAX_OUTPUT_TOKENS = 2048


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
    
    # Build model kwargs based on config type
    model_kwargs = {}
    
    if config_type == "reasoning":
        # Gemini 3 Pro uses thinking_config for high reasoning
        # Native reasoning model - optimal for complex analysis
        model_kwargs["thinking_config"] = {"thinking_budget": 10000}
        temp = 1.0  # Gemini 3 reasoning works best with temperature 1.0
        logger.debug("Using reasoning config with thinking_budget=10000")
    else:
        # Standard models use temperature and topK for accuracy
        temp = temperature if temperature is not None else DEFAULT_TEMPERATURE
        model_kwargs["top_k"] = DEFAULT_TOP_K
        logger.debug(f"Using standard config with temperature={temp}, top_k={DEFAULT_TOP_K}")
    
    return ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=api_key,
        temperature=temp,
        max_output_tokens=max_tokens,
        streaming=streaming,
        convert_system_message_to_human=True,
        **model_kwargs,
    )
