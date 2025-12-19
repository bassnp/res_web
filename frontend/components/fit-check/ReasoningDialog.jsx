'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { 
  Brain, 
  X, 
  Wifi, 
  Search, 
  Scale, 
  Briefcase, 
  FileCheck2, 
  CheckCircle2, 
  Eye, 
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Clock,
  Database,
  FileText,
  Loader2,
  Code2,
  Target,
  Users,
  Gauge,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Shield,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { SystemPromptDialog } from './SystemPromptDialog';
import { extractPhaseInsights, parseThoughtContent, getPhaseDisplayMeta } from '@/lib/phaseInsights';
import { PHASE_CONFIG, PHASE_ORDER } from '@/lib/phaseConfig';

/**
 * ReasoningDialog Component
 * 
 * A beautifully styled dialog that displays the complete chain of thought
 * from the AI pipeline. Features:
 * - Phase-grouped thoughts with visual timeline
 * - Expandable data sections
 * - Click on any phase header to view its system prompt
 * - Smooth animations and modern glassmorphism design
 * 
 * @param {Object} props
 * @param {boolean} props.open - Whether dialog is open
 * @param {function} props.onOpenChange - Callback when open state changes
 * @param {Array} props.thoughts - Array of thought events
 * @param {Array} props.phaseHistory - Completed phase entries with data
 * @param {number} props.durationMs - Total analysis duration
 */
export function ReasoningDialog({
  open,
  onOpenChange,
  thoughts = [],
  phaseHistory = [],
  durationMs = null,
}) {
  const [selectedPhase, setSelectedPhase] = useState(null);
  const [expandedPhases, setExpandedPhases] = useState({});

  // Group thoughts by phase
  const thoughtsByPhase = useMemo(() => {
    const grouped = {};
    
    // Initialize all phases from phase history
    for (const phase of PHASE_ORDER) {
      grouped[phase] = {
        thoughts: [],
        phaseEntry: phaseHistory.find(p => p.phase === phase) || null,
      };
    }
    
    // Group thoughts into their respective phases
    for (const thought of thoughts) {
      if (thought.phase && grouped[thought.phase]) {
        grouped[thought.phase].thoughts.push(thought);
      }
    }
    
    return grouped;
  }, [thoughts, phaseHistory]);

  // Get phases that actually have content
  const activePhasesOrdered = useMemo(() => {
    return PHASE_ORDER.filter(phase => {
      const group = thoughtsByPhase[phase];
      return group.thoughts.length > 0 || group.phaseEntry;
    });
  }, [thoughtsByPhase]);

  // Toggle phase expansion
  const togglePhase = useCallback((phase) => {
    setExpandedPhases(prev => ({
      ...prev,
      [phase]: !prev[phase],
    }));
  }, []);

  // Handle clicking on phase header to show system prompt
  const handlePhasePromptClick = useCallback((phase, e) => {
    e.stopPropagation();
    setSelectedPhase(phase);
  }, []);

  // Close system prompt dialog
  const handlePromptClose = useCallback(() => {
    setSelectedPhase(null);
  }, []);

  // Collapse all phases by default when dialog opens
  useEffect(() => {
    if (open) {
      const initialExpanded = {};
      for (const phase of activePhasesOrdered) {
        initialExpanded[phase] = false;
      }
      setExpandedPhases(initialExpanded);
    }
  }, [open, activePhasesOrdered]);

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className={cn(
          "max-w-4xl max-h-[85vh] overflow-hidden p-0",
          "bg-gradient-to-br from-background via-background to-background/95",
          "border border-twilight/10 dark:border-eggshell/10",
          "shadow-2xl shadow-burnt-peach/10 dark:shadow-burnt-peach/5",
          // Glassmorphism effect
          "backdrop-blur-xl",
          // Custom styling
          "reasoning-dialog"
        )}>
          {/* Header with gradient */}
          <DialogHeader className={cn(
            "p-6 pb-4",
            "bg-gradient-to-r from-burnt-peach/5 via-transparent to-muted-teal/5",
            "border-b border-twilight/10 dark:border-eggshell/10"
          )}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-10 h-10 rounded-sm flex items-center justify-center",
                  "bg-gradient-to-br from-burnt-peach to-burnt-peach/80",
                  "shadow-lg shadow-burnt-peach/25",
                  "animate-icon-bounce"
                )}>
                  <Brain className="w-5 h-5 text-eggshell" />
                </div>
                <div>
                  <DialogTitle className="text-xl font-bold text-twilight dark:text-eggshell">
                    Chain of Thought
                  </DialogTitle>
                  <DialogDescription className="text-sm text-twilight/60 dark:text-eggshell/60 mt-0.5">
                    Complete AI reasoning trace • {activePhasesOrdered.length} phases executed
                  </DialogDescription>
                </div>
              </div>
              
              {/* Duration badge */}
              {durationMs && (
                <div className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-full",
                  "bg-muted-teal/10 text-muted-teal",
                  "text-sm font-medium"
                )}>
                  <Clock className="w-3.5 h-3.5" />
                  {(durationMs / 1000).toFixed(1)}s
                </div>
              )}
            </div>
          </DialogHeader>

          {/* Scrollable content */}
          <div className="overflow-y-auto max-h-[calc(85vh-180px)] p-6 custom-scrollbar">
            <div className="space-y-4">
              {activePhasesOrdered.map((phase, phaseIndex) => (
                <PhaseSection
                  key={phase}
                  phase={phase}
                  config={PHASE_CONFIG[phase]}
                  data={thoughtsByPhase[phase]}
                  isExpanded={expandedPhases[phase] ?? true}
                  onToggle={() => togglePhase(phase)}
                  onViewPrompt={(e) => handlePhasePromptClick(phase, e)}
                  isLast={phaseIndex === activePhasesOrdered.length - 1}
                />
              ))}
            </div>
            
            {/* Empty state */}
            {activePhasesOrdered.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className={cn(
                  "w-16 h-16 rounded-full flex items-center justify-center mb-4",
                  "bg-twilight/5 dark:bg-eggshell/5"
                )}>
                  <Brain className="w-8 h-8 text-twilight/30 dark:text-eggshell/30" />
                </div>
                <p className="text-twilight/60 dark:text-eggshell/60 font-medium">
                  No reasoning data available
                </p>
                <p className="text-sm text-twilight/40 dark:text-eggshell/40 mt-1">
                  The chain of thought will appear after analysis
                </p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Nested System Prompt Dialog */}
      <SystemPromptDialog
        open={selectedPhase !== null}
        onOpenChange={handlePromptClose}
        phase={selectedPhase}
      />
    </>
  );
}

/**
 * PhaseSection Component - Renders a single phase with its thoughts
 */
function PhaseSection({ 
  phase, 
  config, 
  data, 
  isExpanded, 
  onToggle, 
  onViewPrompt,
  isLast 
}) {
  const { thoughts, phaseEntry } = data;
  const Icon = config.icon;
  
  // Extract structured insights from phase summary
  const insights = useMemo(() => {
    return phaseEntry?.summary ? extractPhaseInsights(phase, phaseEntry.summary) : null;
  }, [phase, phaseEntry?.summary]);
  
  const displayMeta = useMemo(() => {
    return insights ? getPhaseDisplayMeta(phase, insights) : null;
  }, [phase, insights]);
  
  return (
    <div className={cn(
      "rounded-sm overflow-hidden",
      "border border-twilight/10 dark:border-eggshell/10",
      "bg-white/50 dark:bg-twilight/20",
      "transition-all duration-300 ease-out",
      isExpanded 
        ? "shadow-lg shadow-twilight/5 dark:shadow-eggshell/5 scale-[1.01]" 
        : "shadow-sm hover:shadow-md"
    )}>
      {/* Phase Header */}
      <button
        onClick={onToggle}
        className={cn(
          "w-full flex items-center gap-3 p-4",
          "hover:bg-twilight/5 dark:hover:bg-eggshell/5",
          "transition-all duration-200",
          "border-l-4",
          config.borderColor,
          isExpanded && "bg-twilight/[0.02] dark:bg-eggshell/[0.02]"
        )}
      >
        {/* Phase Icon */}
        <div className={cn(
          "w-10 h-10 rounded-sm flex items-center justify-center flex-shrink-0",
          config.bgColor,
          "shadow-md"
        )}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        
        {/* Phase Info */}
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <h3 className={cn("font-semibold", config.textColor)}>
              {config.label}
            </h3>
            {phaseEntry?.status === 'complete' && (
              <CheckCircle2 className="w-4 h-4 text-muted-teal" />
            )}
          </div>
          <p className="text-xs text-twilight/60 dark:text-eggshell/60 mt-0.5">
            {config.description}
          </p>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* View Prompt Button */}
          <button
            onClick={onViewPrompt}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-sm",
              "hover:bg-twilight/10 dark:hover:bg-eggshell/10",
              "text-twilight/50 dark:text-eggshell/50",
              "hover:text-burnt-peach transition-all duration-200",
              "group text-xs font-medium"
            )}
            title="View system prompt"
          >
            <FileText className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            <span className="hidden sm:inline">Read Node System Prompt</span>
          </button>
          
          {/* Expand/Collapse */}
          <div className={cn(
            "p-1 rounded-sm",
            "text-twilight/40 dark:text-eggshell/40",
            "transition-transform duration-300 ease-out",
            isExpanded && "rotate-90"
          )}>
            <ChevronRight className="w-5 h-5" />
          </div>
        </div>
      </button>
      
      {/* Expanded Content - Smooth accordion animation */}
      <div 
        className={cn(
          "grid transition-all duration-300 ease-out",
          isExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="overflow-hidden">
          <div className={cn(
            "border-t border-twilight/10 dark:border-eggshell/10",
            "bg-twilight/[0.02] dark:bg-eggshell/[0.02]"
          )}>
            {/* Phase Summary with structured insights */}
            {phaseEntry?.summary && (
              <div className={cn(
                "transition-all duration-300 delay-75",
                isExpanded ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0"
              )}>
                <PhaseInsightsSummary 
                  phase={phase}
                  summary={phaseEntry.summary}
                  insights={insights}
                  displayMeta={displayMeta}
                  config={config}
                />
              </div>
            )}
            
            {/* Thoughts List */}
            <div className="p-4 space-y-3">
              {thoughts.length > 0 ? (
                thoughts.map((thought, index) => (
                  <div 
                    key={`${thought.step}-${index}`}
                    className={cn(
                      "transition-all duration-300",
                      isExpanded ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0"
                    )}
                    style={{ transitionDelay: isExpanded ? `${100 + index * 50}ms` : '0ms' }}
                  >
                    <ThoughtItem
                      thought={thought}
                      config={config}
                      phase={phase}
                    />
                  </div>
                ))
              ) : (
                <div className={cn(
                  "text-center py-4 text-sm text-twilight/40 dark:text-eggshell/40",
                  "transition-all duration-300 delay-100",
                  isExpanded ? "translate-y-0 opacity-100" : "-translate-y-2 opacity-0"
                )}>
                  No detailed thoughts recorded for this phase
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * PhaseInsightsSummary - Renders structured insights for a phase
 */
function PhaseInsightsSummary({ phase, summary, insights, displayMeta, config }) {
  if (!summary) return null;
  
  return (
    <div className={cn(
      "px-4 py-3 border-b border-twilight/5 dark:border-eggshell/5",
      "bg-gradient-to-r",
      `from-${config.color}-500/5 to-transparent`
    )}>
      {/* Metrics row for phases that have them */}
      {displayMeta?.metrics && displayMeta.metrics.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {displayMeta.metrics.map((metric, i) => (
            <div key={i} className={cn(
              "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full",
              "bg-white/80 dark:bg-twilight/40",
              "border border-twilight/10 dark:border-eggshell/10",
              "text-xs font-medium"
            )}>
              {metric.icon === 'code' && <Code2 className="w-3.5 h-3.5 text-purple-500" />}
              {metric.icon === 'target' && <Target className="w-3.5 h-3.5 text-amber-500" />}
              {metric.icon === 'users' && <Users className="w-3.5 h-3.5 text-blue-500" />}
              <span className="text-twilight/70 dark:text-eggshell/70">
                {metric.label}: <span className="font-bold">{metric.value}</span>
              </span>
            </div>
          ))}
        </div>
      )}
      
      {/* Confidence indicator for reranker phases */}
      {insights?.type === 'confidence' && insights.confidence && (
        <div className="mb-3">
          <div className="flex items-center gap-3 mb-1">
            <div className="flex-1 h-2.5 bg-twilight/10 dark:bg-eggshell/10 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  insights.confidence >= 70 ? "bg-muted-teal" :
                  insights.confidence >= 40 ? "bg-amber-500" : "bg-red-500"
                )}
                style={{ width: `${Math.min(100, Math.max(0, insights.confidence))}%` }}
              />
            </div>
            <span className={cn(
              "font-bold tabular-nums text-sm",
              insights.confidence >= 70 ? "text-muted-teal" :
              insights.confidence >= 40 ? "text-amber-500" : "text-red-500"
            )}>
              {insights.confidence}%
            </span>
          </div>
          {insights.tier && (
            <div className="flex items-center gap-1.5">
              <Gauge className={cn(
                "w-4 h-4",
                insights.tier === 'HIGH' ? "text-muted-teal" :
                insights.tier === 'MEDIUM' ? "text-amber-500" : "text-red-500"
              )} />
              <span className={cn(
                "text-xs font-medium",
                insights.tier === 'HIGH' ? "text-muted-teal" :
                insights.tier === 'MEDIUM' ? "text-amber-500" : "text-red-500"
              )}>
                {insights.tier} Confidence
              </span>
            </div>
          )}
        </div>
      )}
      
      {/* Quality gate indicator */}
      {insights?.type === 'quality_gate' && (
        <div className="flex items-center gap-3 mb-2">
          <div className={cn(
            "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
            insights.qualityTier === 'HIGH' ? "bg-muted-teal/10 text-muted-teal" :
            insights.qualityTier === 'MEDIUM' ? "bg-amber-500/10 text-amber-500" :
            "bg-red-500/10 text-red-500"
          )}>
            <Shield className="w-3.5 h-3.5" />
            {insights.qualityTier === 'HIGH' ? 'CONFIDENT' :
             insights.qualityTier === 'MEDIUM' ? 'UNCERTAIN' : 'MISUNDERSTANDING'}
          </div>
          {insights.action && insights.action !== 'CONTINUE' && (
            <div className="inline-flex items-center gap-1 text-xs text-twilight/60 dark:text-eggshell/60">
              <TrendingUp className="w-3 h-3" />
              {insights.action.replace(/_/g, ' ')}
            </div>
          )}
        </div>
      )}
      
      {/* Summary text */}
      <div className="flex items-start gap-2">
        <Lightbulb className="w-4 h-4 text-burnt-peach flex-shrink-0 mt-0.5" />
        <p className="text-sm text-twilight/70 dark:text-eggshell/70">
          {displayMeta?.summary || summary}
        </p>
      </div>
      
      {/* Reasoning excerpt for confidence reranker */}
      {insights?.reasoning && (
        <p className="text-xs text-twilight/50 dark:text-eggshell/50 mt-2 pl-6 italic line-clamp-3">
          {insights.reasoning}
        </p>
      )}
    </div>
  );
}

/**
 * ThoughtItem Component - Renders a single thought entry with enhanced insights
 */
function ThoughtItem({ thought, config, phase }) {
  const [isDataExpanded, setIsDataExpanded] = useState(false);
  
  const thoughtConfig = getThoughtConfig(thought.type, thought.tool);
  const ThoughtIcon = thoughtConfig.icon;
  
  // Parse and enhance thought content
  const enhancedContent = useMemo(() => {
    return parseThoughtContent({
      type: thought.type,
      tool: thought.tool,
      input: thought.input,
      content: thought.content,
    });
  }, [thought.type, thought.tool, thought.input, thought.content]);
  
  return (
    <div className={cn(
      "rounded-sm p-3",
      "bg-white dark:bg-twilight/30",
      "border border-twilight/10 dark:border-eggshell/10",
      "hover:border-twilight/20 dark:hover:border-eggshell/20",
      "transition-colors duration-200"
    )}>
      <div className="flex items-start gap-3">
        {/* Thought Type Icon */}
        <div className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
          thoughtConfig.dotBg
        )}>
          <ThoughtIcon className="w-3.5 h-3.5 text-white" />
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              "text-xs font-semibold uppercase tracking-wide",
              thoughtConfig.labelColor
            )}>
              {thoughtConfig.label}
            </span>
            <span className="text-xs text-twilight/40 dark:text-eggshell/40">
              Step {thought.step}
            </span>
          </div>
          
          {/* Tool Call Content - Enhanced */}
          {thought.type === 'tool_call' && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xs text-twilight/60 dark:text-eggshell/60">Tool:</span>
                <code className={cn(
                  "text-xs px-2 py-0.5 rounded-sm font-mono",
                  "bg-burnt-peach/10 text-burnt-peach",
                  "border border-burnt-peach/20"
                )}>
                  {formatToolName(thought.tool)}
                </code>
              </div>
              {enhancedContent?.displaySummary ? (
                <p className="text-sm text-twilight/70 dark:text-eggshell/70">
                  {enhancedContent.displaySummary}
                </p>
              ) : thought.input && (
                <p className="text-sm text-twilight/70 dark:text-eggshell/70">
                  <span className="text-twilight/50 dark:text-eggshell/50">Query: </span>
                  &quot;{thought.input}&quot;
                </p>
              )}
            </div>
          )}
          
          {/* Observation Content - Enhanced */}
          {thought.type === 'observation' && thought.content && (
            <p className="text-sm text-twilight/70 dark:text-eggshell/70">
              {enhancedContent?.displaySummary || thought.content}
            </p>
          )}
          
          {/* Reasoning Content - Enhanced with extracted insights */}
          {thought.type === 'reasoning' && thought.content && (
            <div className="space-y-2">
              <p className="text-sm text-twilight/70 dark:text-eggshell/70 italic">
                &quot;{enhancedContent?.displaySummary || thought.content}&quot;
              </p>
              
              {/* Show extracted insights if available */}
              {enhancedContent?.extractedData && (
                <div className="flex flex-wrap gap-1.5">
                  {enhancedContent.extractedData.confidence && (
                    <span className={cn(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs",
                      enhancedContent.extractedData.confidence >= 70 ? "bg-muted-teal/10 text-muted-teal" :
                      enhancedContent.extractedData.confidence >= 40 ? "bg-amber-500/10 text-amber-500" :
                      "bg-red-500/10 text-red-500"
                    )}>
                      <Gauge className="w-3 h-3" />
                      {enhancedContent.extractedData.confidence}%
                    </span>
                  )}
                  {enhancedContent.extractedData.tier && (
                    <span className={cn(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs",
                      enhancedContent.extractedData.tier === 'HIGH' ? "bg-muted-teal/10 text-muted-teal" :
                      enhancedContent.extractedData.tier === 'MEDIUM' ? "bg-amber-500/10 text-amber-500" :
                      "bg-red-500/10 text-red-500"
                    )}>
                      {enhancedContent.extractedData.tier}
                    </span>
                  )}
                  {enhancedContent.extractedData.technologies?.slice(0, 4).map((tech, i) => (
                    <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs bg-purple-500/10 text-purple-500">
                      <Code2 className="w-3 h-3" />
                      {tech}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* Data reveal toggle - smaller and less prominent */}
          {(thought.input || thought.content) && (
            <button
              onClick={() => setIsDataExpanded(!isDataExpanded)}
              className={cn(
                "flex items-center gap-1 mt-2",
                "text-[10px] text-twilight/40 dark:text-eggshell/40",
                "hover:text-twilight/60 dark:hover:text-eggshell/60",
                "transition-colors duration-200"
              )}
            >
              <Database className="w-2.5 h-2.5" />
              <span>Raw data</span>
              <ChevronDown className={cn(
                "w-2.5 h-2.5 transition-transform",
                isDataExpanded && "rotate-180"
              )} />
            </button>
          )}
          
          {/* Expanded data */}
          {isDataExpanded && (
            <div className={cn(
              "mt-2 p-2 rounded-sm",
              "bg-twilight/5 dark:bg-eggshell/5",
              "border border-twilight/10 dark:border-eggshell/10",
              "font-mono text-[10px] overflow-x-auto"
            )}>
              <pre className="whitespace-pre-wrap text-twilight/60 dark:text-eggshell/60">
                {JSON.stringify({
                  tool: thought.tool,
                  input: thought.input,
                  content: thought.content,
                }, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get configuration for thought type styling
 */
function getThoughtConfig(type, tool) {
  switch (type) {
    case 'tool_call':
      return {
        icon: getToolIcon(tool),
        label: 'Tool Call',
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

export default ReasoningDialog;
