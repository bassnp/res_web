'use client';

import { Clock, CheckCircle2, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import StrengthsCard from './StrengthsCard';
import GrowthAreasCard from './GrowthAreasCard';
import { ConfidenceGauge } from './ConfidenceGauge';

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
  finalConfidence = null,
  durationMs = null,
  isVisible = false 
}) {
  // Don't render if not visible or no response
  if (!isVisible || !parsedResponse) return null;

  const {
    title,
    strengths = [],
    valueProposition = '',
    growthAreas = [],
    rawContent = '',
    hasFundamentalMismatch = false,
    mismatchReason = ''
  } = parsedResponse;

  // Use finalConfidence from hook if available, otherwise fallback to parsedResponse
  // Ensure score is a valid number before passing to ConfidenceGauge
  const rawScore = finalConfidence?.score ?? parsedResponse?.calibratedScore;
  const confidenceScore = typeof rawScore === 'number' && !isNaN(rawScore) ? rawScore : null;
  const confidenceTier = finalConfidence?.tier || parsedResponse?.confidenceTier;
  const isMismatch = hasFundamentalMismatch || finalConfidence?.flags?.includes('fundamental_mismatch');

  // Show if we have any content at all (parsed or raw)
  const hasContent = strengths.length > 0 || valueProposition || growthAreas.length > 0 || rawContent;
  if (!hasContent) return null;

  return (
    <div className="mt-6 space-y-4 animate-results-entry">
      {/* Results header with title and duration */}
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
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

      {/* Fundamental Mismatch Warning */}
      {isMismatch && (
        <div className={cn(
          "flex items-center gap-3 p-4 rounded-sm mismatch-warning",
          "bg-amber-500/10 border border-amber-500/30"
        )}>
          <Shield className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-700 dark:text-amber-300">
              Domain Mismatch Detected
            </p>
            <p className="text-xs text-amber-600/80 dark:text-amber-400/80">
              {mismatchReason || 
               finalConfidence?.adjustment ||
               "This role's primary requirements differ significantly from the candidate's core expertise."}
            </p>
          </div>
        </div>
      )}

      {/* Confidence Gauge - only render when score is a valid number */}
      {confidenceScore !== null && (
        <div className="flex justify-center py-2">
          <ConfidenceGauge 
            score={confidenceScore}
            tier={confidenceTier}
          />
        </div>
      )}

      {/* Two-column card layout */}
      <div className={cn(
        "grid gap-4",
        "grid-cols-1 lg:grid-cols-3"
      )}>
        {/* Strengths Card - Left (1/3) */}
        <div className="lg:col-span-1">
          <StrengthsCard
            title="Key Strengths"
            strengths={strengths}
            valueProposition={valueProposition}
            isVisible={true}
          />
        </div>

        {/* Growth Areas Card - Right (2/3) */}
        <div className="lg:col-span-2">
          <GrowthAreasCard
            title="Growth Opportunities"
            growthAreas={growthAreas}
            isVisible={true}
          />
        </div>
      </div>
    </div>
  );
}

export default ResultsSection;
