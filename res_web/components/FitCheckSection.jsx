'use client';

import { useState, useRef } from 'react';
import { Sparkles, RefreshCw, AlertCircle, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import InteractiveGridDots from '@/components/InteractiveGridDots';
import { InputPanel } from '@/components/fit-check/InputPanel';
import { ThinkingPanel } from '@/components/fit-check/ThinkingPanel';
import { ResultsSection } from '@/components/fit-check/ResultsSection';
import { ComparisonChain } from '@/components/fit-check/ComparisonChain';
import { useFitCheck } from '@/hooks/use-fit-check';
import { cn } from '@/lib/utils';

/**
 * FitCheckSection Component
 * 
 * Main orchestrator for the "See if I'm fit for you!" feature.
 * Manages three distinct UI phases:
 * 1. Input Phase - Single centered container with input
 * 2. Expanded Phase - Two-column layout with input + thinking panel
 * 3. Results Phase - Compact header + two result cards below
 */
export function FitCheckSection() {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  
  const {
    status,
    statusMessage,
    thoughts,
    response,
    error,
    durationMs,
    uiPhase,
    parsedResponse,
    submitQuery,
    reset,
    isLoading,
  } = useFitCheck();

  // Handle form submission
  const handleSubmit = (query) => {
    if (query.length >= 3) {
      submitQuery(query);
    }
  };

  // Handle new query (reset)
  const handleNewQuery = () => {
    reset();
    setInput('');
    setTimeout(() => textareaRef.current?.focus(), 100);
  };

  // Determine container width class based on phase
  const getContainerClass = () => {
    switch (uiPhase) {
      case 'input':
        return 'max-w-2xl';
      case 'expanded':
        return 'max-w-5xl fit-check-container-expanded';
      case 'results':
        return 'max-w-5xl';
      default:
        return 'max-w-2xl';
    }
  };

  return (
    <section 
      id="fit-check" 
      className="py-16 fit-check-section"
      aria-label="AI Fit Check Analysis"
    >
      <div className="container mx-auto px-6">
        {/* Dynamic width container */}
        <div className={cn(
          "mx-auto transition-all duration-500 ease-out",
          getContainerClass()
        )}>
          
          {/* Section Title - outside card for input phase */}
          {uiPhase === 'input' && <Header compact={false} />}

          {/* Main card container */}
          <div className={cn(
            "relative bg-background/95 backdrop-blur-sm rounded-[10px]",
            "shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)]",
            "border border-twilight/8 dark:border-eggshell/8 overflow-hidden"
          )}>
            <InteractiveGridDots />
            
            <div className="relative z-10">
              {/* Phase-based layout */}
              {uiPhase === 'expanded' ? (
                // EXPANDED PHASE: Two-column layout
                <div className="flex flex-col lg:flex-row min-h-[400px]">
                  {/* Left column: Comparison Chain summary */}
                  <div className="lg:w-1/2 flex flex-col items-center justify-center">
                    <ComparisonChain
                      thoughts={thoughts}
                      status={status}
                      statusMessage={statusMessage}
                    />
                  </div>

                  {/* Divider */}
                  <div className="hidden lg:block w-px bg-twilight/10 dark:bg-eggshell/10 animate-divider-grow" />
                  
                  {/* Right column: Thinking panel */}
                  <div className="lg:w-1/2 border-t lg:border-t-0 border-twilight/10 dark:border-eggshell/10">
                    <ThinkingPanel
                      thoughts={thoughts}
                      isThinking={status === 'thinking'}
                      isVisible={true}
                      status={status}
                      statusMessage={statusMessage}
                    />
                  </div>
                </div>
              ) : uiPhase === 'results' ? (
                // RESULTS PHASE: Compact header with new query button
                <div className="p-4 md:p-6">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-burnt-peach" />
                      <h2 className="text-lg md:text-xl font-bold text-twilight dark:text-eggshell">
                        Analysis Complete
                      </h2>
                      {durationMs && (
                        <span className="flex items-center gap-1 text-xs text-twilight/50 dark:text-eggshell/50 ml-2">
                          <Clock className="w-3 h-3" />
                          {(durationMs / 1000).toFixed(1)}s
                        </span>
                      )}
                    </div>
                    <Button
                      type="button"
                      onClick={handleNewQuery}
                      className="bg-muted-teal hover:bg-muted-teal/90 text-eggshell px-4 py-2 rounded-lg hover:scale-[1.02] transition-all duration-200"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Try Another
                    </Button>
                  </div>
                </div>
              ) : (
                // INPUT PHASE: Standard centered layout
                <div className="p-6 md:p-8">
                  <InputPanel
                    ref={textareaRef}
                    value={input}
                    onChange={setInput}
                    onSubmit={handleSubmit}
                    isDisabled={isLoading || status === 'complete'}
                    isLoading={isLoading}
                    statusMessage={statusMessage}
                    uiPhase={uiPhase}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Error State - shown in any phase */}
          {error && (
            <div className="mt-6 animate-fade-in">
              <div className="bg-red-50 dark:bg-red-950/30 rounded-lg p-4 border border-red-200 dark:border-red-800/50">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-800 dark:text-red-200">
                      {error.code === 'CONNECTION_ERROR' 
                        ? 'Connection Failed'
                        : 'Analysis Error'
                      }
                    </p>
                    <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                      {error.message}
                    </p>
                    <button
                      onClick={handleNewQuery}
                      className="text-sm text-red-600 dark:text-red-300 underline mt-2 hover:text-red-800 dark:hover:text-red-100"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results Section - Two cards below main container */}
          <ResultsSection
            parsedResponse={parsedResponse}
            durationMs={durationMs}
            isVisible={uiPhase === 'results'}
          />
        </div>
      </div>
    </section>
  );
}

/**
 * Header Component - Title and description for the section
 */
function Header({ compact = false }) {
  return (
    <div className={cn(
      "text-center",
      compact ? "mb-3" : "mb-6"
    )}>
      <div className="flex items-center justify-center gap-2 mb-2">
        <Sparkles className={cn(
          "text-burnt-peach animate-pulse",
          compact ? "w-4 h-4" : "w-5 h-5"
        )} />
        <h2 className={cn(
          "font-bold text-twilight dark:text-eggshell",
          compact ? "text-xl" : "text-2xl md:text-3xl"
        )}>
          See if I&apos;m <span className="text-burnt-peach">fit</span> for you!
        </h2>
      </div>
      {!compact && (
        <p className="text-twilight/60 dark:text-eggshell/60 text-sm">
          Tell me about your company or the position, and I&apos;ll explain why we&apos;re a great match.
        </p>
      )}
    </div>
  );
}

export default FitCheckSection;
