# SPOT System - Quick Reference Guide

## Daily Workflow

### Updating Your Profile

1. **Edit the JSON files** in `profile/` directory
   ```bash
   # Example: Update your bio
   notepad profile/identity.json
   ```

2. **Regenerate config files** (or let build scripts do it automatically)
   ```bash
   # Backend
   python scripts/generate-profile-config.py
   
   # Frontend
   node scripts/generate-profile-config.js
   ```

3. **Restart your development servers**
   ```bash
   # Frontend (auto-generates on start)
   cd frontend
   npm run dev
   
   # Backend (auto-generates in Docker)
   cd backend
   .\run_docker_rebuild.bat
   ```

## Common Updates

### Adding a New Skill
**File:** `profile/skills.json`

```json
{
  "display_categories": {
    "primary": {
      "skills": [
        "Python",
        "JavaScript",
        "YOUR_NEW_SKILL"  // Add here
      ]
    }
  },
  "backend_categories": {
    "languages": ["YOUR_NEW_SKILL"]  // Also add to appropriate category
  }
}
```

### Adding a New Project
**File:** `profile/projects.json`

```json
{
  "featured": [
    {
      "id": "new-project",
      "title": "New Project Title",
      "description": "Brief description for card",
      "about": "Extended description for modal",
      "learning_outcomes": [
        "What you learned",
        "Key takeaways"
      ],
      "tags": ["Tech", "Stack"],
      "color": "from-burnt-peach to-apricot",
      "images_folder": "project-new-project",
      "link": "https://github.com/username/repo"
    }
  ]
}
```

### Updating Contact Info
**File:** `profile/contact.json`

```json
{
  "email": "your.new.email@example.com",
  "social": {
    "github": {
      "url": "https://github.com/your-username",
      "display": "your-username"
    }
  }
}
```

### Changing Hero Text
**File:** `profile/identity.json`

```json
{
  "hero": {
    "animation_left": "I'm Your Name",
    "animation_right": "Your Title Here"
  }
}
```

### Updating API Configuration
**File:** `profile/site_metadata.json`

```json
{
  "deployment": {
    "backend_port": 8000,
    "frontend_port": 3003,
    "api_base_url_dev": "http://localhost:8000",
    "cors_origins": ["http://localhost:3003"]
  }
}
```

## File Structure Reference

```
profile/
├── identity.json          # Name, bio, hero text, strengths
├── skills.json            # Technical skills by category
├── projects.json          # Featured projects
├── experience.json        # Work timeline
├── education.json         # Degree and certs
├── contact.json           # Email, GitHub, social
├── assets.json            # Image/document paths
├── site_metadata.json     # Site config, API URLs
├── ai_models.json         # AI model settings
├── pipeline_phases.json   # Pipeline styling
└── schemas/               # JSON validation schemas
```

## Generated Files (Don't Edit!)

❌ **NEVER edit these files directly:**
- `backend/config/engineer_profile.py`
- `frontend/lib/profile-data.js`
- `frontend/lib/phaseConfig.js`
- `frontend/hooks/use-ai-settings.js`

✅ **Instead, edit the source JSON in `profile/` and regenerate**

## Build Commands

### Frontend
```bash
npm run generate:profile   # Generate config manually
npm run dev                 # Auto-generates before starting
npm run build               # Auto-generates before building
```

### Backend
```bash
python scripts/generate-profile-config.py   # Generate config
.\run_docker_rebuild.bat                    # Auto-generates in Docker build
```

## Validation

Check for errors in your JSON files:

```bash
# Visual Studio Code will auto-validate with JSON schemas
# Look for squiggly lines in your JSON files

# Manual validation (if you have a validator installed)
jsonschema -i profile/identity.json profile/schemas/identity.schema.json
```

## Troubleshooting

### "Cannot find module" errors
```bash
# Regenerate all configs
python scripts/generate-profile-config.py
node scripts/generate-profile-config.js
```

### Changes not appearing
```bash
# 1. Verify JSON file saved
# 2. Regenerate configs
# 3. Restart dev server (Ctrl+C, then start again)
```

### JSON validation errors
```
# Check your JSON syntax:
# - Missing commas between items
# - Extra trailing commas
# - Unescaped quotes
# - Invalid schema references
```

### Docker build fails
```bash
# 1. Test generation locally first
python scripts/generate-profile-config.py

# 2. Check for errors in output
# 3. Verify all JSON files are valid
# 4. Try rebuild
.\run_docker_rebuild.bat
```

## Environment Variables

Override SPOT defaults with environment variables:

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://api.production.com

# Backend (.env)
ALLOWED_ORIGINS=https://production.com,https://www.production.com
```

## Quick Checklist

Before deploying:
- [ ] All JSON files validated (no schema errors)
- [ ] Generated configs up to date
- [ ] Email addresses correct
- [ ] GitHub links valid
- [ ] API URLs appropriate for environment
- [ ] Images/assets exist at specified paths
- [ ] Projects have matching image folders

## Getting Help

1. Check [profile/README.md](profile/README.md) for detailed documentation
2. Review [SPOT_IMPLEMENTATION_SUMMARY.md](SPOT_IMPLEMENTATION_SUMMARY.md) for architecture
3. Check JSON schemas in `profile/schemas/` for field requirements
4. Verify generated files match your JSON data

## Pro Tips

💡 **Use VS Code** - Automatic JSON validation with schemas  
💡 **Commit JSON files** - Track profile changes in git  
💡 **Test locally** - Generate and test before deploying  
💡 **One source of truth** - Only edit profile/ directory  
💡 **Schema validation** - Catches errors before runtime  

---

**Last Updated:** December 19, 2025  
**System Version:** 1.0.0  
**Status:** Production Ready ✅
