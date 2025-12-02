# TODO: Frontend UI - "See if I'm fit for you!" AI Chatbot Feature

## Overview
This document outlines the implementation plan for an in-line AI chatbot component that allows employers to interact with an AI agent to learn how the engineer's skills and experience match their company or job requirements.

---

## 1. Component Location & Architecture

### Placement
The component will be placed in `app/page.js` **between the `HeroAboutSection` and `ProjectsSection`** components, creating a natural flow:

```
HeroAboutSection (About Me)
     ↓
[NEW] FitCheckSection ("See if I'm fit for you!")
     ↓
ProjectsSection
```

### File Structure
```
res_web/
├── app/
│   └── page.js                    # Add FitCheckSection component here
├── components/
│   ├── FitCheckChat.jsx           # [NEW] Main chatbot container
│   ├── FitCheckInput.jsx          # [NEW] Input textbox with submit
│   ├── FitCheckMessages.jsx       # [NEW] Message display area
│   ├── FitCheckThinking.jsx       # [NEW] AI thinking animation container
│   ├── ThoughtBubble.jsx          # [NEW] Individual thought/reasoning display
│   ├── ResearchStep.jsx           # [NEW] Research action with tool name & query
│   ├── ReasoningChain.jsx         # [NEW] Chain of thought reasoning display
│   ├── ThinkingTimeline.jsx       # [NEW] Vertical timeline of all thoughts
│   └── ui/
│       └── textarea.jsx           # Already exists (shadcn/ui)
├── hooks/
│   └── use-fit-check.js           # [NEW] Custom hook for API interaction
└── lib/
    └── api.js                     # [NEW] API utilities for SSE streaming
```

---

## 2. Component Design Specifications

### 2.1 FitCheckSection (Main Container)
**Location:** `app/page.js` (inline component or import)

```jsx
// Styling matches existing design language:
// - Rounded card container with backdrop blur
// - InteractiveGridDots background pattern
// - Shadow styling consistent with HeroAboutSection
```

**Visual Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✨ See if I'm fit for you!                                 │
│                                                             │
│  [Subtitle: "Tell me about your company or job opening"]    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [Input Textbox - Multi-line Textarea]               │   │
│  │                                                     │   │
│  │ Placeholder: "Enter your company name (e.g.,       │   │
│  │ 'Google', 'Stripe') or describe the position..."   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [🚀 Analyze Fit - CTA Button]                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [THINKING TIMELINE - Expandable/Collapsible]        │   │
│  │                                                     │   │
│  │  ┌─ 🔍 Research Step ─────────────────────────┐    │   │
│  │  │ Tool: web_search                            │    │   │
│  │  │ Query: "Google engineering culture tech"    │    │   │
│  │  │ Status: ✅ Complete                         │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │       │                                             │   │
│  │       ▼                                             │   │
│  │  ┌─ 🧠 Reasoning ─────────────────────────────┐    │   │
│  │  │ "Based on the research, Google prioritizes  │    │   │
│  │  │  innovation and technical excellence..."    │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │       │                                             │   │
│  │       ▼                                             │   │
│  │  ┌─ 📊 Analysis Step ─────────────────────────┐    │   │
│  │  │ Tool: analyze_skill_match                   │    │   │
│  │  │ Matching: Python, React, Cloud → Google     │    │   │
│  │  │ Status: ⏳ Processing...                    │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [AI FINAL RESPONSE]                                  │   │
│  │                                                     │   │
│  │ • Streaming markdown-formatted response              │   │
│  │ • Typewriter effect with cursor                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 State Machine for Chat Flow

```
IDLE                 → User hasn't typed or submitted
     ↓ (user types)
READY                → User has input, ready to submit
     ↓ (submit)
CONNECTING           → Establishing SSE connection
     ↓ (connected)
THINKING             → AI is reasoning (show thoughts)
     ↓ (streaming response)
RESPONDING           → AI is streaming final answer
     ↓ (complete)
COMPLETE             → Full response displayed
     ↓ (user types again)
READY                → Ready for new query
```

---

## 3. Animation Specifications

### 3.1 Entrance Animation (Section Reveal)
```css
/* Fade in + slide up on scroll into view */
.fit-check-section {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp 0.6s ease-out forwards;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 3.2 Input Focus Animation
```css
/* Subtle glow on focus matching burnt-peach theme */
.fit-check-input:focus {
  box-shadow: 0 0 0 2px rgba(224, 122, 95, 0.3);
  border-color: #e07a5f;
  transition: all 0.2s ease-out;
}
```

### 3.3 AI Thinking & Chain of Thought Display (CORE UNIQUE FEATURE)

**Overview:** This is the signature feature that sets this chatbot apart. The UI displays a real-time, animated timeline of the AI's research steps, tool calls, observations, and reasoning chain. Users can see exactly what the AI is doing and thinking.

#### Thought Event Types (from backend)
```typescript
interface ThoughtEvent {
  step: number;                                    // Sequential step number
  type: 'tool_call' | 'observation' | 'reasoning'; // Type of thought
  tool?: string;                                   // Tool name if tool_call
  input?: string;                                  // Tool input/query if tool_call
  content?: string;                                // Text content for observation/reasoning
  status?: 'pending' | 'active' | 'complete';      // Step status
}
```

#### ThinkingTimeline Component
```jsx
// components/ThinkingTimeline.jsx

const ThinkingTimeline = ({ thoughts, isExpanded, onToggle }) => {
  return (
    <div className="thinking-timeline">
      {/* Header with expand/collapse */}
      <button 
        onClick={onToggle}
        className="flex items-center gap-2 w-full p-3 bg-twilight/5 dark:bg-eggshell/5 rounded-t-lg"
      >
        <Brain className="w-5 h-5 text-burnt-peach animate-pulse" />
        <span className="font-medium text-twilight dark:text-eggshell">
          AI Thinking Process
        </span>
        <span className="text-xs text-twilight/60 dark:text-eggshell/60 ml-2">
          ({thoughts.length} steps)
        </span>
        <ChevronDown className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>
      
      {/* Timeline content */}
      {isExpanded && (
        <div className="relative pl-6 py-4 border-l-2 border-burnt-peach/30 ml-4">
          {thoughts.map((thought, index) => (
            <ThoughtNode 
              key={index} 
              thought={thought} 
              isLast={index === thoughts.length - 1}
              isActive={thought.status === 'active'}
            />
          ))}
        </div>
      )}
    </div>
  );
};
```

#### ThoughtNode Component (Individual thought display)
```jsx
// components/ThoughtNode.jsx

const ThoughtNode = ({ thought, isLast, isActive }) => {
  const icons = {
    tool_call: Search,      // 🔍 Research/search action
    observation: FileText,  // 📄 Results from tool
    reasoning: Brain,       // 🧠 AI reasoning/analysis
  };
  
  const colors = {
    tool_call: 'bg-blue-500',
    observation: 'bg-green-500', 
    reasoning: 'bg-purple-500',
  };
  
  const Icon = icons[thought.type];
  
  return (
    <div className={`
      thought-node relative mb-4 last:mb-0
      opacity-0 animate-thought-appear
      ${isActive ? 'thought-active' : ''}
    `}>
      {/* Timeline dot */}
      <div className={`
        absolute -left-[25px] w-4 h-4 rounded-full ${colors[thought.type]}
        flex items-center justify-center
        ${isActive ? 'animate-pulse ring-4 ring-burnt-peach/30' : ''}
      `}>
        {isActive && <Loader2 className="w-3 h-3 text-white animate-spin" />}
      </div>
      
      {/* Content card */}
      <div className={`
        ml-4 p-3 rounded-lg
        bg-white/50 dark:bg-twilight/30
        border border-twilight/10 dark:border-eggshell/10
        ${isActive ? 'border-burnt-peach/50 shadow-md' : ''}
      `}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          <Icon className="w-4 h-4 text-burnt-peach" />
          <span className="text-xs font-semibold uppercase tracking-wide text-twilight/60 dark:text-eggshell/60">
            {thought.type.replace('_', ' ')}
          </span>
          {thought.tool && (
            <code className="text-xs bg-twilight/10 dark:bg-eggshell/10 px-2 py-0.5 rounded">
              {thought.tool}
            </code>
          )}
        </div>
        
        {/* Tool call: Show query */}
        {thought.type === 'tool_call' && thought.input && (
          <div className="mt-2">
            <span className="text-xs text-twilight/50 dark:text-eggshell/50">Query:</span>
            <p className="text-sm text-twilight dark:text-eggshell font-mono bg-twilight/5 dark:bg-eggshell/5 p-2 rounded mt-1">
              "{thought.input}"
            </p>
          </div>
        )}
        
        {/* Observation/Reasoning: Show content */}
        {(thought.type === 'observation' || thought.type === 'reasoning') && thought.content && (
          <p className="text-sm text-twilight/80 dark:text-eggshell/80 mt-1 leading-relaxed">
            {thought.content}
          </p>
        )}
      </div>
    </div>
  );
};
```

#### CSS Animations for Thoughts
```css
/* Thought appearance animation */
@keyframes thoughtAppear {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.animate-thought-appear {
  animation: thoughtAppear 0.4s ease-out forwards;
}

/* Active thought glow */
.thought-active {
  animation: thoughtGlow 2s ease-in-out infinite;
}

@keyframes thoughtGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(224, 122, 95, 0); }
  50% { box-shadow: 0 0 20px 5px rgba(224, 122, 95, 0.15); }
}

/* Pulsing dot for active step */
.thinking-dot-active {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* Timeline connector animation */
.timeline-connector {
  animation: lineGrow 0.3s ease-out forwards;
}

@keyframes lineGrow {
  from { height: 0; }
  to { height: 100%; }
}

/* Staggered step reveal */
.thinking-step {
  opacity: 0;
  animation: stepReveal 0.4s ease-out forwards;
}

.thinking-step:nth-child(1) { animation-delay: 0s; }
.thinking-step:nth-child(2) { animation-delay: 0.3s; }
.thinking-step:nth-child(3) { animation-delay: 0.6s; }
.thinking-step:nth-child(4) { animation-delay: 0.9s; }
.thinking-step:nth-child(5) { animation-delay: 1.2s; }
```

#### Reasoning Chain Visualization
```jsx
// components/ReasoningChain.jsx
// Displays connected reasoning steps with arrows

const ReasoningChain = ({ reasoningSteps }) => {
  return (
    <div className="reasoning-chain flex flex-col gap-2">
      {reasoningSteps.map((step, index) => (
        <React.Fragment key={index}>
          <div className="reasoning-bubble bg-gradient-to-r from-purple-500/10 to-burnt-peach/10 p-3 rounded-lg border-l-4 border-purple-500">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-twilight dark:text-eggshell">
                {step.content}
              </p>
            </div>
          </div>
          {index < reasoningSteps.length - 1 && (
            <div className="flex justify-center">
              <ArrowDown className="w-4 h-4 text-twilight/30 dark:text-eggshell/30" />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};
```

### 3.4 Response Streaming Animation
```css
/* Typewriter effect for streaming text */
.response-text {
  overflow: hidden;
  border-right: 2px solid #e07a5f;
  animation: blink 0.7s step-end infinite;
}

@keyframes blink {
  50% { border-color: transparent; }
}

/* Fade-in for complete response blocks */
.response-block {
  opacity: 0;
  animation: fadeIn 0.3s ease-out forwards;
}
```

### 3.5 Submit Button Animation
```css
/* Matches existing animate-pulse-glow from globals.css */
.submit-btn {
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(224, 122, 95, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading spinner when submitting */
.submit-btn.loading .spinner {
  animation: spin 1s linear infinite;
}
```

---

## 4. Component Implementation Details

### 4.1 FitCheckSection Component (Enhanced with Chain of Thought)
```jsx
// app/page.js - Add between HeroAboutSection and ProjectsSection

const FitCheckSection = () => {
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('idle'); // idle, connecting, thinking, responding, complete
  const [thoughts, setThoughts] = useState([]);      // All thought events from agent
  const [response, setResponse] = useState('');
  const [error, setError] = useState(null);
  const [isThoughtsExpanded, setIsThoughtsExpanded] = useState(true); // Show thoughts by default
  const [currentStatus, setCurrentStatus] = useState(''); // Human-readable status message

  // Categorize thoughts for display
  const categorizedThoughts = useMemo(() => {
    return {
      toolCalls: thoughts.filter(t => t.type === 'tool_call'),
      observations: thoughts.filter(t => t.type === 'observation'),
      reasoning: thoughts.filter(t => t.type === 'reasoning'),
    };
  }, [thoughts]);

  const handleSubmit = async () => {
    setStatus('connecting');
    setThoughts([]);
    setResponse('');
    setError(null);
    setCurrentStatus('Connecting to AI...');
    setIsThoughtsExpanded(true); // Auto-expand thoughts when starting

    try {
      const response = await fetch(`${API_BASE_URL}/api/fit-check/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, include_thoughts: true }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const events = parseSSE(chunk);

        for (const event of events) {
          switch (event.type) {
            case 'status':
              setCurrentStatus(event.data.message);
              break;
              
            case 'thought':
              setStatus('thinking');
              setThoughts(prev => [...prev, {
                ...event.data,
                status: 'complete', // Mark as complete when received
                timestamp: Date.now(),
              }]);
              // Update the last thought to 'active' status briefly
              setTimeout(() => {
                setThoughts(prev => prev.map((t, i) => 
                  i === prev.length - 1 ? { ...t, status: 'complete' } : t
                ));
              }, 500);
              break;
              
            case 'response':
              setStatus('responding');
              setIsThoughtsExpanded(false); // Collapse thoughts when response starts
              setResponse(prev => prev + event.data.chunk);
              break;
              
            case 'complete':
              setStatus('complete');
              setCurrentStatus('Analysis complete!');
              break;
              
            case 'error':
              setStatus('idle');
              setError(event.data.message);
              break;
          }
        }
      }
    } catch (err) {
      setStatus('idle');
      setError(err.message);
    }
  };

  return (
    <section id="fit-check" className="py-16">
      <div className="container mx-auto px-6">
        <div className="relative bg-background/95 backdrop-blur-sm rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden">
          <InteractiveGridDots />
          <div className="relative z-10 p-6 md:p-8">
            {/* Header */}
            <div className="text-center mb-6">
              <h2 className="text-2xl md:text-3xl font-bold text-twilight dark:text-eggshell mb-2">
                <Sparkles className="inline w-6 h-6 text-burnt-peach mr-2" />
                See if I'm <span className="text-burnt-peach">fit for you!</span>
              </h2>
              <p className="text-twilight/70 dark:text-eggshell/70">
                Tell me about your company or job opening, and I'll research & explain how I can help.
              </p>
            </div>

            {/* Input Area */}
            <div className="max-w-2xl mx-auto">
              <Textarea 
                placeholder="Enter your company name (e.g., 'Google', 'Stripe') or describe the position you're hiring for..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={status === 'connecting' || status === 'thinking' || status === 'responding'}
                className="min-h-[100px]"
              />
              
              <Button 
                onClick={handleSubmit}
                disabled={!input.trim() || (status !== 'idle' && status !== 'complete')}
                className="mt-4 w-full bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell"
              >
                {status === 'idle' || status === 'complete' ? (
                  <><Sparkles className="w-4 h-4 mr-2" /> Analyze Fit</>
                ) : (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> {currentStatus}</>
                )}
              </Button>
            </div>

            {/* Thinking Timeline - THE UNIQUE FEATURE */}
            {thoughts.length > 0 && (
              <div className="mt-8 max-w-2xl mx-auto">
                <ThinkingTimeline 
                  thoughts={thoughts}
                  isExpanded={isThoughtsExpanded}
                  onToggle={() => setIsThoughtsExpanded(!isThoughtsExpanded)}
                  currentStatus={currentStatus}
                  isActive={status === 'thinking'}
                />
              </div>
            )}

            {/* AI Response */}
            {response && (
              <div className="mt-6 max-w-2xl mx-auto">
                <div className="bg-white/50 dark:bg-twilight/30 rounded-lg p-6 border border-twilight/10 dark:border-eggshell/10">
                  <div className="flex items-center gap-2 mb-4">
                    <MessageSquare className="w-5 h-5 text-muted-teal" />
                    <span className="font-semibold text-twilight dark:text-eggshell">Analysis Result</span>
                    {status === 'responding' && (
                      <span className="text-xs text-burnt-peach animate-pulse">● Streaming...</span>
                    )}
                  </div>
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ResponseDisplay 
                      response={response} 
                      isStreaming={status === 'responding'} 
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-6 max-w-2xl mx-auto">
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
```

### 4.2 Custom Hook: useFitCheck (Enhanced for Chain of Thought)
```jsx
// hooks/use-fit-check.js

/**
 * Custom hook for managing the Fit Check AI interaction.
 * Handles SSE streaming with detailed thought event processing.
 */
export function useFitCheck() {
  const [state, setState] = useState({
    status: 'idle',           // idle, connecting, thinking, responding, complete
    statusMessage: '',        // Human-readable status
    thoughts: [],             // Array of thought events with full details
    response: '',             // Accumulated response text
    error: null,              // Error message if any
    duration: 0,              // Total duration in ms
  });
  
  const abortControllerRef = useRef(null);

  const submitQuery = useCallback(async (query) => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setState({
      status: 'connecting',
      statusMessage: 'Connecting to AI agent...',
      thoughts: [],
      response: '',
      error: null,
      duration: 0,
    });

    const startTime = Date.now();

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/fit-check/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, include_thoughts: true }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = parseSSEBuffer(buffer);
        buffer = events.remaining;

        for (const event of events.parsed) {
          processEvent(event, setState, startTime);
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        // Request was cancelled, don't update state
        return;
      }
      setState(prev => ({
        ...prev,
        status: 'idle',
        error: err.message || 'Connection failed. Please try again.',
      }));
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState({
      status: 'idle',
      statusMessage: '',
      thoughts: [],
      response: '',
      error: null,
      duration: 0,
    });
  }, []);

  return { ...state, submitQuery, reset };
}

/**
 * Parse SSE events from buffer, handling partial messages.
 */
function parseSSEBuffer(buffer) {
  const events = [];
  const lines = buffer.split('\n');
  let remaining = '';
  let currentEvent = {};

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Check if this might be an incomplete line at the end
    if (i === lines.length - 1 && line !== '') {
      remaining = line;
      continue;
    }

    if (line.startsWith('event:')) {
      currentEvent.type = line.slice(7).trim();
    } else if (line.startsWith('data:')) {
      try {
        currentEvent.data = JSON.parse(line.slice(6));
        if (currentEvent.type) {
          events.push({ ...currentEvent });
        }
        currentEvent = {};
      } catch (e) {
        // JSON parse failed, might be incomplete
        remaining = `event: ${currentEvent.type}\n${line}`;
        currentEvent = {};
      }
    }
  }

  return { parsed: events, remaining };
}

/**
 * Process individual SSE events and update state.
 */
function processEvent(event, setState, startTime) {
  switch (event.type) {
    case 'status':
      setState(prev => ({
        ...prev,
        statusMessage: event.data.message,
      }));
      break;

    case 'thought':
      setState(prev => ({
        ...prev,
        status: 'thinking',
        thoughts: [
          ...prev.thoughts,
          {
            id: `thought-${Date.now()}-${prev.thoughts.length}`,
            step: event.data.step,
            type: event.data.type,         // 'tool_call', 'observation', 'reasoning'
            tool: event.data.tool,         // Tool name if tool_call
            input: event.data.input,       // Tool input if tool_call
            content: event.data.content,   // Content for observation/reasoning
            timestamp: Date.now(),
            status: 'active',              // Will be marked 'complete' after animation
          },
        ],
      }));
      
      // Mark thought as complete after brief animation
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          thoughts: prev.thoughts.map(t =>
            t.status === 'active' ? { ...t, status: 'complete' } : t
          ),
        }));
      }, 800);
      break;

    case 'response':
      setState(prev => ({
        ...prev,
        status: 'responding',
        response: prev.response + event.data.chunk,
      }));
      break;

    case 'complete':
      setState(prev => ({
        ...prev,
        status: 'complete',
        statusMessage: 'Analysis complete!',
        duration: Date.now() - startTime,
      }));
      break;

    case 'error':
      setState(prev => ({
        ...prev,
        status: 'idle',
        error: event.data.message || 'An error occurred',
      }));
      break;
  }
}
```

---

## 5. Responsive Design Considerations

### Mobile (< 640px)
- Full-width card with reduced padding (p-4)
- Textarea height: 100px minimum
- Stacked layout for input + button
- Smaller font sizes for headers (text-xl)

### Tablet (640px - 1024px)
- Card with moderate padding (p-6)
- Textarea height: 120px
- Side margins: px-4

### Desktop (> 1024px)
- Card with full padding (p-8)
- Textarea height: 150px
- Max-width container: 2xl (max-w-2xl)

---

## 6. Accessibility Requirements

- **Keyboard Navigation:** Tab through input → button → response
- **ARIA Labels:** `aria-label` on buttons, `role="status"` on thinking display
- **Focus Management:** Auto-focus input on section scroll-into-view
- **Screen Reader:** Announce status changes ("Thinking...", "Response ready")
- **Color Contrast:** Ensure 4.5:1 contrast ratio for all text

---

## 7. Error States

### Network Error
```jsx
<div className="text-red-500 text-sm mt-2">
  <AlertCircle className="inline w-4 h-4 mr-1" />
  Connection failed. Please check your internet and try again.
</div>
```

### API Error
```jsx
<div className="text-red-500 text-sm mt-2">
  <AlertCircle className="inline w-4 h-4 mr-1" />
  Something went wrong. Please try again later.
</div>
```

### Empty Input Validation
- Disable submit button when input is empty/whitespace
- No error message needed (button state communicates this)

---

## 8. Integration Points

### Backend API Endpoint
```
POST /api/fit-check/stream
Content-Type: text/event-stream

Request Body:
{
  "query": string,           // Company name or job description
  "include_thoughts": true   // Enable detailed thought streaming
}

SSE Events:

1. status - Agent status updates (human-readable)
   event: status
   data: { "status": "researching", "message": "Searching for company information..." }

2. thought - Detailed AI reasoning step (CORE FEATURE)
   event: thought
   data: {
     "step": 1,                          // Sequential step number
     "type": "tool_call",                // "tool_call" | "observation" | "reasoning"
     "tool": "web_search",               // Tool name (if type=tool_call)
     "input": "Google engineering...",   // Search query (if type=tool_call)
     "content": null                     // Text content (if type=observation/reasoning)
   }

   Example thought types:
   - tool_call:    { type: "tool_call", tool: "web_search", input: "Stripe tech stack" }
   - observation:  { type: "observation", content: "Stripe uses Ruby, Go, and React..." }
   - reasoning:    { type: "reasoning", content: "The candidate's React experience aligns..." }

3. response - Streaming response text chunk
   event: response
   data: { "chunk": "Based on my research, " }

4. complete - Stream finished successfully
   event: complete
   data: { "duration_ms": 5678, "total_thoughts": 6 }

5. error - Error occurred
   event: error
   data: { "code": "AGENT_ERROR", "message": "Failed to complete analysis" }
```

### Environment Variables
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 9. Implementation Checklist

### Phase 1: Basic Structure
- [ ] Create FitCheckSection component skeleton in page.js
- [ ] Add InteractiveGridDots background
- [ ] Implement basic input textarea with styling
- [ ] Add submit button with disabled states

### Phase 2: Chain of Thought UI (CORE UNIQUE FEATURE)
- [ ] Create ThinkingTimeline component with expand/collapse
- [ ] Implement ThoughtNode component for individual thoughts
- [ ] Add tool_call display (tool name + query visualization)
- [ ] Add observation display (results with formatting)
- [ ] Add reasoning display (chain of thought bubbles)
- [ ] Create ReasoningChain component with arrows
- [ ] Implement timeline connector animations
- [ ] Add thought appearance animations (slide-in, fade)
- [ ] Create active thought pulsing/glow effect

### Phase 3: Animations
- [ ] Implement section entrance animation
- [ ] Add input focus glow effect
- [ ] Create thought step staggered reveal
- [ ] Implement response streaming typewriter effect
- [ ] Add timeline line grow animation
- [ ] Create thought status transitions (active → complete)

### Phase 4: API Integration
- [ ] Create useFitCheck custom hook with detailed state
- [ ] Implement SSE connection with POST body
- [ ] Parse SSE buffer handling partial messages
- [ ] Process status events (update statusMessage)
- [ ] Process thought events (tool_call, observation, reasoning)
- [ ] Process response streaming events
- [ ] Handle complete event with duration
- [ ] Implement AbortController for request cancellation

### Phase 5: Polish
- [ ] Add error state handling with icon
- [ ] Implement responsive breakpoints for timeline
- [ ] Add accessibility attributes (ARIA, roles)
- [ ] Test dark/light mode for all thought components
- [ ] Performance optimization (React.memo, useMemo)
- [ ] Auto-collapse thoughts when response starts
- [ ] Add duration display on completion

---

## 10. Dependencies

### Existing (No Install Needed)
- `lucide-react` - Icons (Sparkles, AlertCircle, Brain, Search, FileText, Lightbulb, ArrowDown, ChevronDown, Loader2, MessageSquare, etc.)
- `@/components/ui/button` - Button component
- `@/components/ui/textarea` - Textarea component
- `InteractiveGridDots` - Background pattern
- `tailwindcss-animate` - Animation utilities

### New Dependencies (If Needed)
```bash
# None required - using existing shadcn/ui components
# Optional: For markdown rendering in responses
npm install react-markdown
```

---

## 11. Color Palette Reference

```css
/* Matches existing globals.css theme */
--burnt-peach: #e07a5f;    /* Primary accent */
--muted-teal: #81b29a;     /* Secondary accent */
--twilight: #3d405b;       /* Dark text/bg */
--eggshell: #f4f1de;       /* Light text/bg */
--apricot: #f2cc8f;        /* Tertiary accent */
```

---

## Notes

1. **Performance:** Use `React.memo()` for ThinkingDisplay and ResponseDisplay to prevent unnecessary re-renders during streaming.

2. **Abort Controller:** Implement request cancellation if user navigates away or starts a new query.

3. **Rate Limiting:** Consider adding client-side throttling to prevent spam submissions.

4. **Analytics:** Track submission events for conversion metrics (optional).
