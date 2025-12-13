'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  FileText, 
  X, 
  Copy, 
  Check, 
  ExternalLink,
  Loader2,
  AlertCircle,
  Wifi,
  Search,
  Scale,
  Briefcase,
  FileCheck2,
  CheckCircle2
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * Phase configuration for styling
 */
const PHASE_CONFIG = {
  connecting: {
    label: 'Query Classification',
    icon: Wifi,
    description: 'Classifies queries and extracts entities',
    bgColor: 'bg-blue-400',
    textColor: 'text-blue-400',
  },
  deep_research: {
    label: 'Deep Research',
    icon: Search,
    description: 'Gathers employer intelligence',
    bgColor: 'bg-purple-400',
    textColor: 'text-purple-400',
  },
  research_reranker: {
    label: 'Research Quality Gate',
    icon: CheckCircle2,
    description: 'Validates research quality',
    bgColor: 'bg-violet-400',
    textColor: 'text-violet-400',
  },
  skeptical_comparison: {
    label: 'Skeptical Comparison',
    icon: Scale,
    description: 'Critical gap analysis',
    bgColor: 'bg-amber-400',
    textColor: 'text-amber-400',
  },
  skills_matching: {
    label: 'Skills Matching',
    icon: Briefcase,
    description: 'Maps skills to requirements',
    bgColor: 'bg-muted-teal',
    textColor: 'text-muted-teal',
  },
  confidence_reranker: {
    label: 'Confidence Calibration',
    icon: CheckCircle2,
    description: 'LLM-as-Judge calibration',
    bgColor: 'bg-emerald-400',
    textColor: 'text-emerald-400',
  },
  generate_results: {
    label: 'Response Generation',
    icon: FileCheck2,
    description: 'Synthesizes final response',
    bgColor: 'bg-burnt-peach',
    textColor: 'text-burnt-peach',
  },
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * SystemPromptDialog Component
 * 
 * A beautifully styled dialog that displays the system prompt for a given
 * pipeline phase. Features:
 * - Fetches prompt content from backend API
 * - Syntax-highlighted XML display
 * - Copy to clipboard functionality
 * - Loading and error states
 * 
 * @param {Object} props
 * @param {boolean} props.open - Whether dialog is open
 * @param {function} props.onOpenChange - Callback when open state changes
 * @param {string} props.phase - The phase to display prompt for
 */
export function SystemPromptDialog({
  open,
  onOpenChange,
  phase,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [promptData, setPromptData] = useState(null);
  const [copied, setCopied] = useState(false);

  const config = phase ? PHASE_CONFIG[phase] : null;
  const Icon = config?.icon || FileText;

  // Fetch prompt content when phase changes
  useEffect(() => {
    if (!open || !phase) {
      return;
    }

    let cancelled = false;

    async function fetchPrompt() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_URL}/api/prompts/${phase}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch prompt: ${response.status}`);
        }

        const data = await response.json();
        
        if (!cancelled) {
          setPromptData(data);
        }
      } catch (err) {
        console.error('Error fetching prompt:', err);
        if (!cancelled) {
          setError(err.message || 'Failed to load prompt');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchPrompt();

    return () => {
      cancelled = true;
    };
  }, [open, phase]);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setPromptData(null);
      setError(null);
      setCopied(false);
    }
  }, [open]);

  // Copy prompt to clipboard
  const handleCopy = useCallback(async () => {
    if (!promptData?.content) return;

    try {
      await navigator.clipboard.writeText(promptData.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [promptData]);

  // Don't render if no phase
  if (!phase) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn(
        "max-w-3xl max-h-[80vh] overflow-hidden p-0",
        "bg-gradient-to-br from-background via-background to-background/95",
        "border border-twilight/10 dark:border-eggshell/10",
        "shadow-2xl shadow-twilight/10 dark:shadow-black/20",
        "backdrop-blur-xl",
        "system-prompt-dialog"
      )}>
        {/* Header */}
        <DialogHeader className={cn(
          "p-6 pb-4",
          "bg-gradient-to-r",
          config?.bgColor ? `from-${config.bgColor.split('-')[1]}-400/10` : 'from-burnt-peach/10',
          "via-transparent to-transparent",
          "border-b border-twilight/10 dark:border-eggshell/10"
        )}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-10 h-10 rounded-xl flex items-center justify-center",
                config?.bgColor || "bg-burnt-peach",
                "shadow-lg"
              )}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div>
                <DialogTitle className={cn(
                  "text-lg font-bold",
                  config?.textColor || "text-twilight dark:text-eggshell"
                )}>
                  {promptData?.display_name || config?.label || 'System Prompt'}
                </DialogTitle>
                <DialogDescription className="text-sm text-twilight/60 dark:text-eggshell/60 mt-0.5">
                  {config?.description || 'View the system prompt for this pipeline phase'}
                </DialogDescription>
              </div>
            </div>

            {/* Copy button */}
            {promptData?.content && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className={cn(
                  "gap-2",
                  copied && "bg-muted-teal/10 border-muted-teal text-muted-teal"
                )}
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy
                  </>
                )}
              </Button>
            )}
          </div>
        </DialogHeader>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(80vh-140px)] custom-scrollbar">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className={cn(
                "w-8 h-8 animate-spin",
                config?.textColor || "text-burnt-peach"
              )} />
              <p className="mt-4 text-sm text-twilight/60 dark:text-eggshell/60">
                Loading system prompt...
              </p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
                <AlertCircle className="w-6 h-6 text-red-500" />
              </div>
              <p className="text-sm font-medium text-red-600 dark:text-red-400">
                Failed to load prompt
              </p>
              <p className="text-xs text-twilight/50 dark:text-eggshell/50 mt-1">
                {error}
              </p>
            </div>
          ) : promptData?.content ? (
            <div className="p-4">
              <PromptContent content={promptData.content} />
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className={cn(
          "p-4 border-t border-twilight/10 dark:border-eggshell/10",
          "bg-gradient-to-r from-transparent via-twilight/[0.02] to-transparent"
        )}>
          <p className="text-xs text-center text-twilight/40 dark:text-eggshell/40">
            <span className="inline-flex items-center gap-1">
              <FileText className="w-3 h-3" />
              This prompt is used to guide the AI during the {config?.label || phase} phase
            </span>
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * PromptContent Component - Renders XML prompt with syntax highlighting
 */
function PromptContent({ content }) {
  // Simply escape HTML entities - no syntax highlighting
  const escapedContent = escapeHtml(content);

  return (
    <div className={cn(
      "rounded-lg overflow-hidden",
      "bg-twilight/[0.03] dark:bg-eggshell/[0.03]",
      "border border-twilight/10 dark:border-eggshell/10"
    )}>
      {/* Code header */}
      <div className={cn(
        "flex items-center gap-2 px-4 py-2",
        "bg-twilight/5 dark:bg-eggshell/5",
        "border-b border-twilight/10 dark:border-eggshell/10"
      )}>
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400/60" />
          <div className="w-3 h-3 rounded-full bg-amber-400/60" />
          <div className="w-3 h-3 rounded-full bg-green-400/60" />
        </div>
        <span className="text-xs text-twilight/50 dark:text-eggshell/50 font-mono ml-2">
          system_prompt.xml
        </span>
      </div>
      
      {/* Code content */}
      <div className="p-4 overflow-x-auto">
        <pre className={cn(
          "text-sm font-mono leading-relaxed",
          "text-burnt-peach/90 dark:text-muted-teal/90",
          "whitespace-pre-wrap break-words"
        )}>
          {escapedContent}
        </pre>
      </div>
    </div>
  );
}

/**
 * Escape HTML entities for safe text rendering
 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '<')
    .replace(/>/g, '>')
    .replace(/"/g, '"')
    .replace(/'/g, "'");
}

export default SystemPromptDialog;
