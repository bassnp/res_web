"""
Streaming Callback Handler for SSE Event Emission.

This module provides a callback implementation that converts agent events
into Server-Sent Events (SSE) format for real-time streaming to the frontend.

The callback implements the ThoughtCallback interface from fit_check_agent.py
and queues events for async consumption by the SSE streaming endpoint.
"""

import asyncio
import json
import logging
from typing import Optional, AsyncGenerator, Any

from services.callbacks import ThoughtCallback

logger = logging.getLogger(__name__)


def format_sse(event_type: str, data: dict) -> str:
    """
    Format data as a Server-Sent Event string.
    
    Args:
        event_type: The SSE event type (status, thought, response, complete, error).
        data: The event data to serialize as JSON.
    
    Returns:
        Properly formatted SSE event string.
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


class StreamingCallbackHandler(ThoughtCallback):
    """
    Callback handler that queues events for SSE streaming.
    
    This class implements the ThoughtCallback interface and provides
    an async generator for consuming events as SSE-formatted strings.
    
    Usage:
        callback = StreamingCallbackHandler()
        
        # In one coroutine: produce events
        await callback.on_status("connecting", "Starting...")
        
        # In another coroutine: consume events
        async for event in callback.events():
            yield event  # SSE-formatted string
    """
    
    def __init__(self, include_thoughts: bool = True):
        """
        Initialize the streaming callback handler.
        
        Args:
            include_thoughts: Whether to emit thought events.
        """
        self._queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._include_thoughts = include_thoughts
        self._completed = False
        self._error_occurred = False
        logger.debug("StreamingCallbackHandler initialized")
    
    async def _emit(self, event_type: str, data: dict) -> None:
        """
        Emit an SSE event by adding it to the queue.
        
        Args:
            event_type: The SSE event type.
            data: The event data.
        """
        if self._completed:
            logger.warning(f"Attempted to emit after completion: {event_type}")
            return
        
        sse_event = format_sse(event_type, data)
        await self._queue.put(sse_event)
        logger.debug(f"Emitted {event_type} event")
    
    async def on_status(self, status: str, message: str) -> None:
        """
        Emit a status event.
        
        Args:
            status: Status code (connecting, researching, analyzing, generating).
            message: Human-readable status message.
        """
        await self._emit("status", {
            "status": status,
            "message": message,
        })
    
    async def on_phase(self, phase: str, message: str) -> None:
        """
        Emit a phase transition event.
        
        Args:
            phase: Phase name (connecting, deep_research, skeptical_comparison, 
                   skills_matching, generate_results).
            message: Human-readable phase start message.
        """
        await self._emit("phase", {
            "phase": phase,
            "message": message,
        })
    
    async def on_phase_complete(self, phase: str, summary: str, data: dict = None) -> None:
        """
        Emit a phase completion event with optional structured data.
        
        Args:
            phase: Phase name that completed.
            summary: Brief summary of phase output.
            data: Optional structured data for frontend display.
        """
        await self._emit("phase_complete", {
            "phase": phase,
            "summary": summary,
            "data": data or {},
        })
    
    async def on_thought(
        self,
        step: int,
        thought_type: str,
        content: str,
        tool: Optional[str] = None,
        tool_input: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> None:
        """
        Emit a thought event (tool_call, observation, or reasoning).
        
        Args:
            step: Sequential step number.
            thought_type: Type of thought (tool_call, observation, reasoning).
            content: Thought content or description.
            tool: Tool name (for tool_call type).
            tool_input: Tool input/query (for tool_call type).
            phase: Current pipeline phase (for grouping in frontend).
        """
        if not self._include_thoughts:
            return
        
        data = {
            "step": step,
            "type": thought_type,
        }
        
        # Add phase for frontend grouping
        if phase:
            data["phase"] = phase
        
        # Add type-specific fields
        if thought_type == "tool_call":
            data["tool"] = tool
            data["input"] = tool_input
        else:
            data["content"] = content
        
        await self._emit("thought", data)
    
    async def on_response_chunk(self, chunk: str) -> None:
        """
        Emit a response chunk event.
        
        Args:
            chunk: Text chunk of the streaming response.
        """
        await self._emit("response", {"chunk": chunk})
    
    async def on_complete(self, duration_ms: int) -> None:
        """
        Emit a complete event and signal end of stream.
        
        Args:
            duration_ms: Total execution time in milliseconds.
        """
        await self._emit("complete", {"duration_ms": duration_ms})
        self._completed = True
        # Signal end of stream
        await self._queue.put(None)
        logger.info(f"Stream completed in {duration_ms}ms")
    
    async def on_error(self, code: str, message: str) -> None:
        """
        Emit an error event and signal end of stream.
        
        Args:
            code: Error code (INVALID_QUERY, AGENT_ERROR, etc.).
            message: Human-readable error message.
        """
        await self._emit("error", {
            "code": code,
            "message": message,
        })
        self._error_occurred = True
        self._completed = True
        # Signal end of stream
        await self._queue.put(None)
        logger.error(f"Stream error: {code} - {message}")
    
    async def events(self) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted events.
        
        Yields:
            SSE-formatted event strings until completion or error.
        """
        while True:
            event = await self._queue.get()
            if event is None:
                # End of stream
                break
            yield event
    
    @property
    def is_completed(self) -> bool:
        """Check if the stream has completed."""
        return self._completed
    
    @property
    def has_error(self) -> bool:
        """Check if an error occurred."""
        return self._error_occurred
