'use client';

import { cn } from '@/lib/utils';

/**
 * ConfidenceGauge Component
 * 
 * Renders a circular gauge showing the calibrated confidence score.
 * Handles edge cases for undefined/null scores and tiers gracefully.
 * 
 * @param {Object} props
 * @param {number} props.score - Confidence score (0-100)
 * @param {string} props.tier - Confidence tier (HIGH, MEDIUM, LOW, INSUFFICIENT_DATA)
 */
export function ConfidenceGauge({ score, tier }) {
  const tierConfig = {
    HIGH: { color: 'stroke-emerald-500', bg: 'bg-emerald-500', label: 'Strong Fit' },
    MEDIUM: { color: 'stroke-amber-500', bg: 'bg-amber-500', label: 'Potential Fit' },
    LOW: { color: 'stroke-orange-500', bg: 'bg-orange-500', label: 'Limited Fit' },
    INSUFFICIENT_DATA: { color: 'stroke-gray-400', bg: 'bg-gray-400', label: 'Insufficient Data' },
  };
  
  // Graceful handling of null/undefined values
  const safeScore = typeof score === 'number' && !isNaN(score) ? Math.max(0, Math.min(100, score)) : 0;
  const cfg = tierConfig[tier] || tierConfig.MEDIUM;
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (safeScore / 100) * circumference;
  
  return (
    <div className="relative w-24 h-24">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle
          cx="50" cy="50" r="45"
          fill="none"
          strokeWidth="6"
          className="stroke-twilight/10 dark:stroke-eggshell/10"
        />
        {/* Progress circle */}
        <circle
          cx="50" cy="50" r="45"
          fill="none"
          strokeWidth="6"
          className={cn(cfg.color, "gauge-animate")}
          strokeDasharray={circumference}
          style={{ '--gauge-offset': strokeDashoffset }}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-twilight dark:text-eggshell">
          {safeScore}%
        </span>
        <span className="text-[10px] text-twilight/60 dark:text-eggshell/60 font-medium uppercase tracking-wider">
          {cfg.label}
        </span>
      </div>
    </div>
  );
}
