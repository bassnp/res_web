'use client';

import { TrendingUp, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import InteractiveGridDots from '@/components/InteractiveGridDots';

/**
 * GrowthAreasCard Component
 * 
 * Displays growth areas/development opportunities from the AI analysis.
 * Uses apricot/amber accents and frames growth positively.
 * 
 * @param {Object} props
 * @param {string} props.title - Card title
 * @param {Array} props.growthAreas - Array of growth area items
 * @param {boolean} props.isVisible - Controls animation
 */
export function GrowthAreasCard({ 
  title = "Growth Opportunities",
  growthAreas = [],
  isVisible = false 
}) {
  if (!isVisible) return null;

  return (
    <div className={cn(
      "relative overflow-hidden rounded-[5px]",
      "bg-background/95 backdrop-blur-sm glass-card",
      "shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)]",
      "border border-apricot/30 dark:border-apricot/20",
      "growth-card-glow card-shimmer",
      "animate-slide-up-card-delayed",
      "transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
    )}>
      {/* Gradient border overlay */}
      <div className="absolute inset-0 gradient-border-growth opacity-50" />
      
      {/* Background dots */}
      <InteractiveGridDots />
      
      <div className="relative z-10 p-6 md:p-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center",
            "bg-gradient-to-br from-apricot to-apricot/60",
            "animate-checkmark"
          )}
          style={{ animationDelay: '0.2s' }}
          >
            <TrendingUp className="w-5 h-5 text-twilight" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-twilight dark:text-eggshell">
              {title}
            </h3>
            <p className="text-xs text-apricot dark:text-apricot">
              Room to grow together
            </p>
          </div>
        </div>

        {/* Growth areas list */}
        {growthAreas.length > 0 && (
          <ul className="space-y-3 mb-4">
            {growthAreas.map((area, index) => (
              <li 
                key={index}
                className={cn(
                  "flex items-start gap-3 stagger-item",
                  "group cursor-default",
                  "transition-transform duration-200 hover:-translate-y-0.5"
                )}
                style={{ animationDelay: `${0.2 + (index * 0.1)}s` }}
              >
                <div className="flex-shrink-0 mt-0.5">
                  <ArrowRight className="w-4 h-4 text-apricot group-hover:translate-x-1 transition-transform" />
                </div>
                <span className="text-sm text-twilight/80 dark:text-eggshell/80 leading-relaxed">
                  {formatGrowthText(area)}
                </span>
              </li>
            ))}
          </ul>
        )}

        {/* Empty state */}
        {growthAreas.length === 0 && (
          <div className="text-center py-4">
            <p className="text-sm text-twilight/70 dark:text-eggshell/70">
              Every role is a chance to learn and grow!
            </p>
            <p className="text-xs text-twilight/50 dark:text-eggshell/50 mt-1">
              Let&apos;s discuss how I can contribute to your team.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Format growth area text - handles bold markers and strips unwanted characters
 */
function formatGrowthText(text) {
  if (!text) return '';
  
  // Clean up text: strip leading bullets, dashes, arrows and trailing bullets
  let cleaned = text
    .replace(/^[\s•●○◦▪▸►→\-–—]+/, '') // Strip leading markers
    .replace(/[\s•●○◦▪]+$/, '')          // Strip trailing bullets
    .trim();
  
  const parts = cleaned.split(/(\*\*[^*]+\*\*)/g);
  
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

export default GrowthAreasCard;
