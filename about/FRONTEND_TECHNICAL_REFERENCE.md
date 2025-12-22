# Frontend Technical Reference: Portfolio Website

## Application Overview
The frontend is a high-performance, information-dense portfolio application built with **Next.js 15** and **React 19**. It serves as an interactive resume and technical showcase, featuring an AI-powered "Fit Check" qualification analyzer.

- **Framework**: Next.js 15 (App Router)
- **Rendering Strategy**: Static Site Generation (SSG) via `output: 'export'`.
- **Styling**: Tailwind CSS 3.4 with `tailwindcss-animate`.
- **UI Architecture**: Radix UI primitives (via shadcn/ui) and Lucide React icons.
- **State Management**: React Hooks (State, Effect, Callback, Ref) and Context API.
- **Data Architecture**: Single Point of Truth (SPOT) pattern. Data is managed in `profile/*.json` and auto-generated into `lib/profile-data.js` at build time.

---

## Directory Structure
```text
frontend/
├── app/                    # Next.js App Router (Layouts, Pages, Globals)
├── components/             # React Components
│   ├── fit-check/          # Specialized components for AI Fit Check
│   └── ui/                 # Reusable UI primitives (shadcn/ui)
├── hooks/                  # Custom React Hooks
├── lib/                    # Utility functions and static data
├── public/                 # Static assets (images, manifests, PDFs)
├── scripts/                # Build and asset synchronization scripts
├── components.json         # shadcn/ui configuration
├── jsconfig.json           # Path aliases and JS configuration
├── next.config.js          # Next.js framework configuration
├── package.json            # Dependencies and build scripts
├── postcss.config.js       # PostCSS configuration
└── tailwind.config.js      # Tailwind CSS theme and plugin configuration
```

## Component Hierarchy
- **RootLayout** (`app/layout.js`)
  - **ThemeProvider**
  - **AISettingsProvider**
    - **App** (`app/page.js`)
      - **ParticleBackground**
      - **Header**
        - **InteractiveGridDots**
        - **InfoDialog**
      - **HeroAboutSection**
        - **HeroGridDots**
        - **ImageCarousel**
      - **FitCheckSection** (`components/FitCheckSection.jsx`)
        - **InputPanel**
          - **ModelSelector**
        - **ThinkingPanel**
          - **ChainOfThought**
        - **ResultsSection**
          - **ConfidenceGauge**
          - **StrengthsCard**
          - **GrowthAreasCard**
        - **ComparisonChain**
      - **ProjectsSection**
        - **ProjectModal**
          - **ProjectCardThumbnail**
      - **ExperienceSection**
        - **TimelineShowcaseCarousel**
      - **ContactSection**
      - **Footer**
        - **InteractiveGridDots**

---

## Configuration Reference

### Build & Framework (`next.config.js`)
- **Output**: `export` (Static HTML/CSS/JS).
- **Images**: `unoptimized: true` (Required for static export).
- **Trailing Slash**: `false` (Clean URLs).

### Styling (`tailwind.config.js`)
- **Theme Extensions**:
    - **Colors**:
        - `eggshell`: `#f4f1de` (Background/Text)
        - `burnt-peach`: `#e07a5f` (Primary Accent)
        - `twilight`: `#3d405b` (Secondary Accent/Dark Mode)
        - `muted-teal`: `#81b29a` (Success/Tertiary Accent)
        - `apricot`: `#f2cc8f` (Warning/Quaternary Accent)
    - **Animations**: `morph`, `float`, `pulse-glow`, `gradient-shift`, `typing`, `blink`, `scale-in`, `slide-up`, `rotate-slow`.
- **Safelist**: Explicitly includes dynamic classes for the Experience Timeline and Fit Check Pipeline (e.g., `bg-burnt-peach`, `border-l-blue-400`, `from-muted-teal/5`).

### Project Metadata (`package.json`)
- **Key Dependencies**:
    - `@radix-ui/*`: Accessible UI primitives.
    - `lucide-react`: Icon library.
    - `next-themes`: Dark/Light mode management.
    - `zod`: Schema validation.
    - `react-hook-form`: Form state management.
    - `axios`: API communication.
- **Scripts**:
    - `generate:profile`: Syncs `profile/` JSON to `lib/profile-data.js`.
    - `predev`/`prebuild`: Ensures data and assets are synced before execution.

---

## Application Shell & Routing

### Root Layout (`app/layout.js`)
- **Providers**:
    - `ThemeProvider`: Manages `class`-based dark mode.
    - `AISettingsProvider`: Global state for AI model selection (Quick vs. Deep).
- **Metadata**: Dynamically loaded from `SITE_METADATA` in `lib/profile-data.js`.

### Global Styles (`app/globals.css`)
- Defines CSS variables for shadcn/ui theming.
- Implements custom scrollbar styles (`.custom-scrollbar`).
- Defines utility classes for glassmorphism (`.glass`) and gradient text (`.gradient-text`).

---

## Page Architecture: `app/page.js`
The application is a single-page interface composed of modular sections.

### 1. Hero & About Section (`HeroAboutSection`)
- **Responsibility**: Initial landing and personal introduction.
- **Key Features**:
    - **Multi-Phase Typing Animation**: Cycles between "Software Engineer" and "Recent Graduate" with smooth cursor translation.
    - **Image Carousel**: Rotating personal collage with right-to-left slide transitions.
    - **Skills Grid**: Categorized display of primary and DevOps skills.
    - **CTA**: "Analyze Qualifications" button linking to Fit Check.

### 2. Fit Check Section (`FitCheckSection`)
- **Responsibility**: Interactive AI analysis of user-provided job descriptions.
- **Sub-components**: `InputPanel`, `ThinkingPanel`, `ResultsSection`, `ComparisonChain`.
- **Logic**: Orchestrated by `useFitCheck` hook.

### 3. Projects Section (`ProjectsSection`)
- **Responsibility**: Showcase of featured technical projects.
- **Key Features**:
    - **Project Cards**: Interactive cards with `ProjectCardThumbnail` (dynamic manifest loading).
    - **Project Modals**: Detailed view with learning outcomes, tech stack, and image galleries.

### 4. Experience Section (`ExperienceSection`)
- **Responsibility**: Professional history timeline.
- **Key Features**:
    - **Alternating Layout**: Desktop view alternates cards left/right along a central gradient line.
    - **Showcase Carousels**: Each timeline entry features a `TimelineShowcaseCarousel` with staggered "waterfall" initialization.
    - **Dynamic Theming**: Node colors transition from `muted-teal` to `apricot` to `burnt-peach` based on timeline position.

### 5. Contact & Footer
- **Responsibility**: Final CTA and site navigation.
- **Key Features**: `ContactSection` with mailto link and `Footer` with social links and site map.

---

## Feature Components: Fit Check System

### `FitCheckSection` (`components/FitCheckSection.jsx`)
- **UI Phases**:
    - `input`: Initial state, centered input panel.
    - `expanded`: Active analysis, two-column layout (Input + Thinking).
    - `results`: Analysis complete, compact header + result cards.

### `InputPanel` (`components/fit-check/InputPanel.jsx`)
- **Props**: `value`, `onChange`, `onSubmit`, `isLoading`, `status`, `uiPhase`.
- **Features**:
    - **Model Selector**: Toggle between "Quick Assessment" (Gemini Flash) and "Deep Reasoning" (Gemini Thinking).
    - **Example Generator**: Fetches "Good" or "Bad" job description examples from backend.

### `ThinkingPanel` (`components/fit-check/ThinkingPanel.jsx`)
- **Responsibility**: Displays real-time AI reasoning steps.
- **Features**: `ChainOfThought` component for visualizing the agentic pipeline.

### `ResultsSection` (`components/fit-check/ResultsSection.jsx`)
- **Responsibility**: Displays structured analysis results.
- **Features**: `StrengthsCard`, `GrowthAreasCard`, and `ConfidenceGauge`.

---

## Fit Check Pipeline: Agentic Workflow
The Fit Check feature visualizes a multi-stage agentic pipeline. Each phase is defined in `lib/phaseConfig.js` and mapped to specific UI styles.

### Pipeline Phases
1. **Connecting**: Query classification and entity extraction.
2. **Deep Research**: Web search for employer intelligence.
3. **Research Quality Gate**: Validation of research completeness.
4. **Content Enrichment**: Full page content extraction.
5. **Skeptical Comparison**: Critical gap analysis.
6. **Skills Matching**: Mapping candidate skills to requirements.
7. **Confidence Reranker**: LLM-as-Judge calibration.
8. **Generate Results**: Final response synthesis.

### Visualization Components
- **`WorkflowPipelinePreview`**: A high-level overview of the pipeline stages.
- **`ChainOfThought`**: Real-time display of "thought" events from the SSE stream.
- **`ComparisonChain`**: Detailed view of the current active phase and its progress.
- **`SystemPromptDialog`**: Allows users to view the underlying system prompts for each phase (transparency feature).

---

## Custom Hooks

### `useFitCheck` (`hooks/use-fit-check.js`)
- **Responsibility**: Manages the SSE connection to the backend `/api/fit-check/stream`.
- **State**: `status`, `thoughts`, `response`, `uiPhase`, `currentPhase`.
- **Features**:
    - Automatic retries with exponential backoff for transient network errors.
    - Session ID generation for request tracing.
    - Real-time parsing of streamed markdown via `parseAIResponse`.

### `useAISettings` (`hooks/use-ai-settings.js`)
- **Responsibility**: Persists AI model preferences (Provider/Model ID).
- **Storage**: `localStorage` for persistence across sessions.

### `useHeaderVisibility` (`hooks/use-header-visibility.js`)
- **Responsibility**: Detects scroll direction to show/hide the fixed header.
- **Parameters**: `hideThreshold`, `showDelay`.

---

## Utility Modules

### `lib/parseAIResponse.js`
- **Purpose**: Transforms raw AI markdown into structured JSON.
- **Logic**:
    - Extracts confidence scores and tiers (HIGH/MEDIUM/LOW).
    - Detects "Fundamental Mismatch" warnings.
    - Parses "Key Strengths" and "Growth Opportunities" into arrays.

### `lib/profile-data.js`
- **Purpose**: Authoritative data source for all profile content.
- **Content**: `IDENTITY`, `SKILLS`, `PROJECTS`, `EXPERIENCE`, `SITE_METADATA`.

### `lib/utils.js`
- **Purpose**: Standard `cn` utility combining `clsx` and `tailwind-merge` for clean class manipulation.

---

## Data Flow & Integration

1. **Initialization**: `generate-profile-config.js` reads `profile/*.json` and writes `lib/profile-data.js`.
2. **Hydration**: Components import constants from `lib/profile-data.js` for rendering.
3. **Fit Check Flow**:
    - User submits query via `InputPanel`.
    - `useFitCheck` opens SSE connection to backend.
    - Backend streams `thought` and `answer` events.
    - `useFitCheck` updates `thoughts` array and `response` string.
    - `parseAIResponse` structured the `response` for `ResultsSection`.
4. **Asset Management**: `scripts/sync-all.js` ensures images in `public/resources/` match the manifests used by carousels.
