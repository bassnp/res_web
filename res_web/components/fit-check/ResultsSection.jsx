'use client';

import { Clock, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import StrengthsCard from './StrengthsCard';
import GrowthAreasCard from './GrowthAreasCard';

/**
 * ResultsSection Component
 * 
 * Container for the two-column results layout (Pros/Cons cards).
 * Displays after AI analysis is complete.
 * 
 * @param {Object} props
 * @param {Object} props.parsedResponse - Parsed AI response object
 * @param {number} props.durationMs - Analysis duration in milliseconds
 * @param {boolean} props.isVisible - Controls visibility/animation
 */
export function ResultsSection({ 
  parsedResponse = null,
  durationMs = null,
  isVisible = false 
}) {
  if (!isVisible || !parsedResponse) return null;

  const {
    title,
    strengths = [],
    valueProposition = '',
    growthAreas = [],
    callToAction = ''
  } = parsedResponse;

  return (
    <div className="mt-6 space-y-4 animate-results-entry">
      {/* Results header with title and duration */}
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-burnt-peach animate-icon-bounce" />
          {title ? (
            <h3 className="text-lg font-semibold text-twilight dark:text-eggshell text-glow">
              {title}
            </h3>
          ) : (
            <h3 className="text-lg font-semibold text-twilight dark:text-eggshell">
              Your Fit Analysis
            </h3>
          )}
        </div>
        {durationMs && (
          <div className="flex items-center gap-1 text-xs text-twilight/50 dark:text-eggshell/50">
            <Clock className="w-3 h-3" />
            <span>Analyzed in {(durationMs / 1000).toFixed(1)}s</span>
          </div>
        )}
      </div>

      {/* Two-column card layout */}
      <div className={cn(
        "grid gap-4",
        "grid-cols-1 lg:grid-cols-2"
      )}>
        {/* Strengths Card - Left */}
        <StrengthsCard
          title="Key Strengths"
          strengths={strengths}
          valueProposition={valueProposition}
          isVisible={true}
        />

        {/* Growth Areas Card - Right */}
        <GrowthAreasCard
          title="Growth Opportunities"
          growthAreas={growthAreas}
          callToAction={callToAction}
          isVisible={true}
        />
      </div>
    </div>
  );
}

export default ResultsSection;
