'use client';

import { useState, useEffect, useRef } from 'react';
import { ChevronDown, ChevronUp, Brain, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThoughtNode } from './ThoughtNode';

/**
 * ThinkingTimeline Component
 * 
 * Displays a vertical timeline of AI thoughts with expand/collapse functionality.
 * Shows the thinking process as the AI researches and analyzes data.
 * 
 * @param {Object} props
 * @param {Array} props.thoughts - Array of thought events
 * @param {boolean} props.isThinking - Whether the AI is currently thinking
 * @param {boolean} props.defaultExpanded - Default expanded state
 * @param {boolean} props.hideHeader - Hide the collapsible header (for embedded use)
 */
export function ThinkingTimeline({ 
  thoughts = [], 
  isThinking = false, 
  defaultExpanded = true,
  hideHeader = false
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const containerRef = useRef(null);

  // Auto-scroll to latest thought
  useEffect(() => {
    if ((isExpanded || hideHeader) && containerRef.current && thoughts.length > 0) {
      const container = containerRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [thoughts, isExpanded, hideHeader]);

  // Don't render if no thoughts and not thinking
  if (thoughts.length === 0 && !isThinking) {
    return null;
  }

  // If hideHeader, render just the timeline content directly
  if (hideHeader) {
    return (
      <div className="animate-fade-in">
        <div 
          ref={containerRef}
          className="overflow-y-auto overflow-x-hidden pr-2 custom-scrollbar max-h-[350px]"
        >
          {thoughts.map((thought, index) => (
            <ThoughtNode
              key={`thought-${thought.step}-${index}`}
              thought={thought}
              isLast={index === thoughts.length - 1 && !isThinking}
              isActive={false}
            />
          ))}
          
          {/* Active thinking placeholder */}
          {isThinking && (
            <div className="relative pl-8">
              {/* Timeline connector */}
              <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-burnt-peach/30 to-transparent" />
              
              {/* Pulsing dot */}
              <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-burnt-peach/50 flex items-center justify-center thinking-dot-active">
                <Loader2 className="w-3 h-3 text-eggshell animate-spin" />
              </div>
              
              {/* Placeholder card */}
              <div className="bg-white/50 dark:bg-twilight/30 rounded-lg p-4 border border-dashed border-twilight/20 dark:border-eggshell/20">
                <div className="h-2 w-24 bg-twilight/10 dark:bg-eggshell/10 rounded" />
                <div className="h-3 w-full bg-twilight/5 dark:bg-eggshell/5 rounded mt-2" />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 animate-fade-in">
      {/* Header with expand/collapse toggle */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 rounded-lg bg-twilight/5 dark:bg-eggshell/5 hover:bg-twilight/10 dark:hover:bg-eggshell/10 transition-colors duration-200 group"
        aria-expanded={isExpanded}
        aria-controls="thinking-timeline-content"
      >
        <div className="flex items-center gap-2">
          {isThinking ? (
            <Loader2 className="w-4 h-4 text-burnt-peach animate-spin" />
          ) : (
            <Brain className="w-4 h-4 text-burnt-peach" />
          )}
          <span className="text-sm font-medium text-twilight dark:text-eggshell">
            {isThinking ? 'AI is thinking...' : `${thoughts.length} thinking step${thoughts.length !== 1 ? 's' : ''}`}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Thinking indicator dots */}
          {isThinking && (
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
          
          {/* Expand/collapse icon */}
          <div className="text-twilight/60 dark:text-eggshell/60 group-hover:text-twilight dark:group-hover:text-eggshell transition-colors">
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </div>
        </div>
      </button>

      {/* Timeline content */}
      <div
        id="thinking-timeline-content"
        ref={containerRef}
        className={cn(
          "overflow-hidden transition-all duration-300 ease-out",
          isExpanded ? "max-h-[400px] opacity-100 mt-4" : "max-h-0 opacity-0 mt-0"
        )}
      >
        <div 
          className={cn(
            "overflow-y-auto pr-2 custom-scrollbar",
            isExpanded && thoughts.length > 3 && "max-h-[350px]"
          )}
        >
          {thoughts.map((thought, index) => (
            <ThoughtNode
              key={`thought-${thought.step}-${index}`}
              thought={thought}
              isLast={index === thoughts.length - 1 && !isThinking}
              isActive={false}
            />
          ))}
          
          {/* Active thinking placeholder */}
          {isThinking && (
            <div className="relative pl-8">
              {/* Timeline connector */}
              <div className="absolute left-[11px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-burnt-peach/30 to-transparent" />
              
              {/* Pulsing dot */}
              <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-burnt-peach/50 flex items-center justify-center thinking-dot-active">
                <Loader2 className="w-3 h-3 text-eggshell animate-spin" />
              </div>
              
              {/* Placeholder card */}
              <div className="bg-white/50 dark:bg-twilight/30 rounded-lg p-4 border border-dashed border-twilight/20 dark:border-eggshell/20">
                <div className="h-2 w-24 bg-twilight/10 dark:bg-eggshell/10 rounded" />
                <div className="h-3 w-full bg-twilight/5 dark:bg-eggshell/5 rounded mt-2" />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ThinkingTimeline;
