# TODO: Upgrade Researcher Fit Check UI

## Executive Summary

This document outlines the surgical upgrades required to synchronize the frontend Fit Check Deep Researcher UI with the **v2.0 Semantic Matching Pipeline** enhancements documented in `IMPLEMENTATION_COMPLETE.md`. The goal is to create a visually compelling, transparent chain-of-thought experience that showcases the new pipeline capabilities.

---

## ⚠️ MANDATORY: Pre-Implementation Requirements

> **STOP! Before implementing ANY changes, you MUST complete the following prerequisite reading and validation steps.**

### Required Context Documents

The implementer **MUST** read and understand the following documents in their entirety before proceeding:

| Document | Purpose | Critical Sections |
|----------|---------|-------------------|
| [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) | v2.0 Pipeline enhancements and fixes | Pipeline Architecture, Files Modified, Test Results |
| [BACKEND_DOCUMENTATION.md](BACKEND_DOCUMENTATION.md) | Backend service architecture | Pipeline State, Node Definitions, Callback System |
| [PHASE_1_QUERY_INTELLIGENCE.md](PHASE_1_QUERY_INTELLIGENCE.md) | Query classification logic | Query Types, Entity Extraction |
| [PHASE_2_SCORING_SYSTEM.md](PHASE_2_SCORING_SYSTEM.md) | Research and scoring mechanics | Data Quality Tiers, Scoring Algorithm |
| [PHASE_3_ITERATIVE_RESEARCH.md](PHASE_3_ITERATIVE_RESEARCH.md) | Research retry logic | Enhanced Search, Quality Gates |
| [PHASE_4_RESILIENCE_INTEGRATION.md](PHASE_4_RESILIENCE_INTEGRATION.md) | Error handling and resilience | Circuit Breakers, Fallback Behavior |

### Source Code Files to Review

Before modifying any frontend component, review the corresponding backend implementation:

| Frontend Component | Backend Source | Key Data Structures |
|-------------------|----------------|---------------------|
| Phase configuration | [pipeline_state.py](backend/services/pipeline_state.py) | `PHASE_ORDER`, `Phase*Output` TypedDicts |
| SSE streaming | [streaming_callback.py](backend/services/streaming_callback.py) | `on_phase()`, `on_phase_complete()` signatures |
| Confidence data | [confidence_reranker.py](backend/services/nodes/confidence_reranker.py) | `RerankerOutput` structure |
| Skills matching | [skills_matching.py](backend/services/nodes/skills_matching.py) | `Phase4Output`, score calculation |
| Research quality | [research_reranker.py](backend/services/nodes/research_reranker.py) | `ResearchRerankerOutput`, quality tiers |

---

## 📋 Phase Completion Validation Checklist

**IMPORTANT:** After completing each implementation phase, you MUST verify all requirements are met before proceeding to the next phase. Mark each checkbox only after manual verification.

### Phase 1: Core Structure Validation

After completing Tasks 1.1 and 1.2:

- [x] **READ** [pipeline_state.py](backend/services/pipeline_state.py) and confirm `PHASE_ORDER` matches frontend
- [x] **VERIFY** `content_enrich` phase exists in ALL 4 frontend PHASE_CONFIG locations:
  - [x] [ChainOfThought.jsx](frontend/components/fit-check/ChainOfThought.jsx)
  - [x] [ComparisonChain.jsx](frontend/components/fit-check/ComparisonChain.jsx)
  - [x] [ReasoningDialog.jsx](frontend/components/fit-check/ReasoningDialog.jsx)
  - [x] [WorkflowPipelinePreview.jsx](frontend/components/fit-check/WorkflowPipelinePreview.jsx)
- [x] **VALIDATE** shared `phaseConfig.js` imports correctly in all consuming components
- [x] **TEST** Run frontend with backend and confirm 8 phases appear in ComparisonChain

### Phase 2: Visual Enhancements Validation

After completing Tasks 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 5.1:

- [ ] **READ** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) "Issues Fixed" section
- [ ] **VERIFY** `DataQualityBadge` renders all 5 tiers correctly:
  - [ ] CLEAN → Emerald badge
  - [ ] PARTIAL → Amber badge
  - [ ] SPARSE → Orange badge
  - [ ] UNRELIABLE → Red-400 badge
  - [ ] GARBAGE → Red-600 badge
- [ ] **VERIFY** `ConfidenceGauge` renders at boundary values:
  - [ ] 0% → Empty ring
  - [ ] 50% → Half-filled ring
  - [ ] 100% → Full ring
- [ ] **VERIFY** Mismatch warning banner appears for queries with `hasFundamentalMismatch: true`
- [ ] **TEST** Quality flags display for test case C1 (iOS Engineer) - should show domain mismatch
- [ ] **TEST** Quality flags display for test case E8 (Rust/HFT) - should show INSUFFICIENT tier

### Phase 3: Polish & Animation Validation

After completing Tasks 8, 9, 10:

- [ ] **READ** [streaming_callback.py](backend/services/streaming_callback.py) and confirm event signatures
- [ ] **VERIFY** CSS animations load without console errors
- [ ] **VERIFY** Search retry indicator appears when `recommended_action === "ENHANCE_SEARCH"`
- [ ] **TEST** Run obscure company query (test case D1) and verify retry indicator shows
- [ ] **TEST** Full pipeline flow from input → results with no visual glitches
- [ ] **VERIFY** `phaseHistory` contains `data` field after phase_complete events

### Final Integration Validation

Before marking implementation complete:

- [ ] **CROSS-REFERENCE** All test cases from [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md#test-cases-summary):
  - [ ] Category A (HIGH FIT): Verify confidence gauge shows HIGH tier styling
  - [ ] Category B (MEDIUM FIT): Verify confidence gauge shows MEDIUM tier styling
  - [ ] Category C (LOW FIT): Verify mismatch warnings appear
  - [ ] Category D (EDGE CASES): Verify graceful handling of null/undefined data
- [ ] **VERIFY** No TypeScript/ESLint errors in modified files
- [ ] **VERIFY** Dark mode renders all new components correctly
- [ ] **VERIFY** Mobile responsive layout for new components
- [ ] **DOCUMENT** Any deviations from this specification with justification

---

## Chain of Thought: Requirements Analysis

### Current State Assessment

**Existing Frontend Components:**
1. [FitCheckSection.jsx](frontend/components/FitCheckSection.jsx) - Main orchestrator with 3 UI phases (input → expanded → results)
2. [ThinkingPanel.jsx](frontend/components/fit-check/ThinkingPanel.jsx) - Right panel displaying ChainOfThought
3. [ComparisonChain.jsx](frontend/components/fit-check/ComparisonChain.jsx) - Left panel showing pipeline progress
4. [ChainOfThought.jsx](frontend/components/fit-check/ChainOfThought.jsx) - Continuous stream of pipeline events
5. [ResultsSection.jsx](frontend/components/fit-check/ResultsSection.jsx) - Strengths/Growth cards layout
6. [ReasoningDialog.jsx](frontend/components/fit-check/ReasoningDialog.jsx) - Full chain-of-thought modal
7. [use-fit-check.js](frontend/hooks/use-fit-check.js) - SSE streaming hook with phase tracking

**Current Phase Configuration (6 phases):**
```javascript
const PHASE_ORDER = [
  'connecting',
  'deep_research',
  'research_reranker',
  'skeptical_comparison',
  'skills_matching',
  'confidence_reranker',
  'generate_results',
];
```

### New Backend Enhancements (v2.0)

**Pipeline Architecture Post-Fixes:**
```
Query → Phase 1: CONNECTING (classification)
      → Phase 2: DEEP_RESEARCH (web search)
      → Phase 2B: RESEARCH_RERANKER (quality validation) [FIXED]
      → Phase 2C: CONTENT_ENRICH (full content extraction) [NEW]
      → Phase 3: SKEPTICAL_COMPARISON (gap analysis) [FIXED]
      → Phase 4: SKILLS_MATCHING (semantic matching) [FIXED]
      → Phase 5B: CONFIDENCE_RERANKER (LLM-as-a-Judge)
      → Phase 5: GENERATE_RESULTS (final response)
```

**Key Additions Not Yet Reflected in Frontend:**
1. **`content_enrich` Phase** - New phase for full content extraction
2. **Anti-Sycophancy Scoring** - Visual indication of FUNDAMENTAL MISMATCHES
3. **Data Quality Tiers** - CLEAN/PARTIAL/SPARSE/UNRELIABLE/GARBAGE
4. **Confidence Calibration** - HIGH/MEDIUM/LOW/INSUFFICIENT_DATA tiers
5. **Quality Flags** - Visual display of quality concerns
6. **Search Retry Indicator** - Show when enhanced search is triggered

---

## Upgrade Tasks

### 1. Phase Configuration Updates

**Files to Modify:**
- [ChainOfThought.jsx](frontend/components/fit-check/ChainOfThought.jsx#L27-L93)
- [ComparisonChain.jsx](frontend/components/fit-check/ComparisonChain.jsx#L8-L52)
- [ReasoningDialog.jsx](frontend/components/fit-check/ReasoningDialog.jsx#L40-L115)
- [WorkflowPipelinePreview.jsx](frontend/components/fit-check/WorkflowPipelinePreview.jsx#L16-L58)

**Task 1.1: Add `content_enrich` Phase**
```javascript
// ADD after research_reranker in PHASE_CONFIG:
content_enrich: {
  label: 'Content Enrichment',
  icon: Database, // from lucide-react
  description: 'Extracting full page content from top sources',
  color: 'cyan',
  borderColor: 'border-l-cyan-400',
  bgColor: 'bg-cyan-400',
  textColor: 'text-cyan-400',
},

// UPDATE PHASE_ORDER:
const PHASE_ORDER = [
  'connecting',
  'deep_research',
  'research_reranker',
  'content_enrich', // NEW
  'skeptical_comparison',
  'skills_matching',
  'confidence_reranker',
  'generate_results',
];
```

**Task 1.2: Sync All PHASE_CONFIG Locations**
- Ensure identical phase configuration across all 4 files
- Consider extracting to shared `@/lib/phaseConfig.js`

---

### 2. Data Quality Visualization

**Files to Modify:**
- [phaseInsights.js](frontend/lib/phaseInsights.js#L110-L143)
- [ComparisonChain.jsx](frontend/components/fit-check/ComparisonChain.jsx#L56-L120)
- [ChainOfThought.jsx](frontend/components/fit-check/ChainOfThought.jsx#L461-L510)

**Task 2.1: Enhance Research Reranker Insights**

The backend now returns rich quality data:
```python
# From ResearchRerankerOutput
{
  "data_quality_tier": "CLEAN" | "PARTIAL" | "SPARSE" | "UNRELIABLE" | "GARBAGE",
  "research_quality_tier": "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT",
  "data_confidence_score": 0-100,
  "quality_flags": ["sparse_tech_stack", "no_culture_data", ...],
  "recommended_action": "CONTINUE" | "ENHANCE_SEARCH" | "EARLY_EXIT",
  "company_verifiability": "VERIFIED" | "PLAUSIBLE" | "SUSPICIOUS" | "NOT_FOUND"
}
```

**Add Visual Data Quality Badge:**
```jsx
// In StepInsightSummary for research_reranker phase:
function DataQualityBadge({ tier }) {
  const config = {
    CLEAN: { color: 'bg-emerald-500', icon: CheckCircle2, label: 'Clean Data' },
    PARTIAL: { color: 'bg-amber-500', icon: AlertTriangle, label: 'Partial' },
    SPARSE: { color: 'bg-orange-500', icon: Database, label: 'Sparse' },
    UNRELIABLE: { color: 'bg-red-400', icon: AlertCircle, label: 'Unreliable' },
    GARBAGE: { color: 'bg-red-600', icon: XCircle, label: 'Invalid' },
  };
  
  const cfg = config[tier] || config.PARTIAL;
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium",
      cfg.color, "text-white"
    )}>
      <cfg.icon className="w-2.5 h-2.5" />
      {cfg.label}
    </span>
  );
}
```

**Task 2.2: Enhanced Search Retry Indicator**

When `recommended_action === "ENHANCE_SEARCH"`, show a visual retry indicator:
```jsx
// Show pulsing retry indicator in ComparisonChain when research loops
{step.id === 'deep_research' && searchAttempt > 1 && (
  <span className="text-[10px] text-amber-500 flex items-center gap-1">
    <RefreshCw className="w-2.5 h-2.5 animate-spin" />
    Attempt {searchAttempt}
  </span>
)}
```

---

### 3. Anti-Sycophancy Visual Indicators

**Files to Modify:**
- [StrengthsCard.jsx](frontend/components/fit-check/StrengthsCard.jsx)
- [GrowthAreasCard.jsx](frontend/components/fit-check/GrowthAreasCard.jsx)
- [ResultsSection.jsx](frontend/components/fit-check/ResultsSection.jsx)
- [parseAIResponse.js](frontend/lib/parseAIResponse.js)

**Task 3.1: Detect Fundamental Mismatch from Response**

The backend now includes FUNDAMENTAL MISMATCH indicators in Phase 4 output. Parse these in the response:

```javascript
// In parseAIResponse.js - add mismatch detection:
export function parseAIResponse(rawResponse) {
  // ... existing parsing ...
  
  // Detect fundamental mismatch warning
  result.hasFundamentalMismatch = 
    rawResponse.toLowerCase().includes('fundamental mismatch') ||
    rawResponse.toLowerCase().includes('primarily requires');
  
  // Extract mismatch reason if present
  const mismatchMatch = rawResponse.match(/fundamental(?:ly)?\s+(?:mismatch|different|misaligned)[^.]*\./i);
  if (mismatchMatch) {
    result.mismatchReason = mismatchMatch[0];
  }
  
  return result;
}
```

**Task 3.2: Mismatch Warning Banner**

Add a warning banner when fundamental mismatch is detected:

```jsx
// In ResultsSection.jsx, before the grid:
{parsedResponse?.hasFundamentalMismatch && (
  <div className={cn(
    "flex items-center gap-3 p-4 rounded-sm mb-4",
    "bg-amber-500/10 border border-amber-500/30",
    "animate-fade-in"
  )}>
    <Shield className="w-5 h-5 text-amber-500 flex-shrink-0" />
    <div>
      <p className="text-sm font-medium text-amber-700 dark:text-amber-300">
        Domain Mismatch Detected
      </p>
      <p className="text-xs text-amber-600/80 dark:text-amber-400/80">
        {parsedResponse.mismatchReason || 
         "This role's primary requirements differ significantly from the candidate's core expertise."}
      </p>
    </div>
  </div>
)}
```

---

### 4. Confidence Calibration Display

**Files to Modify:**
- [phaseInsights.js](frontend/lib/phaseInsights.js#L210-L240)
- [ComparisonChain.jsx](frontend/components/fit-check/ComparisonChain.jsx)
- [ResultsSection.jsx](frontend/components/fit-check/ResultsSection.jsx)
- [globals.css](frontend/app/globals.css)

**Task 4.1: Confidence Score Gauge Component**

Create a visual gauge for the calibrated confidence score:

```jsx
// New component: ConfidenceGauge.jsx
export function ConfidenceGauge({ score, tier }) {
  const tierConfig = {
    HIGH: { color: 'stroke-emerald-500', bg: 'bg-emerald-500', label: 'Strong Fit' },
    MEDIUM: { color: 'stroke-amber-500', bg: 'bg-amber-500', label: 'Potential Fit' },
    LOW: { color: 'stroke-orange-500', bg: 'bg-orange-500', label: 'Limited Fit' },
    INSUFFICIENT_DATA: { color: 'stroke-gray-400', bg: 'bg-gray-400', label: 'Insufficient Data' },
  };
  
  const cfg = tierConfig[tier] || tierConfig.MEDIUM;
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (score / 100) * circumference;
  
  return (
    <div className="relative w-24 h-24">
      <svg className="w-full h-full -rotate-90">
        {/* Background circle */}
        <circle
          cx="48" cy="48" r="45"
          fill="none"
          strokeWidth="6"
          className="stroke-twilight/10 dark:stroke-eggshell/10"
        />
        {/* Progress circle */}
        <circle
          cx="48" cy="48" r="45"
          fill="none"
          strokeWidth="6"
          className={cn(cfg.color, "transition-all duration-1000 ease-out")}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-twilight dark:text-eggshell">
          {score}%
        </span>
        <span className="text-[10px] text-twilight/60 dark:text-eggshell/60">
          {cfg.label}
        </span>
      </div>
    </div>
  );
}
```

**Task 4.2: Integrate Gauge into ResultsSection**

```jsx
// In ResultsSection.jsx, add gauge between header and cards:
{parsedResponse?.calibratedScore && (
  <div className="flex justify-center my-4">
    <ConfidenceGauge 
      score={parsedResponse.calibratedScore}
      tier={parsedResponse.confidenceTier}
    />
  </div>
)}
```

---

### 5. Quality Flags Display

**Files to Modify:**
- [ChainOfThought.jsx](frontend/components/fit-check/ChainOfThought.jsx)
- [ReasoningDialog.jsx](frontend/components/fit-check/ReasoningDialog.jsx)
- [phaseInsights.js](frontend/lib/phaseInsights.js)

**Task 5.1: Quality Flags Pills**

Display quality flags as dismissable pills in the phase completion entry:

```jsx
// In PhaseCompleteEntry for confidence_reranker:
function QualityFlagsPills({ flags }) {
  if (!flags || flags.length === 0) return null;
  
  const flagConfig = {
    'sparse_tech_stack': { icon: Code2, label: 'Limited Tech Info' },
    'no_culture_data': { icon: Users, label: 'No Culture Data' },
    'few_gaps_identified': { icon: AlertTriangle, label: 'Few Gaps Found' },
    'high_score_low_data': { icon: TrendingUp, label: 'Score vs Data Mismatch' },
    'insufficient_requirements': { icon: FileText, label: 'Few Requirements' },
  };
  
  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {flags.map((flag, i) => {
        const cfg = flagConfig[flag] || { icon: AlertCircle, label: flag };
        return (
          <span
            key={i}
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm",
              "bg-amber-500/10 text-amber-600 dark:text-amber-400",
              "text-[9px] font-medium"
            )}
          >
            <cfg.icon className="w-2 h-2" />
            {cfg.label}
          </span>
        );
      })}
    </div>
  );
}
```

---

### 6. Shared Phase Configuration Module

**Create New File:**
- `frontend/lib/phaseConfig.js`

**Task 6.1: Centralize Phase Definitions**

Extract all phase configuration to a single source of truth:

```javascript
// frontend/lib/phaseConfig.js
import { 
  Wifi, Search, CheckCircle2, Database, Scale, 
  Briefcase, FileCheck2, Gauge 
} from 'lucide-react';

/**
 * Centralized pipeline phase configuration.
 * Single source of truth for all phase-related UI rendering.
 */
export const PHASE_CONFIG = {
  connecting: {
    id: 'connecting',
    label: 'Query Classification',
    shortLabel: 'Connecting',
    icon: Wifi,
    description: 'Classifying query and extracting entities',
    color: 'blue',
    borderColor: 'border-l-blue-400',
    bgColor: 'bg-blue-400',
    bgColorMuted: 'bg-blue-400/10',
    textColor: 'text-blue-400',
    ringColor: 'ring-blue-400/30',
  },
  deep_research: {
    id: 'deep_research',
    label: 'Deep Research',
    shortLabel: 'Research',
    icon: Search,
    description: 'Gathering employer intelligence via web search',
    color: 'purple',
    borderColor: 'border-l-purple-400',
    bgColor: 'bg-purple-400',
    bgColorMuted: 'bg-purple-400/10',
    textColor: 'text-purple-400',
    ringColor: 'ring-purple-400/30',
  },
  research_reranker: {
    id: 'research_reranker',
    label: 'Quality Gate',
    shortLabel: 'Validation',
    icon: CheckCircle2,
    description: 'Validating research completeness and quality',
    color: 'violet',
    borderColor: 'border-l-violet-400',
    bgColor: 'bg-violet-400',
    bgColorMuted: 'bg-violet-400/10',
    textColor: 'text-violet-400',
    ringColor: 'ring-violet-400/30',
  },
  content_enrich: {
    id: 'content_enrich',
    label: 'Content Enrichment',
    shortLabel: 'Enrichment',
    icon: Database,
    description: 'Extracting full content from top sources',
    color: 'cyan',
    borderColor: 'border-l-cyan-400',
    bgColor: 'bg-cyan-400',
    bgColorMuted: 'bg-cyan-400/10',
    textColor: 'text-cyan-400',
    ringColor: 'ring-cyan-400/30',
  },
  skeptical_comparison: {
    id: 'skeptical_comparison',
    label: 'Gap Analysis',
    shortLabel: 'Analysis',
    icon: Scale,
    description: 'Critical gap analysis with anti-sycophancy checks',
    color: 'amber',
    borderColor: 'border-l-amber-400',
    bgColor: 'bg-amber-400',
    bgColorMuted: 'bg-amber-400/10',
    textColor: 'text-amber-400',
    ringColor: 'ring-amber-400/30',
  },
  skills_matching: {
    id: 'skills_matching',
    label: 'Skills Matching',
    shortLabel: 'Matching',
    icon: Briefcase,
    description: 'Semantic skill-to-requirement mapping',
    color: 'muted-teal',
    borderColor: 'border-l-muted-teal',
    bgColor: 'bg-muted-teal',
    bgColorMuted: 'bg-muted-teal/10',
    textColor: 'text-muted-teal',
    ringColor: 'ring-muted-teal/30',
  },
  confidence_reranker: {
    id: 'confidence_reranker',
    label: 'Confidence Calibration',
    shortLabel: 'Calibration',
    icon: Gauge,
    description: 'LLM-as-Judge quality assessment',
    color: 'emerald',
    borderColor: 'border-l-emerald-400',
    bgColor: 'bg-emerald-400',
    bgColorMuted: 'bg-emerald-400/10',
    textColor: 'text-emerald-400',
    ringColor: 'ring-emerald-400/30',
  },
  generate_results: {
    id: 'generate_results',
    label: 'Response Generation',
    shortLabel: 'Results',
    icon: FileCheck2,
    description: 'Synthesizing final response with insights',
    color: 'burnt-peach',
    borderColor: 'border-l-burnt-peach',
    bgColor: 'bg-burnt-peach',
    bgColorMuted: 'bg-burnt-peach/10',
    textColor: 'text-burnt-peach',
    ringColor: 'ring-burnt-peach/30',
  },
};

/**
 * Ordered list of pipeline phases.
 * Matches backend PHASE_ORDER from pipeline_state.py.
 */
export const PHASE_ORDER = [
  'connecting',
  'deep_research',
  'research_reranker',
  'content_enrich',
  'skeptical_comparison',
  'skills_matching',
  'confidence_reranker',
  'generate_results',
];

/**
 * Get phase config by name.
 * @param {string} phase - Phase name
 * @returns {Object|null} Phase configuration
 */
export function getPhaseConfig(phase) {
  return PHASE_CONFIG[phase] || null;
}

/**
 * Get phase index in the pipeline order.
 * @param {string} phase - Phase name
 * @returns {number} Index (0-based) or -1 if not found
 */
export function getPhaseIndex(phase) {
  return PHASE_ORDER.indexOf(phase);
}
```

---

### 7. Enhanced PhaseInsights Parsing

**Files to Modify:**
- [phaseInsights.js](frontend/lib/phaseInsights.js)

**Task 7.1: Update Parsers for New Data Structures**

```javascript
// Add content_enrich insights extraction:
function extractContentEnrichInsights(summary) {
  const insights = {
    type: 'enrichment',
    pagesExtracted: 0,
    contentSize: null,
    topSources: [],
  };
  
  // Parse "Extracted X pages, Y KB content"
  const pagesMatch = summary.match(/(\d+)\s*page/i);
  const sizeMatch = summary.match(/(\d+(?:\.\d+)?)\s*(?:KB|MB)/i);
  
  if (pagesMatch) insights.pagesExtracted = parseInt(pagesMatch[1], 10);
  if (sizeMatch) insights.contentSize = sizeMatch[0];
  
  return insights;
}

// Update extractPhaseInsights switch:
export function extractPhaseInsights(phase, summary) {
  // ... existing cases ...
  case 'content_enrich':
    return extractContentEnrichInsights(summary);
  // ...
}
```

**Task 7.2: Enhanced Confidence Reranker Parsing**

```javascript
function extractConfidenceInsights(summary) {
  const insights = {
    type: 'confidence',
    calibratedScore: null,
    tier: null,
    qualityFlags: [],
    adjustment: null,
  };
  
  // Parse "Calibrated: 78% (HIGH) | Flags: sparse_tech_stack | Adj: -5%"
  const scoreMatch = summary.match(/(\d+)%/);
  const tierMatch = summary.match(/\((HIGH|MEDIUM|LOW|INSUFFICIENT_DATA)\)/i);
  const flagsMatch = summary.match(/Flags?:\s*([^|]+)/i);
  const adjMatch = summary.match(/Adj(?:ustment)?:\s*([+-]?\d+%?)/i);
  
  if (scoreMatch) insights.calibratedScore = parseInt(scoreMatch[1], 10);
  if (tierMatch) insights.tier = tierMatch[1].toUpperCase();
  if (flagsMatch) {
    insights.qualityFlags = flagsMatch[1].split(',').map(f => f.trim()).filter(Boolean);
  }
  if (adjMatch) insights.adjustment = adjMatch[1];
  
  return insights;
}
```

---

### 8. CSS Animation Enhancements

**Files to Modify:**
- [globals.css](frontend/app/globals.css)

**Task 8.1: Add New Phase-Specific Animations**

```css
/* ===========================================
   PIPELINE PHASE ANIMATIONS
   =========================================== */

/* Content enrichment shimmer effect */
@keyframes dataShimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.enrichment-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(6, 182, 212, 0.2) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: dataShimmer 1.5s ease-in-out infinite;
}

/* Quality gate pulse - for research_reranker */
@keyframes qualityPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(139, 92, 246, 0); }
}

.quality-gate-pulse {
  animation: qualityPulse 2s ease-in-out infinite;
}

/* Confidence gauge fill animation */
@keyframes gaugeCountUp {
  from { stroke-dashoffset: 283; } /* full circle */
  to { stroke-dashoffset: var(--gauge-offset); }
}

.gauge-animate {
  animation: gaugeCountUp 1.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  animation-delay: 0.3s;
}

/* Mismatch warning shake */
@keyframes warningShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
  20%, 40%, 60%, 80% { transform: translateX(2px); }
}

.mismatch-warning {
  animation: warningShake 0.5s ease-in-out;
  animation-delay: 0.2s;
}

/* Search retry spinner enhancement */
.search-retry-active {
  animation: spin 1s linear infinite, pulse 2s ease-in-out infinite;
}
```

---

### 9. Backend SSE Event Enhancements

**Files to Modify (Backend):**
- [streaming_callback.py](backend/services/streaming_callback.py)

**Task 9.1: Emit Richer Phase Data**

Ensure phase completion events include the new data structures:

```python
async def on_phase_complete(self, phase: str, summary: str, data: dict = None) -> None:
    """
    Emit a phase completion event with optional structured data.
    
    Args:
        phase: Phase name that completed.
        summary: Brief summary of phase output.
        data: Optional structured data for frontend display.
    """
    await self._emit("phase_complete", {
        "phase": phase,
        "summary": summary,
        "data": data or {},  # Include structured output
    })
```

**Task 9.2: Update Node Callbacks to Include Data**

Each node should pass relevant structured data in phase_complete:

```python
# Example from confidence_reranker.py:
await callback.on_phase_complete(
    phase="confidence_reranker",
    summary=f"Calibrated: {score}% ({tier}) | Flags: {', '.join(flags)}",
    data={
        "calibrated_score": score,
        "tier": tier,
        "quality_flags": flags,
        "adjustment_rationale": rationale,
    }
)
```

---

### 10. Hook Updates for Enhanced Data

**Files to Modify:**
- [use-fit-check.js](frontend/hooks/use-fit-check.js)

**Task 10.1: Store Phase Data in History**

```javascript
// In processEvent for phase_complete:
case 'phase_complete':
  setState(prev => ({
    ...prev,
    phaseProgress: {
      ...prev.phaseProgress,
      [event.data.phase]: 'complete',
    },
    phaseHistory: prev.phaseHistory.map(entry =>
      entry.phase === event.data.phase && entry.status === 'active'
        ? {
            ...entry,
            summary: event.data.summary,
            data: event.data.data || null, // Store structured data
            endTime: Date.now(),
            status: 'complete',
          }
        : entry
    ),
  }));
  break;
```

**Task 10.2: Extract Final Confidence for Results**

```javascript
// Add derived state for final results:
const finalConfidence = useMemo(() => {
  if (state.status !== 'complete') return null;
  
  const confidencePhase = state.phaseHistory.find(
    p => p.phase === 'confidence_reranker' && p.status === 'complete'
  );
  
  if (!confidencePhase?.data) return null;
  
  return {
    score: confidencePhase.data.calibrated_score,
    tier: confidencePhase.data.tier,
    flags: confidencePhase.data.quality_flags || [],
  };
}, [state.status, state.phaseHistory]);
```

---

## Implementation Priority

### Phase 1: Core Structure (High Priority)
1. ✅ Create shared `phaseConfig.js` module
2. ✅ Add `content_enrich` phase to all configurations
3. ✅ Update `use-fit-check.js` to store phase data

### Phase 2: Visual Enhancements (Medium Priority)
4. ✅ Implement `DataQualityBadge` component
5. ✅ Implement `ConfidenceGauge` component
6. ✅ Add `QualityFlagsPills` component
7. ✅ Add mismatch warning banner

### Phase 3: Polish & Animation (Lower Priority)
8. ✅ Add new CSS animations
9. ✅ Enhanced search retry indicator
10. ✅ Backend SSE data enrichment

---

## Testing Checklist

### Visual Regression Tests
- [ ] Verify all 8 phases render correctly in ComparisonChain
- [ ] Verify phase colors and icons match new configuration
- [ ] Test confidence gauge renders at various score levels (10%, 50%, 90%)
- [ ] Test quality flags display for various flag combinations
- [ ] Test mismatch warning appears for low-fit queries

### Functional Tests
- [ ] SSE stream includes `content_enrich` phase events
- [ ] Phase data is correctly stored in phaseHistory
- [ ] Confidence data flows through to ResultsSection
- [ ] Search retry indicator shows for ENHANCE_SEARCH action

### Edge Cases
- [ ] Handle missing phase data gracefully (null checks)
- [ ] Verify early exit flow displays correctly (GARBAGE data)
- [ ] Test ambiguous query handling (INSUFFICIENT_DATA tier)

---

## Files Summary

### New Files to Create
| File | Purpose |
|------|---------|
| `frontend/lib/phaseConfig.js` | Centralized phase configuration |
| `frontend/components/fit-check/ConfidenceGauge.jsx` | Score visualization |
| `frontend/components/fit-check/DataQualityBadge.jsx` | Quality tier badge |
| `frontend/components/fit-check/QualityFlagsPills.jsx` | Warning flags display |

### Files to Modify
| File | Changes |
|------|---------|
| `frontend/hooks/use-fit-check.js` | Store phase data, add derived confidence |
| `frontend/components/fit-check/ChainOfThought.jsx` | Import shared config, add content_enrich |
| `frontend/components/fit-check/ComparisonChain.jsx` | Import shared config, add new phase |
| `frontend/components/fit-check/ReasoningDialog.jsx` | Import shared config |
| `frontend/components/fit-check/WorkflowPipelinePreview.jsx` | Add content_enrich phase |
| `frontend/components/fit-check/ResultsSection.jsx` | Add confidence gauge, mismatch warning |
| `frontend/lib/phaseInsights.js` | Add content_enrich parser, enhance confidence parser |
| `frontend/lib/parseAIResponse.js` | Add mismatch detection |
| `frontend/app/globals.css` | Add new animations |
| `backend/services/streaming_callback.py` | Emit structured phase data |

---

## 🔍 Traceability Matrix: Requirements to Implementation

This matrix maps each requirement from the backend enhancements to its frontend implementation. Use this to verify complete coverage.

| Backend Requirement | Source Document | Frontend Component | Validation Method |
|---------------------|-----------------|-------------------|-------------------|
| 8-phase pipeline order | [pipeline_state.py#PHASE_ORDER](backend/services/pipeline_state.py) | `phaseConfig.js` | Compare arrays exactly |
| `content_enrich` phase | [fit_check_agent.py#L108](backend/services/fit_check_agent.py) | All PHASE_CONFIG objects | Grep for "content_enrich" |
| Data quality tiers (5) | [pipeline_state.py#ResearchRerankerOutput](backend/services/pipeline_state.py) | `DataQualityBadge.jsx` | Render each tier |
| Confidence calibration | [confidence_reranker.py#RerankerOutput](backend/services/nodes/confidence_reranker.py) | `ConfidenceGauge.jsx` | Test HIGH/MEDIUM/LOW/INSUFF |
| Quality flags array | [confidence_reranker.py#L95](backend/services/nodes/confidence_reranker.py) | `QualityFlagsPills.jsx` | Display sample flags |
| Anti-sycophancy detection | [phase_4_skills_matching_concise.xml](backend/prompts/phase_4_skills_matching_concise.xml) | `parseAIResponse.js` | Parse "fundamental mismatch" |
| ENHANCE_SEARCH action | [fit_check_agent.py#route_after_research_reranker](backend/services/fit_check_agent.py) | Search retry indicator | Trigger with obscure query |
| Phase event streaming | [streaming_callback.py#on_phase_complete](backend/services/streaming_callback.py) | `use-fit-check.js` | Verify data field in event |

---

## 📝 Implementation Sign-Off

Upon completion of all tasks, the implementer must sign off on the following:

### Verification Attestation

```
I, [IMPLEMENTER NAME], hereby attest that:

□ I have read ALL required context documents listed in the Pre-Implementation Requirements
□ I have completed ALL Phase Completion Validation Checklists
□ I have verified ALL items in the Traceability Matrix
□ I have tested the implementation against test cases from IMPLEMENTATION_COMPLETE.md
□ I have verified dark mode compatibility for all new components
□ I have verified mobile responsive behavior for all new components
□ I have documented any deviations from this specification below

Deviations (if any):
_________________________________________________________________
_________________________________________________________________

Date: ____________
Signature: ____________
```

### Code Review Checklist

Before merging, the reviewer must verify:

- [ ] All new files follow existing code style and naming conventions
- [ ] All new components have JSDoc documentation
- [ ] No hardcoded strings (use constants or config)
- [ ] No console.log statements left in production code
- [ ] All error states handled gracefully with user-friendly messages
- [ ] Accessibility: New components have proper ARIA labels
- [ ] Performance: No unnecessary re-renders (useMemo/useCallback where needed)

---

## Conclusion

This upgrade plan ensures the frontend accurately reflects the v2.0 Semantic Matching Pipeline with:

1. **Complete Phase Coverage** - All 8 phases including new `content_enrich`
2. **Rich Data Visualization** - Quality tiers, confidence gauges, and flags
3. **Anti-Sycophancy Transparency** - Visible mismatch warnings
4. **Maintainability** - Centralized configuration, clear component separation
5. **Production-Ready Polish** - Smooth animations, edge case handling

**⚠️ CRITICAL: Execute these tasks in the priority order specified. Complete ALL validation checklists per phase before proceeding to the next phase.**
