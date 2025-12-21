"""
Pydantic Models for Fit Check API.

This module defines the request/response models for the SSE streaming endpoint.
All models follow the CANONICAL contract specified in PROMPT_TODO_BACKEND_AI_STREAM.md.
"""

from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Scoring Models
# =============================================================================

class SourceType(str, Enum):
    """Classification of source type for extractability scoring."""
    VIDEO = "video"
    SOCIAL_MEDIA = "social_media"
    WIKI = "wiki"
    ACADEMIC = "academic"
    NEWS = "news"
    FORUM = "forum"
    GENERAL = "general"

class DocumentScore(BaseModel):
    """3-dimension score for a single document."""
    document_id: str = Field(..., description="Unique identifier")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Document title")
    snippet: Optional[str] = Field(None, description="Original snippet for fallback")
    
    # 3-Dimension Scores (0.0 - 1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    quality_score: float = Field(..., ge=0.0, le=1.0)
    usefulness_score: float = Field(..., ge=0.0, le=1.0)
    
    # Composite and adjusted scores
    raw_composite: float = Field(..., ge=0.0, le=1.0)
    extractability_multiplier: float = Field(default=1.0, ge=0.0, le=1.5)
    final_score: float = Field(..., ge=0.0, le=1.5)
    
    # Metadata
    source_type: SourceType = Field(default=SourceType.GENERAL)
    scoring_rationale: str = Field(..., description="LLM reasoning for scores")

class ScoringResult(BaseModel):
    """Result of parallel document scoring."""
    scores: List[DocumentScore]
    adaptive_threshold: float = Field(..., ge=0.0, le=1.0)
    passing_count: int
    total_count: int
    social_media_ratio: float = Field(..., ge=0.0, le=1.0)


# =============================================================================
# Request Models
# =============================================================================

class FitCheckRequest(BaseModel):
    """
    Request model for the fit check API endpoint.
    
    Attributes:
        query: Company name or job description (3-2000 characters).
        include_thoughts: Whether to include thinking process in stream.
        model_id: AI model to use for analysis.
        config_type: Configuration type for the model (reasoning or standard).
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
    model_id: Optional[str] = Field(
        default="gemini-3-flash-preview",
        description="AI model ID to use for analysis",
        examples=["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-3-flash-preview"],
    )
    config_type: Optional[Literal["reasoning", "standard"]] = Field(
        default="reasoning",
        description="Configuration type: 'reasoning' for high reasoning models, 'standard' for temperature/topK models",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for request tracing (auto-generated if not provided)",
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


# =============================================================================
# Query Expansion Models
# =============================================================================

class ExpandedQuery(BaseModel):
    """Single CSE-optimized search query."""
    query: str = Field(..., description="The search query string")
    purpose: str = Field(..., description="What this query targets")
    operators_used: List[str] = Field(default_factory=list)


class QueryExpansionResult(BaseModel):
    """Result of query expansion."""
    queries: List[ExpandedQuery] = Field(..., min_length=3, max_length=5)
    expansion_strategy: Literal["company_focus", "job_focus", "hybrid"]
    iteration: int = Field(default=1, ge=1, le=3)


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
