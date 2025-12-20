'use client';

import { forwardRef, useState } from 'react';
import { Send, Loader2, Zap, Brain, Sparkles, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { useAISettings, AI_MODELS } from '@/hooks/use-ai-settings';
import { useExampleGenerator } from '@/hooks/use-example-generator';
import { InfoDialog, InfoTriggerLink } from './InfoDialog';

/**
 * ModelSelector Component
 * 
 * Compact button-based AI model selector displayed below the Analyze button.
 */
const ModelSelector = () => {
  const { selectedModel, updateModel } = useAISettings();
  const models = Object.values(AI_MODELS);

  return (
    <div className="flex items-center gap-2 justify-center">
      {models.map((model, index) => {
        const isLast = index === models.length - 1;
        const isSelected = selectedModel === model.id;
        const Icon = model.configType === 'reasoning' ? Brain : Zap;
        const isReasoning = model.configType === 'reasoning';
        
        return (
          <div key={model.id} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => updateModel(model.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium transition-all duration-200",
                isSelected
                  ? isReasoning
                    ? "bg-emerald-500/15 border border-emerald-500 text-emerald-600 dark:text-emerald-400"
                    : "bg-burnt-peach/15 border border-burnt-peach text-burnt-peach"
                  : isReasoning
                    ? "bg-twilight/5 dark:bg-eggshell/5 border border-twilight/15 dark:border-eggshell/15 text-twilight/70 dark:text-eggshell/70 hover:border-emerald-500/50 hover:text-emerald-500"
                    : "bg-twilight/5 dark:bg-eggshell/5 border border-twilight/15 dark:border-eggshell/15 text-twilight/70 dark:text-eggshell/70 hover:border-burnt-peach/50 hover:text-burnt-peach"
              )}
              aria-pressed={isSelected}
              aria-label={`Select ${model.label}`}
            >
              <Icon className="w-3 h-3" />
              <span>{model.configType === 'reasoning' ? 'Use Deep Reasoning' : 'Perform Quick Assessment'}</span>
            </button>
            {!isLast && (
              <span className="text-xs text-twilight/40 dark:text-eggshell/40 font-medium">or</span>
            )}
          </div>
        );
      })}
    </div>
  );
};

/**
 * InputPanel Component
 * 
 * Handles the text input and submit button for the Fit Check feature.
 * Displays a spinning overlay when loading/disabled.
 * 
 * @param {Object} props
 * @param {string} props.value - Current input value
 * @param {Function} props.onChange - Input change handler
 * @param {Function} props.onSubmit - Form submit handler
 * @param {boolean} props.isDisabled - Whether input is disabled
 * @param {boolean} props.isLoading - Whether analysis is in progress
 * @param {string} props.statusMessage - Current status message
 * @param {string} props.uiPhase - Current UI phase
 */
export const InputPanel = forwardRef(function InputPanel({
  value,
  onChange,
  onSubmit,
  isDisabled,
  isLoading,
  statusMessage,
  uiPhase,
}, ref) {
  const [infoOpen, setInfoOpen] = useState(false);
  const {
    isLoading: isGenerating,
    generateGoodExample,
    generateBadExample,
  } = useExampleGenerator();
  
  const isValidInput = value.trim().length >= 3;
  const isSubmitDisabled = !isValidInput || isLoading;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isSubmitDisabled) {
      onSubmit(value.trim());
    }
  };

  // Handle Enter key to submit (Shift+Enter for new line)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSubmitDisabled) {
        onSubmit(value.trim());
      }
    }
  };

  /**
   * Handle generating a good example.
   * Populates the textarea with the generated example.
   */
  const handleGenerateGoodExample = async () => {
    const example = await generateGoodExample();
    if (example) {
      onChange(example);
    }
  };

  /**
   * Handle generating a bad example.
   * Populates the textarea with the generated example.
   */
  const handleGenerateBadExample = async () => {
    const example = await generateBadExample();
    if (example) {
      onChange(example);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* InfoDialog for open-source link */}
      <InfoDialog open={infoOpen} onOpenChange={setInfoOpen} />

      {/* Header */}
      <div className="text-center pb-5 mb-6 border-b border-twilight/10 dark:border-eggshell/10">
        <h2 className="text-lg md:text-xl font-medium text-twilight dark:text-eggshell tracking-tight leading-tight">
          Use my <InfoTriggerLink onClick={() => setInfoOpen(true)} /> <span className="text-burnt-peach font-semibold">Deep Researcher </span> to evaluate my qualifications <span className="text-emerald-600 dark:text-emerald-400 font-semibold">for YOUR needs</span>
        </h2>
      </div>

      {/* Feature Highlights Bubbles */}
      <div className="flex flex-row gap-3 justify-center mb-6">
        <div className="flex-1 max-w-[240px] px-4 py-2 bg-emerald-500/20 dark:bg-emerald-500/15 backdrop-blur-sm border border-emerald-500/40 rounded-2xl shadow-sm text-center flex items-center justify-center transition-[transform,background-color,border-color] duration-300 hover:scale-105 hover:-translate-y-1 hover:bg-emerald-500/30 hover:border-emerald-500/60 cursor-default">
          <p className="text-xs text-twilight dark:text-eggshell leading-relaxed font-semibold">
            Modern AI Agent-Harnesses allow for real-time internet research
          </p>
        </div>
        <div className="flex-1 max-w-[240px] px-4 py-2 bg-emerald-500/20 dark:bg-emerald-500/15 backdrop-blur-sm border border-emerald-500/40 rounded-2xl shadow-sm text-center flex items-center justify-center transition-[transform,background-color,border-color] duration-300 hover:scale-105 hover:-translate-y-1 hover:bg-emerald-500/30 hover:border-emerald-500/60 cursor-default">
          <p className="text-xs text-twilight dark:text-eggshell leading-relaxed font-semibold">
            Visualize the Agents's thoughts as it brutally compares my resume
          </p>
        </div>
      </div>
      
      <div className="relative">
        <Textarea
          ref={ref}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter the job position, description, or company name"
          className={cn(
            "min-h-[80px] resize-none transition-all duration-200",
            "text-center flex items-center justify-center",
            "pt-7",
            "bg-white dark:bg-twilight/30",
            "border-twilight/20 dark:border-eggshell/20",
            "focus:border-burnt-peach focus:ring-burnt-peach/30",
            "placeholder:text-twilight/40 dark:placeholder:text-eggshell/40 placeholder:text-center",
            "fit-check-input",
            isDisabled && "opacity-60"
          )}
          disabled={isDisabled}
          maxLength={2000}
          aria-label="Job position, description, or company name"
        />
        
        {/* Character count */}
        <div className={cn(
          "absolute bottom-2 right-2 text-xs transition-opacity duration-200",
          "text-twilight/40 dark:text-eggshell/40",
          isDisabled && "opacity-0"
        )}>
          {value.length}/2000
        </div>

        {/* Loading overlay */}
        {isLoading && (
          <div className="fit-check-input-disabled-overlay">
            <div className="flex flex-col items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full border-3 border-burnt-peach/30" />
                <div className="absolute inset-0 w-10 h-10 rounded-full border-3 border-transparent border-t-burnt-peach fit-check-spinner" />
              </div>
              <span className="text-sm font-medium text-twilight dark:text-eggshell">
                {statusMessage || 'Analyzing...'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Submit button - only show in input phase */}
      {uiPhase === 'input' && (
        <div className="flex flex-col items-center gap-4">
          <Button
            type="submit"
            disabled={isSubmitDisabled}
            className={cn(
              "w-full max-w-md py-5 rounded-sm transition-all duration-200",
              "bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell",
              isValidInput && !isLoading && "animate-pulse-glow hover:scale-[1.02]",
              isSubmitDisabled && "opacity-60 cursor-not-allowed"
            )}
            aria-label={isLoading ? 'Analyzing...' : 'Analyze fit'}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {statusMessage || 'Analyzing...'}
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Analyze Fit
              </>
            )}
          </Button>
          
          {/* Generate Examples Section */}
          <div className="w-full max-w-md pt-4 border-t border-twilight/10 dark:border-eggshell/10">
            {/* Section Title */}
            <div className="flex items-center justify-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-muted-teal" />
              <span className="text-sm font-medium text-twilight/70 dark:text-eggshell/70">
                Generate Examples
              </span>
            </div>
            
            {/* Example Generator Buttons */}
            <div className="flex items-center justify-center gap-3">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleGenerateGoodExample}
                disabled={isLoading || isGenerating}
                className={cn(
                  "group gap-2 px-4 py-2 rounded-sm",
                  "border-emerald-500/30 hover:border-emerald-500",
                  "text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10",
                  "transition-all duration-200 hover:scale-[1.02]",
                  isGenerating && "opacity-60 cursor-not-allowed"
                )}
                title="Generate a job query that would be a good fit"
              >
                {isGenerating ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ThumbsUp className="w-3.5 h-3.5 group-hover:animate-pulse" />
                )}
                <span className="text-xs font-medium">Good Example</span>
              </Button>
              
              <span className="text-xs text-twilight/40 dark:text-eggshell/40 font-medium">or</span>
              
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleGenerateBadExample}
                disabled={isLoading || isGenerating}
                className={cn(
                  "group gap-2 px-4 py-2 rounded-sm",
                  "border-red-500/30 hover:border-red-500",
                  "text-red-500 dark:text-red-400 hover:bg-red-500/10",
                  "transition-all duration-200 hover:scale-[1.02]",
                  isGenerating && "opacity-60 cursor-not-allowed"
                )}
                title="Generate a job query that would be a poor fit"
              >
                {isGenerating ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <ThumbsDown className="w-3.5 h-3.5 group-hover:animate-pulse" />
                )}
                <span className="text-xs font-medium">Bad Example</span>
              </Button>
            </div>
          </div>
          
          {/* AI Model Selection Buttons - temporarily hidden */}
          {/* <ModelSelector /> */}
        </div>
      )}
    </form>
  );
});

export default InputPanel;
