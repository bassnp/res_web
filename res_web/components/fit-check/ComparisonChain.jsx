'use client';

import { Link2, Wifi, Search, Scale, Briefcase, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Phase configuration with display metadata.
 * Maps backend phase names to UI display properties.
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
  research_reranker: {
    label: 'Research Quality Gate',
    icon: CheckCircle2,
    description: 'Validating research completeness',
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
  confidence_reranker: {
    label: 'Confidence Calibration',
    icon: CheckCircle2,
    description: 'LLM-as-Judge quality assessment',
  },
  generate_results: {
    label: 'Generating Results',
    icon: Sparkles,
    description: 'Synthesizing final response',
  },
};

/** Ordered list of pipeline phases */
const PHASE_ORDER = [
  'connecting',
  'deep_research',
  'research_reranker',
  'skeptical_comparison',
  'skills_matching',
  'confidence_reranker',
  'generate_results',
];

/**
 * ComparisonChain Component
 * 
 * Displays pipeline phase progress with explicit phase props.
 * Uses phase events from backend instead of inferring from tool calls.
 * 
 * @param {Object} props
 * @param {string} props.currentPhase - Currently active phase
 * @param {Object} props.phaseProgress - Map of phase name -> status
 * @param {Array} props.phaseHistory - Completed phase entries
 * @param {string} props.status - Overall status (connecting, thinking, etc.)
 * @param {string} props.statusMessage - Current status message
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
    const phaseStatus = getPhaseStatus(phaseKey);
    const summary = getPhaseSummary(phaseKey);
    
    return {
      id: phaseKey,
      label: config.label,
      icon: config.icon,
      description: config.description,
      isComplete: phaseStatus === 'complete',
      isActive: phaseStatus === 'active',
      isError: phaseStatus === 'error',
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
                    : step.isError
                      ? "bg-red-500 text-eggshell"
                      : "bg-twilight/15 text-twilight/40 dark:bg-eggshell/15 dark:text-eggshell/40"
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
