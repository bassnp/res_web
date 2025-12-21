````markdown
# Phase 4: Sevalla Deployment Configuration Guide

> **Priority:** 🟢 LOW  
> **Estimated Time:** 30 minutes  
> **Prerequisite:** Phases 1-3 complete  
> **Platform:** Sevalla Static Site (Frontend) + Sevalla Application Docker (Backend)

---

## Overview

This phase configures the application for Sevalla PaaS deployment. **Sevalla handles most infrastructure concerns automatically**, significantly reducing deployment complexity compared to self-managed Docker/Kubernetes setups.

### What Sevalla Provides (No Configuration Needed)

| Feature | Status | Notes |
|---------|--------|-------|
| **SSL/HTTPS** | ✅ Automatic | Free certificates, auto-renewed |
| **Reverse Proxy** | ✅ Automatic | Platform handles routing |
| **Load Balancing** | ✅ Automatic | Built into platform |
| **CDN** | ✅ Automatic | For static sites |
| **Health Checks** | ✅ Automatic | Probes `/health` endpoint |
| **Custom Domains** | ✅ Dashboard | Easy configuration |
| **Environment Variables** | ✅ Dashboard | Global + app-level support |
| **Git Deployments** | ✅ Automatic | Push to deploy |
| **Logging** | ✅ Automatic | Platform-provided |

### What We Configure

| Item | Effort | Description |
|------|--------|-------------|
| Dockerfile optimization | 5 min | SSE-optimized settings |
| Environment variables | 10 min | Set in Sevalla dashboard |
| CORS configuration | 5 min | Update allowed origins |
| Frontend build config | 5 min | Verify static export |

---

## Prerequisites

- [ ] Phases 1-3 completed and verified locally
- [ ] Sevalla account created (sevalla.com)
- [ ] Git repository connected to Sevalla
- [ ] Domain configured (optional)

---

## Implementation Checklist

### Step 1: Optimize Dockerfile for Sevalla

**File:** `backend/Dockerfile`

Sevalla runs single-container Docker applications. Optimize for SSE streaming:

#### 1.1 Update CMD for SSE

```dockerfile
# Health check - Sevalla also probes this endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Optimized for SSE streaming on Sevalla PaaS
# - Single worker: async handles concurrency (no need for multiple workers)
# - Extended keep-alive: supports long-lived SSE connections
# - Access log: useful for Sevalla's log viewer
CMD ["uvicorn", "server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "75", \
     "--access-log"]
```

**Why single worker?**
- FastAPI/uvicorn is async-native; concurrency is handled within the event loop
- SSE connections are long-lived; multiple workers can cause routing issues
- Sevalla can scale horizontally if needed (spin up additional containers)

- [ ] **TODO:** Update CMD in Dockerfile
- [ ] **TODO:** Verify HEALTHCHECK is present

---

### Step 2: Configure Environment Variables in Sevalla

Navigate to: **Sevalla Dashboard → Your Application → Settings → Environment Variables**

#### 2.1 Required Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `GOOGLE_API_KEY` | Gemini LLM API key | `AIza...` |
| `GOOGLE_CSE_API_KEY` | Google Custom Search API key | `AIza...` |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID | `abc123...` |
| `ALLOWED_ORIGINS` | Frontend domain (CORS) | `https://portfolio.example.com` |

#### 2.2 Optional Variables

| Variable | Description | Default | Recommendation |
|----------|-------------|---------|----------------|
| `LOG_LEVEL` | Logging verbosity | `INFO` | Keep `INFO` for production |
| `LOG_FORMAT` | Log format | `text` | Use `json` for structured logs |
| `GEMINI_MODEL` | Default model | `gemini-2.0-flash` | Override as needed |

#### 2.3 Use Global Variables (Recommended)

For API keys used across multiple applications:

1. Go to **Sevalla Dashboard → Global Environment Variables**
2. Add shared keys like `GOOGLE_API_KEY`
3. These will be available to all your applications

- [ ] **TODO:** Add `GOOGLE_API_KEY` in Sevalla dashboard
- [ ] **TODO:** Add `GOOGLE_CSE_API_KEY` in Sevalla dashboard
- [ ] **TODO:** Add `GOOGLE_CSE_ID` in Sevalla dashboard
- [ ] **TODO:** Set `ALLOWED_ORIGINS` to your frontend domain

---

### Step 3: Configure Frontend Static Site

#### 3.1 Verify Next.js Static Export

**File:** `frontend/next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Required for static site hosting
  images: {
    unoptimized: true,  // Required for static export
  },
  // ... other config
};

module.exports = nextConfig;
```

#### 3.2 Sevalla Static Site Settings

In **Sevalla Dashboard → Static Sites → Create/Configure**:

| Setting | Value |
|---------|-------|
| **Build Command** | `npm run build` |
| **Output Directory** | `out` |
| **Node Version** | `18` or `20` |
| **Install Command** | `npm install` (automatic) |

#### 3.3 Update API URL for Production

**File:** `frontend/lib/profile-data.js` (or environment variable)

Ensure `API_BASE_URL` points to your Sevalla backend:

```javascript
// Use environment variable or hardcode for static export
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-backend.sevalla.app';
```

Or set in Sevalla Static Site environment:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.sevalla.app` |

- [ ] **TODO:** Verify `output: 'export'` in next.config.js
- [ ] **TODO:** Configure Sevalla Static Site with correct build command
- [ ] **TODO:** Set `NEXT_PUBLIC_API_URL` to backend URL

---

### Step 4: Verify Health Endpoint

Sevalla automatically probes `/health` for container health. Ensure it's working:

**File:** `backend/server.py` (should already exist)

```python
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Sevalla probes."""
    return {
        "status": "healthy",
        "service": "portfolio-backend-api",
        "version": "1.0.0",
    }
```

- [ ] **TODO:** Verify `/health` endpoint exists and returns JSON

---

### Step 5: Git-Based Deployment

Sevalla supports automatic deployments on git push:

1. **Connect Repository:** Link your GitHub/GitLab/Bitbucket repo
2. **Select Branch:** Choose `main` or `production`
3. **Auto Deploy:** Enable for automatic deployments on push

#### Deployment Flow

```
git push origin main
        │
        ▼
┌───────────────────┐
│ Sevalla detects   │
│ push to main      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Docker build      │
│ from Dockerfile   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Container starts  │
│ Health check pass │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Traffic routed    │
│ to new container  │
└───────────────────┘
```

- [ ] **TODO:** Connect git repository to Sevalla
- [ ] **TODO:** Enable auto-deploy on push to main

---

## NOT Required (Sevalla Handles)

The following are **handled by Sevalla automatically** and should NOT be configured:

### ❌ Nginx Reverse Proxy

Sevalla provides its own reverse proxy. Do not create:
- `nginx.conf`
- `docker-compose.prod.yml` with nginx service
- Custom load balancer configuration

### ❌ SSL Certificate Configuration

Sevalla provides free, auto-renewed SSL certificates. No need for:
- Let's Encrypt configuration
- Certificate files
- SSL-related environment variables

### ❌ Docker Compose for Production

Sevalla deploys single Dockerfile per application. Do not use:
- `docker-compose.prod.yml`
- Multi-container orchestration
- Replica configuration in compose files

### ❌ Custom Health Check Scripts

Sevalla probes your `/health` endpoint automatically. The simple health check in `server.py` is sufficient. No need for:
- `scripts/healthcheck.py`
- Complex health check logic

### ❌ Prometheus Metrics Endpoint

Unless you need custom metrics beyond Sevalla's built-in monitoring:
- No need for `/metrics` endpoint
- No need for `prometheus-client` dependency

### ❌ Resource Limits in Docker Compose

Sevalla manages resources based on your selected plan:
- No `deploy.resources.limits` needed
- No CPU/memory configuration in Docker

---

## Verification & Validation

### Test 1: Local Docker Build

Before deploying, verify the Docker build works locally:

```bash
cd backend
docker build -t res_web:test .
docker run -p 8000:8000 --env-file .env.local res_web:test

# In another terminal
curl http://localhost:8000/health
```

- [ ] **TODO:** Docker build succeeds
- [ ] **TODO:** Container starts without errors
- [ ] **TODO:** Health endpoint responds

---

### Test 2: Sevalla Deployment

After pushing to git:

1. Check Sevalla dashboard for build logs
2. Wait for deployment to complete (green status)
3. Test the deployed endpoints:

```bash
# Health check
curl https://your-backend.sevalla.app/health

# SSE endpoint (replace with your domain)
curl -X POST https://your-backend.sevalla.app/api/fit-check/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Google"}' \
  --no-buffer
```

- [ ] **TODO:** Deployment succeeds in Sevalla dashboard
- [ ] **TODO:** Health endpoint responds on Sevalla URL
- [ ] **TODO:** SSE streaming works through Sevalla proxy

---

### Test 3: Frontend to Backend Connection

1. Deploy frontend static site to Sevalla
2. Visit the deployed frontend URL
3. Submit a fit check query
4. Verify SSE stream works end-to-end

- [ ] **TODO:** Frontend loads correctly
- [ ] **TODO:** Fit check query triggers backend SSE
- [ ] **TODO:** Full pipeline completes successfully

---

### Test 4: CORS Configuration

If you see CORS errors:

1. Check `ALLOWED_ORIGINS` in Sevalla environment variables
2. Ensure it matches your frontend domain exactly (including `https://`)
3. Redeploy backend after changing environment variables

```bash
# Example ALLOWED_ORIGINS value (multiple origins comma-separated):
https://portfolio.example.com,https://www.portfolio.example.com
```

- [ ] **TODO:** No CORS errors in browser console
- [ ] **TODO:** SSE connection established successfully

---

## Completion Checklist

After completing all steps and tests:

**File:** `_devnotes/MULTI_SESSION_UPGRADE_PLAN.md`

Mark Phase 4 as complete:
```markdown
| **Phase 4: Sevalla Deployment** | ✅ Complete | 2024-XX-XX |
```

### Summary of Changes

| Item | Change |
|------|--------|
| `backend/Dockerfile` | SSE-optimized CMD with single worker |
| Sevalla Environment | API keys and ALLOWED_ORIGINS configured |
| Sevalla Application | Git deployment connected |
| Sevalla Static Site | Frontend build configured |

### Files NOT Needed (Removed/Skipped)

| File | Reason |
|------|--------|
| `nginx.conf` | Sevalla handles reverse proxy |
| `docker-compose.prod.yml` | Single container deployment |
| `scripts/healthcheck.py` | Platform probes `/health` |
| `nginx/` directory | Not needed |

---

## Troubleshooting

### SSE Not Streaming (Events Batched)

Sevalla's proxy should handle SSE correctly. If events are batched:

1. Verify the `X-Accel-Buffering: no` header is sent by backend
2. Check the SSE endpoint path is not being cached

**File:** `backend/routers/fit_check.py`

```python
return StreamingResponse(
    generate_events(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disables proxy buffering
    },
)
```

### Container Keeps Restarting

Check health check is passing:

1. View Sevalla logs: **Dashboard → Application → Logs**
2. Ensure `/health` endpoint returns 200 status quickly (< 5 seconds)
3. Check for startup errors in logs

### Build Fails

Check Dockerfile syntax and requirements:

```bash
# Test locally first
docker build -t test .
```

Common issues:
- Missing `requirements.txt`
- Python version mismatch
- Missing system dependencies

### Environment Variables Not Working

1. Environment variable changes require a redeploy
2. Check for typos in variable names
3. Ensure no quotes around values in dashboard

---

## Next Steps

With Sevalla deployment complete:

1. **Configure Custom Domain:** Add your domain in Sevalla dashboard
2. **Enable Auto-Deploy:** Automatic deployments on git push
3. **Set Up Monitoring:** Use Sevalla's built-in logs and metrics
4. **Proceed to Phase 5:** Frontend enhancements (optional)

---

## Appendix: Sevalla Quick Reference

### Dashboard Navigation

| Action | Path |
|--------|------|
| View Logs | Application → Logs |
| Environment Variables | Application → Settings → Environment Variables |
| Restart App | Application → Actions → Restart |
| View Deployments | Application → Deployments |
| Custom Domains | Application → Domains |

### Useful Sevalla Features

| Feature | Description |
|---------|-------------|
| **Build Logs** | Real-time Docker build output |
| **Runtime Logs** | Application stdout/stderr |
| **Deployment History** | Rollback to previous versions |
| **Preview Branches** | Deploy PR branches for testing |
| **Global Variables** | Share env vars across apps |
````
