@echo off
cd /d "%~dp0"
echo Installing dependencies...
call npm install
echo.
echo Starting Next.js development server...
echo Website will be available at http://localhost:3000
echo.
call npm run dev
