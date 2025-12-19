"""
Centralized Error Handling for Fit Check Pipeline.

Provides:
- Error classification (recoverable vs fatal)
- Error context preservation
- User-friendly error messages
"""

from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error classification for routing decisions."""
    RECOVERABLE = "recoverable"  # Retry may succeed
    FATAL = "fatal"              # No point retrying
    EXTERNAL = "external"        # External service issue
    VALIDATION = "validation"    # Bad input


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.FATAL,
        phase: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.category = category
        self.phase = phase
        self.context = context or {}
    
    @property
    def is_recoverable(self) -> bool:
        return self.category == ErrorCategory.RECOVERABLE
    
    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        messages = {
            ErrorCategory.RECOVERABLE: "Temporary issue occurred. Please try again.",
            ErrorCategory.FATAL: "Unable to complete the analysis.",
            ErrorCategory.EXTERNAL: "External service is temporarily unavailable.",
            ErrorCategory.VALIDATION: "Please check your input and try again.",
        }
        return messages.get(self.category, str(self))


# Specific error types
class SearchError(PipelineError):
    """Web search failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.EXTERNAL, **kwargs)


class ScoringError(PipelineError):
    """Document scoring failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RECOVERABLE, **kwargs)


class EnrichmentError(PipelineError):
    """Content enrichment failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RECOVERABLE, **kwargs)


class LLMError(PipelineError):
    """LLM API call failed."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.EXTERNAL, **kwargs)


def handle_node_error(
    error: Exception,
    phase: str,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle errors at node level, returning appropriate state update.
    
    Args:
        error: The exception that occurred.
        phase: Current pipeline phase.
        state: Current pipeline state.
    
    Returns:
        State update dict with error information.
    """
    logger.error(f"Error in {phase}: {error}", exc_info=True)
    
    # Build error context
    error_info = {
        "phase": phase,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    # Determine if recoverable
    if isinstance(error, PipelineError):
        is_recoverable = error.is_recoverable
        user_message = error.to_user_message()
    else:
        is_recoverable = False
        user_message = "An unexpected error occurred."
    
    # Add to processing errors list
    existing_errors = state.get("processing_errors", [])
    existing_errors.append(error_info)
    
    return {
        "processing_errors": existing_errors,
        "error": str(error) if not is_recoverable else None,
        "should_abort": not is_recoverable,
        "abort_reason": user_message if not is_recoverable else None,
    }
