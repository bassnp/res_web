# Phase 6: FRONTEND_INTEGRATION Implementation

> **Objective**: Update the frontend to handle new `phase` and `phase_complete` SSE events, display explicit phase progress, and group thoughts by pipeline phase.

---

## 1. Phase Overview

### 1.1 Core Changes

The frontend currently infers phase completion from tool calls (e.g., seeing `web_search` implies "research" phase). The upgraded pipeline emits **explicit phase events**, requiring frontend updates to:

1. Handle new `phase` and `phase_complete` event types
2. Display phase transitions in the ComparisonChain component
3. Group thoughts by phase in the ThinkingPanel
4. Track phase history in the hook state

### 1.2 Files to Modify

| File | Changes |
|------|---------|
| `hooks/use-fit-check.js` | Add `currentPhase`, `phaseHistory` state; handle new events |
| `components/fit-check/ComparisonChain.jsx` | Use explicit phase props instead of tool inference |
| `components/fit-check/ThinkingPanel.jsx` | Group thoughts by phase, show phase headers |
| `components/ThoughtNode.jsx` | Add phase color coding |

---

## 2. Hook State Updates

### 2.1 New State Structure

```javascript
// hooks/use-fit-check.js

const [state, setState] = useState({
  status: 'idle',
  statusMessage: '',
  thoughts: [],
  response: '',
  error: null,
  durationMs: null,
  
  // NEW: Phase tracking
  currentPhase: null,        // Current active phase name
  phaseHistory: [],          // Array of completed phase objects
  phaseProgress: {},         // Map of phase -> status (pending/active/complete)
});
```

### 2.2 Phase Object Structure

```javascript
/**
 * Phase history entry structure.
 * 
 * @typedef {Object} PhaseEntry
 * @property {string} phase - Phase name (connecting, deep_research, etc.)
 * @property {string} message - Phase start message
 * @property {string|null} summary - Phase completion summary
 * @property {number} startTime - Timestamp when phase started
 * @property {number|null} endTime - Timestamp when phase completed
 * @property {'active'|'complete'|'error'} status - Phase status
 */
```

---

## 3. Event Handler Updates

### 3.1 New Event Processing

```javascript
// hooks/use-fit-check.js

/**
 * Process a single SSE event.
 * @param {Object} event - Parsed SSE event
 * @param {Function} setState - State setter function
 * @param {number} startTime - Request start timestamp
 */
function processEvent(event, setState, startTime) {
  const { type, data } = event;
  
  switch (type) {
    // NEW: Phase transition event
    case 'phase':
      setState(prev => ({
        ...prev,
        currentPhase: data.phase,
        statusMessage: data.message,
        phaseProgress: {
          ...prev.phaseProgress,
          [data.phase]: 'active',
        },
        phaseHistory: [
          ...prev.phaseHistory,
          {
            phase: data.phase,
            message: data.message,
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
          [data.phase]: 'complete',
        },
        phaseHistory: prev.phaseHistory.map(entry =>
          entry.phase === data.phase && entry.status === 'active'
            ? {
                ...entry,
                summary: data.summary,
                endTime: Date.now(),
                status: 'complete',
              }
            : entry
        ),
      }));
      break;
    
    case 'status':
      setState(prev => ({
        ...prev,
        status: mapStatusToState(data.status),
        statusMessage: data.message,
      }));
      break;
    
    case 'thought':
      setState(prev => ({
        ...prev,
        status: 'thinking',
        thoughts: [
          ...prev.thoughts,
          {
            step: data.step,
            type: data.type,
            tool: data.tool || null,
            input: data.input || null,
            content: data.content || null,
            phase: data.phase || prev.currentPhase,  // NEW: Include phase
            timestamp: Date.now(),
          },
        ],
      }));
      break;
    
    case 'response':
      setState(prev => ({
        ...prev,
        status: 'responding',
        response: prev.response + data.chunk,
      }));
      break;
    
    case 'complete':
      setState(prev => ({
        ...prev,
        status: 'complete',
        durationMs: data.duration_ms || (Date.now() - startTime),
      }));
      break;
    
    case 'error':
      setState(prev => ({
        ...prev,
        status: 'error',
        error: {
          code: data.code,
          message: data.message,
        },
        phaseProgress: {
          ...prev.phaseProgress,
          [prev.currentPhase]: 'error',
        },
      }));
      break;
    
    default:
      console.warn('Unknown event type:', type);
  }
}
```

### 3.2 Helper Functions

```javascript
/**
 * Map backend status to frontend state.
 */
function mapStatusToState(status) {
  const statusMap = {
    'connecting': 'connecting',
    'researching': 'thinking',
    'analyzing': 'thinking',
    'generating': 'responding',
  };
  return statusMap[status] || 'thinking';
}

/**
 * Get thoughts for a specific phase.
 */
function getThoughtsByPhase(thoughts, phase) {
  return thoughts.filter(t => t.phase === phase);
}

/**
 * Get all unique phases from thoughts.
 */
function getUniquePhasesFromThoughts(thoughts) {
  return [...new Set(thoughts.map(t => t.phase).filter(Boolean))];
}
```

---

## 4. ComparisonChain Component Update

### 4.1 Props Interface

```jsx
/**
 * ComparisonChain Component - Updated Props
 * 
 * @param {Object} props
 * @param {string} props.currentPhase - Currently active phase
 * @param {Object} props.phaseProgress - Map of phase name -> status
 * @param {Array} props.phaseHistory - Completed phase entries
 * @param {string} props.status - Overall status (connecting, thinking, etc.)
 * @param {string} props.statusMessage - Current status message
 */
```

### 4.2 Updated Implementation

```jsx
// components/fit-check/ComparisonChain.jsx

'use client';

import { Link2, Wifi, Search, Scale, Briefcase, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Phase definitions with display metadata.
 */
const PHASE_CONFIG = {
  connecting: {
    label: 'Connecting',
    icon: Wifi,
    description: 'Classifying query and extracting entities',
  },
  deep_research: {
    label: 'Deep Research',
    icon: Search,
    description: 'Gathering employer intelligence',
  },
  skeptical_comparison: {
    label: 'Skeptical Comparison',
    icon: Scale,
    description: 'Critical gap analysis',
  },
  skills_matching: {
    label: 'Skills Matching',
    icon: Briefcase,
    description: 'Mapping skills to requirements',
  },
  generate_results: {
    label: 'Generating Results',
    icon: Sparkles,
    description: 'Synthesizing final response',
  },
};

const PHASE_ORDER = [
  'connecting',
  'deep_research',
  'skeptical_comparison',
  'skills_matching',
  'generate_results',
];

/**
 * ComparisonChain Component
 * 
 * Displays pipeline phase progress with explicit phase props.
 * No longer infers phase from tool calls.
 */
export function ComparisonChain({ 
  currentPhase = null,
  phaseProgress = {},
  phaseHistory = [],
  status = 'connecting',
  statusMessage = '' 
}) {
  /**
   * Get phase status from explicit props.
   */
  const getPhaseStatus = (phaseKey) => {
    if (phaseProgress[phaseKey] === 'complete') return 'complete';
    if (phaseProgress[phaseKey] === 'active') return 'active';
    if (phaseProgress[phaseKey] === 'error') return 'error';
    return 'pending';
  };

  /**
   * Get phase summary from history.
   */
  const getPhaseSummary = (phaseKey) => {
    const entry = phaseHistory.find(h => h.phase === phaseKey && h.status === 'complete');
    return entry?.summary || null;
  };

  /**
   * Build steps array from phase config and status.
   */
  const steps = PHASE_ORDER.map(phaseKey => {
    const config = PHASE_CONFIG[phaseKey];
    const status = getPhaseStatus(phaseKey);
    const summary = getPhaseSummary(phaseKey);
    
    return {
      id: phaseKey,
      label: config.label,
      icon: config.icon,
      description: config.description,
      isComplete: status === 'complete',
      isActive: status === 'active',
      isError: status === 'error',
      summary: summary,
    };
  });

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center",
          "bg-gradient-to-br from-burnt-peach to-burnt-peach/60",
          "shadow-lg shadow-burnt-peach/20"
        )}>
          <Link2 className="w-5 h-5 text-eggshell" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-twilight dark:text-eggshell">
            Analysis Pipeline
          </h3>
          <p className="text-xs text-twilight/60 dark:text-eggshell/60">
            {statusMessage || 'Processing your request...'}
          </p>
        </div>
      </div>

      {/* Steps Chain */}
      <div className="w-full max-w-xs">
        {steps.map((step, index) => (
          <div 
            key={step.id}
            className="comparison-chain-step"
            style={{ animationDelay: `${index * 80}ms` }}
          >
            {/* Step Row */}
            <div className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-xl",
              "border transition-all duration-300",
              step.isComplete 
                ? "bg-muted-teal/10 border-muted-teal/30" 
                : step.isActive
                  ? "bg-burnt-peach/10 border-burnt-peach/40 chain-step-pulse"
                  : step.isError
                    ? "bg-red-500/10 border-red-500/30"
                    : "bg-twilight/5 border-twilight/10 dark:bg-eggshell/5"
            )}>
              {/* Icon Container */}
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                "transition-all duration-300",
                step.isComplete 
                  ? "bg-muted-teal text-eggshell" 
                  : step.isActive
                    ? "bg-burnt-peach text-eggshell"
                    : step.isError
                      ? "bg-red-500 text-eggshell"
                      : "bg-twilight/15 text-twilight/40 dark:bg-eggshell/15"
              )}>
                {step.isComplete ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : step.isError ? (
                  <AlertCircle className="w-4 h-4" />
                ) : (
                  <step.icon className={cn("w-4 h-4", step.isActive && "animate-pulse")} />
                )}
              </div>

              {/* Label and Summary */}
              <div className="flex-1 min-w-0">
                <span className={cn(
                  "text-sm font-medium transition-colors duration-300 block",
                  step.isComplete 
                    ? "text-muted-teal" 
                    : step.isActive
                      ? "text-burnt-peach"
                      : step.isError
                        ? "text-red-500"
                        : "text-twilight/40 dark:text-eggshell/40"
                )}>
                  {step.label}
                </span>
                
                {/* Summary on complete */}
                {step.isComplete && step.summary && (
                  <span className="text-xs text-twilight/50 dark:text-eggshell/50 truncate block">
                    {step.summary}
                  </span>
                )}
              </div>

              {/* Active indicator dots */}
              {step.isActive && (
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" 
                        style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" 
                        style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" 
                        style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>

            {/* Connector line between steps */}
            {index < steps.length - 1 && (
              <div className="flex justify-center">
                <div className={cn(
                  "w-0.5 h-4 transition-all duration-300",
                  step.isComplete
                    ? "bg-muted-teal/50"
                    : "bg-twilight/10 dark:bg-eggshell/10"
                )} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ComparisonChain;
```

---

## 5. ThinkingPanel Updates

### 5.1 Group Thoughts by Phase

```jsx
// components/fit-check/ThinkingPanel.jsx (updated section)

/**
 * Group thoughts by phase for organized display.
 */
function groupThoughtsByPhase(thoughts) {
  const groups = {};
  
  for (const thought of thoughts) {
    const phase = thought.phase || 'unknown';
    if (!groups[phase]) {
      groups[phase] = [];
    }
    groups[phase].push(thought);
  }
  
  return groups;
}

/**
 * Phase display names.
 */
const PHASE_DISPLAY_NAMES = {
  connecting: 'Query Classification',
  deep_research: 'Deep Research',
  skeptical_comparison: 'Critical Analysis',
  skills_matching: 'Skill Mapping',
  generate_results: 'Response Generation',
};

// In the render:
const groupedThoughts = groupThoughtsByPhase(thoughts);

// Render each phase group with header:
{Object.entries(groupedThoughts).map(([phase, phaseThoughts]) => (
  <div key={phase} className="mb-4">
    <h4 className="text-xs font-semibold text-twilight/60 dark:text-eggshell/60 mb-2 uppercase tracking-wide">
      {PHASE_DISPLAY_NAMES[phase] || phase}
    </h4>
    <ThinkingTimeline
      thoughts={phaseThoughts}
      isThinking={isThinking && currentPhase === phase}
      defaultExpanded={true}
      hideHeader={true}
    />
  </div>
))}
```

---

## 6. ThoughtNode Phase Coloring

### 6.1 Phase Color Map

```jsx
// components/ThoughtNode.jsx (add phase colors)

const PHASE_COLORS = {
  connecting: 'border-l-blue-400',
  deep_research: 'border-l-purple-400',
  skeptical_comparison: 'border-l-amber-400',
  skills_matching: 'border-l-green-400',
  generate_results: 'border-l-burnt-peach',
};

// In the component:
<div className={cn(
  "border-l-2 pl-3",
  PHASE_COLORS[thought.phase] || 'border-l-gray-400'
)}>
  {/* Thought content */}
</div>
```

---

## 7. FitCheckSection Integration

### 7.1 Pass New Props to Components

```jsx
// components/FitCheckSection.jsx (updated usage)

import { useFitCheck } from '@/hooks/use-fit-check';
import { ComparisonChain } from './fit-check/ComparisonChain';
import { ThinkingPanel } from './fit-check/ThinkingPanel';

export function FitCheckSection() {
  const {
    status,
    statusMessage,
    thoughts,
    response,
    error,
    currentPhase,      // NEW
    phaseProgress,     // NEW
    phaseHistory,      // NEW
    uiPhase,
    parsedResponse,
    submitQuery,
    reset,
    isLoading,
  } = useFitCheck();

  return (
    <div>
      {/* Input phase... */}
      
      {/* Expanded phase with new props */}
      {uiPhase === 'expanded' && (
        <div className="grid grid-cols-2 gap-4">
          <ComparisonChain
            currentPhase={currentPhase}
            phaseProgress={phaseProgress}
            phaseHistory={phaseHistory}
            status={status}
            statusMessage={statusMessage}
          />
          <ThinkingPanel
            thoughts={thoughts}
            isThinking={isLoading}
            isVisible={true}
            status={status}
            statusMessage={statusMessage}
            currentPhase={currentPhase}  // NEW
          />
        </div>
      )}
      
      {/* Results phase... */}
    </div>
  );
}
```

---

## 8. TypeScript Definitions (if using TypeScript)

```typescript
// types/fit-check.ts

export type PhaseName = 
  | 'connecting'
  | 'deep_research'
  | 'skeptical_comparison'
  | 'skills_matching'
  | 'generate_results';

export type PhaseStatus = 'pending' | 'active' | 'complete' | 'error';

export interface PhaseEntry {
  phase: PhaseName;
  message: string;
  summary: string | null;
  startTime: number;
  endTime: number | null;
  status: PhaseStatus;
}

export interface Thought {
  step: number;
  type: 'tool_call' | 'observation' | 'reasoning';
  tool: string | null;
  input: string | null;
  content: string | null;
  phase: PhaseName | null;
  timestamp: number;
}

export interface FitCheckState {
  status: 'idle' | 'connecting' | 'thinking' | 'responding' | 'complete' | 'error';
  statusMessage: string;
  thoughts: Thought[];
  response: string;
  error: { code: string; message: string } | null;
  durationMs: number | null;
  currentPhase: PhaseName | null;
  phaseHistory: PhaseEntry[];
  phaseProgress: Record<PhaseName, PhaseStatus>;
}
```

---

## 9. CSS Updates

```css
/* Add to app/globals.css */

/* Phase-specific thought colors */
.thought-connecting { border-left-color: theme('colors.blue.400'); }
.thought-deep_research { border-left-color: theme('colors.purple.400'); }
.thought-skeptical_comparison { border-left-color: theme('colors.amber.400'); }
.thought-skills_matching { border-left-color: theme('colors.green.400'); }
.thought-generate_results { border-left-color: theme('colors.burnt-peach'); }

/* Phase group headers */
.phase-group-header {
  @apply text-xs font-semibold uppercase tracking-wide;
  @apply text-twilight/60 dark:text-eggshell/60;
  @apply mb-2 pb-1;
  @apply border-b border-twilight/10 dark:border-eggshell/10;
}

/* Phase transition animation */
@keyframes phaseEnter {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.phase-enter {
  animation: phaseEnter 0.3s ease-out forwards;
}
```

---

## 10. Unit Tests

```javascript
// __tests__/use-fit-check.test.js

import { renderHook, act } from '@testing-library/react';
import { useFitCheck } from '@/hooks/use-fit-check';

describe('useFitCheck hook', () => {
  describe('phase event handling', () => {
    it('handles phase event correctly', () => {
      const { result } = renderHook(() => useFitCheck());
      
      // Simulate phase event
      act(() => {
        processEvent(
          { type: 'phase', data: { phase: 'deep_research', message: 'Researching...' } },
          result.current.setState,
          Date.now()
        );
      });
      
      expect(result.current.currentPhase).toBe('deep_research');
      expect(result.current.phaseProgress.deep_research).toBe('active');
    });
    
    it('handles phase_complete event correctly', () => {
      const { result } = renderHook(() => useFitCheck());
      
      // Start phase
      act(() => {
        processEvent(
          { type: 'phase', data: { phase: 'connecting', message: 'Starting...' } },
          result.current.setState,
          Date.now()
        );
      });
      
      // Complete phase
      act(() => {
        processEvent(
          { type: 'phase_complete', data: { phase: 'connecting', summary: 'Done' } },
          result.current.setState,
          Date.now()
        );
      });
      
      expect(result.current.phaseProgress.connecting).toBe('complete');
      const historyEntry = result.current.phaseHistory.find(h => h.phase === 'connecting');
      expect(historyEntry.status).toBe('complete');
      expect(historyEntry.summary).toBe('Done');
    });
    
    it('includes phase in thought events', () => {
      const { result } = renderHook(() => useFitCheck());
      
      // Set current phase
      act(() => {
        processEvent(
          { type: 'phase', data: { phase: 'deep_research', message: 'Researching...' } },
          result.current.setState,
          Date.now()
        );
      });
      
      // Add thought without explicit phase (should inherit current)
      act(() => {
        processEvent(
          { type: 'thought', data: { step: 1, type: 'reasoning', content: 'Thinking...' } },
          result.current.setState,
          Date.now()
        );
      });
      
      expect(result.current.thoughts[0].phase).toBe('deep_research');
    });
  });
});
```

---

## 11. Validation Checklist

Before marking frontend integration complete:

- [ ] `hooks/use-fit-check.js` handles `phase` event
- [ ] `hooks/use-fit-check.js` handles `phase_complete` event
- [ ] `phaseProgress` and `phaseHistory` state tracked
- [ ] Thoughts include `phase` field
- [ ] `ComparisonChain` uses explicit props, not tool inference
- [ ] `ThinkingPanel` groups thoughts by phase
- [ ] `ThoughtNode` has phase-specific colors
- [ ] CSS animations for phase transitions
- [ ] Unit tests for event handling

---

## 12. Migration Notes

### 12.1 Backward Compatibility

The frontend should handle both old and new event formats during transition:

```javascript
// Fallback if phase not present in thought
const thoughtPhase = data.phase || state.currentPhase || 'unknown';
```

### 12.2 Feature Flag (Optional)

```javascript
// Enable new pipeline via feature flag
const USE_NEW_PIPELINE = process.env.NEXT_PUBLIC_USE_NEW_PIPELINE === 'true';

// In submitQuery:
const endpoint = USE_NEW_PIPELINE 
  ? '/api/fit-check/stream'  // New pipeline
  : '/api/fit-check/stream'; // Same endpoint, backend handles version
```

---

## 13. Next Steps

After implementing this phase:
1. Proceed to **PHASE_7_TESTING_VALIDATION.md**
2. Execute implementation in order
3. Run integration tests
4. Validate full flow end-to-end

---

## 14. Build Verification Gate

> ⛔ **STOP**: Do NOT proceed to the next phase until this phase compiles and builds successfully.

### Frontend Build Verification

```powershell
# Navigate to frontend directory
cd res_web

# Install dependencies (if needed)
npm install

# Run ESLint to check for errors
npm run lint

# Run production build
npm run build

# Start dev server and verify no console errors
npm run dev
```

### Verification Checklist

- [ ] `npm install` completes without errors
- [ ] `npm run lint` passes with no errors
- [ ] `npm run build` succeeds
- [ ] Application loads in browser without console errors
- [ ] Phase transitions display correctly in UI
- [ ] Thought timeline groups by phase
- [ ] ComparisonChain shows phase completion status
- [ ] SSE events are parsed correctly

---

## 15. Requirements Tracking

> 📋 **IMPORTANT**: Refer to **[TRACK_ALL_REQUIREMENTS.md](./TRACK_ALL_REQUIREMENTS.md)** for the complete requirements checklist.

### After Completing This Phase:

1. Open `TRACK_ALL_REQUIREMENTS.md`
2. Locate the **Phase 6: Frontend Integration** section
3. Mark each completed requirement with ✅
4. Fill in the "Verified By" and "Date" columns
5. Complete the **Build Verification** checkboxes
6. Update the **Completion Summary** table at the bottom

### Phase 6 Requirement IDs to Update:

- P6-001 through P6-012

---

*Document Version: 1.1 | Phase 6 of 7 | Frontend Integration*
