# Frontend Technical Reference: Portfolio Website

This document provides a comprehensive, surgically precise technical reference for the frontend application. It serves as the authoritative source of truth for the UI architecture, component hierarchy, and data flow.

## 1. Application Overview

- **Framework**: Next.js 15.5.7 (App Router)
- **Language**: JavaScript (ES6+)
- **Styling**: Tailwind CSS 3.4.1 with CSS Variables for theming
- **State Management**: React Context API and Custom Hooks
- **Rendering Strategy**: Static Site Generation (SSG) with Client-side Interactivity
- **API Integration**: Server-Sent Events (SSE) for real-time AI streaming

---

## 2. Directory Structure Enumeration

```text
frontend/
├── app/                        # Next.js App Router directory
│   ├── globals.css             # Global styles and Tailwind layers
│   ├── layout.js               # Root layout with providers
│   └── page.js                 # Main landing page (Client Component)
├── components/                 # React components
│   ├── fit-check/              # Fit Check feature-specific components
│   │   ├── ChainOfThought.jsx  # Vertical stream of AI thoughts
│   │   ├── ChainOfThoughtShowcase.jsx # Static preview of CoT
│   │   ├── ComparisonChain.jsx # Pipeline phase visualization
│   │   ├── ConfidenceGauge.jsx # Radial gauge for fit score
│   │   ├── GrowthAreasCard.jsx # Detailed "Cons" analysis card
│   │   ├── index.js            # Component exports
│   │   ├── InfoDialog.jsx      # Feature explanation modal
│   │   ├── InputPanel.jsx      # Query input and model selection
│   │   ├── InsightCard.jsx     # Individual phase insight display
│   │   ├── ReasoningDialog.jsx # Full raw reasoning viewer
│   │   ├── ResultsSection.jsx  # Orchestrator for analysis results
│   │   ├── StrengthsCard.jsx   # Detailed "Pros" analysis card
│   │   ├── SystemPromptDialog.jsx # Debug view for system prompts
│   │   ├── ThinkingPanel.jsx   # Container for real-time thinking
│   │   └── WorkflowPipelinePreview.jsx # Static pipeline overview
│   ├── ui/                     # Reusable UI primitives (Radix-based)
│   │   ├── button.jsx          # Custom button component
│   │   ├── dialog.jsx          # Modal/Dialog primitive
│   │   ├── select.jsx          # Dropdown select primitive
│   │   └── textarea.jsx        # Auto-resizing textarea
│   ├── CardGridDots.jsx        # Decorative background element
│   ├── FitCheckSection.jsx     # Main feature orchestrator
│   ├── HeroGridDots.jsx        # Decorative background element
│   ├── InteractiveGridDots.jsx # Mouse-reactive background
│   ├── ParticleBackground.jsx  # Canvas-based particle system
│   ├── ProjectModal.jsx        # Detailed project showcase modal
│   ├── ThinkingTimeline.jsx    # Collapsible thinking history
│   └── ThoughtNode.jsx         # Individual thought step item
├── hooks/                      # Custom React hooks
│   ├── use-ai-settings.js      # AI model configuration context
│   ├── use-example-generator.js # Example query generation
│   ├── use-fit-check.js        # Fit Check state machine & SSE
│   └── use-header-visibility.js # Scroll-based header control
├── lib/                        # Utility modules
│   ├── parseAIResponse.js      # Markdown to structured data parser
│   ├── particleConfig.js       # tsparticles configuration
│   ├── phaseConfig.js          # Pipeline phase UI metadata
│   ├── phaseInsights.js        # Phase-specific data extractors
│   └── utils.js                # Tailwind class merging (cn)
├── public/                     # Static assets
│   └── resources/              # Dynamic JSON manifests and images
├── next.config.js              # Next.js configuration
├── tailwind.config.js          # Tailwind theme and safelist
├── package.json                # Dependencies and scripts
└── jsconfig.json               # Path aliases (@/*)
```

---

## 2. Configuration

### Build & Framework Configuration
- **`next.config.js`**: Configured for static export (`output: 'export'`). Images are unoptimized for static hosting compatibility.
- **`package.json`**: 
    - **Core**: `next`, `react`, `react-dom`
    - **UI**: `@radix-ui/*` (primitives), `lucide-react` (icons), `framer-motion` (animations - inferred from behavior, though not in top dependencies, check again), `clsx`, `tailwind-merge`
    - **Forms/Validation**: `react-hook-form`, `zod`
    - **Data Fetching**: `axios`
- **`jsconfig.json`**: Defines path aliases:
    - `@/*` -> `./*`
    - `@/components/*` -> `./components/*`
    - `@/lib/*` -> `./lib/*`
    - `@/app/*` -> `./app/*`

### Styling Configuration
- **`tailwind.config.js`**:
    - **Custom Theme**: Extends colors with a specific palette:
        - `eggshell`: `#f4f1de`
        - `burnt-peach`: `#e07a5f`
        - `twilight`: `#3d405b`
        - `muted-teal`: `#81b29a`
        - `apricot`: `#f2cc8f`
    - **Safelist**: Includes dynamic classes for timeline backgrounds, gradients, and Fit Check pipeline phases to prevent purging.
    - **Plugins**: `tailwindcss-animate`
- **`postcss.config.js`**: Standard PostCSS configuration with `tailwindcss` and `autoprefixer`.

---

## 3. Application Shell

### Root Layout (`app/layout.js`)
- **Responsibility**: Defines the HTML structure, global providers, and metadata.
- **Providers**:
    - `ThemeProvider` (from `next-themes`): Manages dark/light mode using the `class` attribute.
    - `AISettingsProvider` (from `@/hooks/use-ai-settings`): Provides global AI model configuration.
- **Metadata**: Sets default title and description for SEO.

### Global Styles (`app/globals.css`)
- **Responsibility**: Defines Tailwind layers, CSS variables for themes, and custom animations.
- **Key Features**:
    - Theme variables for `background`, `foreground`, `primary`, `secondary`, etc.
    - Custom scrollbar styling.
    - Animation definitions: `bounce-slow`, `fade-in`, `results-entry`, `thinking-dot-active`.

---

## 4. Routes & Pages

### Main Page (`app/page.js`)
- **Type**: Client Component (`'use client'`)
- **Responsibility**: The primary landing page containing all portfolio sections.
- **Key Components**:
    - `ImageCarousel`: Dynamically loads images from `collage_manifest.json` and cycles through them with slide transitions.
    - `FitCheckSection`: The main interactive AI feature.
    - `ParticleBackground`, `InteractiveGridDots`, `HeroGridDots`: Decorative background elements.
- **Hooks Used**: `useTheme`, `useHeaderVisibility`.

---

## 5. Feature Components: Fit Check

The "Fit Check" is a multi-phase AI analysis tool.

### `FitCheckSection` (`components/FitCheckSection.jsx`)
- **Responsibility**: Orchestrates the Fit Check UI states.
- **UI Phases**:
    - `input`: Initial state, centered input panel.
    - `expanded`: Analysis in progress, two-column layout (Input/Comparison vs. Thinking).
    - `results`: Analysis complete, summary header and detailed result cards.
- **Key Logic**: Manages the transition between phases based on the `status` from `useFitCheck`.
- **Child Components**: `HeroGridDots`, `WorkflowPipelinePreview`, `ComparisonChain`, `InputPanel`, `ThinkingPanel`, `ResultsSection`.

### `InputPanel` (`components/fit-check/InputPanel.jsx`)
- **Props**: 
    - `value`: Current input string.
    - `onChange`: Handler for input changes.
    - `onSubmit`: Handler for form submission.
    - `isDisabled`: Boolean to disable input.
    - `isLoading`: Boolean indicating analysis is in progress.
    - `statusMessage`: Current status text.
    - `uiPhase`: Current UI phase string.
- **Features**:
    - `ModelSelector`: Allows switching between "Quick Assessment" (Flash) and "Deep Reasoning" (Pro - currently disabled).
    - Example generation buttons (Good/Bad examples) using `useExampleGenerator`.
    - Textarea for job description/company input.

### `ThinkingPanel` (`components/fit-check/ThinkingPanel.jsx`)
- **Props**: `thoughts`, `isThinking`, `isVisible`, `status`, `statusMessage`, `currentPhase`, `phaseProgress`, `phaseHistory`.
- **Responsibility**: Displays the real-time "Chain of Thought" from the AI.
- **Child Components**: `ChainOfThought`.

### `ResultsSection` (`components/fit-check/ResultsSection.jsx`)
- **Props**: 
    - `parsedResponse`: Object containing structured analysis data.
    - `finalConfidence`: Object with score and tier.
    - `durationMs`: Total analysis time.
    - `isVisible`: Boolean for visibility.
- **Responsibility**: Displays the final structured analysis.
- **Features**:
    - Fundamental Mismatch warning if detected.
    - `StrengthsCard` and `GrowthAreasCard` in a two-column layout.
    - `ConfidenceGauge` for visual score representation.

### `ChainOfThought` (`components/fit-check/ChainOfThought.jsx`)
- **Props**: `thoughts`, `currentPhase`, `phaseProgress`, `phaseHistory`, `isThinking`, `statusMessage`.
- **Responsibility**: Renders a vertical timeline of thought nodes.
- **Features**: Auto-scrolls to the latest thought, highlights the active phase.

### `ComparisonChain` (`components/fit-check/ComparisonChain.jsx`)
- **Props**: `currentPhase`, `phaseProgress`, `phaseHistory`.
- **Responsibility**: Visualizes the backend pipeline phases (Connecting, Research, Reranking, etc.).
- **Features**: Uses `extractPhaseInsights` to show compact metrics (e.g., "4 tech identified") for completed phases.

### `InsightCard` (`components/fit-check/InsightCard.jsx`)
- **Props**: 
    - `type`: 'technologies' | 'requirements' | 'culture' | 'gaps' | 'matches' | 'confidence' | 'quality' | 'summary'.
    - `title`: Card title.
    - `data`: Insight data (Array/Object/String).
    - `variant`: 'success' | 'warning' | 'error' | 'info' | 'neutral'.
    - `compact`: Boolean for compact styling.
- **Responsibility**: Displays phase-specific insights in a scannable format.

### `ProjectModal` (`components/ProjectModal.jsx`)
- **Props**: `project`, `isOpen`, `onClose`.
- **Responsibility**: Detailed project showcase modal.
- **Features**:
    - `ProjectImageCarousel`: Fetches images from a per-project `manifest.json`.
    - Displays project description, tech stack, and links.
    - Keyboard navigation support for carousel.

---

## 6. UI Primitives (`components/ui/`)

Reusable, low-level components based on Radix UI and styled with Tailwind.
- **`button.jsx`**: Customizable button with variants (default, destructive, outline, secondary, ghost, link).
- **`dialog.jsx`**: Modal dialog component.
- **`select.jsx`**: Dropdown selection component.
- **`textarea.jsx`**: Auto-resizing or standard textarea.

---

## 7. Custom Hooks (`hooks/`)

### `useFitCheck` (`hooks/use-fit-check.js`)
- **Module Type**: Custom Hook
- **Responsibility**: Manages the SSE connection to the backend and the complex state of the fit check flow.
- **Returns**: `status`, `statusMessage`, `thoughts`, `response`, `error`, `durationMs`, `uiPhase`, `parsedResponse`, `finalConfidence`, `submitQuery`, `reset`, `isLoading`, `currentPhase`, `phaseProgress`, `phaseHistory`.
- **Internal State**: `state` (object containing status, thoughts, response, etc.).
- **Effects**:
    - Manages `EventSource` lifecycle (opening/closing connection).
    - Listens for `thought`, `phase_start`, `phase_complete`, `answer`, `error`, `done` events.
- **Dependencies**: `useAISettings`, `parseAIResponse`.

### `useAISettings` (`hooks/use-ai-settings.js`)
- **Module Type**: Context Hook
- **Responsibility**: Manages the selected AI model and provides its configuration.
- **Context**: `AISettingsProvider` wraps the app.
- **Returns**: `selectedModel`, `modelInfo`, `models`, `updateModel`, `getModelConfig`.

### `useExampleGenerator` (`hooks/use-example-generator.js`)
- **Module Type**: Custom Hook
- **Responsibility**: Provides pre-defined or dynamically generated example inputs for the Fit Check.
- **Returns**: `isLoading`, `generateGoodExample`, `generateBadExample`.

### `useHeaderVisibility` (`hooks/use-header-visibility.js`)
- **Module Type**: Custom Hook
- **Responsibility**: Tracks scroll position to show/hide the navigation header.
- **Returns**: `isVisible`.

---

## 8. Utilities & Libs (`lib/`)

### `parseAIResponse.js`
- **Function**: `parseAIResponse(rawResponse)`
- **Signature**: `(rawResponse: string) => Object`
- **Responsibility**: Uses Regex to extract structured data (Title, Strengths, Growth Areas, Confidence Score) from the AI's markdown response.
- **Designation**: Pure function.

### `phaseInsights.js`
- **Function**: `extractPhaseInsights(phase, summary)`
- **Signature**: `(phase: string, summary: string) => Object`
- **Responsibility**: Parses phase-specific summary strings into structured objects (e.g., counting technologies, identifying company names).
- **Designation**: Pure function.

### `utils.js`
- **Function**: `cn(...inputs)`
- **Signature**: `(...inputs: any[]) => string`
- **Responsibility**: Combines `clsx` and `tailwind-merge` for safe dynamic class name application.
- **Designation**: Pure function.

---

## 9. Data Flow & API Integration

### Fit Check Data Flow
1. **User Input**: User enters text in `InputPanel`.
2. **Submission**: `submitQuery` in `useFitCheck` is called.
3. **SSE Connection**: `useFitCheck` opens an `EventSource` to `/api/fit-check/stream`.
4. **Real-time Updates**:
    - `thought` events update the `thoughts` array (displayed in `ThinkingPanel`).
    - `phase_*` events update `currentPhase` and `phaseHistory` (displayed in `ComparisonChain`).
    - `answer` events accumulate in the `response` string.
5. **Completion**: `done` event triggers `status: 'complete'`.
6. **Parsing**: `parsedResponse` is derived from the full `response` string using `parseAIResponse`.
7. **Rendering**: `ResultsSection` renders the structured data.

---

## 10. Component Hierarchy (Simplified)

```
RootLayout
└── AISettingsProvider
    └── ThemeProvider
        └── Page (app/page.js)
            ├── ImageCarousel
            ├── FitCheckSection
            │   ├── HeroGridDots
            │   ├── WorkflowPipelinePreview (Input Phase)
            │   ├── ComparisonChain (Expanded Phase)
            │   ├── InputPanel
            │   ├── ThinkingPanel
            │   │   └── ChainOfThought
            │   │       └── ThoughtNode
            │   └── ResultsSection
            │       ├── ConfidenceGauge
            │       ├── StrengthsCard
            │       └── GrowthAreasCard
            └── ... (Other Sections)
```
