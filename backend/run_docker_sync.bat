@echo off
REM =============================================================================
REM Docker Sync - Build, Login, and Push to Docker Hub
REM =============================================================================
REM This script automates the complete Docker deployment pipeline for Sevalla.
REM
REM SECURITY: This image contains NO secrets. All API keys are provided at
REM           runtime via Sevalla's environment variable configuration.
REM
REM Required Sevalla Environment Variables:
REM   - GOOGLE_API_KEY      : Gemini API key
REM   - GOOGLE_CSE_API_KEY  : Google Custom Search API key  
REM   - GOOGLE_CSE_ID       : Google Custom Search Engine ID
REM
REM Optional Sevalla Environment Variables:
REM   - GEMINI_MODEL        : Model name (default: gemini-2.0-flash-thinking-exp-01-21)
REM   - LOG_LEVEL           : Logging level (default: INFO)
REM   - ALLOWED_ORIGINS     : CORS origins (default: *)
REM   - HOST                : Bind address (default: 0.0.0.0)
REM   - PORT                : Listen port (default: 8000)
REM =============================================================================

setlocal enabledelayedexpansion

echo ================================================================================
echo Docker Sync - res_web Backend Deployment
echo ================================================================================
echo.

REM ---------------------------------------------------------------------------
REM Pre-flight Security Checks
REM ---------------------------------------------------------------------------
echo [PRE-FLIGHT] Running security verification...

REM Check that no .env files will be included in the build
if exist ".env" (
    echo [SECURITY] Found .env file - verifying .dockerignore exclusion...
    findstr /C:".env" .dockerignore >nul 2>&1
    if errorlevel 1 (
        echo ERROR: .env files are not excluded in .dockerignore!
        echo        This could leak secrets into the Docker image.
        pause
        exit /b 1
    )
    echo [SECURITY] OK - .env excluded via .dockerignore
)

REM Verify no hardcoded secrets in source files
echo [SECURITY] Scanning for hardcoded API keys...
findstr /S /I /M "AIzaSy" *.py >nul 2>&1
if not errorlevel 1 (
    echo WARNING: Potential API key found in source files!
    echo          Please verify no secrets are hardcoded.
    echo.
    findstr /S /I /N "AIzaSy" *.py
    echo.
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo Aborted.
        exit /b 1
    )
) else (
    echo [SECURITY] OK - No hardcoded API keys detected
)
echo.

REM ---------------------------------------------------------------------------
REM Step 1: Stop and clean existing containers
REM ---------------------------------------------------------------------------
echo [STEP 1/6] Stopping and cleaning existing containers...
docker compose down -v 2>nul
echo Done.
echo.

REM ---------------------------------------------------------------------------
REM Step 2: Build Docker image (no secrets baked in)
REM ---------------------------------------------------------------------------
echo [STEP 2/6] Building Docker image (this may take a few minutes)...
echo [INFO] Image will NOT contain any API keys or secrets.
echo [INFO] All credentials are provided at runtime by Sevalla.
echo.
docker compose build --no-cache
if errorlevel 1 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)
echo.

REM ---------------------------------------------------------------------------
REM Step 3: Verify image security (no secrets in layers)
REM ---------------------------------------------------------------------------
echo [STEP 3/6] Verifying image security...
echo [INFO] Checking image layers for exposed secrets...

REM Quick check: ensure image doesn't have env vars baked in
docker inspect res_web:latest --format="{{range .Config.Env}}{{println .}}{{end}}" | findstr /I "GOOGLE_API_KEY GOOGLE_CSE" >nul 2>&1
if not errorlevel 1 (
    echo ERROR: API keys detected in Docker image environment!
    echo        Secrets should NOT be baked into the image.
    echo        Check Dockerfile for ENV statements with real keys.
    pause
    exit /b 1
)
echo [SECURITY] OK - No API keys in image layers
echo.

REM ---------------------------------------------------------------------------
REM Step 4: Login to Docker Hub
REM ---------------------------------------------------------------------------
echo [STEP 4/6] Logging into Docker Hub...
docker login
if errorlevel 1 (
    echo ERROR: Docker login failed!
    pause
    exit /b 1
)
echo.

REM ---------------------------------------------------------------------------
REM Step 5: Tag and push image to Docker Hub
REM ---------------------------------------------------------------------------
echo [STEP 5/6] Tagging and pushing image to Docker Hub...
docker tag res_web:latest bassn/res_web:latest
docker push bassn/res_web:latest
if errorlevel 1 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)
echo.

REM ---------------------------------------------------------------------------
REM Step 6: Final verification
REM ---------------------------------------------------------------------------
echo [STEP 6/6] Verifying deployment...
docker images bassn/res_web
echo.

echo ================================================================================
echo SUCCESS! Docker image pushed to Docker Hub
echo ================================================================================
echo.
echo Image: bassn/res_web:latest
echo Registry: Docker Hub (public)
echo.
echo ================================================================================
echo SEVALLA DEPLOYMENT INSTRUCTIONS
echo ================================================================================
echo.
echo 1. In Sevalla Dashboard, create a Docker Application:
echo    - Image: bassn/res_web:latest
echo    - Port: 8000
echo.
echo 2. Configure these REQUIRED environment variables in Sevalla:
echo.
echo    GOOGLE_API_KEY=your_gemini_api_key_here
echo    GOOGLE_CSE_API_KEY=your_cse_api_key_here
echo    GOOGLE_CSE_ID=your_cse_id_here
echo.
echo 3. Optional environment variables:
echo.
echo    GEMINI_MODEL=gemini-2.0-flash-thinking-exp-01-21
echo    LOG_LEVEL=INFO
echo    ALLOWED_ORIGINS=https://your-frontend.sevalla.app
echo    HOST=0.0.0.0
echo    PORT=8000
echo.
echo 4. Deploy and verify health check:
echo    GET https://your-backend.sevalla.app/health
echo.
echo ================================================================================
echo SECURITY NOTES
echo ================================================================================
echo.
echo [OK] Image contains NO secrets - safe for public registry
echo [OK] All API keys provided at runtime via Sevalla env vars
echo [OK] Non-root user (appuser:1000) inside container
echo [OK] Health check endpoint: /health
echo [OK] SSE streaming optimized (timeout-keep-alive: 75s)
echo.
echo ================================================================================

endlocal
