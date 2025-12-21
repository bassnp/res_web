````markdown
# Phase 5: Frontend Enhancements Implementation Guide

> **Priority:** 🟢 LOW (Nice-to-have)  
> **Estimated Time:** 1-2 hours  
> **Prerequisite:** Phase 1 complete (Phases 2-4 optional)  
> **Risk if Skipped:** Minor UX issues, no critical functionality loss

---

## Overview

This phase improves client-side session management, error resilience, and user experience. These are quality-of-life enhancements that make the frontend more robust when dealing with the multi-session backend.

### Scope

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| Session ID Tracking | Correlate logs/events | UUID generation, header |
| Reconnection Logic | Handle transient failures | Retry with backoff |
| Connection State UI | User feedback | Visual indicators |
| Error Recovery | Graceful degradation | Contextual error messages |
| Cleanup on Unmount | Prevent memory leaks | AbortController cleanup |

---

## Prerequisites

- [ ] Phase 1 (Session Isolation) complete on backend
- [ ] Frontend development environment running
- [ ] Understanding of React hooks and SSE

---

## Implementation Checklist

### Step 1: Add Session ID Generation

**File:** `frontend/hooks/use-fit-check.js`

#### 1.1 Add UUID Generation Utility

```javascript
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
```

#### 1.2 Update State to Include Session ID

```javascript
const [state, setState] = useState({
  status: 'idle',
  statusMessage: '',
  thoughts: [],
  response: '',
  error: null,
  durationMs: null,
  currentPhase: null,
  phaseHistory: [],
  phaseProgress: {},
  sessionId: null,  // NEW: Track current session ID
});
```

#### 1.3 Generate and Send Session ID

In the `submitQuery` function:

```javascript
const submitQuery = useCallback(async (query) => {
  // Abort any previous request
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
  }
  
  // Create new abort controller and session ID
  abortControllerRef.current = new AbortController();
  startTimeRef.current = Date.now();
  const sessionId = generateSessionId();  // NEW
  
  // Get current model configuration
  const modelConfig = getModelConfig();
  
  // Reset state with new session ID
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
    sessionId,  // NEW: Store session ID in state
  });
  
  try {
    const response = await fetch(`${API_URL}/api/fit-check/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'X-Session-ID': sessionId,  // NEW: Send in header for correlation
      },
      body: JSON.stringify({
        query: query,
        include_thoughts: true,
        model_id: modelConfig.model_id,
        config_type: modelConfig.config_type,
        session_id: sessionId,  // NEW: Also in body for backend processing
      }),
      signal: abortControllerRef.current.signal,
    });
    // ... rest of handler
```

- [ ] **TODO:** Add `generateSessionId()` function
- [ ] **TODO:** Add `sessionId` to state
- [ ] **TODO:** Generate ID in `submitQuery()`
- [ ] **TODO:** Send ID in both header and body

---

### Step 2: Add Retry Logic with Exponential Backoff

**File:** `frontend/hooks/use-fit-check.js`

#### 2.1 Define Retry Constants

```javascript
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
```

#### 2.2 Add Retry Helper Function

```javascript
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
```

#### 2.3 Wrap Submit with Retry Logic

```javascript
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
```

#### 2.4 Export Retry-Enabled Submit

Update the return statement to expose the retry version:

```javascript
return {
  ...state,
  uiPhase,
  parsedResponse,
  finalConfidence,
  submitQuery: submitQueryWithRetry,  // Use retry-enabled version
  reset,
  isLoading: ['connecting', 'thinking', 'responding'].includes(state.status),
};
```

- [ ] **TODO:** Add retry constants
- [ ] **TODO:** Add `isRetryableError()` function
- [ ] **TODO:** Add `getRetryDelay()` function
- [ ] **TODO:** Create `submitQueryWithRetry()` wrapper
- [ ] **TODO:** Export retry-enabled version

---

### Step 3: Add Connection State UI Feedback

**File:** `frontend/components/fit-check/InputPanel.jsx`

#### 3.1 Add Retry Indicator

```jsx
import { RefreshCw, AlertCircle, Loader2 } from 'lucide-react';

function ConnectionStatusIndicator({ status, statusMessage, error }) {
  if (status === 'connecting' && statusMessage?.includes('Retrying')) {
    return (
      <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
        <RefreshCw className="h-4 w-4 animate-spin" />
        <span>{statusMessage}</span>
      </div>
    );
  }
  
  if (status === 'connecting') {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>{statusMessage || 'Connecting...'}</span>
      </div>
    );
  }
  
  if (status === 'error' && error?.retryable) {
    return (
      <div className="flex items-center gap-2 text-sm text-destructive">
        <AlertCircle className="h-4 w-4" />
        <span>Connection lost. Please try again.</span>
      </div>
    );
  }
  
  return null;
}
```

#### 3.2 Integrate into InputPanel

```jsx
export function InputPanel({ 
  status, 
  statusMessage,
  error,
  onSubmit, 
  // ... other props 
}) {
  return (
    <div className="space-y-4">
      {/* Existing input form */}
      
      {/* Connection status indicator */}
      <ConnectionStatusIndicator 
        status={status}
        statusMessage={statusMessage}
        error={error}
      />
      
      {/* Existing submit button */}
    </div>
  );
}
```

- [ ] **TODO:** Create `ConnectionStatusIndicator` component
- [ ] **TODO:** Add retry animation styles
- [ ] **TODO:** Integrate into InputPanel

---

### Step 4: Add Proper Cleanup on Component Unmount

**File:** `frontend/hooks/use-fit-check.js`

#### 4.1 Add Cleanup Effect

```javascript
// Cleanup on unmount
useEffect(() => {
  return () => {
    // Abort any ongoing request when component unmounts
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };
}, []);
```

#### 4.2 Enhance Reset Function

```javascript
const reset = useCallback(() => {
  // Abort any ongoing request
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
    abortControllerRef.current = null;
  }
  
  // Clear any pending timeouts (if using retry)
  // Note: In a full implementation, store timeout IDs in refs
  
  // Reset state completely
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
  
  // Clear refs
  startTimeRef.current = null;
}, []);
```

- [ ] **TODO:** Add cleanup effect with dependency array
- [ ] **TODO:** Enhance reset to clear all refs
- [ ] **TODO:** Verify no memory leaks on rapid mount/unmount

---

### Step 5: Add Enhanced Error Messages

**File:** `frontend/lib/errorMessages.js` (new file)

```javascript
/**
 * User-friendly error messages for common error codes.
 * 
 * Maps backend error codes to actionable user messages.
 */

export const ERROR_MESSAGES = {
  // Connection errors
  CONNECTION_ERROR: {
    title: 'Connection Failed',
    message: 'Unable to reach the server. Please check your internet connection.',
    action: 'Try Again',
    retryable: true,
  },
  
  TIMEOUT: {
    title: 'Request Timeout',
    message: 'The analysis took too long. The query might be too complex.',
    action: 'Try Simpler Query',
    retryable: true,
  },
  
  CANCELLED: {
    title: 'Request Cancelled',
    message: 'The request was cancelled.',
    action: null,
    retryable: false,
  },
  
  // Backend errors
  INVALID_QUERY: {
    title: 'Invalid Query',
    message: 'Please enter a valid company name or job description.',
    action: 'Edit Query',
    retryable: false,
  },
  
  AGENT_ERROR: {
    title: 'Analysis Error',
    message: 'An error occurred during analysis. Please try again.',
    action: 'Try Again',
    retryable: true,
  },
  
  PIPELINE_ERROR: {
    title: 'Processing Error',
    message: 'An error occurred in the analysis pipeline.',
    action: 'Try Again',
    retryable: true,
  },
  
  RATE_LIMITED: {
    title: 'Too Many Requests',
    message: 'Please wait a moment before trying again.',
    action: 'Wait',
    retryable: true,
  },
  
  // Fallback
  UNKNOWN: {
    title: 'Unexpected Error',
    message: 'Something went wrong. Please try again later.',
    action: 'Try Again',
    retryable: true,
  },
};

/**
 * Get user-friendly error info for an error code.
 * @param {string} code - Error code from backend
 * @param {string} fallbackMessage - Optional fallback message
 * @returns {Object} Error info with title, message, action, retryable
 */
export function getErrorInfo(code, fallbackMessage = null) {
  const info = ERROR_MESSAGES[code] || ERROR_MESSAGES.UNKNOWN;
  
  return {
    ...info,
    message: fallbackMessage || info.message,
    code,
  };
}
```

#### 5.1 Integrate Error Messages in Hook

```javascript
import { getErrorInfo } from '@/lib/errorMessages';

// In processEvent function, update error handling:
case 'error':
  const errorInfo = getErrorInfo(event.data.code, event.data.message);
  setState(prev => ({
    ...prev,
    status: 'error',
    error: {
      code: event.data.code,
      message: event.data.message,
      ...errorInfo,  // Add title, action, retryable
    },
    // ... rest
  }));
  break;
```

- [ ] **TODO:** Create `lib/errorMessages.js`
- [ ] **TODO:** Define all error codes and messages
- [ ] **TODO:** Integrate in SSE event processing

---

### Step 6: Add Error Display Component

**File:** `frontend/components/fit-check/ErrorDisplay.jsx` (new file)

```jsx
'use client';

import { AlertCircle, RefreshCw, ArrowLeft, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * Error display component for fit check failures.
 * Shows contextual error information with appropriate actions.
 */
export function ErrorDisplay({ error, onRetry, onReset, className }) {
  if (!error) return null;
  
  const { title, message, action, retryable, code } = error;
  
  // Choose icon based on error type
  const Icon = code === 'TIMEOUT' ? Clock : AlertCircle;
  
  return (
    <div
      className={cn(
        'rounded-lg border border-destructive/50 bg-destructive/5 p-6',
        className
      )}
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <Icon className="h-6 w-6 text-destructive" />
        </div>
        
        <div className="flex-1 space-y-2">
          <h3 className="font-semibold text-destructive">
            {title || 'Error'}
          </h3>
          
          <p className="text-sm text-muted-foreground">
            {message}
          </p>
          
          {/* Debug info (only in development) */}
          {process.env.NODE_ENV === 'development' && code && (
            <p className="text-xs text-muted-foreground/60">
              Error code: {code}
            </p>
          )}
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="mt-4 flex gap-2">
        {retryable && action && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            {action}
          </Button>
        )}
        
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Start Over
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **TODO:** Create `ErrorDisplay.jsx` component
- [ ] **TODO:** Style with Tailwind
- [ ] **TODO:** Integrate in FitCheckSection

---

### Step 7: Add Session Debug Panel (Development Only)

**File:** `frontend/components/fit-check/SessionDebugPanel.jsx` (new file)

```jsx
'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Bug } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Debug panel showing session information (development only).
 */
export function SessionDebugPanel({ 
  sessionId, 
  status, 
  phaseHistory,
  durationMs,
  className 
}) {
  const [isOpen, setIsOpen] = useState(false);
  
  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }
  
  return (
    <div className={cn('fixed bottom-4 right-4 z-50', className)}>
      <div className="rounded-lg border bg-background/95 backdrop-blur shadow-lg max-w-sm">
        {/* Toggle header */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm font-mono hover:bg-muted/50"
        >
          <Bug className="h-4 w-4 text-muted-foreground" />
          <span className="flex-1 text-left truncate">
            {sessionId ? sessionId.slice(0, 8) : 'No session'}
          </span>
          {isOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronUp className="h-4 w-4" />
          )}
        </button>
        
        {/* Debug info */}
        {isOpen && (
          <div className="px-3 py-2 border-t space-y-2 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status:</span>
              <span className={cn(
                status === 'error' && 'text-destructive',
                status === 'complete' && 'text-green-600',
              )}>
                {status}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-muted-foreground">Session ID:</span>
              <span className="truncate max-w-[150px]">{sessionId || 'none'}</span>
            </div>
            
            {durationMs && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Duration:</span>
                <span>{(durationMs / 1000).toFixed(2)}s</span>
              </div>
            )}
            
            <div className="flex justify-between">
              <span className="text-muted-foreground">Phases:</span>
              <span>{phaseHistory?.length || 0}</span>
            </div>
            
            {/* Phase list */}
            {phaseHistory?.length > 0 && (
              <div className="mt-2 pt-2 border-t space-y-1">
                {phaseHistory.slice(-5).map((phase, i) => (
                  <div key={i} className="flex justify-between text-[10px]">
                    <span className="text-muted-foreground">{phase.phase}</span>
                    <span className={cn(
                      phase.status === 'complete' && 'text-green-600',
                      phase.status === 'error' && 'text-destructive',
                      phase.status === 'active' && 'text-blue-600',
                    )}>
                      {phase.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **TODO:** Create `SessionDebugPanel.jsx`
- [ ] **TODO:** Only render in development
- [ ] **TODO:** Show useful debugging info

---

## Verification & Validation

### Test 1: Session ID Tracking

```javascript
// In browser console during a request:
// Check network tab for the request

// Headers should include:
// X-Session-ID: <uuid>

// Body should include:
// session_id: <uuid>
```

- [ ] **TODO:** Verify session ID appears in request headers
- [ ] **TODO:** Verify session ID appears in request body
- [ ] **TODO:** Verify different requests have different IDs

---

### Test 2: Retry Behavior

```bash
# Temporarily block the backend to simulate network error
docker compose stop backend

# In the UI, submit a query
# Should see retry messages

# Restart backend
docker compose start backend

# Retry should succeed
```

- [ ] **TODO:** Verify retry status messages appear
- [ ] **TODO:** Verify exponential backoff (increasing delays)
- [ ] **TODO:** Verify request succeeds after backend recovers

---

### Test 3: Cleanup on Unmount

```javascript
// In React DevTools or console:
// 1. Start a request
// 2. Navigate away from FitCheckSection
// 3. Check for console errors about state updates on unmounted component

// Should see NO warnings about:
// "Can't perform a React state update on an unmounted component"
```

- [ ] **TODO:** Start request, then navigate away
- [ ] **TODO:** Verify no React warnings in console
- [ ] **TODO:** Verify no memory leaks (use Chrome DevTools Memory tab)

---

### Test 4: Error Display

```javascript
// Simulate different error types:

// 1. TIMEOUT - Let a request run for 5+ minutes (or lower timeout for testing)
// 2. INVALID_QUERY - Submit empty or very short query
// 3. CONNECTION_ERROR - Stop backend and submit query

// Each should show appropriate error UI with correct:
// - Title
// - Message
// - Action button
```

- [ ] **TODO:** Test TIMEOUT error display
- [ ] **TODO:** Test CONNECTION_ERROR display
- [ ] **TODO:** Test INVALID_QUERY display
- [ ] **TODO:** Verify retry button works

---

### Test 5: Debug Panel (Development)

```bash
# Run in development mode
npm run dev

# Submit a query
# Check bottom-right corner for debug panel
# Should show session ID, status, phases
```

- [ ] **TODO:** Verify debug panel appears in development
- [ ] **TODO:** Verify debug panel shows correct info
- [ ] **TODO:** Verify debug panel is hidden in production build

---

## Completion Checklist

After completing all steps and tests:

**File:** `_devnotes/MULTI_SESSION_UPGRADE_PLAN.md`

Mark Phase 5 as complete:
```markdown
| **Phase 5: Frontend Enhancements** | ✅ Complete | 2024-XX-XX |
```

### Summary of Changes

| File | Change |
|------|--------|
| `hooks/use-fit-check.js` | Session ID, retry logic, cleanup |
| `lib/errorMessages.js` | User-friendly error messages |
| `components/fit-check/ErrorDisplay.jsx` | Error display component |
| `components/fit-check/InputPanel.jsx` | Connection status indicator |
| `components/fit-check/SessionDebugPanel.jsx` | Development debug panel |

---

## Next Steps

With all phases complete:

1. **Production Deployment:** Deploy with Phase 4 Docker config
2. **User Testing:** Gather feedback on error messages and retry UX
3. **Performance Monitoring:** Use Phase 3 metrics to identify bottlenecks
4. **Documentation:** Update user-facing docs with new features

---

## Appendix: Complete Hook Return Value

After all changes, `useFitCheck()` returns:

```typescript
{
  // State
  status: 'idle' | 'connecting' | 'thinking' | 'responding' | 'complete' | 'error',
  statusMessage: string,
  thoughts: ThoughtEntry[],
  response: string,
  error: ErrorInfo | null,
  durationMs: number | null,
  currentPhase: string | null,
  phaseHistory: PhaseEntry[],
  phaseProgress: Record<string, string>,
  sessionId: string | null,  // NEW
  
  // Derived state
  uiPhase: 'input' | 'expanded' | 'results',
  parsedResponse: ParsedResponse | null,
  finalConfidence: ConfidenceInfo | null,
  isLoading: boolean,
  
  // Actions
  submitQuery: (query: string) => Promise<void>,  // With retry
  reset: () => void,
}
```
````
