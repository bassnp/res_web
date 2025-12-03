'use client';

import { forwardRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

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

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <Textarea
          ref={ref}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter a company name (e.g., 'Google') or job description..."
          className={cn(
            "min-h-[80px] resize-none transition-all duration-200 text-center",
            "bg-white dark:bg-twilight/30",
            "border-twilight/20 dark:border-eggshell/20",
            "focus:border-burnt-peach focus:ring-burnt-peach/30",
            "placeholder:text-twilight/40 dark:placeholder:text-eggshell/40",
            "fit-check-input",
            isDisabled && "opacity-60"
          )}
          disabled={isDisabled}
          maxLength={2000}
          aria-label="Company name or job description"
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
      )}
    </form>
  );
});

export default InputPanel;
