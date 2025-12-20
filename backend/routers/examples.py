"""
Examples Router - API Endpoint for Generating Sample Job Queries.

This module provides a simple endpoint for generating example job queries
that can be used to demonstrate the fit check feature.

Endpoints:
    POST /api/examples/generate - Generate a good or bad example query
"""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.example_generator import generate_example, get_fallback_example

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateExampleRequest(BaseModel):
    """Request model for example generation."""
    quality: Literal["good", "bad"] = Field(
        ...,
        description="Quality of example to generate: 'good' for well-matched, 'bad' for poorly-matched"
    )


class GenerateExampleResponse(BaseModel):
    """Response model for generated example."""
    success: bool = Field(..., description="Whether generation succeeded")
    example: str | None = Field(None, description="Generated example text")
    example_type: str | None = Field(None, description="Type of example generated")
    quality: str = Field(..., description="Quality of the example")
    error: str | None = Field(None, description="Error message if failed")


# =============================================================================
# Router Definition
# =============================================================================

router = APIRouter(
    prefix="/api/examples",
    tags=["Examples"],
    responses={
        400: {"description": "Invalid quality parameter"},
        500: {"description": "Generation failed"},
    },
)


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=GenerateExampleResponse,
    summary="Generate a sample job query",
    description="""
    Generates a sample job query for demonstration purposes.
    
    - **good**: Generates a position that matches the engineer's skills well
    - **bad**: Generates a position with poor skill alignment
    
    Uses AI to create contextually relevant examples based on the engineer's profile.
    Falls back to predefined examples if AI generation fails.
    """,
)
async def generate_example_endpoint(request: GenerateExampleRequest) -> GenerateExampleResponse:
    """
    Generate a sample job query for demo purposes.
    
    Args:
        request: GenerateExampleRequest with quality parameter.
    
    Returns:
        GenerateExampleResponse with generated example.
    """
    logger.info(f"Generating {request.quality} example")
    
    try:
        # Try AI generation first
        result = await generate_example(request.quality)
        
        # If AI generation failed, use fallback
        if not result["success"]:
            logger.warning(f"AI generation failed, using fallback: {result['error']}")
            result = get_fallback_example(request.quality)
        
        return GenerateExampleResponse(**result)
        
    except Exception as e:
        logger.error(f"Example generation error: {e}")
        # Return fallback on any error
        fallback = get_fallback_example(request.quality)
        return GenerateExampleResponse(**fallback)
