@echo off
title Intelligent Logistics & Delivery Optimization Platform (ILDO)
echo ==============================================================
echo Starting Intelligent Logistics & Delivery Optimization Platform
echo ==============================================================

cd /d "%~dp0"

echo [1/2] Starting Backend API (FastAPI) on http://127.0.0.1:8000 ...
start "ILDO Backend - FastAPI" cmd /k "python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"

echo [2/2] Starting Frontend UI (React + Vite) on http://localhost:5173 ...
start "ILDO Frontend - Vite" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo.
echo ==============================================================
echo All services have been launched in separate console windows!
echo - Frontend:    http://localhost:5173
echo - Backend API: http://127.0.0.1:8000/docs
echo ==============================================================
timeout /t 3 >nul
start http://localhost:5173

