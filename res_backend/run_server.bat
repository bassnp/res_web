@echo off
echo ============================================
echo   Portfolio Backend - Docker Restart
echo ============================================
echo.

cd /d "%~dp0"

echo Stopping existing containers...
docker-compose down

echo.
echo Rebuilding and starting containers...
docker-compose up --build -d

echo.
echo Waiting for server to start...
timeout /t 5 /nobreak >nul

echo.
echo Checking health status...
docker inspect portfolio-backend --format="{{.State.Health.Status}}"

echo.
echo ============================================
echo   Server running at http://localhost:8000
echo   Logs: docker logs -f portfolio-backend
echo ============================================