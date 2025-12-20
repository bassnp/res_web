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

      {/* Two-column card layout */}
      <div className={cn(
        "grid gap-4",
        "grid-cols-1 lg:grid-cols-2"
      )}>
        {/* Strengths Card - Left (50%) */}
        <StrengthsCard
            title="Key Strengths"
            strengths={strengths}
            valueProposition={valueProposition}
            isVisible={true}
          />

        {/* Growth Areas Card - Right (50%) */}
        <GrowthAreasCard
            title="Growth Opportunities"
            growthAreas={growthAreas}
            isVisible={true}
          />
      </div>
    </div>
  );
}

export default ResultsSection;
