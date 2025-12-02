@echo off
REM Build for Sevalla Production Deployment
REM This script builds the static export with production API URLs

echo ================================================================================
echo res_web - Production Build for Sevalla
echo ================================================================================
echo.

echo [1/4] Backing up local development .env.local...
if exist .env.local (
    move .env.local .env.local.dev.backup >nul 2>&1
    echo Backed up .env.local to .env.local.dev.backup
) else (
    echo No .env.local found, using .env production values
)
echo.

echo [2/4] Verifying production environment...
echo Production API URL: http://us-west4-001.proxy.sevalla.app:30981
echo.

echo [3/4] Building static export...
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    if exist .env.local.dev.backup (
        move .env.local.dev.backup .env.local >nul 2>&1
    )
    pause
    exit /b 1
)
echo.

echo [4/4] Restoring local development .env.local...
if exist .env.local.dev.backup (
    move .env.local.dev.backup .env.local >nul 2>&1
    echo Restored .env.local
)
echo.

echo ================================================================================
echo SUCCESS! Production build complete
echo ================================================================================
echo.
echo Static files are in the 'out' folder
echo Upload 'out' folder contents to Sevalla static hosting
echo.
echo API URL baked in: http://us-west4-001.proxy.sevalla.app:30981
echo ================================================================================
