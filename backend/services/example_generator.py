"""
Example Generator Service - Quick AI Generation for Job Examples.

This module provides a lightweight AI generation service that creates
sample job descriptions or company positions for demo purposes.
Generates either:
- "good" examples: Short, generalized positions matching the engineer's field
- "bad" examples: Obscure, unrelated positions for contrast demonstration

Uses the engineer profile to create contextually relevant examples
that showcase the fit check feature's capabilities.
"""

import logging
import random
from typing import Dict, Any, Literal

from langchain_core.messages import HumanMessage

from config.llm import get_llm
from config.engineer_profile import get_formatted_profile, ENGINEER_PROFILE
from services.utils import get_response_text

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

GENERATION_TEMPERATURE = 0.9  # Higher for creativity/variety
GENERATION_MAX_TOKENS = 64  # Short outputs for fast generation


# =============================================================================
# Prompt Templates (Concise)
# =============================================================================

GOOD_EXAMPLE_PROMPT = """Generate a SHORT job query (one sentence max) for a software engineering position.

The engineer has skills in: Python, JavaScript, React, FastAPI, AI/ML, cloud technologies.

Generate ONE of these at random:
- A tech company name (e.g., "Stripe", "Notion", "Datadog")
- A brief job title (e.g., "Full Stack Developer at a fintech startup")
- A one-line role description (e.g., "Backend engineer working on AI products")

Output ONLY the query text. No quotes, no labels, no explanation. Keep it under 15 words."""

BAD_EXAMPLE_PROMPT = """Generate a SHORT job query (one sentence max) for a position completely UNRELATED to software engineering.

Pick something obscure and random like:
- Trades: Barber, Plumber, Electrician, HVAC Technician
- Creative: Florist, Tattoo Artist, Wedding Photographer
- Physical: MMA Fighter, Personal Trainer, Yoga Instructor
- Service: Dog Groomer, Bartender, Cruise Ship Captain
- Other: Beekeeper, Taxidermist, Fortune Teller, Sommelier

Output ONLY the query text. No quotes, no labels, no explanation. Keep it under 15 words.
Be creative and pick something unexpected."""


# =============================================================================
# Main Generation Function
# =============================================================================

async def generate_example(
    example_quality: Literal["good", "bad"]
) -> Dict[str, Any]:
    """
    Generate a sample job query for demonstration purposes.
    
    This function creates contextually relevant examples based on
    the engineer's profile, showcasing the fit check feature.
    
    Args:
        example_quality: Either "good" for well-matched positions
                        or "bad" for completely unrelated positions.
    
    Returns:
        Dict containing:
            - success: bool indicating generation success
            - example: The generated text
            - example_type: Type of example generated
            - quality: "good" or "bad"
            - error: Error message if failed
    """
    try:
        # Select appropriate prompt
        prompt = GOOD_EXAMPLE_PROMPT if example_quality == "good" else BAD_EXAMPLE_PROMPT
        example_type = "tech_position" if example_quality == "good" else "unrelated_position"
        
        # Get LLM with higher temperature for creativity
        # Use standard config (no reasoning) and low max tokens for fast generation
        llm = get_llm(
            temperature=GENERATION_TEMPERATURE,
            max_output_tokens=GENERATION_MAX_TOKENS,
            config_type="standard",
        )
        
        # Generate the example
        logger.info(f"Generating {example_quality} example")
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        generated_text = get_response_text(response).strip()
        
        # Clean up any quotes or labels that might slip through
        generated_text = generated_text.strip('"\'')
        if generated_text.lower().startswith(("example:", "query:", "result:", "output:")):
            generated_text = generated_text.split(":", 1)[1].strip()
        
        logger.info(f"Generated example: {generated_text}")
        
        return {
            "success": True,
            "example": generated_text,
            "example_type": example_type,
            "quality": example_quality,
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate example: {e}")
        return {
            "success": False,
            "example": None,
            "example_type": None,
            "quality": example_quality,
            "error": str(e),
        }


# =============================================================================
# Predefined Fallback Examples (for when API fails or for testing)
# =============================================================================

FALLBACK_GOOD_EXAMPLES = [
    "Full stack developer at a growing startup",
    "Software engineer for AI products",
    "Backend developer at a cloud company",
    "React developer for a SaaS platform",
    "Junior engineer at a tech company",
    "Stripe",
    "Vercel",
    "OpenAI",
    "Notion",
    "Figma",
]

FALLBACK_BAD_EXAMPLES = [
    "Professional dog groomer",
    "Licensed barber",
    "MMA fighter",
    "Wedding photographer",
    "Cruise ship captain",
    "Beekeeper",
    "Tattoo artist",
    "Yoga instructor",
    "Sommelier at a fine dining restaurant",
    "Fortune teller",
    "Taxidermist",
    "Florist",
    "HVAC technician",
    "Personal trainer",
]


def get_fallback_example(example_quality: Literal["good", "bad"]) -> Dict[str, Any]:
    """
    Get a predefined fallback example when generation fails.
    
    Args:
        example_quality: Either "good" or "bad".
    
    Returns:
        Dict with fallback example data.
    """
    examples = FALLBACK_GOOD_EXAMPLES if example_quality == "good" else FALLBACK_BAD_EXAMPLES
    return {
        "success": True,
        "example": random.choice(examples),
        "example_type": "fallback",
        "quality": example_quality,
        "error": None,
    }
