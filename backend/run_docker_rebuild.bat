@echo off
REM Clean rebuild script for res_web Backend Docker container
echo ========================================
echo res_web Backend - Clean Rebuild
echo ========================================
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
echo [1/5] Stopping and removing existing containers...
docker compose down --remove-orphans 2>nul
docker stop res_web-backend 2>nul
docker rm -f res_web-backend 2>nul
echo Done.

echo.
echo [2/5] Killing any process using port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)
echo Done.

echo.
echo [3/5] Building Docker image...
docker compose build --no-cache

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
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Rebuild Complete!
echo ========================================
echo.
echo API: http://localhost:8000
echo Health: http://localhost:8000/health
echo Docs: http://localhost:8000/docs
echo.
echo View logs: docker logs -f res_web-backend
echo.
