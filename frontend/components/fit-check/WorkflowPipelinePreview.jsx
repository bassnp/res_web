'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Wifi, 
  Search, 
  CheckCircle2, 
  Scale, 
  Briefcase, 
  FileCheck2,
  Loader2,
  Brain
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { PHASE_CONFIG, PHASE_ORDER } from '@/lib/phaseConfig';

/**
 * Pipeline phases with metadata for the animated preview.
 */
const PIPELINE_PHASES = PHASE_ORDER.map(id => ({
  id,
  ...PHASE_CONFIG[id],
  color: PHASE_CONFIG[id].gradient,
  borderColor: PHASE_CONFIG[id].previewBorder,
}));

/**
 * WorkflowPipelinePreview Component
 * 
 * Animated showcase of the AI pipeline phases that runs in a loop.
 * Displays on the left side of the input panel to preview the workflow.
 * 
 * @param {Object} props
 * @param {boolean} props.compact - Whether to render in compact horizontal mode for mobile
 */
export function WorkflowPipelinePreview({ compact = false }) {
  const [activePhaseIndex, setActivePhaseIndex] = useState(-1);
  const [completedPhases, setCompletedPhases] = useState([]);
  const [isAnimating, setIsAnimating] = useState(false);
  const animationRef = useRef(null);
  const phaseRef = useRef(activePhaseIndex);
  const containerRef = useRef(null);
  const phaseRefs = useRef([]);

  // Keep ref in sync with state
  useEffect(() => {
    phaseRef.current = activePhaseIndex;
  }, [activePhaseIndex]);

  // Single, reliable animation loop using recursive setTimeout
  useEffect(() => {
    const runAnimationStep = () => {
      const currentPhase = phaseRef.current;
      
      if (currentPhase === -1) {
        // Start: activate first phase
        setActivePhaseIndex(0);
        setIsAnimating(true);
        animationRef.current = setTimeout(runAnimationStep, 1200);
      } else if (currentPhase < PIPELINE_PHASES.length - 1) {
        // Middle: mark current complete, advance to next
        setCompletedPhases(prev => [...prev, currentPhase]);
        setActivePhaseIndex(currentPhase + 1);
        animationRef.current = setTimeout(runAnimationStep, 1200);
      } else {
        // End: mark last phase (Generate Results) as complete (green)
        setCompletedPhases(prev => [...prev, currentPhase]);
        setActivePhaseIndex(-1); // No active phase - all complete
        setIsAnimating(false);
        
        // Show all green for same duration as phase transitions, then restart
        animationRef.current = setTimeout(() => {
          setCompletedPhases([]);
          setActivePhaseIndex(0);
          setIsAnimating(true);
          animationRef.current = setTimeout(runAnimationStep, 1200);
        }, 1200); // Same timing as phase transitions for even rhythm
      }
    };

    // Initial start delay
    setIsAnimating(true);
    animationRef.current = setTimeout(runAnimationStep, 800);

    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
    };
  }, []); // Only run once on mount

  return (
    <div className={cn(
      "flex w-full",
      compact 
        ? "flex-col items-center justify-center py-3 px-4 gap-2" 
        : "flex-col h-full py-4 px-3"
    )}>
      {/* Header - docked at top */}
      <div className={cn(
        "flex flex-col items-center justify-center",
        compact ? "flex-shrink-0" : "mb-4 flex-shrink-0"
      )}>
        <div className="flex items-center justify-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-burnt-peach to-burnt-peach/60 flex items-center justify-center pipeline-icon-glow">
            <Brain className="w-3 h-3 text-eggshell" />
          </div>
          <span className={cn(
            "font-semibold text-twilight/80 dark:text-eggshell/80 uppercase tracking-wide",
            compact ? "text-[10px]" : "text-xs"
          )}>
            {"Powered by Agentic A.I."}
          </span>
        </div>
      </div>

      {/* Compact Mode: Horizontal pill layout */}
      {compact ? (
        <div className="flex flex-wrap items-center justify-center gap-1.5" ref={containerRef}>
          {PIPELINE_PHASES.map((phase, index) => {
            const isActive = index === activePhaseIndex;
            const isComplete = completedPhases.includes(index);
            const Icon = phase.icon;

            return (
              <div 
                key={phase.id}
                ref={(el) => (phaseRefs.current[index] = el)}
                className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded-full transition-all duration-300",
                  "border text-[9px] font-medium whitespace-nowrap cursor-default hover:scale-110 hover:-translate-y-0.5",
                  isComplete && "bg-muted-teal/20 border-muted-teal/50 text-muted-teal",
                  isActive && `${phase.bgColorMuted} ${phase.previewBorder} ${phase.textColor} pipeline-phase-active`,
                  !isComplete && !isActive && "bg-twilight/5 dark:bg-eggshell/5 border-twilight/15 dark:border-eggshell/15 text-twilight/40 dark:text-eggshell/40"
                )}
              >
                <div className={cn(
                  "w-3.5 h-3.5 rounded-full flex items-center justify-center flex-shrink-0",
                  isComplete && "bg-muted-teal text-eggshell",
                  isActive && `bg-gradient-to-br ${phase.color} text-eggshell`,
                  !isComplete && !isActive && "bg-twilight/10 dark:bg-eggshell/10"
                )}>
                  {isComplete ? (
                    <CheckCircle2 className="w-2 h-2" />
                  ) : (
                    <Icon className="w-2 h-2" />
                  )}
                </div>
              </div>
            );
          })}
          {/* Active spinner */}
          {activePhaseIndex >= 0 && isAnimating && (
            <Loader2 className={cn("w-3.5 h-3.5 animate-spin flex-shrink-0", PIPELINE_PHASES[activePhaseIndex].textColor)} />
          )}
        </div>
      ) : (
        /* Full Mode: Vertical pipeline layout - centered in remaining space */
        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Pipeline Steps - wrapper includes space for spinner to keep content centered */}
          <div className="relative w-full max-w-[184px] pl-3" ref={containerRef}>
            <div className="flex flex-col">
              {PIPELINE_PHASES.map((phase, index) => {
                const isActive = index === activePhaseIndex;
                const isComplete = completedPhases.includes(index);
                const isPending = !isActive && !isComplete;
                const Icon = phase.icon;

                return (
                  <div key={phase.id} className="relative">
                    {/* Phase Node */}
                    <div
                      ref={(el) => (phaseRefs.current[index] = el)}
                      className={cn(
                        "flex items-center gap-2 px-2.5 py-2 rounded-sm transition-all duration-300",
                        "border cursor-default hover:scale-110 hover:-translate-y-1 relative",
                        isComplete && "bg-muted-teal/15 border-muted-teal/40",
                        isActive && `${phase.bgColorMuted} ${phase.previewBorder} pipeline-phase-active`,
                        isPending && "bg-twilight/5 dark:bg-eggshell/5 border-twilight/10 dark:border-eggshell/10"
                      )}
                    >
                      {/* Active Spinner - Surgical addition to ensure perfect alignment with card transforms */}
                      {isActive && isAnimating && (
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                          <Loader2 className={cn("w-3.5 h-3.5 animate-spin", phase.textColor)} />
                        </div>
                      )}

                      {/* Icon */}
                      <div
                        className={cn(
                          "w-5 h-5 rounded-sm flex items-center justify-center flex-shrink-0 transition-all duration-300",
                          isComplete && "bg-muted-teal text-eggshell",
                          isActive && `bg-gradient-to-br ${phase.color} text-eggshell`,
                          isPending && "bg-twilight/10 dark:bg-eggshell/10 text-twilight/30 dark:text-eggshell/30"
                        )}
                      >
                        {isComplete ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <Icon className="w-3 h-3" />
                        )}
                      </div>

                      {/* Label */}
                      <span
                        className={cn(
                          "text-[10px] font-medium transition-colors duration-300 truncate",
                          isComplete && "text-muted-teal",
                          isActive && "text-twilight dark:text-eggshell font-semibold pr-6",
                          isPending && "text-twilight/30 dark:text-eggshell/30"
                        )}
                      >
                        {phase.label}
                      </span>
                    </div>

                    {/* Connector - centered line between phases with even spacing */}
                    {index < PIPELINE_PHASES.length - 1 && (
                      <div className="flex items-center justify-center h-4 w-full py-1">
                        <div
                          className={cn(
                            "w-0.5 h-full rounded-full transition-all duration-500",
                            isComplete ? "bg-muted-teal/60" : "bg-twilight/10 dark:bg-eggshell/10"
                          )}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowPipelinePreview;
