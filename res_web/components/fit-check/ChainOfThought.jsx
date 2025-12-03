'use client';

import { useRef, useEffect, useMemo, useState } from 'react';
import { 
  Wifi, 
  Search, 
  Scale, 
  Briefcase, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  ChevronDown,
  ChevronUp,
  Eye,
  Brain,
  Database,
  ArrowRight,
  Code2,
  Target,
  Users,
  Gauge,
  FileText,
  Lightbulb,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { extractPhaseInsights, parseThoughtContent, getPhaseDisplayMeta } from '@/lib/phaseInsights';

/**
 * Phase configuration with display metadata.
 * Maps backend phase names to UI display properties.
 */
const PHASE_CONFIG = {
  connecting: {
    label: 'Connecting',
    icon: Wifi,
    description: 'Classifying query and extracting entities',
    color: 'blue',
    borderColor: 'border-l-blue-400',
    bgColor: 'bg-blue-400',
    textColor: 'text-blue-400',
  },
  deep_research: {
    label: 'Deep Research',
    icon: Search,
    description: 'Gathering employer intelligence via web search',
    color: 'purple',
    borderColor: 'border-l-purple-400',
    bgColor: 'bg-purple-400',
    textColor: 'text-purple-400',
  },
  research_reranker: {
    label: 'Research Quality Gate',
    icon: CheckCircle2,
    description: 'Validating research completeness and quality',
    color: 'violet',
    borderColor: 'border-l-violet-400',
    bgColor: 'bg-violet-400',
    textColor: 'text-violet-400',
  },
  skeptical_comparison: {
    label: 'Skeptical Comparison',
    icon: Scale,
    description: 'Critical gap analysis between candidate and requirements',
    color: 'amber',
    borderColor: 'border-l-amber-400',
    bgColor: 'bg-amber-400',
    textColor: 'text-amber-400',
  },
  skills_matching: {
    label: 'Skills Matching',
    icon: Briefcase,
    description: 'Mapping skills to job requirements',
    color: 'green',
    borderColor: 'border-l-green-400',
    bgColor: 'bg-green-400',
    textColor: 'text-green-400',
  },
  confidence_reranker: {
    label: 'Confidence Calibration',
    icon: CheckCircle2,
    description: 'LLM-as-Judge quality assessment and calibration',
    color: 'emerald',
    borderColor: 'border-l-emerald-400',
    bgColor: 'bg-emerald-400',
    textColor: 'text-emerald-400',
  },
  generate_results: {
    label: 'Generating Results',
    icon: Sparkles,
    description: 'Synthesizing final response with insights',
    color: 'burnt-peach',
    borderColor: 'border-l-burnt-peach',
    bgColor: 'bg-burnt-peach',
    textColor: 'text-burnt-peach',
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
 * ChainOfThought Component
 * 
 * Displays a continuous traced stream of all pipeline steps with:
 * - Newest entries at the top, oldest at the bottom
 * - Active node prominently displayed
 * - Data passed to each node revealed
 * - Scrollable container with auto-scroll to new entries
 * 
 * @param {Object} props
 * @param {Array} props.thoughts - Array of thought events from the pipeline
 * @param {string} props.currentPhase - Currently active phase name
 * @param {Object} props.phaseProgress - Map of phase -> status
 * @param {Array} props.phaseHistory - Completed phase entries with data
 * @param {boolean} props.isThinking - Whether AI is actively processing
 * @param {string} props.statusMessage - Current status message
 */
export function ChainOfThought({
  thoughts = [],
  currentPhase = null,
  phaseProgress = {},
  phaseHistory = [],
  isThinking = false,
  statusMessage = '',
}) {
  const scrollContainerRef = useRef(null);

  // Build a continuous stream of entries ordered newest-first
  const streamEntries = useMemo(() => {
    const entries = [];
    
    // Process phase history to create phase start entries
    for (const phaseEntry of phaseHistory) {
      entries.push({
        id: `phase-${phaseEntry.phase}-${phaseEntry.startTime}`,
        type: 'phase_start',
        phase: phaseEntry.phase,
        message: phaseEntry.message,
        timestamp: phaseEntry.startTime,
        data: null,
      });
      
      // If phase is complete, add completion entry
      if (phaseEntry.status === 'complete' && phaseEntry.endTime) {
        entries.push({
          id: `phase-complete-${phaseEntry.phase}-${phaseEntry.endTime}`,
          type: 'phase_complete',
          phase: phaseEntry.phase,
          summary: phaseEntry.summary,
          timestamp: phaseEntry.endTime,
          duration: phaseEntry.endTime - phaseEntry.startTime,
          data: phaseEntry.data || null,
        });
      }
    }
    
    // Add thought entries
    for (const thought of thoughts) {
      entries.push({
        id: `thought-${thought.step}-${thought.timestamp || Date.now()}`,
        type: 'thought',
        phase: thought.phase,
        thoughtType: thought.type,
        tool: thought.tool,
        input: thought.input,
        content: thought.content,
        step: thought.step,
        timestamp: thought.timestamp || Date.now(),
        data: {
          tool: thought.tool,
          input: thought.input,
          content: thought.content,
        },
      });
    }
    
    // Sort by timestamp descending (newest first)
    entries.sort((a, b) => b.timestamp - a.timestamp);
    
    return entries;
  }, [thoughts, phaseHistory]);

  // Auto-scroll to top when new entries are added
  useEffect(() => {
    if (scrollContainerRef.current && streamEntries.length > 0) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [streamEntries.length]);

  return (
    <div className="flex flex-col h-full">
      {/* Active Node Header */}
      <ActiveNodeHeader 
        currentPhase={currentPhase}
        isThinking={isThinking}
        statusMessage={statusMessage}
      />
      
      {/* Scrollable Stream Container */}
      <div 
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden p-4 custom-scrollbar max-h-[400px]"
      >
        {streamEntries.length === 0 && !isThinking ? (
          <EmptyState />
        ) : (
          <div className="space-y-3">
            {/* Active thinking placeholder at top if thinking */}
            {isThinking && currentPhase && (
              <ActiveThinkingEntry 
                phase={currentPhase}
                statusMessage={statusMessage}
              />
            )}
            
            {/* Stream entries - newest first */}
            {streamEntries.map((entry, index) => (
              <StreamEntry 
                key={entry.id}
                entry={entry}
                isLatest={index === 0 && !isThinking}
                animationDelay={Math.min(index * 50, 300)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Active Node Header - Shows the currently active phase prominently
 */
function ActiveNodeHeader({ currentPhase, isThinking, statusMessage }) {
  const config = currentPhase ? PHASE_CONFIG[currentPhase] : null;
  
  return (
    <div className={cn(
      "p-4 border-b border-twilight/10 dark:border-eggshell/10",
      "bg-gradient-to-r",
      currentPhase 
        ? `from-${config?.color}-400/10 to-transparent` 
        : "from-burnt-peach/10 to-transparent"
    )}>
      <div className="flex items-center gap-3">
        {/* Phase Icon */}
        <div className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center",
          "transition-all duration-300",
          isThinking ? "animate-pulse" : "",
          config?.bgColor || "bg-burnt-peach"
        )}>
          {isThinking ? (
            <Loader2 className="w-5 h-5 text-white animate-spin" />
          ) : config ? (
            <config.icon className="w-5 h-5 text-white" />
          ) : (
            <Brain className="w-5 h-5 text-white" />
          )}
        </div>
        
        {/* Phase Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={cn(
              "text-sm font-bold",
              config?.textColor || "text-burnt-peach"
            )}>
              {config?.label || 'Initializing'}
            </h3>
            {isThinking && (
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-burnt-peach animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            )}
          </div>
          <p className="text-xs text-twilight/60 dark:text-eggshell/60 truncate">
            {statusMessage || config?.description || 'Processing...'}
          </p>
        </div>
        
        {/* Phase Progress Indicator */}
        {currentPhase && (
          <PhaseProgressPills 
            currentPhase={currentPhase}
          />
        )}
      </div>
    </div>
  );
}

/**
 * Phase Progress Pills - Shows small dots for pipeline progress
 */
function PhaseProgressPills({ currentPhase }) {
  const currentIndex = PHASE_ORDER.indexOf(currentPhase);
  
  return (
    <div className="flex gap-1">
      {PHASE_ORDER.map((phase, index) => {
        const isComplete = index < currentIndex;
        const isCurrent = index === currentIndex;
        const config = PHASE_CONFIG[phase];
        
        return (
          <div
            key={phase}
            className={cn(
              "w-2 h-2 rounded-full transition-all duration-300",
              isComplete ? config.bgColor : 
              isCurrent ? `${config.bgColor} animate-pulse` :
              "bg-twilight/20 dark:bg-eggshell/20"
            )}
            title={config.label}
          />
        );
      })}
    </div>
  );
}

/**
 * Active Thinking Entry - Animated placeholder for current processing
 */
function ActiveThinkingEntry({ phase, statusMessage }) {
  const config = PHASE_CONFIG[phase];
  
  return (
    <div className={cn(
      "cot-entry-new",
      "bg-white/80 dark:bg-twilight/40 rounded-lg p-4",
      "border-l-2",
      config?.borderColor || "border-l-burnt-peach",
      "border border-twilight/10 dark:border-eggshell/10",
      "shadow-sm"
    )}>
      <div className="flex items-start gap-3">
        {/* Animated Icon */}
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          config?.bgColor || "bg-burnt-peach",
          "animate-pulse"
        )}>
          <Loader2 className="w-4 h-4 text-white animate-spin" />
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={cn(
              "text-xs font-semibold uppercase tracking-wide",
              config?.textColor || "text-burnt-peach"
            )}>
              Processing
            </span>
            <span className="text-xs text-twilight/40 dark:text-eggshell/40">
              Now
            </span>
          </div>
          
          {/* Skeleton loader */}
          <div className="space-y-2">
            <div className="h-3 w-3/4 bg-twilight/10 dark:bg-eggshell/10 rounded animate-pulse" />
            <div className="h-3 w-1/2 bg-twilight/5 dark:bg-eggshell/5 rounded animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Stream Entry - Renders a single entry in the chain of thought stream
 */
function StreamEntry({ entry, isLatest, animationDelay }) {
  const config = PHASE_CONFIG[entry.phase];
  
  // Entry type specific rendering
  switch (entry.type) {
    case 'phase_start':
      return (
        <PhaseStartEntry 
          entry={entry}
          config={config}
          isLatest={isLatest}
          animationDelay={animationDelay}
        />
      );
    case 'phase_complete':
      return (
        <PhaseCompleteEntry 
          entry={entry}
          config={config}
          isLatest={isLatest}
          animationDelay={animationDelay}
        />
      );
    case 'thought':
      return (
        <ThoughtEntry 
          entry={entry}
          config={config}
          isLatest={isLatest}
          animationDelay={animationDelay}
        />
      );
    default:
      return null;
  }
}

/**
 * Phase Start Entry - Shows when a phase begins
 */
function PhaseStartEntry({ entry, config, isLatest, animationDelay }) {
  return (
    <div 
      className={cn(
        "cot-entry",
        isLatest && "cot-entry-new"
      )}
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div className={cn(
        "flex items-center gap-2 py-2 px-3 rounded-lg",
        "bg-twilight/5 dark:bg-eggshell/5",
        "border-l-2",
        config?.borderColor || "border-l-gray-400"
      )}>
        <ArrowRight className={cn("w-3 h-3", config?.textColor || "text-gray-400")} />
        <span className={cn(
          "text-xs font-medium",
          config?.textColor || "text-gray-400"
        )}>
          Started: {config?.label || entry.phase}
        </span>
        <span className="text-xs text-twilight/40 dark:text-eggshell/40 ml-auto">
          {formatTime(entry.timestamp)}
        </span>
      </div>
    </div>
  );
}

/**
 * Phase Complete Entry - Shows when a phase completes with data
 */
function PhaseCompleteEntry({ entry, config, isLatest, animationDelay }) {
  // Extract insights from the summary
  const insights = useMemo(() => {
    return extractPhaseInsights(entry.phase, entry.summary);
  }, [entry.phase, entry.summary]);
  
  const displayMeta = useMemo(() => {
    return getPhaseDisplayMeta(entry.phase, insights);
  }, [entry.phase, insights]);

  return (
    <div 
      className={cn(
        "cot-entry",
        isLatest && "cot-entry-new"
      )}
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div className={cn(
        "bg-white/80 dark:bg-twilight/40 rounded-lg p-3",
        "border-l-2",
        config?.borderColor || "border-l-gray-400",
        "border border-twilight/10 dark:border-eggshell/10"
      )}>
        <div className="flex items-start gap-3">
          {/* Completed Icon */}
          <div className={cn(
            "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0",
            "bg-muted-teal"
          )}>
            <CheckCircle2 className="w-3 h-3 text-white" />
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-muted-teal">
                Completed: {config?.label || entry.phase}
              </span>
              <span className="text-xs text-twilight/40 dark:text-eggshell/40">
                {entry.duration ? `${(entry.duration / 1000).toFixed(1)}s` : ''}
              </span>
            </div>
            
            {/* Enhanced insights display */}
            <PhaseInsightReveal 
              data={entry.data}
              phase={entry.phase}
              summary={entry.summary}
              compact
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Thought Entry - Shows individual thought/tool call/observation
 */
function ThoughtEntry({ entry, config, isLatest, animationDelay }) {
  const thoughtConfig = getThoughtConfig(entry.thoughtType, entry.tool);
  
  // Parse and enhance thought content
  const enhancedContent = useMemo(() => {
    return parseThoughtContent({
      type: entry.thoughtType,
      tool: entry.tool,
      input: entry.input,
      content: entry.content,
    });
  }, [entry.thoughtType, entry.tool, entry.input, entry.content]);
  
  return (
    <div 
      className={cn(
        "cot-entry",
        isLatest && "cot-entry-new"
      )}
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div className={cn(
        "bg-white/80 dark:bg-twilight/40 rounded-lg p-3",
        "border-l-2",
        config?.borderColor || "border-l-gray-400",
        "border border-twilight/10 dark:border-eggshell/10"
      )}>
        <div className="flex items-start gap-3">
          {/* Thought Type Icon */}
          <div className={cn(
            "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0",
            thoughtConfig.dotBg
          )}>
            <thoughtConfig.icon className="w-3 h-3 text-white" />
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={cn("text-xs font-semibold uppercase tracking-wide", thoughtConfig.labelColor)}>
                {thoughtConfig.label}
              </span>
              <span className="text-xs text-twilight/40 dark:text-eggshell/40">
                Step {entry.step}
              </span>
              <span className="text-xs text-twilight/30 dark:text-eggshell/30 ml-auto">
                {formatTime(entry.timestamp)}
              </span>
            </div>
            
            {/* Tool Call Content - Enhanced */}
            {entry.thoughtType === 'tool_call' && (
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-twilight/60 dark:text-eggshell/60">Tool:</span>
                  <code className={cn(
                    "text-xs px-2 py-0.5 rounded font-mono",
                    "bg-burnt-peach/10 text-burnt-peach",
                    "border border-burnt-peach/20"
                  )}>
                    {formatToolName(entry.tool)}
                  </code>
                </div>
                {enhancedContent?.displaySummary ? (
                  <p className="text-xs text-twilight/70 dark:text-eggshell/70">
                    {enhancedContent.displaySummary}
                  </p>
                ) : entry.input && (
                  <p className="text-xs text-twilight/70 dark:text-eggshell/70">
                    <span className="text-twilight/50 dark:text-eggshell/50">Query: </span>
                    &quot;{truncateText(entry.input, 80)}&quot;
                  </p>
                )}
              </div>
            )}
            
            {/* Observation Content - Enhanced */}
            {entry.thoughtType === 'observation' && (
              <p className="text-xs text-twilight/70 dark:text-eggshell/70">
                {enhancedContent?.displaySummary || truncateText(entry.content, 150)}
              </p>
            )}
            
            {/* Reasoning Content - Enhanced with extracted data */}
            {entry.thoughtType === 'reasoning' && (
              <div className="space-y-1.5">
                <p className="text-xs text-twilight/70 dark:text-eggshell/70 italic">
                  &quot;{enhancedContent?.displaySummary || truncateText(entry.content, 150)}&quot;
                </p>
                
                {/* Show extracted insights if available */}
                {enhancedContent?.extractedData && (
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {enhancedContent.extractedData.confidence && (
                      <span className={cn(
                        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px]",
                        enhancedContent.extractedData.confidence >= 70 ? "bg-muted-teal/10 text-muted-teal" :
                        enhancedContent.extractedData.confidence >= 40 ? "bg-amber-500/10 text-amber-500" :
                        "bg-red-500/10 text-red-500"
                      )}>
                        <Gauge className="w-2.5 h-2.5" />
                        {enhancedContent.extractedData.confidence}%
                      </span>
                    )}
                    {enhancedContent.extractedData.tier && (
                      <span className={cn(
                        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px]",
                        enhancedContent.extractedData.tier === 'HIGH' ? "bg-muted-teal/10 text-muted-teal" :
                        enhancedContent.extractedData.tier === 'MEDIUM' ? "bg-amber-500/10 text-amber-500" :
                        "bg-red-500/10 text-red-500"
                      )}>
                        {enhancedContent.extractedData.tier}
                      </span>
                    )}
                    {enhancedContent.extractedData.technologies?.slice(0, 3).map((tech, i) => (
                      <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-500">
                        <Code2 className="w-2.5 h-2.5" />
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Smart data reveal */}
            <PhaseInsightReveal 
              data={entry.data}
              phase={entry.phase}
              compact
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Phase Insight Reveal Component - Shows structured insights instead of raw JSON
 */
function PhaseInsightReveal({ data, phase, summary, compact = false }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Extract structured insights from summary
  const insights = useMemo(() => {
    if (!summary && !data) return null;
    return extractPhaseInsights(phase, summary);
  }, [phase, summary, data]);
  
  const displayMeta = useMemo(() => {
    if (!insights) return null;
    return getPhaseDisplayMeta(phase, insights);
  }, [phase, insights]);
  
  // Determine what to show
  const hasStructuredInsights = insights && displayMeta && (displayMeta.summary || displayMeta.metrics?.length > 0);
  const hasRawData = data && Object.values(data).some(v => v != null && v !== '');
  
  if (!hasStructuredInsights && !hasRawData) return null;

  return (
    <div className={cn("mt-2", compact ? "text-xs" : "text-sm")}>
      {/* Structured insights summary */}
      {hasStructuredInsights && (
        <div className={cn(
          "rounded-lg p-2 mb-2",
          "bg-gradient-to-r",
          phase === 'deep_research' ? "from-purple-500/5 to-transparent" :
          phase === 'research_reranker' ? "from-violet-500/5 to-transparent" :
          phase === 'skeptical_comparison' ? "from-amber-500/5 to-transparent" :
          phase === 'skills_matching' ? "from-green-500/5 to-transparent" :
          phase === 'confidence_reranker' ? "from-emerald-500/5 to-transparent" :
          "from-burnt-peach/5 to-transparent"
        )}>
          {/* Metrics row */}
          {displayMeta.metrics && displayMeta.metrics.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-1.5">
              {displayMeta.metrics.map((metric, i) => (
                <div key={i} className={cn(
                  "inline-flex items-center gap-1 px-2 py-0.5 rounded-full",
                  "bg-white/50 dark:bg-twilight/30",
                  "border border-twilight/10 dark:border-eggshell/10",
                  compact ? "text-[10px]" : "text-xs"
                )}>
                  {metric.icon === 'code' && <Code2 className="w-3 h-3 text-purple-500" />}
                  {metric.icon === 'target' && <Target className="w-3 h-3 text-amber-500" />}
                  {metric.icon === 'users' && <Users className="w-3 h-3 text-blue-500" />}
                  <span className="font-medium text-twilight/70 dark:text-eggshell/70">
                    {metric.label}: {metric.value}
                  </span>
                </div>
              ))}
            </div>
          )}
          
          {/* Summary text */}
          {displayMeta.summary && (
            <p className={cn(
              "text-twilight/60 dark:text-eggshell/60",
              compact ? "text-[10px]" : "text-xs"
            )}>
              <Lightbulb className="w-3 h-3 inline-block mr-1 text-burnt-peach" />
              {displayMeta.summary}
            </p>
          )}
        </div>
      )}
      
      {/* Raw data toggle (for debugging/transparency) */}
      {hasRawData && (
        <details className="group">
          <summary className={cn(
            "cursor-pointer select-none",
            "flex items-center gap-1",
            "text-twilight/40 dark:text-eggshell/40 hover:text-twilight/60 dark:hover:text-eggshell/60",
            "transition-colors duration-200",
            compact ? "text-[10px]" : "text-xs"
          )}>
            <Database className="w-2.5 h-2.5" />
            <span>View raw data</span>
            <ChevronDown className="w-2.5 h-2.5 group-open:rotate-180 transition-transform" />
          </summary>
          <div className={cn(
            "mt-1.5 p-2 rounded-md",
            "bg-twilight/5 dark:bg-eggshell/5",
            "border border-twilight/10 dark:border-eggshell/10",
            "font-mono text-[10px] overflow-x-auto"
          )}>
            <pre className="whitespace-pre-wrap text-twilight/60 dark:text-eggshell/60">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </div>
  );
}

/**
 * Data Reveal Component - Expandable section showing data passed to node
 * @deprecated Use PhaseInsightReveal instead
 */
function DataReveal({ data, phase, compact = false }) {
  // Filter out empty data
  const hasData = data && Object.values(data).some(v => v != null && v !== '');
  if (!hasData) return null;
  
  return (
    <details className={cn(
      "mt-2 group",
      compact ? "text-xs" : "text-sm"
    )}>
      <summary className={cn(
        "cursor-pointer select-none",
        "flex items-center gap-1",
        "text-twilight/50 dark:text-eggshell/50 hover:text-twilight/70 dark:hover:text-eggshell/70",
        "transition-colors duration-200"
      )}>
        <Database className="w-3 h-3" />
        <span className="text-xs">View data passed to node</span>
        <ChevronDown className="w-3 h-3 group-open:rotate-180 transition-transform" />
      </summary>
      <div className={cn(
        "mt-2 p-2 rounded-md",
        "bg-twilight/5 dark:bg-eggshell/5",
        "border border-twilight/10 dark:border-eggshell/10",
        "font-mono text-xs overflow-x-auto"
      )}>
        <pre className="whitespace-pre-wrap text-twilight/70 dark:text-eggshell/70">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </details>
  );
}

/**
 * Empty State - When no entries exist
 */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center py-8">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-2 border-burnt-peach/30 flex items-center justify-center">
          <Brain className="w-6 h-6 text-burnt-peach/40" />
        </div>
      </div>
      <div>
        <p className="text-sm font-medium text-twilight/60 dark:text-eggshell/60">
          Waiting for analysis
        </p>
        <p className="text-xs text-twilight/40 dark:text-eggshell/40 mt-1">
          Submit a query to see the chain of thought
        </p>
      </div>
    </div>
  );
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

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
        labelColor: 'text-burnt-peach',
      };
    case 'observation':
      return {
        icon: Eye,
        label: 'Observation',
        dotBg: 'bg-muted-teal',
        labelColor: 'text-muted-teal',
      };
    case 'reasoning':
      return {
        icon: Brain,
        label: 'Reasoning',
        dotBg: 'bg-twilight dark:bg-apricot',
        labelColor: 'text-twilight dark:text-apricot',
      };
    default:
      return {
        icon: Brain,
        label: 'Thought',
        dotBg: 'bg-twilight',
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

/**
 * Format timestamp to readable time
 */
function formatTime(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
}

export default ChainOfThought;
