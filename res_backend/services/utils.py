"""
Utility Functions for LLM Response Handling.

This module provides common utilities for handling LLM responses,
particularly for dealing with different content formats returned by
various LLM providers (e.g., Gemini's structured content).
"""

from typing import Any, Union


def extract_text_from_content(content: Any) -> str:
    """
    Extract text from various LLM response content formats.
    
    Handles:
    - Plain strings
    - Lists of text strings
    - Lists of dicts with {"type": "text", "text": "..."} format (Gemini)
    - None values
    
    Args:
        content: The content attribute from an LLM response.
    
    Returns:
        Extracted text as a single string.
    
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
                # Handle Gemini's structured format: {"type": "text", "text": "..."}
                if part.get("type") == "text":
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
    
    Safely extracts text from response.content, handling various formats.
    
    Args:
        response: LLM response object (e.g., AIMessage, ChatCompletionMessage).
    
    Returns:
        Extracted text as a string.
    """
    if hasattr(response, 'content'):
        return extract_text_from_content(response.content)
    return str(response)
