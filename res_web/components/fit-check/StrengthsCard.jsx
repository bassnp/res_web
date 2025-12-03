'use client';

import { CheckCircle2, Award } from 'lucide-react';
import { cn } from '@/lib/utils';
import InteractiveGridDots from '@/components/InteractiveGridDots';

/**
 * StrengthsCard Component
 * 
 * Displays the strengths/pros from the AI analysis in a visually
 * appealing card with teal/green accents.
 * 
 * @param {Object} props
 * @param {string} props.title - Card title
 * @param {Array} props.strengths - Array of strength items
 * @param {string} props.valueProposition - Optional value proposition text
 * @param {boolean} props.isVisible - Controls animation
 */
export function StrengthsCard({ 
  title = "Key Strengths",
  strengths = [],
  valueProposition = '',
  isVisible = false 
}) {
  if (!isVisible) return null;

  return (
    <div className={cn(
      "relative overflow-hidden rounded-[10px]",
      "bg-background/95 backdrop-blur-sm glass-card",
      "shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)]",
      "border border-muted-teal/30 dark:border-muted-teal/20",
      "strengths-card-glow card-shimmer",
      "animate-slide-up-card"
    )}>
      {/* Gradient border overlay */}
      <div className="absolute inset-0 gradient-border-strengths opacity-50" />
      
      {/* Background dots */}
      <InteractiveGridDots />
      
      <div className="relative z-10 p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center",
            "bg-gradient-to-br from-muted-teal to-muted-teal/60",
            "animate-checkmark"
          )}>
            <Award className="w-5 h-5 text-eggshell" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-twilight dark:text-eggshell">
              {title}
            </h3>
            <p className="text-xs text-muted-teal">
              Why we&apos;re a great match
            </p>
          </div>
        </div>

        {/* Value proposition */}
        {valueProposition && (
          <p className="text-sm text-twilight/80 dark:text-eggshell/80 mb-4 leading-relaxed">
            {valueProposition}
          </p>
        )}

        {/* Strengths list */}
        <ul className="space-y-3">
          {strengths.map((strength, index) => (
            <li 
              key={index}
              className={cn(
                "flex items-start gap-3 stagger-item",
                "group"
              )}
            >
              <div className="flex-shrink-0 mt-0.5">
                <CheckCircle2 className="w-4 h-4 text-muted-teal group-hover:scale-110 transition-transform" />
              </div>
              <span className="text-sm text-twilight/80 dark:text-eggshell/80 leading-relaxed">
                {formatStrengthText(strength)}
              </span>
            </li>
          ))}
        </ul>

        {/* Empty state */}
        {strengths.length === 0 && !valueProposition && (
          <p className="text-sm text-twilight/50 dark:text-eggshell/50 italic text-center py-4">
            Analyzing key alignments...
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * Format strength text - handles bold markers and arrows
 */
function formatStrengthText(text) {
  if (!text) return '';
  
  // Handle **bold** markers
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-twilight dark:text-eggshell">
          {part.slice(2, -2)}
        </strong>
      );
    }
    // Replace arrows with styled version
    return part.replace(/→/g, ' → ');
  });
}

export default StrengthsCard;
