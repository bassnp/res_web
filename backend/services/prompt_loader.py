"""
Prompt Loader Utility for Model-Specific Prompt Selection.

This module provides utilities for loading prompts based on AI model configuration.
Gemini 3 Pro (reasoning models) use concise, objective-based prompts.
Gemini Flash/Flash-Lite (standard models) use verbose, schema-focused prompts.

Design Philosophy:
- Reasoning models (Gemini 3 Pro): Concise prompts prevent "double-think" timeouts
- Standard models (Flash/Flash-Lite): Verbose prompts with examples for accuracy
"""

import logging
from pathlib import Path
from typing import Optional, Literal

logger = logging.getLogger(__name__)

# Base path for all prompts
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Model config type determines prompt selection
ConfigType = Literal["reasoning", "standard"]


def get_prompt_path(
    phase_name: str,
    config_type: Optional[ConfigType] = None,
    prefer_concise: bool = True,
) -> Path:
    """
    Get the appropriate prompt file path based on model configuration.
    
    Args:
        phase_name: The phase name (e.g., "phase_1_connecting", "phase_2_deep_research")
        config_type: The model config type ("reasoning" or "standard")
        prefer_concise: If True, use concise prompts for reasoning models
    
    Returns:
        Path to the appropriate prompt file.
    
    Selection Logic:
        - reasoning config + prefer_concise → phase_X_concise.xml
        - standard config OR no preference → phase_X.xml (verbose)
        - Falls back to verbose if concise not found
    """
    base_name = phase_name.replace("_node", "")
    
    # Determine if we should use concise prompt
    use_concise = config_type == "reasoning" and prefer_concise
    
    if use_concise:
        concise_path = PROMPTS_DIR / f"{base_name}_concise.xml"
        if concise_path.exists():
            logger.debug(f"Using concise prompt for {phase_name}: {concise_path}")
            return concise_path
        else:
            logger.warning(f"Concise prompt not found for {phase_name}, falling back to verbose")
    
    # Default to verbose prompt
    verbose_path = PROMPTS_DIR / f"{base_name}.xml"
    logger.debug(f"Using verbose prompt for {phase_name}: {verbose_path}")
    return verbose_path


def load_prompt(
    phase_name: str,
    config_type: Optional[ConfigType] = None,
    prefer_concise: bool = True,
) -> str:
    """
    Load the prompt content for a phase based on model configuration.
    
    Args:
        phase_name: The phase name (e.g., "phase_1_connecting")
        config_type: The model config type ("reasoning" or "standard")
        prefer_concise: If True, use concise prompts for reasoning models
    
    Returns:
        The prompt template as a string.
    
    Raises:
        FileNotFoundError: If neither concise nor verbose prompt exists.
    """
    prompt_path = get_prompt_path(phase_name, config_type, prefer_concise)
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
            logger.info(f"Loaded prompt from {prompt_path.name} ({len(content)} chars)")
            return content
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise


def get_prompt_variant_info(config_type: Optional[ConfigType] = None) -> dict:
    """
    Get information about which prompt variant will be used.
    
    Useful for debugging and logging which prompts are active.
    
    Args:
        config_type: The model config type
    
    Returns:
        Dict with variant info and rationale.
    """
    if config_type == "reasoning":
        return {
            "variant": "concise",
            "rationale": "Gemini 3 Pro uses native reasoning - concise prompts prevent double-think",
            "optimization": "Objective-based prompting, no step-by-step instructions",
        }
    else:
        return {
            "variant": "verbose", 
            "rationale": "Standard models benefit from detailed examples and schemas",
            "optimization": "Few-shot examples, explicit behavioral constraints",
        }


# Phase name constants for consistency
PHASE_CONNECTING = "phase_1_connecting"
PHASE_DEEP_RESEARCH = "phase_2_deep_research"
PHASE_RESEARCH_RERANKER = "phase_2b_research_reranker"
PHASE_SKEPTICAL_COMPARISON = "phase_3_skeptical_comparison"
PHASE_SKILLS_MATCHING = "phase_4_skills_matching"
PHASE_GENERATE_RESULTS = "phase_5_generate_results"
PHASE_CONFIDENCE_RERANKER = "phase_5b_confidence_reranker"
