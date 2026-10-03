@echo off
title FleetFlow Platform Launcher
echo ================================================================
echo          Starting FleetFlow Platform (Milestone 2)
echo ================================================================

:: 1. Start FastAPI Backend in a separate window
echo [1/3] Launching FastAPI Backend on http://localhost:8000...
if exist "%~dp0venv\Scripts\uvicorn.exe" (
    start "FleetFlow Backend" cmd /k "cd /d "%~dp0" && "%~dp0venv\Scripts\uvicorn.exe" app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"
) else (
    start "FleetFlow Backend" cmd /k "cd /d "%~dp0" && uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"
)

:: 2. Start Vite Frontend in a separate window
echo [2/3] Launching Vite Frontend on http://localhost:5173...
start "FleetFlow Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: 3. Wait 3 seconds and open default browser
echo [3/3] Opening browser at http://localhost:5173...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo ================================================================
echo FleetFlow is now running!
echo - Local Frontend:  http://localhost:5173
echo - Local Swagger:   http://localhost:8000/docs
echo - Live Deployed:   https://fleetflow-ssts.onrender.com
echo ================================================================
