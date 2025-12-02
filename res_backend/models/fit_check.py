"""
Pydantic Models for Fit Check API.

This module defines the request/response models for the SSE streaming endpoint.
All models follow the CANONICAL contract specified in PROMPT_TODO_BACKEND_AI_STREAM.md.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================

class FitCheckRequest(BaseModel):
    """
    Request model for the fit check API endpoint.
    
    Attributes:
        query: Company name or job description (3-2000 characters).
        include_thoughts: Whether to include thinking process in stream.
    """
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Company name or job description to analyze fit against",
        examples=["Google", "Senior Software Engineer at Stripe working on payment infrastructure"],
    )
    include_thoughts: bool = Field(
        default=True,
        description="Whether to include detailed thinking process in the stream",
    )


# =============================================================================
# SSE Event Models (CANONICAL FORMAT)
# =============================================================================

class StatusEvent(BaseModel):
    """
    Status update event - indicates current agent phase.
    
    Status values (CANONICAL):
        - connecting: Initial connection, agent starting up
        - researching: Agent is performing web searches
        - analyzing: Agent is analyzing skills/experience match
        - generating: Agent is generating final response
    """
    status: Literal["connecting", "researching", "analyzing", "generating"]
    message: str = Field(
        ...,
        description="Human-readable status message",
    )


class ThoughtEvent(BaseModel):
    """
    AI thinking step event - represents one step in the reasoning process.
    
    Thought types (CANONICAL):
        - tool_call: Agent is invoking a tool
        - observation: Tool returned results
        - reasoning: Agent is reasoning about data
    
    Tool names (CANONICAL):
        - web_search: Web search via Google CSE
        - analyze_skill_match: Skill alignment analysis
        - analyze_experience_relevance: Experience relevance analysis
    """
    step: int = Field(
        ...,
        ge=1,
        description="Sequential step number in the reasoning process",
    )
    type: Literal["tool_call", "observation", "reasoning"] = Field(
        ...,
        description="Type of thought",
    )
    tool: Optional[str] = Field(
        default=None,
        description="Tool name (only for tool_call type)",
    )
    input: Optional[str] = Field(
        default=None,
        description="Tool input/query (only for tool_call type)",
    )
    content: Optional[str] = Field(
        default=None,
        description="Thought content (for observation and reasoning types)",
    )


class ResponseEvent(BaseModel):
    """Response text chunk event - streaming response content."""
    chunk: str = Field(
        ...,
        description="Text chunk of the streaming response",
    )


class CompleteEvent(BaseModel):
    """Stream complete event - signals successful completion."""
    duration_ms: int = Field(
        ...,
        ge=0,
        description="Total execution time in milliseconds",
    )


class ErrorEvent(BaseModel):
    """
    Error event - signals an error occurred.
    
    Error codes (CANONICAL):
        - INVALID_QUERY: Query too short or too long (400)
        - RATE_LIMITED: Too many requests (429)
        - AGENT_ERROR: AI agent execution failed (500)
        - SEARCH_ERROR: Web search tool failed (502)
        - LLM_ERROR: Gemini API unavailable (503)
        - TIMEOUT: Agent execution timed out (504)
    """
    code: Literal[
        "INVALID_QUERY",
        "RATE_LIMITED",
        "AGENT_ERROR",
        "SEARCH_ERROR",
        "LLM_ERROR",
        "TIMEOUT",
    ] = Field(
        ...,
        description="Error code for programmatic handling",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
