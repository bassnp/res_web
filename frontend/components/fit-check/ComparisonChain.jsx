'use client';

import { 
  Link2, Wifi, Search, Scale, Briefcase, FileCheck2, 
  CheckCircle2, AlertCircle, Gauge, Target, Code2,
  AlertTriangle, XCircle, RefreshCw, Database
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { extractPhaseInsights } from '@/lib/phaseInsights';
import { useMemo } from 'react';
import { PHASE_CONFIG, PHASE_ORDER } from '@/lib/phaseConfig';

/**
 * DataQualityBadge Component
 * Renders a badge indicating the quality tier of research data.
 */
function DataQualityBadge({ tier }) {
  const config = {
    CLEAN: { color: 'bg-emerald-500', icon: CheckCircle2, label: 'Clean Data' },
    PARTIAL: { color: 'bg-amber-500', icon: AlertTriangle, label: 'Partial' },
    SPARSE: { color: 'bg-orange-500', icon: Database, label: 'Sparse' },
    UNRELIABLE: { color: 'bg-red-400', icon: AlertCircle, label: 'Unreliable' },
    GARBAGE: { color: 'bg-red-600', icon: XCircle, label: 'Invalid' },
  };
  
  const cfg = config[tier] || config.PARTIAL;
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-medium",
      cfg.color, "text-white"
    )}>
      <cfg.icon className="w-2 h-2" />
      {cfg.label}
    </span>
  );
}

/**
 * StepInsightSummary Component
 * 
 * Displays a compact enhanced summary for completed steps.
 * Extracts key metrics and displays them inline.
 */
function StepInsightSummary({ phase, summary, data }) {
  const insights = useMemo(() => {
    const baseInsights = extractPhaseInsights(phase, summary);
    if (!data) return baseInsights;
    
    // Merge structured data into insights for more accurate display
    return { ...baseInsights, ...data };
  }, [phase, summary, data]);
  
  if (!insights) {
    return (
      <span className="text-xs text-twilight/50 dark:text-eggshell/50 truncate block">
        {summary}
      </span>
    );
  }
  
  // Render different compact summaries based on phase
  switch (phase) {
    case 'connecting':
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {insights.company && (
            <span className="text-xs text-twilight/60 dark:text-eggshell/60 truncate">
              {insights.company}
            </span>
          )}
          {insights.queryType && (
            <span className={cn(
              "text-[10px] px-1.5 py-0.5 rounded-sm",
              "bg-muted-teal/10 text-muted-teal"
            )}>
              {insights.queryType}
            </span>
          )}
        </div>
      );
      
    case 'deep_research':
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {insights.techCount > 0 && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50 flex items-center gap-0.5">
              <Code2 className="w-2.5 h-2.5" />
              {insights.techCount} tech
            </span>
          )}
          {insights.requirementsCount > 0 && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50 flex items-center gap-0.5">
              <Target className="w-2.5 h-2.5" />
              {insights.requirementsCount} reqs
            </span>
          )}
        </div>
      );
      
    case 'research_reranker':
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {insights.dataLevel && (
            <DataQualityBadge tier={insights.dataLevel} />
          )}
          {insights.confidence && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50 flex items-center gap-0.5">
              <Gauge className="w-2.5 h-2.5" />
              {insights.confidence}%
            </span>
          )}
          {insights.action === 'ENHANCE_SEARCH' && (
            <span className="text-[10px] text-amber-500 flex items-center gap-0.5">
              <RefreshCw className="w-2.5 h-2.5 animate-spin" />
              Retrying...
            </span>
          )}
        </div>
      );

    case 'confidence_reranker':
      const tier = insights.tier;
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {tier && (
            <span className={cn(
              "text-[10px] px-1.5 py-0.5 rounded-sm flex items-center gap-0.5",
              tier === 'HIGH' ? "bg-muted-teal/10 text-muted-teal" :
              tier === 'MEDIUM' ? "bg-amber-500/10 text-amber-500" :
              "bg-red-500/10 text-red-500"
            )}>
              <Target className="w-2.5 h-2.5" />
              {tier === 'HIGH' ? 'CONFIDENT' :
               tier === 'MEDIUM' ? 'UNCERTAIN' : 'MISUNDERSTANDING'}
            </span>
          )}
          {insights.confidence && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50 flex items-center gap-0.5">
              <Gauge className="w-2.5 h-2.5" />
              {insights.confidence}%
            </span>
          )}
        </div>
      );
      
    case 'skeptical_comparison':
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {insights.gapCount !== undefined && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50">
              {insights.gapCount} gaps found
            </span>
          )}
          {insights.riskLevel && (
            <span className={cn(
              "text-[10px] px-1.5 py-0.5 rounded-sm",
              insights.riskLevel === 'low' ? "bg-muted-teal/10 text-muted-teal" :
              insights.riskLevel === 'medium' ? "bg-amber-500/10 text-amber-500" :
              "bg-red-500/10 text-red-500"
            )}>
              {insights.riskLevel.toUpperCase()} RISK
            </span>
          )}
        </div>
      );
      
    case 'content_enrich':
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {insights.enrichedCount !== undefined && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50">
              {insights.enrichedCount}/{insights.totalCount} sources enriched
            </span>
          )}
        </div>
      );
      
    case 'skills_matching':
      return (
        <div className="flex items-center gap-1.5 flex-wrap">
          {insights.matchedCount !== undefined && (
            <span className="text-[10px] text-twilight/50 dark:text-eggshell/50">
              {insights.matchedCount} matched
            </span>
          )}
          {insights.matchScore !== null && (
            <span className={cn(
              "text-[10px] px-1.5 py-0.5 rounded-sm flex items-center gap-0.5",
              insights.matchScore >= 70 ? "bg-muted-teal/10 text-muted-teal" :
              insights.matchScore >= 40 ? "bg-amber-500/10 text-amber-500" :
              "bg-red-500/10 text-red-500"
            )}>
              <Gauge className="w-2.5 h-2.5" />
              {insights.matchScore}%
            </span>
          )}
        </div>
      );
      
    default:
      return (
        <span className="text-xs text-twilight/50 dark:text-eggshell/50 truncate block">
          {summary}
        </span>
      );
  }
}

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
    const historyEntry = phaseHistory.find(h => h.phase === phaseKey);
    const summary = historyEntry?.summary || null;
    const data = historyEntry?.data || null;
    
    // Calculate search attempts for deep_research
    let searchAttempt = 0;
    if (phaseKey === 'deep_research') {
      searchAttempt = phaseHistory.filter(h => h.phase === 'deep_research').length;
    }
    
    return {
      id: phaseKey,
      label: config.label,
      icon: config.icon,
      description: config.description,
      isComplete: phaseStatus === 'complete',
      isActive: phaseStatus === 'active',
      isError: phaseStatus === 'error',
      summary: summary,
      data: data,
      config: config,
      searchAttempt: searchAttempt,
    };
  });

  return (
    <div className="flex flex-col items-center px-4 py-4 h-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 flex-shrink-0">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center",
          "bg-gradient-to-br from-burnt-peach to-burnt-peach/60",
          "shadow-lg shadow-burnt-peach/20"
        )}>
          <Link2 className="w-4 h-4 text-eggshell" />
        </div>
        <div>
          <h3 className="text-base font-bold text-twilight dark:text-eggshell">
            Analysis Pipeline
          </h3>
          <p className="text-xs text-twilight/60 dark:text-eggshell/60 truncate max-w-[180px]">
            {statusMessage || 'Processing your request...'}
          </p>
        </div>
      </div>

      {/* Steps Chain */}
      <div className="w-full max-w-xs flex-1 overflow-y-auto custom-scrollbar">
        {steps.map((step, index) => (
          <div 
            key={step.id}
            className="comparison-chain-step"
            style={{ animationDelay: `${index * 80}ms` }}
          >
            {/* Step Row */}
            <div className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-sm",
              "border transition-all duration-300",
              step.isComplete 
                ? `${step.config.bgColorMuted} ${step.config.borderColor.replace('border-l-', 'border-')}/30` 
                : step.isActive
                  ? `${step.config.bgColorMuted} ${step.config.borderColor.replace('border-l-', 'border-')}/40 chain-step-pulse`
                  : step.isError
                    ? "bg-red-500/10 border-red-500/30"
                    : "bg-twilight/5 border-twilight/10 dark:bg-eggshell/5 dark:border-eggshell/10"
            )}>
              {/* Icon Container */}
              <div className={cn(
                "w-6 h-6 rounded-sm flex items-center justify-center flex-shrink-0",
                "transition-all duration-300",
                step.isComplete 
                  ? "bg-muted-teal text-eggshell" 
                  : step.isActive
                    ? step.config.bgColor
                    : step.isError
                      ? "bg-red-500 text-eggshell"
                      : "bg-twilight/15 text-twilight/40 dark:bg-eggshell/15 dark:text-eggshell/40"
              )}>
                {step.isComplete ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : step.isError ? (
                  <AlertCircle className="w-3.5 h-3.5" />
                ) : (
                  <step.icon className={cn("w-3.5 h-3.5", step.isActive && "animate-pulse", step.isActive && "text-white")} />
                )}
              </div>

              {/* Label and Summary */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className={cn(
                    "text-sm font-medium transition-colors duration-300 block",
                    step.isComplete 
                      ? "text-muted-teal" 
                      : step.isActive
                        ? step.config.textColor
                        : step.isError
                          ? "text-red-500"
                          : "text-twilight/40 dark:text-eggshell/40"
                  )}>
                    {step.label}
                  </span>

                  {/* Search Retry Indicator */}
                  {step.id === 'deep_research' && step.searchAttempt > 1 && (
                    <span className="text-[10px] text-amber-500 flex items-center gap-1 font-medium animate-pulse">
                      <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                      Attempt {step.searchAttempt}
                    </span>
                  )}
                </div>
                
                {/* Enhanced Summary on complete */}
                {step.isComplete && step.summary && (
                  <StepInsightSummary phase={step.id} summary={step.summary} data={step.data} />
                )}
              </div>

              {/* Active indicator dots */}
              {step.isActive && (
                <div className="flex gap-1">
                  <span className={cn("w-1.5 h-1.5 rounded-full animate-bounce", step.config.bgColor)} 
                        style={{ animationDelay: '0ms' }} />
                  <span className={cn("w-1.5 h-1.5 rounded-full animate-bounce", step.config.bgColor)} 
                        style={{ animationDelay: '150ms' }} />
                  <span className={cn("w-1.5 h-1.5 rounded-full animate-bounce", step.config.bgColor)} 
                        style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>

            {/* Connector line between steps */}
            {index < steps.length - 1 && (
              <div className="flex justify-center">
                <div className={cn(
                  "w-0.5 h-2 transition-all duration-300",
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
