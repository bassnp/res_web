'use client';

import { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, AlertCircle, RefreshCw, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import InteractiveGridDots from '@/components/InteractiveGridDots';
import ThinkingTimeline from '@/components/ThinkingTimeline';
import { useFitCheck } from '@/hooks/use-fit-check';
import { cn } from '@/lib/utils';

/**
 * FitCheckSection Component
 * 
 * Main chatbot interface for the "See if I'm fit for you!" feature.
 * Allows employers to enter company names or job descriptions,
 * displays AI thinking process, and streams the personalized response.
 */
export function FitCheckSection() {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const responseRef = useRef(null);
  
  const {
    status,
    statusMessage,
    thoughts,
    response,
    error,
    durationMs,
    submitQuery,
    reset,
    isLoading,
  } = useFitCheck();

  // Auto-scroll response into view when streaming
  useEffect(() => {
    if (response && responseRef.current) {
      responseRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [response]);

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    const query = input.trim();
    if (query.length >= 3) {
      submitQuery(query);
    }
  };

  // Handle new query (reset)
  const handleNewQuery = () => {
    reset();
    setInput('');
    textareaRef.current?.focus();
  };

  // Check if input is valid
  const isValidInput = input.trim().length >= 3;
  const isSubmitDisabled = !isValidInput || isLoading;

  return (
    <section 
      id="fit-check" 
      className="py-16 fit-check-section"
      aria-label="AI Fit Check Analysis"
    >
      <div className="container mx-auto px-6">
        <div className="max-w-2xl mx-auto">
          {/* Main card container */}
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden">
            <InteractiveGridDots />
            
            <div className="relative z-10 p-6 md:p-8">
              {/* Header */}
              <div className="text-center mb-6">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-burnt-peach animate-pulse" />
                  <h2 className="text-2xl md:text-3xl font-bold text-twilight dark:text-eggshell">
                    See if I&apos;m <span className="text-burnt-peach">fit</span> for you!
                  </h2>
                </div>
                <p className="text-twilight/60 dark:text-eggshell/60 text-sm">
                  Tell me about your company or the position, and I&apos;ll explain why we&apos;re a great match.
                </p>
              </div>

              {/* Input Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Enter a company name (e.g., 'Google', 'Stripe') or describe the position you're hiring for..."
                    className={cn(
                      "min-h-[120px] resize-none transition-all duration-200",
                      "bg-white dark:bg-twilight/30",
                      "border-twilight/20 dark:border-eggshell/20",
                      "focus:border-burnt-peach focus:ring-burnt-peach/30",
                      "placeholder:text-twilight/40 dark:placeholder:text-eggshell/40",
                      "fit-check-input"
                    )}
                    disabled={isLoading || status === 'complete'}
                    maxLength={2000}
                    aria-label="Company name or job description"
                  />
                  
                  {/* Character count */}
                  <div className="absolute bottom-2 right-2 text-xs text-twilight/40 dark:text-eggshell/40">
                    {input.length}/2000
                  </div>
                </div>

                {/* Submit button or New Query button */}
                {status === 'complete' ? (
                  <Button
                    type="button"
                    onClick={handleNewQuery}
                    className="w-full bg-muted-teal hover:bg-muted-teal/90 text-eggshell py-5 rounded-xl hover:scale-[1.02] transition-all duration-200"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Try Another Query
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    disabled={isSubmitDisabled}
                    className={cn(
                      "w-full py-5 rounded-xl transition-all duration-200",
                      "bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell",
                      isValidInput && !isLoading && "animate-pulse-glow hover:scale-[1.02]",
                      isSubmitDisabled && "opacity-60 cursor-not-allowed"
                    )}
                    aria-label={isLoading ? 'Analyzing...' : 'Analyze fit'}
                  >
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 mr-2 border-2 border-eggshell/30 border-t-eggshell rounded-full animate-spin" />
                        {statusMessage || 'Analyzing...'}
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Analyze Fit
                      </>
                    )}
                  </Button>
                )}
              </form>

              {/* Thinking Timeline */}
              <ThinkingTimeline
                thoughts={thoughts}
                isThinking={status === 'thinking'}
                defaultExpanded={true}
              />

              {/* Response Section */}
              {response && (
                <div 
                  ref={responseRef}
                  className="mt-6 animate-fade-in"
                >
                  <div className="bg-white/80 dark:bg-twilight/40 rounded-lg p-5 border border-muted-teal/30">
                    {/* Response header */}
                    <div className="flex items-center gap-2 mb-3 pb-3 border-b border-twilight/10 dark:border-eggshell/10">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-burnt-peach to-muted-teal flex items-center justify-center">
                        <Sparkles className="w-4 h-4 text-eggshell" />
                      </div>
                      <span className="text-sm font-medium text-twilight dark:text-eggshell">
                        AI Analysis
                      </span>
                      {durationMs && (
                        <span className="ml-auto flex items-center gap-1 text-xs text-twilight/50 dark:text-eggshell/50">
                          <Clock className="w-3 h-3" />
                          {(durationMs / 1000).toFixed(1)}s
                        </span>
                      )}
                    </div>
                    
                    {/* Response content with typewriter effect */}
                    <div 
                      className={cn(
                        "prose prose-sm dark:prose-invert max-w-none",
                        "text-twilight/90 dark:text-eggshell/90",
                        status === 'responding' && "response-streaming"
                      )}
                    >
                      <ResponseRenderer content={response} isStreaming={status === 'responding'} />
                    </div>
                  </div>
                </div>
              )}

              {/* Error State */}
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
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/**
 * ResponseRenderer Component
 * 
 * Renders the AI response with basic markdown-like formatting.
 * Handles bold text, bullet points, and headers.
 */
function ResponseRenderer({ content, isStreaming }) {
  if (!content) return null;

  // Split content into paragraphs
  const paragraphs = content.split('\n').filter(line => line.trim());

  return (
    <div className="space-y-3">
      {paragraphs.map((paragraph, index) => {
        // Check for headers (### or **)
        if (paragraph.startsWith('###')) {
          return (
            <h3 key={index} className="text-base font-semibold text-twilight dark:text-eggshell mt-4 first:mt-0">
              {paragraph.replace(/^###\s*/, '')}
            </h3>
          );
        }
        
        // Check for bullet points
        if (paragraph.startsWith('- ') || paragraph.startsWith('• ')) {
          return (
            <div key={index} className="flex items-start gap-2 pl-2">
              <span className="text-burnt-peach mt-1">•</span>
              <span className="flex-1">{formatBoldText(paragraph.replace(/^[-•]\s*/, ''))}</span>
            </div>
          );
        }
        
        // Check for bold headers (starting with **)
        if (paragraph.startsWith('**') && paragraph.includes(':**')) {
          const [header, ...rest] = paragraph.split(':**');
          return (
            <p key={index} className="mt-3 first:mt-0">
              <strong className="text-twilight dark:text-eggshell">
                {header.replace(/^\*\*/, '')}:
              </strong>
              {rest.join(':**') && (
                <span className="ml-1">{formatBoldText(rest.join(':**'))}</span>
              )}
            </p>
          );
        }
        
        // Regular paragraph
        return (
          <p key={index} className="leading-relaxed">
            {formatBoldText(paragraph)}
          </p>
        );
      })}
      
      {/* Streaming cursor */}
      {isStreaming && (
        <span className="inline-block w-2 h-4 bg-burnt-peach animate-blink ml-0.5" />
      )}
    </div>
  );
}

/**
 * Format bold text within a string (handles **text**)
 */
function formatBoldText(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-twilight dark:text-eggshell">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export default FitCheckSection;
