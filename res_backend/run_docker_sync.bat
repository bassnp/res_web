@echo off
REM Docker Sync - Build, Login, and Push to Docker Hub
REM This script automates the complete Docker deployment pipeline

echo ================================================================================
echo Docker Sync - res_web Backend Deployment
echo ================================================================================
echo.

echo [STEP 1/5] Stopping and cleaning existing containers...
docker compose down -v
echo Done.
echo.

echo [STEP 2/5] Building Docker image (this may take a few minutes)...
docker compose build --no-cache
if errorlevel 1 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)
echo.

echo [STEP 3/5] Logging into Docker Hub...
docker login
if errorlevel 1 (
    echo ERROR: Docker login failed!
    pause
    exit /b 1
)
echo.

echo [STEP 4/5] Tagging and pushing image to Docker Hub...
docker tag res_web:latest bassn/res_web:latest
docker push bassn/res_web:latest
if errorlevel 1 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)
echo.

echo [STEP 5/5] Verifying deployment...
docker images bassn/res_web
echo.

echo ================================================================================
echo SUCCESS! Docker image pushed to Docker Hub
echo ================================================================================
echo Image: bassn/res_web:latest
echo.
echo TO DEPLOY ON ANY SERVER:
echo   docker pull bassn/res_web:latest
echo   docker run -d -p 8000:8000 --env-file .env bassn/res_web:latest
echo.
echo Or with auto-restart and custom name:
echo   docker run -d --name res_web-backend --restart unless-stopped -p 8000:8000 --env-file .env bassn/res_web:latest
echo.
echo IMPORTANT: You must provide .env file with API keys at runtime!
echo   - GOOGLE_API_KEY
echo   - GOOGLE_CSE_API_KEY
echo   - GOOGLE_CSE_ID
echo.
echo Port exposed: 8000 (HTTP)
echo Health check: http://YOUR_SERVER_IP:8000/health
echo ================================================================================
