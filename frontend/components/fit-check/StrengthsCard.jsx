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
    <div className="animate-slide-up-card h-full">
      <div className={cn(
        "relative overflow-hidden rounded-[5px] h-full",
        "bg-background/95 backdrop-blur-sm glass-card",
        "shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)]",
        "border border-muted-teal/30 dark:border-muted-teal/20",
        "strengths-card-glow card-shimmer",
        "transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
      )}>
        {/* Gradient border overlay */}
        <div className="absolute inset-0 gradient-border-strengths opacity-50 pointer-events-none" />
      
      {/* Background dots */}
      <InteractiveGridDots />
      
      <div className="relative z-10 p-6 md:p-8 h-full">
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
                "group cursor-default",
                "transition-transform duration-200 hover:-translate-y-0.5"
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
  </div>
  );
}

/**
 * Format strength text - handles bold markers and strips unwanted characters.
 * 
 * Returns properly wrapped React elements to prevent visual rendering issues
 * when mixing React elements with plain strings.
 * 
 * @param {string} text - Raw strength text that may contain markdown bold markers
 * @returns {React.ReactNode} Formatted text with styled bold sections
 */
function formatStrengthText(text) {
  if (!text) return null;
  
  // Clean up text: strip leading bullets, dashes, checkmarks and trailing bullets
  const cleaned = text
    .replace(/^[\s•●○◦▪▸►✓✔☑→\-–—]+/, '') // Strip leading markers
    .replace(/[\s•●○◦▪]+$/, '')              // Strip trailing bullets
    .trim();
  
  if (!cleaned) return null;
  
  // Handle **bold** markers by splitting on bold patterns
  const parts = cleaned.split(/(\*\*[^*]+\*\*)/g);
  
  // Filter out empty parts and map to React elements
  const elements = parts
    .filter(part => part.length > 0)
    .map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        // Render bold text with proper styling
        return (
          <strong key={i} className="font-semibold text-twilight dark:text-eggshell">
            {part.slice(2, -2)}
          </strong>
        );
      }
      // For regular text, replace arrows with properly spaced version
      // Wrap in span to ensure consistent rendering
      const formattedText = part.replace(/→/g, ' → ');
      return <span key={i}>{formattedText}</span>;
    });
  
  // Return wrapped elements to ensure proper React rendering
  return <>{elements}</>;
}

export default StrengthsCard;
