# SPOT (Single Point of Truth) Profile System

## Overview

The SPOT Profile System centralizes all engineer profile data, projects, skills, and configuration into a single, maintainable directory structure. This eliminates data duplication across frontend and backend codebases and provides a single source of truth for all profile information.

## Architecture

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
│   ├── ai_models.json                ← AI model configurations
│   ├── pipeline_phases.json          ← Pipeline phase metadata
│   └── schemas/                      ← JSON schema validation files
│
├── scripts/
│   ├── generate-profile-config.py    ← Build script for backend
│   └── generate-profile-config.js    ← Build script for frontend
│
├── backend/
│   └── config/
│       └── engineer_profile.py       ← GENERATED from SPOT
│
└── frontend/
    ├── lib/
    │   ├── profile-data.js           ← GENERATED from SPOT
    │   └── phaseConfig.js            ← GENERATED from pipeline_phases.json
    └── hooks/
        └── use-ai-settings.js        ← GENERATED from ai_models.json
```

## Quick Start

### 1. Edit Profile Data

All profile data lives in the `profile/` directory. Edit the JSON files to update your information:

- **`identity.json`** - Your name, bio, hero text, strengths, career interests
- **`skills.json`** - Technical skills organized by category
- **`projects.json`** - Featured projects with descriptions and tech stacks
- **`experience.json`** - Work experience timeline
- **`education.json`** - Degree and certifications
- **`contact.json`** - Email and social media links
- **`assets.json`** - Paths to images and documents
- **`site_metadata.json`** - Site title, description, API URLs, CORS settings
- **`ai_models.json`** - AI model configuration
- **`pipeline_phases.json`** - Pipeline phase styling and metadata

### 2. Generate Configuration Files

After editing profile data, regenerate the configuration modules:

#### Backend
```bash
# From workspace root
python scripts/generate-profile-config.py
```

#### Frontend
```bash
# From workspace root
node scripts/generate-profile-config.js
```

### 3. Automatic Generation

The generation scripts are automatically triggered:

- **Frontend**: Before `npm run dev` and `npm run build` (via `predev` and `prebuild` scripts)
- **Backend**: During Docker build and via `run_docker_rebuild.bat`

## File Descriptions

### Core Profile Files

#### `identity.json`
Personal identity and biographical information:
- Name variants (full, display, professional title)
- Portrait path and alt text
- Hero animation text
- Bio (TLDR and full versions)
- Experience summary
- Key strengths
- Career interests

#### `skills.json`
Technical skills organized into:
- **Display Categories** - Skills shown in the UI with labels
- **Backend Categories** - Skills used by the AI agent for matching
  - Languages
  - Frameworks
  - Cloud/DevOps
  - AI/ML
  - Tools

#### `projects.json`
Featured projects with:
- ID (must match image folder name)
- Title and description
- Extended "about" text for modals
- Learning outcomes
- Technology tags
- Gradient color class
- Optional external link

#### `experience.json`
Work experience timeline entries with:
- Job title and company
- Time period
- Description
- Technology tags
- Color theme
- Optional showcase folder

#### `education.json`
Academic credentials:
- Primary degree information
- Institution and graduation date
- Logo path
- Certifications (array)

#### `contact.json`
Contact information:
- Email address
- Social media links (GitHub, etc.)
- Repository URL

#### `assets.json`
Static asset paths:
- Portrait image
- School logo
- Resume PDF (path, thumbnail, label)
- Personal collage folder and manifest
- Project images base path
- Timeline images base path

#### `site_metadata.json`
Site-wide configuration:
- **Site**: Title, description, OG image
- **Theme**: Default theme preference
- **Deployment**: Ports, API URLs, CORS origins
- **Repository**: Docker image name, maintainer, source URL

#### `ai_models.json`
AI model definitions:
- Model ID, label, description
- Configuration type (standard/reasoning)
- Badge text
- Disabled models with reasons

#### `pipeline_phases.json`
Pipeline phase styling:
- Phase ID, label, icon name
- Description
- Color and intensity
- Glow RGB values
- Phase execution order

### Schema Files

All JSON files have corresponding JSON schemas in `profile/schemas/` for validation and IDE autocomplete.

## Generated Files

**DO NOT EDIT THESE FILES DIRECTLY** - They are auto-generated from the SPOT profile data.

### Backend
- `backend/config/engineer_profile.py`
  - Contains `ENGINEER_PROFILE` dictionary
  - Provides helper functions like `get_formatted_profile()`, `get_skills_list()`, etc.
  - Used by AI agent for skill matching and analysis

### Frontend
- `frontend/lib/profile-data.js`
  - Exports all profile data as ES modules
  - Provides convenience exports like `HERO_TEXT`, `PRIMARY_SKILLS`, `EMAIL`, etc.
  - Used throughout UI components

- `frontend/lib/phaseConfig.js`
  - Pipeline phase UI configuration
  - Icon mappings, colors, gradients
  - Used by Fit Check components

- `frontend/hooks/use-ai-settings.js`
  - AI model configuration hook
  - Model selection and settings context
  - Used by AI-powered features

## Build Integration

### Frontend Package.json
```json
{
  "scripts": {
    "generate:profile": "node ../scripts/generate-profile-config.js",
    "predev": "npm run generate:profile",
    "prebuild": "npm run generate:profile",
    "dev": "next dev ...",
    "build": "..."
  }
}
```

### Backend Docker Build
The Dockerfile includes a step to generate the profile before copying application code:

```dockerfile
# Generate the engineer_profile.py from SPOT before copying other code
RUN python ../scripts/generate-profile-config.py
```

### Backend Build Script
`run_docker_rebuild.bat` generates the profile as the first step:

```bat
echo [0/5] Generating profile configuration from SPOT...
python scripts\generate-profile-config.py
```

## Validation

All JSON files reference JSON schemas for validation. VS Code will automatically validate files if you have the JSON Language Features extension.

To manually validate:
```bash
# Example using a JSON schema validator
jsonschema -i profile/identity.json profile/schemas/identity.schema.json
```

## Environment Variables

The SPOT system respects environment variable overrides:

- `NEXT_PUBLIC_API_URL` - Overrides `site_metadata.json` API base URL
- `ALLOWED_ORIGINS` - Overrides default CORS origins
- `GEMINI_MODEL` - Overrides default AI model

## Best Practices

### When to Regenerate

Run generation scripts after:
- ✅ Editing any JSON file in `profile/`
- ✅ Adding new projects or experience entries
- ✅ Updating contact information
- ✅ Changing AI model configuration
- ✅ Modifying pipeline phases

### Development Workflow

1. Edit JSON files in `profile/`
2. Run generation script manually (optional, auto-runs on dev start)
3. Start development server
4. Changes are reflected immediately

### Production Deployment

1. Edit JSON files in `profile/`
2. Commit changes to version control
3. Build process automatically generates configs
4. Deploy with generated files

### Adding New Profile Fields

1. Add field to appropriate JSON file in `profile/`
2. Update corresponding schema in `profile/schemas/`
3. Modify generation script to export the new field
4. Update components to consume the new field

## Troubleshooting

### "File not found" errors
- Ensure you're running scripts from the workspace root
- Check that all profile JSON files exist

### Generated files out of sync
```bash
# Regenerate all configs
python scripts/generate-profile-config.py
node scripts/generate-profile-config.js
```

### Build fails in Docker
- Check that profile generation succeeds locally first
- Verify Docker has access to parent directories (profile/, scripts/)

### Frontend import errors
- Ensure `predev` script ran successfully
- Check that generated files exist in `frontend/lib/` and `frontend/hooks/`

## Maintenance

### Adding a New Profile JSON File

1. Create the JSON file in `profile/`
2. Create a corresponding schema in `profile/schemas/`
3. Update `generate-profile-config.py` to load the new file
4. Update `generate-profile-config.js` to load the new file
5. Add appropriate exports to generated modules
6. Update this README

### Modifying Generated Modules

If you need to change the structure of generated files:
1. Edit the generation script (`generate-profile-config.py` or `.js`)
2. Regenerate the files
3. Test thoroughly
4. Update any dependent code

## Benefits

✅ **Single Source of Truth** - Edit profile data in one place
✅ **Type Safety** - JSON schemas validate data structure
✅ **Maintainability** - No duplicate data across codebase
✅ **Consistency** - Frontend and backend stay in sync
✅ **Modularity** - Easy to add/modify profile sections
✅ **Automation** - Automatic regeneration on build
✅ **Version Control** - Track profile changes over time
✅ **Documentation** - Self-documenting JSON structure

## Migration Notes

This SPOT system replaced hardcoded values across:
- Frontend: `app/page.js`, `app/layout.js`, various components
- Backend: `config/engineer_profile.py`
- Hooks: API URLs and model configuration

All data is now sourced from the `profile/` directory.
