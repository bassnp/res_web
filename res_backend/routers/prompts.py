"""
Prompts Router - API Endpoints for Prompt Transparency.

This module provides endpoints to retrieve system prompts used in the
AI pipeline, enabling transparency for users who want to understand
how the AI reasoning works.

Endpoints:
    GET /api/prompts           - List all available prompt phases
    GET /api/prompts/{phase}   - Get prompt content for a specific phase
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/prompts",
    tags=["Prompts"],
    responses={
        404: {"description": "Prompt not found"},
        500: {"description": "Server error"},
    },
)

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


# =============================================================================
# Response Models
# =============================================================================

class PhaseInfo(BaseModel):
    """Information about a pipeline phase and its prompt."""
    
    phase: str
    display_name: str
    description: str
    order: int


class PromptListResponse(BaseModel):
    """Response containing list of all available prompts."""
    
    phases: List[PhaseInfo]


class PromptContentResponse(BaseModel):
    """Response containing a single prompt's content."""
    
    phase: str
    display_name: str
    description: str
    content: str
    order: int


# =============================================================================
# Phase Metadata
# =============================================================================

PHASE_METADATA: Dict[str, Dict] = {
    "connecting": {
        "display_name": "Query Classification",
        "description": "Classifies the input query, extracts entities (company name, job title), and validates for security. Acts as a gatekeeper to reject malicious or irrelevant queries.",
        "order": 1,
        "filename": "phase_1_connecting.xml",
    },
    "deep_research": {
        "display_name": "Deep Research",
        "description": "Gathers comprehensive employer intelligence via web search, extracting tech stack, culture signals, and job requirements from external sources.",
        "order": 2,
        "filename": "phase_2_deep_research.xml",
    },
    "research_reranker": {
        "display_name": "Research Quality Gate",
        "description": "Validates research completeness and quality. Determines if data is sufficient to proceed or if enhanced search is needed. Prunes unreliable sources.",
        "order": 3,
        "filename": "phase_2b_research_reranker.xml",
    },
    "skeptical_comparison": {
        "display_name": "Skeptical Comparison",
        "description": "Performs critical gap analysis between the engineer's profile and employer requirements. Identifies genuine gaps and assesses risk levels without over-claiming.",
        "order": 4,
        "filename": "phase_3_skeptical_comparison.xml",
    },
    "skills_matching": {
        "display_name": "Skills Matching",
        "description": "Maps the engineer's skills to job requirements, calculating match percentages by category and identifying transferable skills and learning gaps.",
        "order": 5,
        "filename": "phase_4_skills_matching.xml",
    },
    "confidence_reranker": {
        "display_name": "Confidence Calibration",
        "description": "LLM-as-Judge meta-cognitive review of all prior phases. Detects reasoning flaws, score inflation, and contradictions. Adjusts confidence with explicit audit trail.",
        "order": 6,
        "filename": "phase_5b_confidence_reranker.xml",
    },
    "generate_results": {
        "display_name": "Response Generation",
        "description": "Synthesizes all phase outputs into a coherent, personalized narrative. Applies confidence-appropriate framing and maintains an honest, calibrated tone.",
        "order": 7,
        "filename": "phase_5_generate_results.xml",
    },
}


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "",
    response_model=PromptListResponse,
    summary="List all pipeline phases",
    description="Returns metadata for all pipeline phases including display names and descriptions.",
)
async def list_prompts():
    """
    List all available pipeline phases.
    
    Returns:
        PromptListResponse: List of phase metadata.
    """
    phases = [
        PhaseInfo(
            phase=phase,
            display_name=meta["display_name"],
            description=meta["description"],
            order=meta["order"],
        )
        for phase, meta in sorted(
            PHASE_METADATA.items(),
            key=lambda x: x[1]["order"]
        )
    ]
    
    return PromptListResponse(phases=phases)


@router.get(
    "/{phase}",
    response_model=PromptContentResponse,
    summary="Get prompt content for a phase",
    description="Returns the full prompt template for the specified pipeline phase.",
)
async def get_prompt(phase: str):
    """
    Get the prompt content for a specific pipeline phase.
    
    Args:
        phase: The phase name (e.g., 'connecting', 'deep_research').
    
    Returns:
        PromptContentResponse: Phase metadata and prompt content.
    
    Raises:
        HTTPException: If the phase is not found.
    """
    # Validate phase exists
    if phase not in PHASE_METADATA:
        raise HTTPException(
            status_code=404,
            detail=f"Phase '{phase}' not found. Available phases: {list(PHASE_METADATA.keys())}",
        )
    
    meta = PHASE_METADATA[phase]
    prompt_path = PROMPTS_DIR / meta["filename"]
    
    # Read prompt content
    try:
        content = prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Prompt file not found for phase '{phase}'",
        )
    except Exception as e:
        logger.error(f"Error reading prompt file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading prompt for phase '{phase}'",
        )
    
    return PromptContentResponse(
        phase=phase,
        display_name=meta["display_name"],
        description=meta["description"],
        content=content,
        order=meta["order"],
    )
