"""
Utility Functions for LLM Response Handling.

This module provides common utilities for handling LLM responses,
particularly for dealing with different content formats returned by
various LLM providers (e.g., Gemini's structured content with thinking).
"""

from typing import Any, Union
import logging

logger = logging.getLogger(__name__)


def extract_text_from_content(content: Any) -> str:
    """
    Extract text from various LLM response content formats.
    
    Handles:
    - Plain strings
    - Lists of text strings
    - Lists of dicts with {"type": "text", "text": "..."} format (Gemini)
    - Lists of dicts with {"type": "thinking", ...} format (Gemini reasoning)
    - None values
    
    Args:
        content: The content attribute from an LLM response.
    
    Returns:
        Extracted text as a single string (excludes thinking content).
    
    Examples:
        >>> extract_text_from_content("Hello world")
        "Hello world"
        
        >>> extract_text_from_content([{"type": "text", "text": "Hello"}])
        "Hello"
        
        >>> extract_text_from_content(["Hello", "world"])
        "Helloworld"
    """
    if content is None:
        return ""
    
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type", "")
                
                # Skip thinking/reasoning content - we only want the final answer
                if part_type == "thinking":
                    logger.debug("Skipping thinking content block")
                    continue
                
                # Handle Gemini's structured format: {"type": "text", "text": "..."}
                if part_type == "text":
                    text_parts.append(str(part.get("text", "")))
                elif "text" in part:
                    text_parts.append(str(part["text"]))
            elif isinstance(part, str):
                text_parts.append(part)
            else:
                # Fallback: convert to string
                text_parts.append(str(part))
        return "".join(text_parts)
    
    # Fallback: convert to string
    return str(content)


def get_response_text(response: Any) -> str:
    """
    Get text content from an LLM response object.
    
    Safely extracts text from response.content, handling various formats
    including Gemini's thinking/reasoning models that return structured content.
    
    Args:
        response: LLM response object (e.g., AIMessage, ChatCompletionMessage).
    
    Returns:
        Extracted text as a string.
    """
    if hasattr(response, 'content'):
        text = extract_text_from_content(response.content)
        if text:
            return text
        
        # Fallback: check for text in additional_kwargs (some models put it there)
        if hasattr(response, 'additional_kwargs'):
            kwargs = response.additional_kwargs
            if isinstance(kwargs, dict):
                # Check for text in various possible locations
                if 'text' in kwargs:
                    return str(kwargs['text'])
                if 'content' in kwargs:
                    return extract_text_from_content(kwargs['content'])
        
        # Log warning if we couldn't extract text
        logger.warning(f"Could not extract text from response. Content type: {type(response.content)}, Content: {str(response.content)[:200]}")
        return ""
    
    return str(response)
