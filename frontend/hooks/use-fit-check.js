'use client';

import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import { parseAIResponse } from '@/lib/parseAIResponse';
import { useAISettings } from './use-ai-settings';

/**
 * Generate a unique session ID for request tracing.
 * Uses crypto.randomUUID() if available, falls back to custom implementation.
 * 
 * @returns {string} UUID v4 format string
 */
function generateSessionId() {
  // Modern browsers support crypto.randomUUID()
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  // Fallback for older browsers
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Retry configuration
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY_MS = 1000;
const MAX_RETRY_DELAY_MS = 10000;
const RETRY_BACKOFF_MULTIPLIER = 2;

// Retryable error codes/patterns
const RETRYABLE_ERRORS = [
  'ECONNRESET',
  'ETIMEDOUT',
  'NetworkError',
  'Failed to fetch',
  'network error',
  'connection reset',
];

/**
 * Check if an error is retryable.
 * @param {Error} error - The error to check
 * @returns {boolean} True if the error is transient and retryable
 */
function isRetryableError(error) {
  if (error.name === 'AbortError') {
    return false; // User-initiated cancellation
  }
  
  const errorMessage = error.message?.toLowerCase() || '';
  return RETRYABLE_ERRORS.some(pattern => 
    errorMessage.includes(pattern.toLowerCase())
  );
}

/**
 * Calculate retry delay with exponential backoff and jitter.
 * @param {number} attempt - Current attempt number (1-indexed)
 * @returns {number} Delay in milliseconds
 */
function getRetryDelay(attempt) {
  const delay = INITIAL_RETRY_DELAY_MS * Math.pow(RETRY_BACKOFF_MULTIPLIER, attempt - 1);
  const jitter = Math.random() * 0.3 * delay; // Add 0-30% jitter
  return Math.min(delay + jitter, MAX_RETRY_DELAY_MS);
}

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
 * - content_enrich: Full content extraction from top sources
 * - skeptical_comparison: Critical gap analysis
 * - skills_matching: Skill-to-requirement mapping
 * - confidence_reranker: LLM-as-Judge confidence calibration
 * - generate_results: Final response synthesis
 */

import { API_BASE_URL } from '@/lib/profile-data';

const API_URL = process.env.NEXT_PUBLIC_API_URL || API_BASE_URL;

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
 * Integrates with AI settings for model selection.
 * 
 * @returns {Object} State and control functions
 */
export function useFitCheck() {
  // Get AI model settings from context
  const { getModelConfig } = useAISettings();
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
    sessionId: null,          // Track current session ID
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
  
  // Add derived state for final confidence results
  const finalConfidence = useMemo(() => {
    if (state.status !== 'complete') return null;
    
    const confidencePhase = state.phaseHistory.find(
      p => p.phase === 'confidence_reranker' && p.status === 'complete'
    );
    
    if (!confidencePhase?.data) return null;
    
    return {
      score: confidencePhase.data.calibrated_score,
      tier: confidencePhase.data.tier,
      flags: confidencePhase.data.quality_flags || [],
      adjustment: confidencePhase.data.adjustment_rationale,
    };
  }, [state.status, state.phaseHistory]);
  
  const abortControllerRef = useRef(null);
  const startTimeRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

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
      sessionId: null,
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
    const sessionId = generateSessionId();
    
    // Get current model configuration
    const modelConfig = getModelConfig();
    
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
      sessionId,
    });

    try {
      const response = await fetch(`${API_URL}/api/fit-check/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'X-Session-ID': sessionId,
        },
        body: JSON.stringify({
          query: query,
          include_thoughts: true,
          model_id: modelConfig.model_id,
          config_type: modelConfig.config_type,
          session_id: sessionId,
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
  }, [getModelConfig]);

  /**
   * Submit query with automatic retry on transient failures.
   * @param {string} query - The query to submit
   * @param {number} attempt - Current attempt number (internal use)
   */
  const submitQueryWithRetry = useCallback(async (query, attempt = 1) => {
    try {
      await submitQuery(query);
    } catch (error) {
      // Don't retry user cancellations
      if (error.name === 'AbortError') {
        return;
      }
      
      // Check if we should retry
      if (attempt < MAX_RETRIES && isRetryableError(error)) {
        const delay = getRetryDelay(attempt);
        console.log(
          `[${state.sessionId}] Retry attempt ${attempt}/${MAX_RETRIES} in ${delay}ms`,
          error.message
        );
        
        // Update state to show retry status
        setState(prev => ({
          ...prev,
          status: 'connecting',
          statusMessage: `Connection failed. Retrying (${attempt}/${MAX_RETRIES})...`,
        }));
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Recursive retry
        return submitQueryWithRetry(query, attempt + 1);
      }
      
      // Max retries exceeded or non-retryable error
      console.error(`[${state.sessionId}] Request failed after ${attempt} attempts:`, error);
      setState(prev => ({
        ...prev,
        status: 'error',
        error: {
          code: 'CONNECTION_ERROR',
          message: attempt > 1 
            ? `Failed after ${attempt} attempts: ${error.message}`
            : error.message || 'Failed to connect to the server',
          retryable: isRetryableError(error),
        },
      }));
    }
  }, [submitQuery, state.sessionId]);

  return {
    ...state,
    uiPhase,
    parsedResponse,
    finalConfidence,
    submitQuery: submitQueryWithRetry,
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
                data: event.data.data || null, // Store structured data
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
