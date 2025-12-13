'use client';

import { Search, Eye, Brain, Briefcase, CheckCircle2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Phase-specific color classes for left border.
 * Visual distinction for thoughts from different pipeline phases.
 */
const PHASE_COLORS = {
  connecting: 'border-l-blue-400',
  deep_research: 'border-l-purple-400',
  research_reranker: 'border-l-violet-400',
  skeptical_comparison: 'border-l-amber-400',
  skills_matching: 'border-l-muted-teal',
  confidence_reranker: 'border-l-emerald-400',
  generate_results: 'border-l-burnt-peach',
};

/**
 * ThoughtNode Component
 * 
 * Displays an individual AI thought step in the thinking timeline.
 * Supports three types: tool_call, observation, and reasoning.
 * Includes phase-specific color coding via left border.
 * 
 * @param {Object} props
 * @param {Object} props.thought - Thought event data
 * @param {number} props.thought.step - Sequential step number
 * @param {string} props.thought.type - Type: 'tool_call' | 'observation' | 'reasoning'
 * @param {string} props.thought.tool - Tool name (for tool_call type)
 * @param {string} props.thought.input - Tool input (for tool_call type)
 * @param {string} props.thought.content - Content (for observation/reasoning types)
 * @param {string} props.thought.phase - Pipeline phase this thought belongs to
 * @param {boolean} props.isLast - Whether this is the last thought in the list
 * @param {boolean} props.isActive - Whether this thought is currently active/processing
 */
export function ThoughtNode({ thought, isLast = false, isActive = false }) {
  const { step, type, tool, input, content, phase } = thought;

  // Icon and colors based on thought type
  const config = getThoughtConfig(type, tool);
  
  // Get phase-specific border color
  const phaseColorClass = PHASE_COLORS[phase] || 'border-l-gray-400';

  return (
    <div 
      className={cn(
        "relative pl-8 animate-thought-appear",
        !isLast && "pb-4"
      )}
    >
      {/* Timeline connector line */}
      {!isLast && (
        <div 
          className="absolute left-[11px] top-8 bottom-0 w-0.5 bg-gradient-to-b from-burnt-peach/50 to-muted-teal/30 timeline-connector" 
        />
      )}

      {/* Timeline dot/icon */}
      <div 
        className={cn(
          "absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300",
          config.dotBg,
          isActive && "thought-active"
        )}
      >
        {isActive ? (
          <Loader2 className="w-3 h-3 text-eggshell animate-spin" />
        ) : (
          <config.icon className="w-3 h-3 text-eggshell" />
        )}
      </div>

      {/* Content card with phase-specific left border */}
      <div 
        className={cn(
          "bg-white/80 dark:bg-twilight/40 rounded-lg p-4 border transition-all duration-300",
          "border-l-2",
          phaseColorClass,
          config.borderColor,
          isActive && "thought-node-active shadow-md"
        )}
      >
        {/* Header with type label */}
        <div className="flex items-center gap-2 mb-2">
          <span 
            className={cn(
              "text-xs font-semibold uppercase tracking-wide",
              config.labelColor
            )}
          >
            {config.label}
          </span>
          <span className="text-xs text-twilight/40 dark:text-eggshell/40">
            Step {step}
          </span>
        </div>

        {/* Content based on type */}
        {type === 'tool_call' && (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-twilight/60 dark:text-eggshell/60">Tool:</span>
              <code className="text-xs bg-twilight/10 dark:bg-eggshell/10 px-2 py-0.5 rounded font-mono">
                {formatToolName(tool)}
              </code>
            </div>
            {input && (
              <p className="text-sm text-twilight/80 dark:text-eggshell/80 mt-2">
                <span className="text-twilight/60 dark:text-eggshell/60">Query: </span>
                &quot;{truncateText(input, 100)}&quot;
              </p>
            )}
          </div>
        )}

        {type === 'observation' && (
          <p className="text-sm text-twilight/80 dark:text-eggshell/80 leading-relaxed">
            {truncateText(content, 200)}
          </p>
        )}

        {type === 'reasoning' && (
          <p className="text-sm text-twilight/80 dark:text-eggshell/80 leading-relaxed italic">
            &quot;{truncateText(content, 200)}&quot;
          </p>
        )}

        {/* Status indicator */}
        {!isActive && (
          <div className="flex items-center gap-1 mt-2">
            <CheckCircle2 className="w-3 h-3 text-muted-teal" />
            <span className="text-xs text-muted-teal">Complete</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Get configuration for thought type styling
 */
function getThoughtConfig(type, tool) {
  switch (type) {
    case 'tool_call':
      return {
        icon: getToolIcon(tool),
        label: 'Research',
        dotBg: 'bg-burnt-peach',
        borderColor: 'border-burnt-peach/20',
        labelColor: 'text-burnt-peach',
      };
    case 'observation':
      return {
        icon: Eye,
        label: 'Observation',
        dotBg: 'bg-muted-teal',
        borderColor: 'border-muted-teal/20',
        labelColor: 'text-muted-teal',
      };
    case 'reasoning':
      return {
        icon: Brain,
        label: 'Reasoning',
        dotBg: 'bg-twilight dark:bg-apricot',
        borderColor: 'border-twilight/20 dark:border-apricot/20',
        labelColor: 'text-twilight dark:text-apricot',
      };
    default:
      return {
        icon: Brain,
        label: 'Thought',
        dotBg: 'bg-twilight',
        borderColor: 'border-twilight/20',
        labelColor: 'text-twilight',
      };
  }
}

/**
 * Get icon based on tool name
 */
function getToolIcon(tool) {
  switch (tool) {
    case 'web_search':
      return Search;
    case 'analyze_skill_match':
    case 'analyze_experience_relevance':
      return Briefcase;
    default:
      return Search;
  }
}

/**
 * Format tool name for display
 */
function formatToolName(tool) {
  switch (tool) {
    case 'web_search':
      return 'Web Search';
    case 'analyze_skill_match':
      return 'Skill Matcher';
    case 'analyze_experience_relevance':
      return 'Experience Analyzer';
    default:
      return tool || 'Unknown Tool';
  }
}

/**
 * Truncate text to a maximum length
 */
function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

export default ThoughtNode;
