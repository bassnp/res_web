@echo off
REM Quick refresh script for res_web Backend Docker container
echo ========================================
echo res_web Backend - Quick Refresh
echo ========================================
echo.

echo [PRE-CHECK] Verifying Docker is running...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Docker is not running! 
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo Done.

echo.
echo [0/5] Generating profile configuration from SPOT...
cd ..
python scripts\generate-profile-config.py
if errorlevel 1 (
    echo.
    echo ERROR: Profile generation failed!
    pause
    exit /b 1
)
cd backend
echo Done.

echo.
echo [1/5] Stopping existing containers...
docker compose down 2>nul
echo Done.

echo.
echo [2/5] Killing any process using port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)
echo Done.

echo.
echo [3/5] Building Docker image (using cache)...
docker compose build

if errorlevel 1 (
    echo.
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo.
echo [4/5] Starting container...
docker compose up -d

if errorlevel 1 (
    echo.
    echo ERROR: Container failed to start!
    pause
    exit /b 1
)

echo.
echo [5/5] Waiting for health check...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Refresh Complete!
echo ========================================
echo.
echo API: http://localhost:8000
echo Health: http://localhost:8000/health
echo Docs: http://localhost:8000/docs
echo.
echo View logs: docker logs -f res_web-backend
echo.
