@echo off
REM Clean rebuild script for res_web Backend Docker container
echo ========================================
echo res_web Backend - Clean Rebuild
echo ========================================
echo.

echo [1/4] Stopping and removing existing containers...
docker stop res_web-backend 2>nul
docker rm res_web-backend 2>nul
docker compose down -v 2>nul
echo Done.

echo.
echo [2/4] Building Docker image...
docker compose build --no-cache

if errorlevel 1 (
    echo.
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Starting container...
docker compose up -d

if errorlevel 1 (
    echo.
    echo ERROR: Container failed to start!
    pause
    exit /b 1
)

echo.
echo [4/4] Waiting for health check...
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
