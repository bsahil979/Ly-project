@echo off
REM Start Frontend Only
cd /d "%~dp0frontend"
echo Starting Frontend...
npm install --legacy-peer-deps
npm run dev
pause
