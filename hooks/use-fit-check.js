'use client';

import { useState, useCallback, useRef } from 'react';

/**
 * State machine states for the fit check flow:
 * - idle: User hasn't typed or submitted
 * - ready: User has input, ready to submit
 * - connecting: Establishing SSE connection
 * - thinking: AI is reasoning (show thoughts)
 * - responding: AI is streaming final answer
 * - complete: Full response displayed
 * - error: Error occurred
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom hook for managing the Fit Check AI interaction.
 * Handles SSE streaming, state management, and event processing.
 * 
 * @returns {Object} State and control functions
 */
export function useFitCheck() {
  const [state, setState] = useState({
    status: 'idle',           // Current state machine status
    statusMessage: '',        // Human-readable status message
    thoughts: [],             // Array of thought events for timeline
    response: '',             // Accumulated response text
    error: null,              // Error object if any
    durationMs: null,         // Total duration in milliseconds
  });
  
  const abortControllerRef = useRef(null);
  const startTimeRef = useRef(null);

  /**
   * Reset state to idle for new query
   */
  const reset = useCallback(() => {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    setState({
      status: 'idle',
      statusMessage: '',
      thoughts: [],
      response: '',
      error: null,
      durationMs: null,
    });
  }, []);

  /**
   * Submit query to the backend and process SSE stream
   * @param {string} query - Company name or job description
   */
  const submitQuery = useCallback(async (query) => {
    // Abort any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    startTimeRef.current = Date.now();
    
    // Reset state and set to connecting
    setState({
      status: 'connecting',
      statusMessage: 'Initializing AI agent...',
      thoughts: [],
      response: '',
      error: null,
      durationMs: null,
    });

    try {
      const response = await fetch(`${API_URL}/api/fit-check/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          query: query,
          include_thoughts: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: Request failed`);
      }

      // Process SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE events from buffer
        const { parsed, remaining } = parseSSEBuffer(buffer);
        buffer = remaining;
        
        // Process each parsed event
        for (const event of parsed) {
          processEvent(event, setState, startTimeRef.current);
        }
      }
      
    } catch (error) {
      // Handle abort gracefully
      if (error.name === 'AbortError') {
        return;
      }
      
      console.error('Fit check error:', error);
      setState(prev => ({
        ...prev,
        status: 'error',
        error: {
          code: 'CONNECTION_ERROR',
          message: error.message || 'Failed to connect to the server',
        },
      }));
    }
  }, []);

  return {
    ...state,
    submitQuery,
    reset,
    isLoading: ['connecting', 'thinking', 'responding'].includes(state.status),
  };
}

/**
 * Parse SSE events from buffer, handling partial messages.
 * @param {string} buffer - Raw SSE data buffer
 * @returns {Object} Object with parsed events array and remaining buffer
 */
function parseSSEBuffer(buffer) {
  const events = [];
  const lines = buffer.split('\n');
  let currentEvent = { type: null, data: null };
  let i = 0;
  
  while (i < lines.length) {
    const line = lines[i];
    
    // Empty line signals end of event
    if (line === '') {
      if (currentEvent.type && currentEvent.data) {
        try {
          events.push({
            type: currentEvent.type,
            data: JSON.parse(currentEvent.data),
          });
        } catch (e) {
          console.warn('Failed to parse SSE event data:', currentEvent.data);
        }
      }
      currentEvent = { type: null, data: null };
      i++;
      continue;
    }
    
    // Parse event type
    if (line.startsWith('event:')) {
      currentEvent.type = line.substring(6).trim();
    }
    // Parse event data
    else if (line.startsWith('data:')) {
      currentEvent.data = line.substring(5).trim();
    }
    
    i++;
  }
  
  // Calculate remaining buffer (incomplete event)
  let remaining = '';
  if (currentEvent.type || currentEvent.data) {
    // Reconstruct incomplete event
    const lastEventStart = buffer.lastIndexOf('event:');
    if (lastEventStart !== -1) {
      remaining = buffer.substring(lastEventStart);
    }
  }
  
  return { parsed: events, remaining };
}

/**
 * Process individual SSE events and update state.
 * @param {Object} event - Parsed SSE event { type, data }
 * @param {Function} setState - State setter function
 * @param {number} startTime - Request start timestamp
 */
function processEvent(event, setState, startTime) {
  switch (event.type) {
    case 'status':
      // Update status and message
      setState(prev => ({
        ...prev,
        status: mapStatusToState(event.data.status),
        statusMessage: event.data.message,
      }));
      break;
      
    case 'thought':
      // Add thought to timeline
      setState(prev => ({
        ...prev,
        status: 'thinking',
        thoughts: [...prev.thoughts, {
          ...event.data,
          timestamp: Date.now(),
          status: 'complete', // Mark as complete when received
        }],
      }));
      break;
      
    case 'response':
      // Append response chunk
      setState(prev => ({
        ...prev,
        status: 'responding',
        response: prev.response + event.data.chunk,
      }));
      break;
      
    case 'complete':
      // Stream finished
      setState(prev => ({
        ...prev,
        status: 'complete',
        statusMessage: 'Analysis complete',
        durationMs: event.data.duration_ms || (Date.now() - startTime),
      }));
      break;
      
    case 'error':
      // Handle error
      setState(prev => ({
        ...prev,
        status: 'error',
        error: {
          code: event.data.code,
          message: event.data.message,
        },
      }));
      break;
      
    default:
      console.warn('Unknown SSE event type:', event.type);
  }
}

/**
 * Map backend status values to frontend state machine states.
 * @param {string} backendStatus - Status from backend
 * @returns {string} Frontend state
 */
function mapStatusToState(backendStatus) {
  switch (backendStatus) {
    case 'connecting':
      return 'connecting';
    case 'researching':
    case 'analyzing':
      return 'thinking';
    case 'generating':
      return 'responding';
    default:
      return 'thinking';
  }
}

export default useFitCheck;
