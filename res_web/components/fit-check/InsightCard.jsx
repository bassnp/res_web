'use client';

import { useMemo } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Code2,
  Users,
  Target,
  Shield,
  Lightbulb,
  Building2,
  Search,
  Briefcase,
  Gauge,
  FileQuestion,
  ArrowRight,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * InsightCard Component
 * 
 * Displays phase-specific insights in a beautiful, scannable format.
 * Replaces raw JSON data reveals with meaningful summaries.
 * 
 * @param {Object} props
 * @param {'technologies'|'requirements'|'culture'|'gaps'|'matches'|'confidence'|'quality'|'summary'} props.type - Type of insight
 * @param {string} props.title - Card title
 * @param {Array|Object|string} props.data - Insight data to display
 * @param {'success'|'warning'|'error'|'info'|'neutral'} props.variant - Visual variant
 * @param {boolean} props.compact - Use compact styling
 */
export function InsightCard({
  type = 'summary',
  title,
  data,
  variant = 'neutral',
  compact = false,
}) {
  const config = useMemo(() => getInsightConfig(type, variant), [type, variant]);
  
  if (!data || (Array.isArray(data) && data.length === 0)) {
    return null;
  }

  return (
    <div className={cn(
      "rounded-lg overflow-hidden",
      "border transition-all duration-200",
      config.borderColor,
      config.bgColor,
      compact ? "p-2" : "p-3"
    )}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div className={cn(
          "flex items-center justify-center rounded-md flex-shrink-0",
          compact ? "w-5 h-5" : "w-6 h-6",
          config.iconBg
        )}>
          <config.icon className={cn(
            "text-white",
            compact ? "w-3 h-3" : "w-3.5 h-3.5"
          )} />
        </div>
        <span className={cn(
          "font-semibold",
          compact ? "text-xs" : "text-sm",
          config.textColor
        )}>
          {title || config.defaultTitle}
        </span>
      </div>

      {/* Content based on type */}
      <div className={cn(compact ? "text-xs" : "text-sm")}>
        {renderContent(type, data, config, compact)}
      </div>
    </div>
  );
}

/**
 * Render content based on insight type
 */
function renderContent(type, data, config, compact) {
  switch (type) {
    case 'technologies':
      return <TechnologyList items={data} compact={compact} />;
    case 'requirements':
      return <RequirementsList items={data} compact={compact} />;
    case 'culture':
      return <CultureSignals items={data} compact={compact} />;
    case 'gaps':
      return <GapsList items={data} compact={compact} />;
    case 'matches':
      return <MatchesList items={data} compact={compact} />;
    case 'confidence':
      return <ConfidenceDisplay data={data} compact={compact} />;
    case 'quality':
      return <QualityDisplay data={data} compact={compact} />;
    case 'summary':
    default:
      return <SummaryText text={data} compact={compact} />;
  }
}

/**
 * Technology stack display
 */
function TechnologyList({ items, compact }) {
  const techs = Array.isArray(items) ? items : [];
  
  return (
    <div className="flex flex-wrap gap-1.5">
      {techs.map((tech, i) => (
        <span
          key={i}
          className={cn(
            "inline-flex items-center gap-1 rounded-full",
            "bg-purple-400/15 text-purple-500 dark:text-purple-300",
            "border border-purple-400/20",
            compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs"
          )}
        >
          <Code2 className={cn(compact ? "w-2.5 h-2.5" : "w-3 h-3")} />
          {tech}
        </span>
      ))}
      {techs.length === 0 && (
        <span className="text-twilight/40 dark:text-eggshell/40 italic">
          No technologies identified
        </span>
      )}
    </div>
  );
}

/**
 * Requirements list display
 */
function RequirementsList({ items, compact }) {
  const reqs = Array.isArray(items) ? items : [];
  
  return (
    <ul className="space-y-1">
      {reqs.slice(0, compact ? 3 : 5).map((req, i) => (
        <li key={i} className="flex items-start gap-2">
          <Target className={cn(
            "flex-shrink-0 text-amber-500",
            compact ? "w-3 h-3 mt-0.5" : "w-3.5 h-3.5 mt-0.5"
          )} />
          <span className="text-twilight/70 dark:text-eggshell/70 line-clamp-2">
            {typeof req === 'string' ? req : req.requirement || req.text || JSON.stringify(req)}
          </span>
        </li>
      ))}
      {reqs.length > (compact ? 3 : 5) && (
        <li className="text-twilight/40 dark:text-eggshell/40 pl-5">
          +{reqs.length - (compact ? 3 : 5)} more
        </li>
      )}
    </ul>
  );
}

/**
 * Culture signals display
 */
function CultureSignals({ items, compact }) {
  const signals = Array.isArray(items) ? items : [];
  
  return (
    <div className="flex flex-wrap gap-1.5">
      {signals.slice(0, compact ? 4 : 6).map((signal, i) => (
        <span
          key={i}
          className={cn(
            "inline-flex items-center gap-1 rounded-full",
            "bg-blue-400/15 text-blue-500 dark:text-blue-300",
            "border border-blue-400/20",
            compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs"
          )}
        >
          <Users className={cn(compact ? "w-2.5 h-2.5" : "w-3 h-3")} />
          {typeof signal === 'string' ? signal : signal.signal || signal.text}
        </span>
      ))}
    </div>
  );
}

/**
 * Gaps list display
 */
function GapsList({ items, compact }) {
  const gaps = Array.isArray(items) ? items : [];
  
  return (
    <ul className="space-y-1.5">
      {gaps.slice(0, compact ? 2 : 4).map((gap, i) => (
        <li key={i} className="flex items-start gap-2">
          <AlertTriangle className={cn(
            "flex-shrink-0 text-amber-500",
            compact ? "w-3 h-3 mt-0.5" : "w-3.5 h-3.5 mt-0.5"
          )} />
          <span className="text-twilight/70 dark:text-eggshell/70">
            {typeof gap === 'string' ? gap : gap.gap || gap.area || JSON.stringify(gap)}
          </span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Matches list display
 */
function MatchesList({ items, compact }) {
  const matches = Array.isArray(items) ? items : [];
  
  return (
    <ul className="space-y-1.5">
      {matches.slice(0, compact ? 3 : 5).map((match, i) => (
        <li key={i} className="flex items-start gap-2">
          <CheckCircle2 className={cn(
            "flex-shrink-0 text-muted-teal",
            compact ? "w-3 h-3 mt-0.5" : "w-3.5 h-3.5 mt-0.5"
          )} />
          <span className="text-twilight/70 dark:text-eggshell/70">
            {typeof match === 'string' ? match : match.skill || match.match || JSON.stringify(match)}
          </span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Confidence score display
 */
function ConfidenceDisplay({ data, compact }) {
  const score = typeof data === 'number' ? data : (data?.score || data?.confidence || 0);
  const tier = data?.tier || getConfidenceTier(score);
  const reasoning = data?.reasoning || data?.explanation || null;
  
  const tierConfig = {
    HIGH: { color: 'text-muted-teal', bg: 'bg-muted-teal', label: 'High Confidence' },
    MEDIUM: { color: 'text-amber-500', bg: 'bg-amber-500', label: 'Medium Confidence' },
    LOW: { color: 'text-red-500', bg: 'bg-red-500', label: 'Low Confidence' },
  };
  
  const config = tierConfig[tier] || tierConfig.MEDIUM;
  
  return (
    <div className="space-y-2">
      {/* Score bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-twilight/10 dark:bg-eggshell/10 rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", config.bg)}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
        <span className={cn("font-bold tabular-nums", config.color, compact ? "text-sm" : "text-base")}>
          {score}%
        </span>
      </div>
      
      {/* Tier label */}
      <div className="flex items-center gap-2">
        <Gauge className={cn("w-3.5 h-3.5", config.color)} />
        <span className={cn("font-medium", config.color, compact ? "text-xs" : "text-sm")}>
          {config.label}
        </span>
      </div>
      
      {/* Reasoning */}
      {reasoning && !compact && (
        <p className="text-xs text-twilight/60 dark:text-eggshell/60 mt-1 line-clamp-3">
          {reasoning}
        </p>
      )}
    </div>
  );
}

/**
 * Quality assessment display
 */
function QualityDisplay({ data, compact }) {
  const tier = data?.tier || data?.quality_tier || 'MEDIUM';
  const flags = data?.flags || data?.quality_flags || [];
  const action = data?.action || data?.recommended_action || 'CONTINUE';
  
  const tierConfig = {
    HIGH: { color: 'text-muted-teal', icon: CheckCircle2, label: 'High Quality' },
    MEDIUM: { color: 'text-amber-500', icon: Minus, label: 'Medium Quality' },
    LOW: { color: 'text-red-500', icon: TrendingDown, label: 'Low Quality' },
    INSUFFICIENT: { color: 'text-red-600', icon: XCircle, label: 'Insufficient Data' },
  };
  
  const config = tierConfig[tier] || tierConfig.MEDIUM;
  
  return (
    <div className="space-y-2">
      {/* Quality tier */}
      <div className="flex items-center gap-2">
        <config.icon className={cn("w-4 h-4", config.color)} />
        <span className={cn("font-medium", config.color, compact ? "text-xs" : "text-sm")}>
          {config.label}
        </span>
      </div>
      
      {/* Quality flags */}
      {flags.length > 0 && !compact && (
        <div className="flex flex-wrap gap-1">
          {flags.slice(0, 3).map((flag, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-400"
            >
              <AlertTriangle className="w-2.5 h-2.5" />
              {formatFlag(flag)}
            </span>
          ))}
        </div>
      )}
      
      {/* Action indicator */}
      {action !== 'CONTINUE' && (
        <div className="flex items-center gap-1 text-xs text-twilight/60 dark:text-eggshell/60">
          <ArrowRight className="w-3 h-3" />
          <span>{formatAction(action)}</span>
        </div>
      )}
    </div>
  );
}

/**
 * Summary text display
 */
function SummaryText({ text, compact }) {
  const displayText = typeof text === 'string' ? text : JSON.stringify(text);
  
  return (
    <p className={cn(
      "text-twilight/70 dark:text-eggshell/70",
      compact ? "line-clamp-2" : "line-clamp-4"
    )}>
      {displayText}
    </p>
  );
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get configuration for insight type and variant
 */
function getInsightConfig(type, variant) {
  const configs = {
    technologies: {
      icon: Code2,
      defaultTitle: 'Tech Stack',
      iconBg: 'bg-purple-500',
      textColor: 'text-purple-500 dark:text-purple-400',
      borderColor: 'border-purple-400/20',
      bgColor: 'bg-purple-400/5',
    },
    requirements: {
      icon: Target,
      defaultTitle: 'Requirements',
      iconBg: 'bg-amber-500',
      textColor: 'text-amber-500 dark:text-amber-400',
      borderColor: 'border-amber-400/20',
      bgColor: 'bg-amber-400/5',
    },
    culture: {
      icon: Users,
      defaultTitle: 'Culture Signals',
      iconBg: 'bg-blue-500',
      textColor: 'text-blue-500 dark:text-blue-400',
      borderColor: 'border-blue-400/20',
      bgColor: 'bg-blue-400/5',
    },
    gaps: {
      icon: AlertTriangle,
      defaultTitle: 'Identified Gaps',
      iconBg: 'bg-amber-500',
      textColor: 'text-amber-500 dark:text-amber-400',
      borderColor: 'border-amber-400/20',
      bgColor: 'bg-amber-400/5',
    },
    matches: {
      icon: CheckCircle2,
      defaultTitle: 'Skill Matches',
      iconBg: 'bg-muted-teal',
      textColor: 'text-muted-teal',
      borderColor: 'border-muted-teal/20',
      bgColor: 'bg-muted-teal/5',
    },
    confidence: {
      icon: Gauge,
      defaultTitle: 'Confidence Score',
      iconBg: 'bg-emerald-500',
      textColor: 'text-emerald-500 dark:text-emerald-400',
      borderColor: 'border-emerald-400/20',
      bgColor: 'bg-emerald-400/5',
    },
    quality: {
      icon: Shield,
      defaultTitle: 'Research Quality',
      iconBg: 'bg-violet-500',
      textColor: 'text-violet-500 dark:text-violet-400',
      borderColor: 'border-violet-400/20',
      bgColor: 'bg-violet-400/5',
    },
    summary: {
      icon: Lightbulb,
      defaultTitle: 'Summary',
      iconBg: 'bg-burnt-peach',
      textColor: 'text-burnt-peach',
      borderColor: 'border-burnt-peach/20',
      bgColor: 'bg-burnt-peach/5',
    },
  };
  
  return configs[type] || configs.summary;
}

/**
 * Get confidence tier from score
 */
function getConfidenceTier(score) {
  if (score >= 70) return 'HIGH';
  if (score >= 40) return 'MEDIUM';
  return 'LOW';
}

/**
 * Format quality flag for display
 */
function formatFlag(flag) {
  return flag
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Format action for display
 */
function formatAction(action) {
  const actions = {
    'ENHANCE_SEARCH': 'Enhancing search...',
    'FLAG_LOW_DATA': 'Flagged as low data',
    'EARLY_EXIT': 'Early exit',
  };
  return actions[action] || action;
}

export default InsightCard;
