'use client';

import { Brain, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import ThinkingTimeline from '@/components/ThinkingTimeline';

/**
 * Phase display names for grouping headers.
 */
const PHASE_DISPLAY_NAMES = {
  connecting: 'Query Classification',
  deep_research: 'Deep Research',
  research_reranker: 'Research Quality Gate',
  skeptical_comparison: 'Critical Analysis',
  skills_matching: 'Skill Mapping',
  confidence_reranker: 'Confidence Calibration',
  generate_results: 'Response Generation',
};

/**
 * Group thoughts by their phase for organized display.
 * @param {Array} thoughts - All thoughts
 * @returns {Object} Thoughts grouped by phase name
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
 * ThinkingPanel Component
 * 
 * Expandable right panel that shows AI thinking process.
 * Groups thoughts by pipeline phase with visual headers.
 * 
 * @param {Object} props
 * @param {Array} props.thoughts - Array of thought events
 * @param {boolean} props.isThinking - Whether AI is currently thinking
 * @param {boolean} props.isVisible - Whether panel should be visible
 * @param {string} props.status - Current status (connecting, thinking, responding)
 * @param {string} props.statusMessage - Current status message
 * @param {string} props.currentPhase - Currently active phase from backend
 */
export function ThinkingPanel({ 
  thoughts = [], 
  isThinking = false, 
  isVisible = false,
  status = 'thinking',
  statusMessage = '',
  currentPhase = null
}) {
  if (!isVisible) return null;

  const getStatusDisplay = () => {
    switch (status) {
      case 'connecting':
        return { text: 'Connecting...', icon: Loader2, spin: true };
      case 'thinking':
        return { text: 'Researching & Analyzing', icon: Brain, spin: false };
      case 'responding':
        return { text: 'Generating Response', icon: Loader2, spin: true };
      default:
        return { text: statusMessage || 'Processing...', icon: Loader2, spin: true };
    }
  };

  const statusDisplay = getStatusDisplay();
  
  // Group thoughts by phase for organized display
  const groupedThoughts = groupThoughtsByPhase(thoughts);
  const hasGroupedThoughts = Object.keys(groupedThoughts).length > 0;

  return (
    <div className={cn(
      "flex flex-col h-full",
      "bg-twilight/5 dark:bg-eggshell/5",
      "rounded-lg overflow-hidden"
    )}>
      {/* Panel Header */}
      <div className="flex items-center gap-3 p-4 border-b border-twilight/10 dark:border-eggshell/10">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center",
          "bg-burnt-peach/20"
        )}>
          {statusDisplay.spin ? (
            <Loader2 className="w-4 h-4 text-burnt-peach animate-spin" />
          ) : (
            <Brain className="w-4 h-4 text-burnt-peach" />
          )}
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-twilight dark:text-eggshell">
            AI Analysis
          </h3>
          <p className="text-xs text-twilight/60 dark:text-eggshell/60">
            {statusDisplay.text}
          </p>
        </div>
        
        {/* Status dots */}
        {isThinking && (
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        )}
      </div>

      {/* Thinking Timeline - scrollable content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 custom-scrollbar">
        {thoughts.length === 0 && status === 'connecting' ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-2 border-burnt-peach/30" />
              <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-transparent border-t-burnt-peach fit-check-spinner" />
            </div>
            <p className="text-sm text-twilight/60 dark:text-eggshell/60">
              Initializing AI agent...
            </p>
          </div>
        ) : hasGroupedThoughts ? (
          // Render thoughts grouped by phase with headers
          <div className="space-y-4">
            {Object.entries(groupedThoughts).map(([phase, phaseThoughts]) => (
              <div key={phase} className="phase-group phase-enter">
                {/* Phase group header */}
                <h4 className="phase-group-header">
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
          </div>
        ) : (
          // Fallback to ungrouped timeline (backward compatibility)
          <ThinkingTimeline
            thoughts={thoughts}
            isThinking={isThinking}
            defaultExpanded={true}
            hideHeader={true}
          />
        )}
      </div>
    </div>
  );
}

export default ThinkingPanel;
