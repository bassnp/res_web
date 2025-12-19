"""
Callback Interface Definitions for Streaming Events.

This module defines the base callback interface used by pipeline nodes
to emit SSE events. Placed in a separate module to avoid circular imports.
"""

from typing import Optional


class ThoughtCallback:
    """
    Callback interface for streaming agent thoughts.
    
    Implement this to receive real-time updates about agent progress.
    """
    
    async def on_status(self, status: str, message: str) -> None:
        """Called when agent status changes."""
        pass
    
    async def on_phase(self, phase: str, message: str) -> None:
        """Called when a pipeline phase starts."""
        pass
    
    async def on_phase_complete(self, phase: str, summary: str, data: Optional[dict] = None) -> None:
        """Called when a pipeline phase completes."""
        pass
    
    async def on_thought(
        self,
        step: int,
        thought_type: str,
        content: str,
        tool: Optional[str] = None,
        tool_input: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> None:
        """Called when agent has a thought (tool_call, observation, or reasoning)."""
        pass
    
    async def on_response_chunk(self, chunk: str) -> None:
        """Called when streaming response text."""
        pass
    
    async def on_complete(self, duration_ms: int) -> None:
        """Called when agent completes."""
        pass
    
    async def on_error(self, code: str, message: str) -> None:
        """Called when an error occurs."""
        pass
