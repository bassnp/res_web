# TODO: Create Single Point of Truth (SPOT) Architecture for Engineer Profile

> **Created:** December 19, 2025  
> **Purpose:** Consolidate all hardcoded engineer profile data into a modular, single-source configuration system for maximum maintainability and configurability.

---

## 📋 CHAIN-OF-THOUGHT ANALYSIS

### Problem Statement

The current codebase has **engineer profile data scattered across multiple files** in both frontend and backend, creating:
1. **Maintenance Burden**: Changes require edits in 10+ locations
2. **Inconsistency Risk**: Profile data can drift between frontend/backend
3. **Configuration Complexity**: No clear place to update engineer information
4. **Duplication**: Same data exists in different formats across modules

### Core Insight

The solution requires a **Single Point of Truth (SPOT)** folder structure that:
- Centralizes ALL engineer profile data in one location
- Uses JSON/YAML for language-agnostic configuration
- Generates typed modules for both frontend (JS) and backend (Python)
- Maintains type safety while enabling easy non-technical editing
- Supports hot-reloading in development for rapid iteration

### Design Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│  SPOT Folder (Source of Truth)                                   │
│  └── profile/                                                    │
│       ├── identity.json         ← Name, bio, contact            │
│       ├── skills.json           ← Tech stack, DevOps            │
│       ├── projects.json         ← Featured projects             │
│       ├── experience.json       ← Timeline entries              │
│       ├── education.json        ← Degrees, certifications       │
│       ├── assets.json           ← Image paths, PDFs             │
│       └── site_metadata.json    ← SEO, titles, descriptions     │
├─────────────────────────────────────────────────────────────────┤
│  Build Script → Generates:                                       │
│  ├── backend/config/engineer_profile.py  (Python dict)          │
│  └── frontend/lib/profile-data.js        (JS export)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 HARDCODED DATA AUDIT

### FRONTEND: `frontend/app/page.js`

| Line(s) | Data Type | Current Value | Target SPOT File |
|---------|-----------|---------------|------------------|
| 389 | Hero Animation Text (Left) | `"I'm Jaden Bruha"` | `identity.json` |
| 390 | Hero Animation Text (Right) | `"A Technical Engineer"` | `identity.json` |
| 432-434 | Skills Array | `['TODO']` | `skills.json` |
| 437 | DevOps Array | `['Jira', 'Slack', 'Git', 'Github', 'Figma', 'Excel Sheets', 'CapCut']` | `skills.json` |
| 665 | Portrait Alt Text | `"Jaden Bruha Portrait"` | `identity.json` |
| 741-746 | Education Block | `"Bachelor of Science Degree in Computer Science"`, `"California State University, Sacramento • 2025 Winter Graduate"` | `education.json` |
| 750-752 | Bio Paragraph | TLDR bio text about Jaden | `identity.json` |
| 289-291 | Footer Social Links | `[{icon: Github, href: '#'}, {icon: Mail, href: '#'}]` | `contact.json` |
| 325 | Footer Email | `"hello@example.com"` | `contact.json` |
| 834-879 | Projects Data (PROJECTS_DATA) | 3 placeholder projects | `projects.json` |
| 1091-1207 | Experience Timeline | 7 experience entries | `experience.json` |
| 1470 | Contact Email Link | `"mailto:hello@example.com"` | `contact.json` |

### FRONTEND: `frontend/app/layout.js`

| Line(s) | Data Type | Current Value | Target SPOT File |
|---------|-----------|---------------|------------------|
| 5-7 | Page Metadata | `title: 'Portfolio | Software Engineer'`, `description: '...'` | `site_metadata.json` |

### FRONTEND: `frontend/components/fit-check/InfoDialog.jsx`

| Line(s) | Data Type | Current Value | Target SPOT File |
|---------|-----------|---------------|------------------|
| 46 | GitHub Repo URL | `"https://github.com/bassnp/res_web"` | `contact.json` |

### FRONTEND: Public Resources Structure

| Location | Purpose | Target SPOT Reference |
|----------|---------|----------------------|
| `public/resources/portrait.jpg` | Profile photo | `assets.json` |
| `public/resources/school_logo.png` | University logo | `assets.json` |
| `public/resources/SSR_TSRPT.pdf` | Resume PDF | `assets.json` |
| `public/resources/personal_collage/` | Photo gallery | `assets.json` |
| `public/resources/project_images/` | Project screenshots | `projects.json` |
| `public/resources/timeline_images/` | Experience showcases | `experience.json` |

---

### BACKEND: `backend/config/engineer_profile.py`

| Line(s) | Data Type | Current Value | Target SPOT File |
|---------|-----------|---------------|------------------|
| 17-20 | Basic Info | `name: "Software Engineer"`, `education: "B.S. in Computer Science"` | `identity.json`, `education.json` |
| 22-50 | Skills Dictionary | Languages, Frameworks, Cloud/DevOps, AI/ML, Tools | `skills.json` |
| 52-67 | Experience Summary | Multi-line experience narrative | `identity.json` |
| 69-85 | Notable Projects | 3 project objects with name, description, tech | `projects.json` |
| 87-93 | Strengths | 5 strength statements | `identity.json` |
| 95-101 | Career Interests | 5 interest areas | `identity.json` |

### BACKEND: `backend/services/example_generator.py`

| Line(s) | Data Type | Current Value | Target SPOT File |
|---------|-----------|---------------|------------------|
| 43-48 | Good Example Prompt | Inline skill list for AI generation | Should reference `skills.json` |
| 131-145 | Fallback Examples | Hardcoded example lists | `examples.json` (new) |

### BACKEND: Services Using Engineer Profile

| File | Import | Usage |
|------|--------|-------|
| `services/tools/skill_matcher.py` | `get_skills_by_category, get_skills_list, ENGINEER_PROFILE` | Skill matching logic |
| `services/tools/experience_matcher.py` | `ENGINEER_PROFILE, get_experience_summary` | Experience matching |
| `services/nodes/skeptical_comparison.py` | `get_formatted_profile` | Profile injection into prompts |

### BACKEND: Configuration & Infrastructure

| File/Line(s) | Data Type | Current Value | Target SPOT File |
|--------------|-----------|---------------|------------------|
| `server.py:71` | Default CORS Origin | `"http://localhost:3003"` | `site_metadata.json` or `.env` |
| `docker-compose.yml:40` | Default CORS Origin | `"http://localhost:3003"` | `site_metadata.json` or `.env` |
| `Dockerfile:47` | Image Metadata | `maintainer="res_web"`, GitHub source | `site_metadata.json` |
| `tests/conftest.py:20,41` | Test CORS Origin | `"http://localhost:3003"` | Test config |

### FRONTEND: API Configuration

| File/Line(s) | Data Type | Current Value | Target SPOT File |
|--------------|-----------|---------------|------------------|
| `hooks/use-fit-check.js:33` | API Base URL | `"http://localhost:8000"` | `site_metadata.json` or `.env` |
| `hooks/use-example-generator.js:9` | API Base URL | `"http://localhost:8000"` | `site_metadata.json` or `.env` |
| `components/fit-check/SystemPromptDialog.jsx:30` | API Base URL | `"http://localhost:8000"` | `site_metadata.json` or `.env` |

### FRONTEND: Additional Hardcoded Values

| File/Line(s) | Data Type | Current Value | Target SPOT File |
|--------------|-----------|---------------|------------------|
| `app/page.js:433` | Skills Placeholder | `['TODO']` | `skills.json` |
| `components/fit-check/InfoDialog.jsx:61` | GitHub Username Display | `"bassnp"` | `contact.json` |
| `hooks/use-ai-settings.js:17-31` | AI Model Configuration | Model IDs, labels, descriptions | `ai_models.json` (new) |

### FRONTEND: Pipeline Phase Configuration

| File/Line(s) | Data Type | Current Value | Target SPOT File |
|--------------|-----------|---------------|------------------|
| `lib/phaseConfig.js:25-164` | Phase Configuration | Labels, icons, colors, descriptions | `pipeline_phases.json` (new) |
| `tailwind.config.js:14-49` | Safelist Classes | Dynamic color classes for phases | Generated from `pipeline_phases.json` |

---

## 🏗️ PROPOSED SPOT FOLDER STRUCTURE

### Root Location: `profile/` (workspace root)

```
resume/
├── profile/                          ← SINGLE POINT OF TRUTH
│   ├── identity.json                 ← Personal info, bio, name
│   ├── skills.json                   ← Technical skills by category
│   ├── projects.json                 ← Featured projects with metadata
│   ├── experience.json               ← Timeline/work history
│   ├── education.json                ← Academic credentials
│   ├── contact.json                  ← Email, social links, GitHub
│   ├── assets.json                   ← Path references to images/PDFs
│   ├── site_metadata.json            ← SEO, deployment config, ports
│   ├── ai_models.json                ← AI model configurations (NEW)
│   ├── pipeline_phases.json          ← Pipeline phase metadata (NEW)
│   └── examples.json                 ← Demo query examples (optional)
│
├── scripts/
│   ├── generate-profile-config.js    ← Build script for frontend
│   └── generate-profile-config.py    ← Build script for backend
│
├── backend/
│   └── config/
│       └── engineer_profile.py       ← GENERATED from SPOT
│
└── frontend/
    └── lib/
        ├── profile-data.js           ← GENERATED from SPOT
        └── phaseConfig.js            ← GENERATED from pipeline_phases.json
```

---

## 📁 SPOT FILE SCHEMAS

### `profile/identity.json`

```json
{
  "$schema": "./schemas/identity.schema.json",
  "name": {
    "full": "Jaden Bruha",
    "display": "Jaden Bruha",
    "title": "Technical Engineer",
    "professional_title": "Software Engineer"
  },
  "portrait": {
    "path": "/resources/portrait.jpg",
    "alt": "Jaden Bruha Portrait"
  },
  "hero": {
    "animation_left": "I'm Jaden Bruha",
    "animation_right": "A Technical Engineer"
  },
  "bio": {
    "tldr": "TLDR; I am Jaden Bruha, I'm a 22 year old new-grad, and I'm a very nerdy engineer with big aspirations.",
    "full": "I have a passion for building anything and everything from software, computers to serve my software, AI agents, and motorcycles. My journey started at a young age as a hobbyist, and I've grown into a full stack developer striving for elegant solutions. My current fixations include learning about quantum philosophy, parallelized programming, and artificial (general) intelligence."
  },
  "experience_summary": "Full-stack software engineer with experience building modern web applications and AI-powered systems...",
  "strengths": [
    "Fast learner who quickly adapts to new technologies",
    "Strong problem-solving and debugging skills",
    "Experience with end-to-end software development lifecycle",
    "Excellent communication and collaboration abilities",
    "Passionate about building AI-powered applications"
  ],
  "career_interests": [
    "Full-Stack Development",
    "AI/ML Engineering",
    "Backend Systems",
    "Cloud Architecture",
    "Developer Tools"
  ]
}
```

### `profile/skills.json`

```json
{
  "$schema": "./schemas/skills.schema.json",
  "display_categories": {
    "primary": {
      "label": "Skills & Technologies",
      "skills": ["Python", "JavaScript", "TypeScript", "React", "Next.js", "FastAPI", "LangChain", "LangGraph"]
    },
    "devops": {
      "label": "Dev Ops",
      "skills": ["Jira", "Slack", "Git", "GitHub", "Figma", "Excel Sheets", "CapCut"]
    }
  },
  "backend_categories": {
    "languages": ["Python", "JavaScript", "TypeScript", "SQL", "HTML/CSS"],
    "frameworks": ["React", "Next.js", "FastAPI", "Node.js", "TailwindCSS"],
    "cloud_devops": ["Docker", "AWS", "PostgreSQL", "Redis", "CI/CD"],
    "ai_ml": ["LangChain", "LangGraph", "OpenAI API", "Google Gemini", "RAG Systems", "Prompt Engineering"],
    "tools": ["Git", "VS Code", "Linux", "REST APIs", "GraphQL"]
  }
}
```

### `profile/projects.json`

```json
{
  "$schema": "./schemas/projects.schema.json",
  "featured": [
    {
      "id": "churchlink",
      "title": "ChurchLink — Team of 6, Graduation Project",
      "description": "Deployed Web Builder Platform for Churches to customize a Website + App w/ Localization, Admin Dashboards, & Payments",
      "about": "Extended description for modal view...",
      "learning_outcomes": [
        "Mastered Flutter cross-platform development",
        "Implemented complex payment integrations"
      ],
      "tags": ["Python", "Flutter", "TypeScript", "Vite", "FastAPI", "Firebase", "MongoDB", "PayPal"],
      "color": "from-burnt-peach to-apricot",
      "images_folder": "project-churchlink",
      "link": null
    }
  ],
  "backend_projects": [
    {
      "name": "AI Portfolio Assistant",
      "description": "Real-time AI agent that analyzes employer fit using web research and skill matching",
      "tech": ["Python", "FastAPI", "LangGraph", "React", "SSE Streaming"]
    }
  ]
}
```

### `profile/experience.json`

```json
{
  "$schema": "./schemas/experience.schema.json",
  "timeline": [
    {
      "id": 1,
      "title": "Software Engineer",
      "company": "Tech Innovation Corp",
      "period": "December 2025",
      "description": "Leading full-stack development initiatives...",
      "tags": ["React", "Node.js", "AWS", "TypeScript"],
      "color": "burnt-peach",
      "showcase_folder": "showcase1"
    }
  ]
}
```

### `profile/education.json`

```json
{
  "$schema": "./schemas/education.schema.json",
  "primary": {
    "degree": "Bachelor of Science Degree in Computer Science",
    "institution": "California State University, Sacramento",
    "graduation": "2025 Winter Graduate",
    "logo_path": "/resources/school_logo.png"
  },
  "certifications": []
}
```

### `profile/contact.json`

```json
{
  "$schema": "./schemas/contact.schema.json",
  "email": "hello@example.com",
  "social": {
    "github": {
      "url": "https://github.com/bassnp",
      "display": "bassnp"
    }
  },
  "repo": {
    "url": "https://github.com/bassnp/res_web",
    "display": "View Source Code"
  }
}
```

### `profile/assets.json`

```json
{
  "$schema": "./schemas/assets.schema.json",
  "portrait": "/resources/portrait.jpg",
  "school_logo": "/resources/school_logo.png",
  "resume_pdf": {
    "path": "/resources/SSR_TSRPT.pdf",
    "thumbnail": "/resources/SSR_TSRPT_thumb.jpg",
    "label": "PDF Formatted Resume"
  },
  "personal_collage": {
    "folder": "/resources/personal_collage/",
    "manifest": "/resources/collage_manifest.json"
  }
}
```

### `profile/site_metadata.json`

```json
{
  "$schema": "./schemas/site_metadata.schema.json",
  "site": {
    "title": "Portfolio | Software Engineer",
    "description": "Personal resume and portfolio showcasing projects and work experience",
    "og_image": "/resources/og-image.png"
  },
  "theme": {
    "default": "system"
  },
  "deployment": {
    "backend_port": 8000,
    "frontend_port": 3003,
    "api_base_url_dev": "http://localhost:8000",
    "frontend_url_dev": "http://localhost:3003",
    "cors_origins": ["http://localhost:3003"]
  },
  "repository": {
    "name": "res_web",
    "image_name": "res_web",
    "image_tag": "latest"
  }
}
```

### `profile/ai_models.json` (NEW)

```json
{
  "$schema": "./schemas/ai_models.schema.json",
  "models": {
    "gemini-3-flash-preview": {
      "id": "gemini-3-flash-preview",
      "label": "Gemini Flash",
      "description": "Fast responses with balanced accuracy",
      "config_type": "standard",
      "badge": "Active"
    }
  },
  "default_model": "gemini-3-flash-preview"
}
```

### `profile/pipeline_phases.json` (NEW)

```json
{
  "$schema": "./schemas/pipeline_phases.schema.json",
  "phases": {
    "connecting": {
      "id": "connecting",
      "label": "Connecting",
      "icon": "Wifi",
      "description": "Classifying query and extracting entities",
      "color": "blue",
      "color_intensity": 400,
      "glow_rgb": "96, 165, 250"
    },
    "deep_research": {
      "id": "deep_research",
      "label": "Deep Research",
      "icon": "Search",
      "description": "Gathering employer intelligence via web search",
      "color": "purple",
      "color_intensity": 400,
      "glow_rgb": "192, 132, 252"
    },
    "research_reranker": {
      "id": "research_reranker",
      "label": "Research Quality Gate",
      "icon": "ShieldCheck",
      "description": "Validating research completeness and quality",
      "color": "violet",
      "color_intensity": 400,
      "glow_rgb": "167, 139, 250"
    },
    "skeptical_comparison": {
      "id": "skeptical_comparison",
      "label": "Skeptical Comparison",
      "icon": "Scale",
      "description": "Critical gap analysis between candidate and requirements",
      "color": "amber",
      "color_intensity": 400,
      "glow_rgb": "251, 191, 36"
    },
    "skills_matching": {
      "id": "skills_matching",
      "label": "Skills Matching",
      "icon": "Briefcase",
      "description": "Mapping requirements to engineer capabilities",
      "color": "emerald",
      "color_intensity": 400,
      "glow_rgb": "52, 211, 153"
    },
    "confidence_reranker": {
      "id": "confidence_reranker",
      "label": "Confidence Calibration",
      "icon": "Gauge",
      "description": "Recalibrating match confidence scores",
      "color": "teal",
      "color_intensity": 400,
      "glow_rgb": "45, 212, 191"
    },
    "generate_results": {
      "id": "generate_results",
      "label": "Generate Results",
      "icon": "CheckCircle2",
      "description": "Synthesizing final fit analysis",
      "color": "emerald",
      "color_intensity": 400,
      "glow_rgb": "52, 211, 153"
    }
  },
  "phase_order": [
    "connecting",
    "deep_research",
    "research_reranker",
    "skeptical_comparison",
    "skills_matching",
    "confidence_reranker",
    "generate_results"
  ]
}
```

---

## 🔧 IMPLEMENTATION TASKS

### Phase 1: Create SPOT Folder Structure (Priority: HIGH)

- [ ] **1.1** Create `profile/` directory at workspace root
- [ ] **1.2** Create all JSON schema files for validation
- [ ] **1.3** Create initial JSON files by extracting current hardcoded data
- [ ] **1.4** Validate JSON files against schemas

### Phase 2: Backend Integration (Priority: HIGH)

- [ ] **2.1** Create `scripts/generate-profile-config.py`:
  - Read all JSON files from `profile/`
  - Generate `backend/config/engineer_profile.py` with proper Python types
  - Preserve existing API (ENGINEER_PROFILE dict, helper functions)
  - Add docstrings referencing SPOT files
  
- [ ] **2.2** Update `backend/services/example_generator.py`:
  - Import skills from generated config
  - Reference `examples.json` for fallback examples
  
- [ ] **2.3** Update deployment configuration:
  - `backend/server.py`: Read CORS origins from generated config
  - `backend/docker-compose.yml`: Reference deployment ports from config
  - `backend/Dockerfile`: Update metadata from site_metadata.json
  
- [ ] **2.4** Add build step to Docker workflow:
  - Run generation script before starting server
  - Or use runtime JSON loading with caching

### Phase 3: Frontend Integration (Priority: HIGH)

- [ ] **3.1** Create `scripts/generate-profile-config.js`:
  - Read all JSON files from `profile/`
  - Generate `frontend/lib/profile-data.js` as ES module export
  - Generate `frontend/lib/phaseConfig.js` from `pipeline_phases.json`
  - Generate `frontend/hooks/use-ai-settings.js` model config from `ai_models.json`
  - Support tree-shaking for optimal bundle size
  
- [ ] **3.2** Refactor `frontend/app/page.js`:
  - Import profile data from `@/lib/profile-data`
  - Replace all hardcoded values with imported constants
  - Replace `['TODO']` skills with actual skills from config
  - Maintain JSX structure, only swap data sources
  
- [ ] **3.3** Refactor `frontend/app/layout.js`:
  - Import site metadata from profile data
  - Dynamic `metadata` export using imported values
  
- [ ] **3.4** Refactor `frontend/components/fit-check/InfoDialog.jsx`:
  - Import contact/repo URLs from profile data
  - Import GitHub username from contact config
  
- [ ] **3.5** Refactor API configuration hooks:
  - `hooks/use-fit-check.js`: Import API_URL from site_metadata
  - `hooks/use-example-generator.js`: Import API_URL from site_metadata
  - `components/fit-check/SystemPromptDialog.jsx`: Import API_URL from site_metadata
  
- [ ] **3.6** Update `tailwind.config.js`:
  - Auto-generate safelist from `pipeline_phases.json` colors
  - Ensure dynamic phase colors compile correctly

### Phase 4: Asset Management (Priority: MEDIUM)

- [ ] **4.1** Update manifest generation scripts:
  - `sync_collage_images.js` → Reference `assets.json`
  - `sync_project_images.js` → Reference `projects.json` for folder names
  - `sync_timeline_images.js` → Reference `experience.json` for showcase folders
  
- [ ] **4.2** Create asset validation script:
  - Verify all referenced paths exist
  - Report missing assets during build

### Phase 5: Build Pipeline Integration (Priority: MEDIUM)

- [ ] **5.1** Add npm scripts to `frontend/package.json`:
  ```json
  {
    "scripts": {
      "generate:profile": "node ../scripts/generate-profile-config.js",
      "prebuild": "npm run generate:profile",
      "predev": "npm run generate:profile"
    }
  }
  ```

- [ ] **5.2** Update Docker configuration:
  - Mount `profile/` folder into container
  - Run generation script in Dockerfile or entrypoint

- [ ] **5.3** Add file watcher for development:
  - Watch `profile/*.json` for changes
  - Auto-regenerate configs on save

### Phase 6: Documentation & Validation (Priority: LOW)

- [ ] **6.1** Create `profile/README.md`:
  - Document each JSON file's purpose
  - Provide examples of common edits
  - Explain build process
  
- [ ] **6.2** Add JSON schema validation:
  - Create `profile/schemas/` directory
  - Add VS Code settings for schema association
  - Integrate validation into build scripts

---

## ⚠️ EDGE CASES & CONSIDERATIONS

### 1. Circular Reference Prevention
- Projects reference image folders; assets.json references the same paths
- Solution: Projects own their image references; assets.json only handles global assets

### 2. Build Order Dependencies
- Backend config must generate BEFORE server starts
- Frontend config must generate BEFORE build/dev
- Solution: Use `pre*` npm/pip scripts

### 3. Runtime vs Build-Time Loading
- **Build-Time (Recommended)**: Generated files are static, maximum performance
- **Runtime**: More flexible but adds I/O overhead
- Solution: Build-time generation with watch mode for development

### 4. Type Safety Preservation
- Backend uses typed Python; frontend uses plain JS
- Solution: Generate type hints in Python, JSDoc in JavaScript
- Future: Consider TypeScript for frontend profile types

### 5. Image Path Consistency
- Frontend uses `/resources/...` (public folder)
- Profile JSON should use the same paths
- Solution: All asset paths are frontend-relative URLs

### 6. Environment-Specific Overrides
- Different emails for dev vs production?
- Solution: Optional `profile/overrides/` folder with environment files

### 7. Environment-Specific Overrides
- Different emails for dev vs production?
- Different API URLs for local vs deployed?
- Solution: Use environment variables that override SPOT defaults
  - `NEXT_PUBLIC_API_URL` overrides `site_metadata.json` API URL
  - `ALLOWED_ORIGINS` env var overrides default CORS origins
  - Generated configs should respect env vars when present

### 8. Backward Compatibility
- Existing imports must continue working
- Solution: Generated files maintain exact same export signatures
- All existing functions (`get_formatted_profile`, `get_skills_list`) preserved

---

## 📊 IMPACT ANALYSIS

### Before SPOT

```
Files with hardcoded profile data:
├── frontend/app/page.js              → 50+ hardcoded values
├── frontend/app/layout.js            → 2 hardcoded values
├── frontend/components/...           → 3+ hardcoded values
├── backend/config/engineer_profile.py → 100+ hardcoded values
└── backend/services/example_generator.py → 20+ hardcoded values

Total: ~175+ scattered hardcoded values across 5+ files
```

### After SPOT

```
Centralized configuration:
├── profile/identity.json     → 1 file for personal info
├── profile/skills.json       → 1 file for all skills
├── profile/projects.json     → 1 file for all projects
├── profile/experience.json   → 1 file for timeline
├── profile/education.json    → 1 file for education
├── profile/contact.json      → 1 file for contact info
├── profile/assets.json       → 1 file for asset paths
├── profile/site_metadata.json → 1 file for SEO & deployment
├── profile/ai_models.json    → 1 file for AI model config
└── profile/pipeline_phases.json → 1 file for pipeline phases

Total: 10 focused configuration files, ZERO hardcoded values in code
```

### Benefits Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Files to edit for name change | 5+ | 1 | 80% reduction |
| Files to edit for skill update | 3+ | 1 | 66% reduction |
| Files to edit for API URL change | 4+ | 1 | 75% reduction |
| Files to edit for phase metadata | 2+ | 1 | 50% reduction |
| Risk of inconsistency | High | Zero | 100% improvement |
| Onboarding complexity | Medium | Low | Significant |
| Non-dev can edit profile? | No | Yes | New capability |

---

## 🚀 QUICK START AFTER IMPLEMENTATION

To update the engineer profile:

1. **Edit the appropriate JSON file in `profile/`**
2. **Run the generation scripts:**
   ```bash
   # From workspace root
   node scripts/generate-profile-config.js
   python scripts/generate-profile-config.py
   ```
3. **Restart dev servers** (or rely on watch mode)

That's it. All frontend and backend code will automatically use the new values.

---

## ✅ ACCEPTANCE CRITERIA

- [ ] All 200+ hardcoded values extracted to SPOT files (was 175+, now includes API URLs, phase configs, model configs)
- [ ] `backend/config/engineer_profile.py` is GENERATED, not manually edited
- [ ] `frontend/lib/profile-data.js` is GENERATED, not manually edited
- [ ] `frontend/lib/phaseConfig.js` is GENERATED from `pipeline_phases.json`
- [ ] `frontend/hooks/use-ai-settings.js` model config is GENERATED from `ai_models.json`
- [ ] API URLs and deployment config centralized in `site_metadata.json`
- [ ] Pipeline phase metadata centralized and used for both frontend display and tailwind safelist generation
- [ ] Existing functionality unchanged (no regressions)
- [ ] All tests pass with generated configs
- [ ] README documentation explains the new workflow
- [ ] Build scripts integrated into existing workflows
- [ ] Environment variables can override SPOT defaults where appropriate

---

## 📝 ADDITIONAL NOTES

### Discovered During Deep Audit

**Additional Hardcoded References Found:**
1. **API Configuration** (4 files): Three frontend files + backend default = scattered API URL configuration
2. **Pipeline Phase Metadata** (`phaseConfig.js`): 164 lines of phase definitions with colors, icons, descriptions
3. **AI Model Configuration** (`use-ai-settings.js`): Model definitions, labels, config types
4. **Tailwind Safelist** (`tailwind.config.js`): 36+ lines of manually maintained safelist for dynamic classes
5. **Deployment Configuration**: Ports, CORS origins in multiple Docker/server files
6. **Docker Metadata** (`Dockerfile`): Repository name, maintainer, labels

**Critical Integration Points:**
- Phase colors in `phaseConfig.js` must match Tailwind safelist
- API URLs must match between frontend hooks and backend CORS
- Model IDs must match between frontend settings and backend LLM config
- Docker image names must match across Dockerfile, docker-compose, and documentation

**Risk Areas Without SPOT:**
- Changing API port requires edits in 7+ locations
- Adding a pipeline phase requires editing phaseConfig + tailwind safelist manually
- Changing project name requires updates in 5+ Docker/metadata files
- Skills list marked as `['TODO']` indicates incomplete migration

This comprehensive audit ensures the SPOT architecture will capture **ALL** configuration points for maximum modularity.
