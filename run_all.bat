@echo off
title FinEasy AI - Complete Ecosystem Launcher
echo ========================================================
echo Launching FinEasy AI Full Stack (Backend + Gov + UI)...
echo ========================================================
cd /d "%~dp0"

echo 1. Starting Mock Government API on Port 8001...
start "FinEasy AI - Mock Government (8001)" cmd /c "run_mock_gov.bat"
timeout /t 2 /nobreak >nul

echo 2. Starting FastAPI Main Backend on Port 8000...
start "FinEasy AI - Main Backend (8000)" cmd /c "run_backend.bat"
timeout /t 2 /nobreak >nul

echo 3. Starting Web Frontend on Port 3000...
start "FinEasy AI - Web Frontend (3000)" cmd /c "run_frontend.bat"
timeout /t 2 /nobreak >nul

echo ========================================================
echo FinEasy AI is fully launched!
echo - Web Frontend:     http://127.0.0.1:3000
echo - Backend Docs:     http://127.0.0.1:8000/docs
echo - Mock Gov Docs:    http://127.0.0.1:8001/docs
echo ========================================================
start http://127.0.0.1:3000
