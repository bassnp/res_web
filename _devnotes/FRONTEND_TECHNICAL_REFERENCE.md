# Frontend Technical Reference: Portfolio Website

## Application Overview

- **Framework**: Next.js 15.5.7 (App Router)
- **Language**: JavaScript (JSX)
- **Styling**: Tailwind CSS 3.4.1 with `tailwindcss-animate`
- **State Management**: React Hooks (useState, useEffect, useMemo, useCallback), Context API
- **Rendering Strategy**: Static Site Generation (SSG) with Client-side Interactivity
- **Key Features**: 
    - **AI Fit Check**: Real-time agentic analysis of candidate-to-employer fit using Server-Sent Events (SSE).
    - **Interactive Portfolio**: Dynamic project showcase, experience timeline, and personal collage.
    - **Generative UI**: Dynamic rendering of AI reasoning and structured insights.

---

## Configuration

### Build & Framework
- **[package.json](frontend/package.json)**: Defines project dependencies and scripts. Key dependencies include `@radix-ui/react-*` for accessible primitives, `lucide-react` for iconography, and `zod` for schema validation.
- **[next.config.js](frontend/next.config.js)**: Configured for static export (`output: 'export'`). Disables image optimization for compatibility with static hosting.
- **[jsconfig.json](frontend/jsconfig.json)**: Defines path aliases: `@/*` maps to the root, with specific aliases for `components`, `lib`, and `app`.

### Styling & UI
- **[tailwind.config.js](frontend/tailwind.config.js)**: 
    - **Theme Extensions**: Custom color palette (`eggshell`, `burnt-peach`, `twilight`, `muted-teal`, `apricot`).
    - **Animations**: Extensive custom keyframes for `morph`, `float`, `pulse-glow`, `typing`, and `shimmer`.
    - **Safelist**: Explicitly includes dynamic classes for timeline nodes and pipeline phases to prevent purging.
- **[components.json](frontend/components.json)**: Shadcn UI configuration using the "New York" style and "Slate" base color.
- **[app/globals.css](frontend/app/globals.css)**: Global CSS variables for light/dark modes and base styles.

---

## Application Shell

### Layouts
- **[app/layout.js](frontend/app/layout.js)**: 
    - **Responsibility**: Root layout providing global providers.
    - **Providers**: `ThemeProvider` (next-themes) for dark mode, `AISettingsProvider` for AI configuration.
    - **Metadata**: Injects site title and description from `SITE_METADATA`.

### Global Components
- **[components/ParticleBackground.jsx](frontend/components/ParticleBackground.jsx)**: Interactive background using `react-tsparticles`.
- **[components/InteractiveGridDots.jsx](frontend/components/InteractiveGridDots.jsx)**: SVG-based grid background with hover-responsive dot scaling.

---

## Routes & Pages

### Main Entry Point
- **[app/page.js](frontend/app/page.js)**: 
    - **Type**: Client Component (`'use client'`)
    - **Responsibility**: Orchestrates the single-page portfolio experience.
    - **Internal Components**:
        - `ImageCarousel`: Auto-advancing slider for the personal collage.
        - `Header`: Responsive navigation with scroll-aware visibility (via `useHeaderVisibility`).
        - `Footer`: Site footer with social links and contact info.
        - `HeroAboutSection`: Combines a multi-phase typing animation with the personal bio and skills grid.
        - `ProjectsSection`: Renders featured projects using `ProjectModal`.
        - `ExperienceSection`: A centered, alternating timeline of career milestones.
        - `ContactSection`: Simple CTA for email contact.

---

## Feature: AI Fit Check

The Fit Check feature is a sophisticated AI integration that simulates a multi-phase agentic workflow to analyze how well the candidate fits a specific company or role.

### Core Components
- **[components/FitCheckSection.jsx](frontend/components/FitCheckSection.jsx)**: 
    - **Responsibility**: Main orchestrator for the Fit Check UI.
    - **UI Phases**:
        - `input`: Initial state showing the `InputPanel` and `WorkflowPipelinePreview`.
        - `expanded`: Active state showing the `ThinkingPanel` and `ComparisonChain`.
        - `results`: Final state showing the `ResultsSection` and `ConfidenceGauge`.
- **[components/fit-check/InputPanel.jsx](frontend/components/fit-check/InputPanel.jsx)**: Handles user input and model selection.
- **[components/fit-check/ThinkingPanel.jsx](frontend/components/fit-check/ThinkingPanel.jsx)**: Displays real-time "thoughts" from the AI agent.
- **[components/fit-check/ResultsSection.jsx](frontend/components/fit-check/ResultsSection.jsx)**: Renders structured `StrengthsCard` and `GrowthAreasCard` after analysis.
- **[components/fit-check/ComparisonChain.jsx](frontend/components/fit-check/ComparisonChain.jsx)**: Visualizes the 8-phase pipeline progress.

### State Management
- **[hooks/use-fit-check.js](frontend/hooks/use-fit-check.js)**: 
    - **Responsibility**: Manages the SSE connection to the backend.
    - **State Machine**: Tracks status (`idle`, `connecting`, `thinking`, `responding`, `complete`, `error`).
    - **Event Processing**: Parses SSE events (`phase`, `thought`, `response`, `complete`) to update the UI.

### Data Processing
- **[lib/parseAIResponse.js](frontend/lib/parseAIResponse.js)**: Parses the final markdown response from the AI into structured sections (Strengths, Growth Areas, Value Proposition).
- **[lib/phaseInsights.js](frontend/lib/phaseInsights.js)**: Extracts specific metadata from each pipeline phase (e.g., number of technologies identified during research).

---

## UI Components & Primitives

### Reusable UI ([components/ui/](frontend/components/ui/))
- **`button.jsx`**: CVA-based button with multiple variants (default, outline, destructive, etc.).
- **`dialog.jsx`**: Accessible modal primitive based on Radix UI.
- **`select.jsx`**: Custom-styled dropdown for model selection.
- **`textarea.jsx`**: Styled auto-resizing textarea.

### Feature-Specific Components
- **[components/ProjectModal.jsx](frontend/components/ProjectModal.jsx)**: Modal-based project detail view with image gallery support.
- **[components/ThinkingTimeline.jsx](frontend/components/ThinkingTimeline.jsx)**: Vertical timeline for displaying AI reasoning steps.
- **[components/ThoughtNode.jsx](frontend/components/ThoughtNode.jsx)**: Individual node in the thinking timeline.

---

## Hooks & Utilities

### Custom Hooks ([hooks/](frontend/hooks/))
- **`use-ai-settings.js`**: Manages persistence and state for AI model selection (e.g., Gemini 2.0 Flash vs Pro).
- **`use-header-visibility.js`**: Tracks scroll position to show/hide the header with a "pop-in" effect.
- **`use-example-generator.js`**: Provides pre-defined example queries for the Fit Check input.

### Utility Modules ([lib/](frontend/lib/))
- **[lib/profile-data.js](frontend/lib/profile-data.js)**: **Single Point of Truth (SPOT)**. Auto-generated from the `profile/` directory. Contains all portfolio content (projects, experience, skills).
- **[lib/phaseConfig.js](frontend/lib/phaseConfig.js)**: Defines UI metadata (icons, colors, descriptions) for the 8 pipeline phases.
- **[lib/utils.js](frontend/lib/utils.js)**: Exports `cn` for tailwind-merge and clsx integration.

---

## Component Hierarchy (Simplified)

```
RootLayout (app/layout.js)
├── ThemeProvider
└── AISettingsProvider
    └── App (app/page.js)
        ├── ParticleBackground
        ├── Header
        │   ├── InteractiveGridDots
        │   ├── InfoDialog
        │   └── ThemeToggle
        ├── Main
        │   ├── HeroAboutSection
        │   │   ├── HeroGridDots
        │   │   └── ImageCarousel
        │   ├── FitCheckSection
        │   │   ├── InputPanel
        │   │   ├── ThinkingPanel
        │   │   │   └── ChainOfThought
        │   │   ├── ResultsSection
        │   │   │   ├── StrengthsCard
        │   │   │   └── GrowthAreasCard
        │   │   └── ComparisonChain
        │   ├── ProjectsSection
        │   │   └── ProjectModal
        │   │       └── CardGridDots
        │   └── ExperienceSection
        │       ├── InteractiveGridDots
        │       └── TimelineShowcaseCarousel
        └── Footer
            └── InteractiveGridDots
```

---

## Styling Patterns

- **Glassmorphism**: Extensive use of `backdrop-blur-sm` and semi-transparent backgrounds (`bg-background/95`).
- **Dynamic Theming**: Full support for light/dark modes using CSS variables and `next-themes`.
- **Responsive Design**: Mobile-first approach with `md:` and `lg:` breakpoints. Grid-based layouts for complex sections (Hero, Fit Check, Projects).
- **Micro-interactions**: Hover-triggered scaling, translation, and shadow effects on cards and buttons.
- **Custom Animations**: 
    - `morph`: Fluid shape-shifting for background blobs.
    - `typing`: Multi-phase text animation in the Hero section.
    - `pulse-glow`: Subtle glowing effect for primary CTA buttons.
