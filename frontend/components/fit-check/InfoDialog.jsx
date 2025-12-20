'use client';

import { useState } from 'react';
import { Info, Github, ExternalLink, AlertTriangle, Shield, Circle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import { GITHUB_USERNAME, REPO_URL } from '@/lib/profile-data';

/**
 * InfoDialog Component
 * 
 * Elegant modal displaying:
 * - Open-source codebase information with GitHub link
 * - AI-generated content disclaimer and terms of use
 * 
 * Features modern glassmorphism effects and smooth animations.
 */
export function InfoDialog({ 
  open, 
  onOpenChange, 
  trigger,
  triggerClassName 
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {trigger && (
        <DialogTrigger asChild>
          {trigger}
        </DialogTrigger>
      )}
      <DialogContent className={cn(
        "bg-eggshell dark:bg-twilight",
        "border-twilight/20 dark:border-eggshell/20",
        "max-w-lg",
        "overflow-hidden"
      )}>
        <DialogHeader>
          <DialogTitle className="text-twilight dark:text-eggshell flex items-center gap-2">
            <Info className="w-5 h-5 text-muted-teal" />
            About my Portfolio
          </DialogTitle>
        </DialogHeader>
        
        <div className="py-4 space-y-4">
          {/* GitHub Repo Card - Visual Style */}
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "block p-4 rounded-sm",
              "bg-twilight/5 dark:bg-eggshell/5",
              "border border-twilight/15 dark:border-eggshell/15",
              "hover:border-emerald-500/40 dark:hover:border-emerald-400/40",
              "hover:bg-emerald-500/5 dark:hover:bg-emerald-400/5",
              "transition-all duration-300 group cursor-pointer"
            )}
          >
            {/* Header row */}
            <div className="flex items-center gap-2 mb-2">
              <Github className="w-4 h-4 text-twilight/70 dark:text-eggshell/70" />
              <span className="text-xs text-twilight/60 dark:text-eggshell/60">{GITHUB_USERNAME}</span>
              <span className="text-twilight/40 dark:text-eggshell/40">/</span>
              <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 group-hover:underline">
                res_web
              </span>
              <span className={cn(
                "ml-auto text-[10px] px-2 py-0.5 rounded-full",
                "border border-twilight/20 dark:border-eggshell/20",
                "text-twilight/60 dark:text-eggshell/60"
              )}>
                Public
              </span>
            </div>
            
            {/* Description */}
            <p className="text-xs text-twilight/70 dark:text-eggshell/70 mb-3 leading-relaxed">
              Interactive, open-source, portfolio with AI-powered assessments.
            </p>
            
            {/* Tech stack / Languages */}
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center gap-1.5">
                <Circle className="w-2.5 h-2.5 fill-yellow-400 text-yellow-400" />
                <span className="text-[11px] text-twilight/60 dark:text-eggshell/60">JavaScript</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Circle className="w-2.5 h-2.5 fill-sky-400 text-sky-400" />
                <span className="text-[11px] text-twilight/60 dark:text-eggshell/60">React</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Circle className="w-2.5 h-2.5 fill-emerald-400 text-emerald-400" />
                <span className="text-[11px] text-twilight/60 dark:text-eggshell/60">Next.js</span>
              </div>
              
              {/* External link icon */}
              <ExternalLink className="w-3.5 h-3.5 ml-auto text-twilight/30 dark:text-eggshell/30 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors" />
            </div>
          </a>

          {/* AI Disclaimer Card */}
          <div className={cn(
            "p-4 rounded-sm",
            "bg-amber-500/10 dark:bg-amber-400/10",
            "border border-amber-500/20 dark:border-amber-400/20",
            "transition-all duration-300"
          )}>
            <div className="flex items-start gap-3">
              <div className={cn(
                "flex-shrink-0 p-2 rounded-sm",
                "bg-amber-500/10 dark:bg-amber-400/10"
              )}>
                <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-twilight dark:text-eggshell mb-1">
                  AI-Generated Content
                </h3>
                <p className="text-xs text-twilight/70 dark:text-eggshell/70 leading-relaxed">
                  Gemini AI models analyze and generate insights using an Agentic Framework.
                  AI generated results can be incorrect.
                </p>
              </div>
            </div>
          </div>

          {/* Terms Notice */}
          <div className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-sm",
            "bg-twilight/5 dark:bg-eggshell/5",
            "border border-twilight/10 dark:border-eggshell/10"
          )}>
            <Shield className="w-4 h-4 text-twilight/50 dark:text-eggshell/50 flex-shrink-0" />
            <p className="text-[11px] text-twilight/60 dark:text-eggshell/60">
              By using this site, you acknowledge these terms and agree to use the features responsibly.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * InfoTriggerLink Component
 * 
 * A styled link that opens the InfoDialog when clicked.
 * Used for the "(open-source)" text in the InputPanel.
 */
export function InfoTriggerLink({ onClick, className }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "text-emerald-600 dark:text-emerald-400",
        "hover:text-emerald-500 dark:hover:text-emerald-300",
        "underline decoration-emerald-600/30 dark:decoration-emerald-400/30",
        "hover:decoration-emerald-500/50 dark:hover:decoration-emerald-300/50",
        "underline-offset-2",
        "transition-all duration-200",
        "cursor-pointer font-medium",
        className
      )}
    >
      Open-Source
    </button>
  );
}

/**
 * InfoButton Component
 * 
 * Header info button that opens the InfoDialog.
 */
export function InfoButton({ onClick, className }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "group p-2 rounded-sm",
        "hover:bg-twilight/10 dark:hover:bg-eggshell/10",
        "transition-all duration-300",
        className
      )}
      aria-label="About this project"
    >
      <Info className={cn(
        "w-6 h-6",
        "text-twilight dark:text-eggshell",
        "transition-all duration-300",
        "group-hover:text-muted-teal",
        "group-hover:scale-110"
      )} />
    </button>
  );
}

export default InfoDialog;
