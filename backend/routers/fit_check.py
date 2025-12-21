"""
Fit Check Router - SSE Streaming Endpoint for AI Fit Analysis.

This module provides the POST /api/fit-check/stream endpoint that:
1. Validates incoming employer queries
2. Initiates the AI agent analysis
3. Streams real-time status, thoughts, and response via SSE

SSE Event Types (CANONICAL):
    - status: Agent status updates
    - thought: AI reasoning steps (tool_call, observation, reasoning)
    - response: Response text chunks
    - complete: Stream finished successfully
    - error: Error occurred
"""

import asyncio
import logging
import time
import uuid
from typing import AsyncGenerator, Optional

from async_timeout import timeout as async_timeout
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from models.fit_check import (
    FitCheckRequest,
    StatusEvent,
    ThoughtEvent,
    ResponseEvent,
    CompleteEvent,
    ErrorEvent,
)
from services.fit_check_agent import get_agent
from services.streaming_callback import StreamingCallbackHandler, format_sse
from services.metrics import (
    track_request_start,
    track_request_end,
    ACTIVE_SESSIONS,
    PROMETHEUS_AVAILABLE,
)

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/fit-check",
    tags=["Fit Check"],
    responses={
        400: {"description": "Invalid query"},
        429: {"description": "Rate limited"},
        500: {"description": "Server error"},
    },
)


# =============================================================================
# SSE Streaming Endpoint
# =============================================================================

# Request timeout in seconds (5 minutes)
REQUEST_TIMEOUT_SECONDS = 300

@router.post(
    "/stream",
    summary="Stream AI fit analysis via SSE",
    description="""
    Executes an AI agent to analyze fit between an employer's query
    (company name or job description) and the engineer's profile.
    
    Returns a Server-Sent Events (SSE) stream with real-time updates
    about the agent's thinking process and final response.
    
    **SSE Event Types:**
    - `status`: Agent status updates (connecting, researching, analyzing, generating)
    - `thought`: AI reasoning steps (tool_call, observation, reasoning)
    - `response`: Streaming response text chunks
    - `complete`: Stream finished successfully with duration
    - `error`: Error occurred with code and message
    """,
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "SSE stream of AI analysis",
            "content": {
                "text/event-stream": {
                    "example": 'event: status\ndata: {"status": "connecting", "message": "Initializing AI agent..."}\n\n'
                }
            },
        },
    },
)
async def stream_fit_check(
    request: FitCheckRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Stream AI fit analysis via Server-Sent Events.
    
    Args:
        request: FitCheckRequest with query and options.
        x_session_id: Optional session ID from header for tracing.
    
    Returns:
        StreamingResponse with SSE events.
    """
    # Generate session ID for tracing if not provided
    # Priority: Request Body > Header > Auto-generated
    session_id = request.session_id or x_session_id or str(uuid.uuid4())
    
    # Track request start
    track_request_start()
    start_time = time.time()
    request_status = "success"
    
    logger.info(
        f"[{session_id}] Received fit check request: query={request.query[:50]}..., "
        f"model={request.model_id}, config_type={request.config_type}",
        extra={
            "session_id": session_id,
            "query_length": len(request.query),
            "model_id": request.model_id,
            "config_type": request.config_type
        }
    )
    
    # Create callback handler with session ID
    callback = StreamingCallbackHandler(
        include_thoughts=request.include_thoughts,
        session_id=session_id
    )
    
    async def generate_events() -> AsyncGenerator[str, None]:
        """
        Async generator that produces SSE events.
        
        This runs the agent and streams events via the callback.
        """
        nonlocal request_status
        agent = get_agent()
        
        try:
            # Wrap entire execution with timeout
            async with async_timeout(REQUEST_TIMEOUT_SECONDS):
                # Run the agent in a separate task so we can stream events concurrently
                async def run_agent():
                    nonlocal request_status
                    try:
                        # Collect response chunks (they're also emitted via callback)
                        async for chunk in agent.stream_analysis(
                            query=request.query,
                            callback=callback,
                            model_id=request.model_id,
                            config_type=request.config_type,
                        ):
                            pass  # Response chunks are handled by callback
                    except asyncio.CancelledError:
                        request_status = "cancelled"
                        logger.warning(f"[{session_id}] Agent task cancelled")
                        if not callback.is_completed:
                            await callback.on_error("CANCELLED", "Request was cancelled")
                    except Exception as e:
                        request_status = "error"
                        logger.error(f"[{session_id}] Agent error: {e}")
                        if not callback.is_completed:
                            # Map exception to appropriate error code
                            error_code = _map_exception_to_code(e)
                            await callback.on_error(error_code, str(e))
                
                # Start agent task
                agent_task = asyncio.create_task(run_agent())
                
                # Stream events from callback
                try:
                    async for event in callback.events():
                        yield event
                except asyncio.CancelledError:
                    request_status = "cancelled"
                    agent_task.cancel()
                    raise
                
                # Wait for agent to complete
                await agent_task
                
        except asyncio.TimeoutError:
            request_status = "timeout"
            logger.error(f"[{session_id}] Request timed out after {REQUEST_TIMEOUT_SECONDS}s")
            if not callback.is_completed:
                yield format_sse("error", {
                    "code": "TIMEOUT",
                    "message": f"Request exceeded {REQUEST_TIMEOUT_SECONDS} second limit",
                })
        except asyncio.CancelledError:
            request_status = "cancelled"
            logger.info(f"[{session_id}] Stream cancelled by client")
            raise
        except Exception as e:
            request_status = "error"
            logger.error(f"[{session_id}] Stream generation error: {e}")
            # Emit error if not already completed
            if not callback.is_completed:
                error_code = _map_exception_to_code(e)
                yield format_sse("error", {
                    "code": error_code,
                    "message": str(e),
                })
        finally:
            # Track request end
            duration = time.time() - start_time
            track_request_end(request_status, duration)
            logger.info(
                f"[{session_id}] Request completed",
                extra={
                    "session_id": session_id,
                    "status": request_status,
                    "duration_ms": int(duration * 1000),
                }
            )
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# =============================================================================
# Health Check for Fit Check Service
# =============================================================================

@router.get(
    "/health",
    summary="Fit Check service health",
    description="Check if the Fit Check service is ready to handle requests.",
)
async def fit_check_health():
    """
    Health check specific to the Fit Check service.
    
    Returns:
        dict: Service health status.
    """
    # Check if agent can be instantiated
    try:
        agent = get_agent()
        
        # Get active session count from metrics if available
        active_count = 0
        if PROMETHEUS_AVAILABLE:
            # Accessing internal value for health check display
            active_count = int(ACTIVE_SESSIONS._value.get())
            
        return {
            "status": "healthy",
            "service": "fit-check",
            "agent_ready": agent is not None,
            "active_sessions": active_count,
        }
    except Exception as e:
        logger.error(f"Fit Check health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "fit-check",
            "error": str(e),
        }


# =============================================================================
# Helper Functions
# =============================================================================

def _map_exception_to_code(exception: Exception) -> str:
    """
    Map an exception to the appropriate error code.
    
    Args:
        exception: The exception to map.
    
    Returns:
        str: Error code (AGENT_ERROR, SEARCH_ERROR, LLM_ERROR, TIMEOUT).
    """
    error_str = str(exception).lower()
    exception_type = type(exception).__name__.lower()
    
    # Check for timeout
    if "timeout" in error_str or "timed out" in error_str:
        return "TIMEOUT"
    
    # Check for search/tool errors
    if "search" in error_str or "tool" in error_str or "cse" in error_str:
        return "SEARCH_ERROR"
    
    # Check for LLM errors
    if any(term in error_str for term in ["gemini", "llm", "model", "api", "quota", "rate"]):
        return "LLM_ERROR"
    
    # Check for validation errors
    if "validation" in error_str or isinstance(exception, ValidationError):
        return "INVALID_QUERY"
    
    # Default to agent error
    return "AGENT_ERROR"
