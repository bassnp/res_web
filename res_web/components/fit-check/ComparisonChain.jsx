'use client';

import { Link2, Wifi, Search, Scale, Briefcase, Sparkles, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * ComparisonChain Component
 * 
 * Displays a visually appealing summary of the AI analysis steps
 * in the left panel during the expanded phase. Shows completed steps
 * dynamically as they happen.
 * 
 * @param {Object} props
 * @param {Array} props.thoughts - Array of thought events from the AI
 * @param {string} props.status - Current status (connecting, thinking, responding)
 * @param {string} props.statusMessage - Current status message
 */
export function ComparisonChain({ 
  thoughts = [], 
  status = 'connecting',
  statusMessage = '' 
}) {
  // Derive completed steps from thoughts and status
  const isConnected = status !== 'connecting';
  const hasWebSearch = thoughts.some(t => t.tool === 'web_search');
  const hasSkillMatch = thoughts.some(t => t.tool === 'analyze_skill_match');
  const hasExperienceMatch = thoughts.some(t => t.tool === 'analyze_experience_relevance');
  const isGenerating = status === 'responding';
  const isComplete = status === 'complete';

  // Build steps with proper state tracking
  const steps = [
    {
      id: 'connecting',
      label: 'Connecting',
      icon: Wifi,
      isComplete: isConnected,
      isActive: status === 'connecting',
    },
    {
      id: 'research',
      label: 'Deep Research',
      icon: Search,
      isComplete: hasWebSearch,
      isActive: isConnected && !hasWebSearch && status === 'thinking',
    },
    {
      id: 'comparison',
      label: 'Skeptical Comparison',
      icon: Scale,
      isComplete: hasExperienceMatch,
      isActive: hasWebSearch && !hasExperienceMatch && status === 'thinking',
    },
    {
      id: 'skills',
      label: 'Skills Matching',
      icon: Briefcase,
      isComplete: hasSkillMatch,
      isActive: hasExperienceMatch && !hasSkillMatch && status === 'thinking',
    },
    {
      id: 'generate',
      label: 'Generating Results',
      icon: Sparkles,
      isComplete: isComplete,
      isActive: isGenerating || (hasSkillMatch && status === 'thinking'),
    },
  ];

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
            Comparison Chain
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
                ? "bg-muted-teal/10 border-muted-teal/30 dark:bg-muted-teal/10 dark:border-muted-teal/20" 
                : step.isActive
                  ? "bg-burnt-peach/10 border-burnt-peach/40 chain-step-pulse"
                  : "bg-twilight/5 border-twilight/10 dark:bg-eggshell/5 dark:border-eggshell/10"
            )}>
              {/* Icon Container */}
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                "transition-all duration-300",
                step.isComplete 
                  ? "bg-muted-teal text-eggshell" 
                  : step.isActive
                    ? "bg-burnt-peach text-eggshell"
                    : "bg-twilight/15 dark:bg-eggshell/15 text-twilight/40 dark:text-eggshell/40"
              )}>
                {step.isComplete ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <step.icon className={cn("w-4 h-4", step.isActive && "animate-pulse")} />
                )}
              </div>

              {/* Label */}
              <span className={cn(
                "text-sm font-medium transition-colors duration-300 flex-1",
                step.isComplete 
                  ? "text-muted-teal" 
                  : step.isActive
                    ? "text-burnt-peach"
                    : "text-twilight/40 dark:text-eggshell/40"
              )}>
                {step.label}
              </span>

              {/* Active indicator dots */}
              {step.isActive && (
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>

            {/* Connector line between steps */}
            {index < steps.length - 1 && (
              <div className="flex justify-center">
                <div className={cn(
                  "w-0.5 h-2 rounded-full transition-colors duration-300 my-1",
                  step.isComplete 
                    ? "bg-muted-teal/40" 
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
