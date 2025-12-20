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
      <div
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle();
          }
        }}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        className={cn(
          "w-full flex items-center gap-3 p-4",
          "hover:bg-twilight/5 dark:hover:bg-eggshell/5",
          "transition-all duration-200 cursor-pointer",
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
            onClick={(e) => {
              e.stopPropagation();
              onViewPrompt(e);
            }}
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
      </div>
      
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
                  data={phaseEntry.data}
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
 * QualityFlagsPills Component
 * Displays quality flags as small pills.
 */
function QualityFlagsPills({ flags }) {
  if (!flags || flags.length === 0) return null;
  
  const flagConfig = {
    'sparse_tech_stack': { icon: Code2, label: 'Limited Tech Info' },
    'no_culture_data': { icon: Users, label: 'No Culture Data' },
    'few_gaps_identified': { icon: AlertTriangle, label: 'Few Gaps Found' },
    'high_score_low_data': { icon: TrendingUp, label: 'Score vs Data Mismatch' },
    'insufficient_requirements': { icon: FileText, label: 'Few Requirements' },
    'SPARSE_TECH_STACK': { icon: Code2, label: 'Limited Tech' },
    'NO_REQUIREMENTS': { icon: Target, label: 'No Requirements' },
    'NO_CULTURE_SIGNALS': { icon: Users, label: 'No Culture Data' },
    'INFERRED_INDUSTRY': { icon: Lightbulb, label: 'Industry Inferred' },
    'LOW_SOURCE_COUNT': { icon: Database, label: 'Few Sources' },
    'default_score_suspected': { icon: AlertTriangle, label: 'Default Score' },
    'insufficient_gaps': { icon: Scale, label: 'Few Gaps' },
    'fundamental_mismatch': { icon: AlertTriangle, label: 'Mismatch Detected' },
  };
  
  return (
    <div className="flex flex-wrap gap-1 mt-2 pl-6">
      {flags.map((flag, i) => {
        const cfg = flagConfig[flag] || { icon: AlertTriangle, label: flag.replace(/_/g, ' ') };
        return (
          <span
            key={i}
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm",
              "bg-amber-500/10 text-amber-600 dark:text-amber-400",
              "text-[10px] font-medium border border-amber-500/20"
            )}
          >
            <cfg.icon className="w-2.5 h-2.5" />
            {cfg.label}
          </span>
        );
      })}
    </div>
  );
}

/**
 * EnrichedInsightCard - Phase-specific insight display for ReasoningDialog
 * Renders structured data as meaningful visual elements instead of raw JSON
 */
function EnrichedInsightCard({ data, phase }) {
  if (!data) return null;
  
  // Phase-specific rendering logic
  switch (phase) {
    case 'connecting':
      return (
        <div className="mt-3 space-y-1.5 pl-6 text-sm">
          {data.extracted_skills?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <span className="text-twilight/50 dark:text-eggshell/50 text-xs">Extracted skills:</span>
              {data.extracted_skills.map((skill, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium text-xs">
                  {skill}
                </span>
              ))}
            </div>
          )}
          {data.classification_reasoning && (
            <p className="text-twilight/50 dark:text-eggshell/50 italic text-xs">
              "{data.classification_reasoning}"
            </p>
          )}
        </div>
      );
      
    case 'deep_research':
      return (
        <div className="mt-3 space-y-2 pl-6 text-sm">
          {data.tech_stack?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <Code2 className="w-4 h-4 text-purple-500 shrink-0" />
              {data.tech_stack.map((tech, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium text-xs">
                  {tech}
                </span>
              ))}
            </div>
          )}
          {data.top_requirements?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-start">
              <Target className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <div className="flex-1">
                {data.top_requirements.map((req, i) => (
                  <span key={i} className="text-twilight/60 dark:text-eggshell/60 text-xs">
                    {req}{i < data.top_requirements.length - 1 && ' • '}
                  </span>
                ))}
              </div>
            </div>
          )}
          {data.search_queries?.length > 0 && (
            <details className="group">
              <summary className="cursor-pointer text-twilight/40 dark:text-eggshell/40 hover:text-twilight/60 flex items-center gap-1.5 text-xs">
                <Search className="w-3 h-3" />
                <span>{data.search_queries.length} search queries executed</span>
              </summary>
              <ul className="mt-1.5 ml-5 text-twilight/50 dark:text-eggshell/50 list-disc list-inside text-xs space-y-0.5">
                {data.search_queries.map((q, i) => (
                  <li key={i} className="truncate" title={q.query}>{q.purpose || q.query}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      );
      
    case 'research_reranker':
      return (
        <div className="mt-3 space-y-2 pl-6 text-sm">
          {data.top_sources?.length > 0 && (
            <details className="group" open>
              <summary className="cursor-pointer text-twilight/50 dark:text-eggshell/50 hover:text-twilight/70 flex items-center gap-1.5 text-xs">
                <Database className="w-3 h-3" />
                <span>{data.passing_count}/{data.total_count} sources passed quality gate</span>
              </summary>
              <ul className="mt-1.5 space-y-1">
                {data.top_sources.map((src, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0",
                      src.score >= 0.7 ? "bg-emerald-500/20 text-emerald-600" :
                      src.score >= 0.4 ? "bg-amber-500/20 text-amber-600" :
                      "bg-red-500/20 text-red-600"
                    )}>
                      {Math.round(src.score * 100)}%
                    </span>
                    <a href={src.url} target="_blank" rel="noopener noreferrer" 
                       className="truncate hover:text-burnt-peach transition-colors text-twilight/60 dark:text-eggshell/60" title={src.title}>
                      {src.title}
                    </a>
                  </li>
                ))}
              </ul>
            </details>
          )}
          {data.inferred_industry && (
            <div className="flex items-center gap-1.5 text-xs text-twilight/50 dark:text-eggshell/50">
              <Lightbulb className="w-3 h-3 text-amber-500" />
              <span>Inferred industry: <strong className="text-amber-600 dark:text-amber-400">{data.inferred_industry}</strong></span>
              {data.inferred_tech?.length > 0 && (
                <span className="text-twilight/40">({data.inferred_tech.join(', ')})</span>
              )}
            </div>
          )}
        </div>
      );
      
    case 'skeptical_comparison':
      return (
        <div className="mt-3 space-y-2 pl-6 text-sm">
          {data.genuine_gaps?.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-red-500 dark:text-red-400 font-medium mb-1 text-xs">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Gaps Identified:</span>
              </div>
              <ul className="ml-5 text-twilight/60 dark:text-eggshell/60 list-disc list-inside text-xs space-y-0.5">
                {data.genuine_gaps.map((gap, i) => (
                  <li key={i}>{gap}</li>
                ))}
              </ul>
            </div>
          )}
          {data.genuine_strengths?.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-emerald-500 dark:text-emerald-400 font-medium mb-1 text-xs">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Strengths:</span>
              </div>
              <ul className="ml-5 text-twilight/60 dark:text-eggshell/60 list-disc list-inside text-xs space-y-0.5">
                {data.genuine_strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {data.risk_justification && (
            <p className="text-twilight/50 dark:text-eggshell/50 italic text-xs">
              "{data.risk_justification}"
            </p>
          )}
        </div>
      );
      
    case 'skills_matching':
      return (
        <div className="mt-3 space-y-2 pl-6 text-sm">
          {data.top_matches?.length > 0 && (
            <div className="space-y-1">
              {data.top_matches.map((match, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className={cn(
                    "px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0",
                    match.confidence >= 70 ? "bg-emerald-500/20 text-emerald-600" :
                    match.confidence >= 40 ? "bg-amber-500/20 text-amber-600" :
                    "bg-red-500/20 text-red-600"
                  )}>
                    {match.confidence}%
                  </span>
                  <span className="text-twilight/60 dark:text-eggshell/60 truncate">
                    {match.requirement} → <strong>{match.matched_skill}</strong>
                  </span>
                </div>
              ))}
            </div>
          )}
          {data.unmatched_requirements?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center text-xs">
              <span className="text-red-500 dark:text-red-400">Unmatched:</span>
              {data.unmatched_requirements.map((req, i) => (
                <span key={i} className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-600 dark:text-red-400 text-[10px]">
                  {req}
                </span>
              ))}
            </div>
          )}
        </div>
      );
      
    case 'confidence_reranker':
      return (
        <div className="mt-3 space-y-2 pl-6 text-sm">
          {data.adjustment_rationale && (
            <p className="text-twilight/60 dark:text-eggshell/60 text-xs">
              <strong>Adjustment:</strong> {data.adjustment_rationale}
            </p>
          )}
          {data.data_quality && Object.keys(data.data_quality).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(data.data_quality).map(([key, value]) => (
                <span key={key} className={cn(
                  "px-2 py-0.5 rounded text-[10px] font-medium",
                  value === 'adequate' ? "bg-emerald-500/10 text-emerald-600" :
                  value === 'moderate' ? "bg-amber-500/10 text-amber-600" :
                  "bg-red-500/10 text-red-600"
                )}>
                  {key.replace(/_/g, ' ')}: {value}
                </span>
              ))}
            </div>
          )}
        </div>
      );
      
    case 'generate_results':
      return (
        <div className="mt-3 space-y-1 pl-6 text-sm">
          <div className="flex items-center gap-2 text-twilight/60 dark:text-eggshell/60 text-xs">
            <span>Context: <strong className="text-burnt-peach">{data.employer_context_type || 'default'}</strong></span>
            <span>•</span>
            <span>Score: <strong>{data.calibrated_score}%</strong> ({data.confidence_tier})</span>
          </div>
          {data.quality_warnings?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {data.quality_warnings.map((w, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 text-[10px]">
                  {w}
                </span>
              ))}
            </div>
          )}
        </div>
      );
      
    default:
      return null;
  }
}

/**
 * PhaseInsightsSummary - Renders structured insights for a phase
 * Now includes EnrichedInsightCard for meaningful data visualization
 */
function PhaseInsightsSummary({ phase, summary, insights, displayMeta, config, data }) {
  if (!summary) return null;
  
  // Determine if we have enriched data to show
  const hasEnrichedData = data && (
    data.tech_stack?.length > 0 ||
    data.extracted_skills?.length > 0 ||
    data.top_sources?.length > 0 ||
    data.genuine_gaps?.length > 0 ||
    data.top_matches?.length > 0 ||
    data.sources?.length > 0 ||
    data.adjustment_rationale ||
    data.search_queries?.length > 0
  );
  
  return (
    <div className={cn(
      "px-4 py-3 border-b border-twilight/5 dark:border-eggshell/5",
      "bg-gradient-to-r",
      config.gradientFromLight || "from-burnt-peach/5",
      "to-transparent"
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
              {metric.icon === 'database' && <Database className="w-3.5 h-3.5 text-cyan-500" />}
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

      {/* Quality Flags */}
      {displayMeta?.flags && displayMeta.flags.length > 0 && (
        <QualityFlagsPills flags={displayMeta.flags} />
      )}
      
      {/* Enriched Data Visualization */}
      {hasEnrichedData && (
        <EnrichedInsightCard data={data} phase={phase} />
      )}
      
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
          <ThoughtIcon className={cn("w-3.5 h-3.5", thoughtConfig.iconColor)} />
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
 * 
 * IMPORTANT: Icon colors must contrast with dotBg in both light and dark mode.
 * - dotBg provides the background color for the icon circle
 * - iconColor provides the icon's fill/stroke color
 */
function getThoughtConfig(type, tool) {
  switch (type) {
    case 'tool_call':
      return {
        icon: getToolIcon(tool),
        label: 'Tool Call',
        dotBg: 'bg-burnt-peach',
        iconColor: 'text-white',
        labelColor: 'text-burnt-peach',
      };
    case 'observation':
      return {
        icon: Eye,
        label: 'Observation',
        dotBg: 'bg-muted-teal',
        iconColor: 'text-white',
        labelColor: 'text-muted-teal',
      };
    case 'reasoning':
      return {
        icon: Brain,
        label: 'Reasoning',
        // Use purple-500 for consistent visibility in both modes
        dotBg: 'bg-purple-500',
        iconColor: 'text-white',
        labelColor: 'text-purple-500 dark:text-purple-400',
      };
    default:
      return {
        icon: Brain,
        label: 'Thought',
        dotBg: 'bg-twilight dark:bg-slate-600',
        iconColor: 'text-white dark:text-eggshell',
        labelColor: 'text-twilight dark:text-eggshell',
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
