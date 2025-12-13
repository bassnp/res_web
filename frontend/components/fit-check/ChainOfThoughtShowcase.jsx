'use client';

import { useState, useEffect } from 'react';
import { Search, Eye, Brain, Briefcase, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Mock thought cards that cycle through to showcase the chain of thought feature.
 */
const MOCK_THOUGHTS = [
  {
    id: 1,
    type: 'tool_call',
    icon: Search,
    label: 'Research',
    content: 'Searching company tech stack...',
    color: 'burnt-peach',
    phase: 'deep_research',
  },
  {
    id: 2,
    type: 'observation',
    icon: Eye,
    label: 'Observation',
    content: 'Found: React, TypeScript, Python...',
    color: 'muted-teal',
    phase: 'deep_research',
  },
  {
    id: 3,
    type: 'reasoning',
    icon: Brain,
    label: 'Reasoning',
    content: 'Strong alignment with requirements...',
    color: 'twilight',
    phase: 'skeptical_comparison',
  },
  {
    id: 4,
    type: 'tool_call',
    icon: Briefcase,
    label: 'Skill Match',
    content: 'Analyzing experience relevance...',
    color: 'burnt-peach',
    phase: 'skills_matching',
  },
  {
    id: 5,
    type: 'observation',
    icon: Eye,
    label: 'Observation',
    content: '85% skill coverage identified',
    color: 'muted-teal',
    phase: 'skills_matching',
  },
  {
    id: 6,
    type: 'reasoning',
    icon: Brain,
    label: 'Reasoning',
    content: 'Excellent fit with minor gaps...',
    color: 'twilight',
    phase: 'generate_results',
  },
];

/**
 * Floating thought card with fade animation
 */
function FloatingThoughtCard({ thought, isVisible, position, delay }) {
  const Icon = thought.icon;
  
  const colorClasses = {
    'burnt-peach': {
      bg: 'bg-burnt-peach',
      text: 'text-burnt-peach',
      border: 'border-burnt-peach/30',
    },
    'muted-teal': {
      bg: 'bg-muted-teal',
      text: 'text-muted-teal',
      border: 'border-muted-teal/30',
    },
    'twilight': {
      bg: 'bg-twilight',
      text: 'text-twilight dark:text-eggshell',
      border: 'border-twilight/30',
    },
  };

  const colors = colorClasses[thought.color] || colorClasses['burnt-peach'];

  return (
    <div
      className={cn(
        "absolute w-[140px] showcase-thought-card",
        "bg-white/90 dark:bg-twilight/60 backdrop-blur-sm",
        "rounded-sm border shadow-lg",
        colors.border,
        isVisible ? "showcase-card-visible" : "showcase-card-hidden"
      )}
      style={{
        ...position,
        animationDelay: `${delay}ms`,
        transitionDelay: `${delay}ms`,
      }}
    >
      <div className="p-2.5">
        {/* Header */}
        <div className="flex items-center gap-1.5 mb-1.5">
          <div className={cn("w-4 h-4 rounded-sm flex items-center justify-center", colors.bg)}>
            <Icon className="w-2.5 h-2.5 text-eggshell" />
          </div>
          <span className={cn("text-[9px] font-semibold uppercase tracking-wide", colors.text)}>
            {thought.label}
          </span>
        </div>

        {/* Content */}
        <p className="text-[10px] text-twilight/70 dark:text-eggshell/70 leading-relaxed line-clamp-2">
          {thought.content}
        </p>
      </div>
    </div>
  );
}

/**
 * ChainOfThoughtShowcase Component
 * 
 * Displays floating mock thought cards that fade in and out
 * to showcase the AI's chain of thought visualization.
 * 
 * @param {Object} props
 * @param {boolean} props.compact - Whether to render in compact horizontal mode for mobile
 */
export function ChainOfThoughtShowcase({ compact = false }) {
  const [visibleCards, setVisibleCards] = useState([0, 1]);
  const [cycleIndex, setCycleIndex] = useState(0);

  // Cycle through cards with fade animation
  useEffect(() => {
    const interval = setInterval(() => {
      setCycleIndex((prev) => {
        const next = (prev + 1) % MOCK_THOUGHTS.length;
        // Show 2-3 cards at a time
        const visible = [
          next,
          (next + 1) % MOCK_THOUGHTS.length,
          (next + 2) % MOCK_THOUGHTS.length,
        ];
        setVisibleCards(visible);
        return next;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  // Card positions - properly distributed across the full container height
  const positions = [
    { top: '10%', left: '5%', transform: 'rotate(-2deg)' },
    { top: '48%', right: '0%', transform: 'rotate(1deg)' },
    { top: '86%', left: '8%', transform: 'rotate(-1deg)' },
  ];

  // Compact horizontal positions
  const compactPositions = [
    { left: '2%', top: '50%', transform: 'translateY(-50%) rotate(-1deg)' },
    { left: '38%', top: '50%', transform: 'translateY(-50%) rotate(0.5deg)' },
    { right: '2%', top: '50%', transform: 'translateY(-50%) rotate(1deg)' },
  ];

  // Compact mode: Horizontal layout
  if (compact) {
    return (
      <div className="flex items-center justify-center w-full py-3 px-4 gap-3">
        {/* Header */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-muted-teal to-muted-teal/60 flex items-center justify-center cot-icon-glow">
            <Brain className="w-3 h-3 text-eggshell" />
          </div>
          <span className="text-[10px] font-semibold text-twilight/80 dark:text-eggshell/80 uppercase tracking-wide">
            Thoughts
          </span>
        </div>

        {/* Compact Floating Cards */}
        <div className="flex items-center gap-2 overflow-hidden flex-1 min-w-0">
          {MOCK_THOUGHTS.slice(0, 3).map((thought, index) => {
            const currentThought = MOCK_THOUGHTS[(cycleIndex + index) % MOCK_THOUGHTS.length];
            const isVisible = visibleCards.includes((cycleIndex + index) % MOCK_THOUGHTS.length);
            const Icon = currentThought.icon;
            
            const colorClasses = {
              'burnt-peach': 'bg-burnt-peach text-burnt-peach border-burnt-peach/30',
              'muted-teal': 'bg-muted-teal text-muted-teal border-muted-teal/30',
              'twilight': 'bg-twilight text-twilight dark:text-eggshell border-twilight/30',
            };
            const colors = colorClasses[currentThought.color] || colorClasses['burnt-peach'];
            const [bgColor, textColor, borderColor] = colors.split(' ');

            return (
              <div
                key={`compact-${index}`}
                className={cn(
                  "flex items-center gap-1.5 px-2 py-1 rounded-sm border transition-all duration-500",
                  "bg-white/80 dark:bg-twilight/60 backdrop-blur-sm",
                  borderColor,
                  isVisible ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-2"
                )}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className={cn("w-4 h-4 rounded-sm flex items-center justify-center flex-shrink-0", bgColor)}>
                  <Icon className="w-2.5 h-2.5 text-eggshell" />
                </div>
                <span className={cn("text-[9px] font-medium truncate max-w-[60px]", textColor)}>
                  {currentThought.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Full mode: Vertical layout with floating cards
  return (
    <div className="relative h-full w-full py-4 px-3 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-center gap-2 mb-2">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-muted-teal to-muted-teal/60 flex items-center justify-center cot-icon-glow">
          <Brain className="w-3 h-3 text-eggshell" />
        </div>
        <span className="text-xs font-semibold text-twilight/80 dark:text-eggshell/80 uppercase tracking-wide">
          Chain of Thought
        </span>
      </div>

      {/* Floating Cards Container - use flex-1 to fill available space */}
      <div className="relative flex-1 h-[calc(100%-80px)] min-h-[200px] w-full">
        {/* Background subtle glow effect */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-burnt-peach/10 to-muted-teal/10 blur-2xl showcase-glow-pulse" />
        </div>

        {/* Floating Cards */}
        {MOCK_THOUGHTS.slice(0, 3).map((thought, index) => (
          <FloatingThoughtCard
            key={thought.id}
            thought={MOCK_THOUGHTS[(cycleIndex + index) % MOCK_THOUGHTS.length]}
            isVisible={visibleCards.includes((cycleIndex + index) % MOCK_THOUGHTS.length)}
            position={positions[index]}
            delay={index * 200}
          />
        ))}
      </div>
    </div>
  );
}

export default ChainOfThoughtShowcase;
