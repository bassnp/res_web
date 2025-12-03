'use client';

import { useState, useCallback, useRef, useMemo } from 'react';
import { parseAIResponse } from '@/lib/parseAIResponse';

/**
 * State machine states for the fit check flow:
 * - idle: User hasn't typed or submitted
 * - ready: User has input, ready to submit
 * - connecting: Establishing SSE connection
 * - thinking: AI is reasoning (show thoughts)
 * - responding: AI is streaming final answer
 * - complete: Full response displayed
 * - error: Error occurred
 * 
 * UI Phases (derived from status):
 * - input: Idle state, single input container visible
 * - expanded: Thinking/responding, horizontal two-column layout
 * - results: Complete, show pros/cons cards below
 * 
 * Pipeline Phases (from backend):
 * - connecting: Query classification and entity extraction
 * - deep_research: Web search and intelligence gathering
 * - research_reranker: Research quality gate and data validation
 * - skeptical_comparison: Critical gap analysis
 * - skills_matching: Skill-to-requirement mapping
 * - confidence_reranker: LLM-as-Judge confidence calibration
 * - generate_results: Final response synthesis
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Phase entry structure for tracking pipeline progress.
 * @typedef {Object} PhaseEntry
 * @property {string} phase - Phase name (connecting, deep_research, etc.)
 * @property {string} message - Phase start message
 * @property {string|null} summary - Phase completion summary
 * @property {number} startTime - Timestamp when phase started
 * @property {number|null} endTime - Timestamp when phase completed
 * @property {'active'|'complete'|'error'} status - Phase status
 */

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
    
    // Phase tracking for new pipeline
    currentPhase: null,       // Currently active phase name
    phaseHistory: [],         // Array of completed phase objects
    phaseProgress: {},        // Map of phase -> status (pending/active/complete)
  });
  
  // Derive UI phase from status
  const uiPhase = useMemo(() => {
    switch (state.status) {
      case 'idle':
        return 'input';
      case 'connecting':
      case 'thinking':
      case 'responding':
        return 'expanded';
      case 'complete':
        return 'results';
      case 'error':
        return state.thoughts.length > 0 ? 'expanded' : 'input';
      default:
        return 'input';
    }
  }, [state.status, state.thoughts.length]);

  // Parse response into structured data for pros/cons cards
  const parsedResponse = useMemo(() => {
    if (!state.response || state.status !== 'complete') {
      return null;
    }
    return parseAIResponse(state.response);
  }, [state.response, state.status]);
  
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
      currentPhase: null,
      phaseHistory: [],
      phaseProgress: {},
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
      currentPhase: null,
      phaseHistory: [],
      phaseProgress: {},
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
    uiPhase,
    parsedResponse,
    submitQuery,
    reset,
    isLoading: ['connecting', 'thinking', 'responding'].includes(state.status),
  };
}

/**
 * Get thoughts filtered by a specific phase.
 * @param {Array} thoughts - All thoughts
 * @param {string} phase - Phase to filter by
 * @returns {Array} Filtered thoughts
 */
export function getThoughtsByPhase(thoughts, phase) {
  return thoughts.filter(t => t.phase === phase);
}

/**
 * Get all unique phases from thoughts.
 * @param {Array} thoughts - All thoughts
 * @returns {Array} Unique phase names
 */
export function getUniquePhasesFromThoughts(thoughts) {
  return [...new Set(thoughts.map(t => t.phase).filter(Boolean))];
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
    // NEW: Phase transition event
    case 'phase':
      setState(prev => ({
        ...prev,
        currentPhase: event.data.phase,
        statusMessage: event.data.message,
        phaseProgress: {
          ...prev.phaseProgress,
          [event.data.phase]: 'active',
        },
        phaseHistory: [
          ...prev.phaseHistory,
          {
            phase: event.data.phase,
            message: event.data.message,
            summary: null,
            startTime: Date.now(),
            endTime: null,
            status: 'active',
          },
        ],
      }));
      break;

    // NEW: Phase completion event
    case 'phase_complete':
      setState(prev => ({
        ...prev,
        phaseProgress: {
          ...prev.phaseProgress,
          [event.data.phase]: 'complete',
        },
        phaseHistory: prev.phaseHistory.map(entry =>
          entry.phase === event.data.phase && entry.status === 'active'
            ? {
                ...entry,
                summary: event.data.summary,
                endTime: Date.now(),
                status: 'complete',
              }
            : entry
        ),
      }));
      break;
      
    case 'status':
      // Update status and message
      setState(prev => ({
        ...prev,
        status: mapStatusToState(event.data.status),
        statusMessage: event.data.message,
      }));
      break;
      
    case 'thought':
      // Add thought to timeline with phase info
      setState(prev => ({
        ...prev,
        status: 'thinking',
        thoughts: [...prev.thoughts, {
          ...event.data,
          phase: event.data.phase || prev.currentPhase, // Include phase
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
      // Handle error with phase tracking
      setState(prev => ({
        ...prev,
        status: 'error',
        error: {
          code: event.data.code,
          message: event.data.message,
        },
        phaseProgress: prev.currentPhase
          ? {
              ...prev.phaseProgress,
              [prev.currentPhase]: 'error',
            }
          : prev.phaseProgress,
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
