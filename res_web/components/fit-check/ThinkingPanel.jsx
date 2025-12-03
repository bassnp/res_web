'use client';

import { cn } from '@/lib/utils';
import { ChainOfThought } from './ChainOfThought';

/**
 * ThinkingPanel Component
 * 
 * Right panel that shows AI thinking process as a continuous traced stream.
 * Uses ChainOfThought component to display:
 * - Active node prominently at top
 * - Newest entries first, oldest at bottom  
 * - Data passed to each node revealed
 * - Scrollable container with new entries appearing at top
 * 
 * @param {Object} props
 * @param {Array} props.thoughts - Array of thought events
 * @param {boolean} props.isThinking - Whether AI is currently thinking
 * @param {boolean} props.isVisible - Whether panel should be visible
 * @param {string} props.status - Current status (connecting, thinking, responding)
 * @param {string} props.statusMessage - Current status message
 * @param {string} props.currentPhase - Currently active phase from backend
 * @param {Object} props.phaseProgress - Map of phase -> status
 * @param {Array} props.phaseHistory - Completed phase entries with data
 */
export function ThinkingPanel({ 
  thoughts = [], 
  isThinking = false, 
  isVisible = false,
  status = 'thinking',
  statusMessage = '',
  currentPhase = null,
  phaseProgress = {},
  phaseHistory = [],
}) {
  if (!isVisible) return null;

  return (
    <div className={cn(
      "flex flex-col h-full",
      "bg-twilight/5 dark:bg-eggshell/5",
      "rounded-lg overflow-hidden"
    )}>
      <ChainOfThought
        thoughts={thoughts}
        currentPhase={currentPhase}
        phaseProgress={phaseProgress}
        phaseHistory={phaseHistory}
        isThinking={['connecting', 'thinking'].includes(status)}
        statusMessage={statusMessage}
      />
    </div>
  );
}

export default ThinkingPanel;
