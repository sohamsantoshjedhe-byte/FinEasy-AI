@echo off
title FinEasy AI - Main Backend (Port 8000)
echo ========================================================
echo Starting FinEasy AI FastAPI Backend on Port 8000...
echo Interactive Swagger Docs: http://127.0.0.1:8000/docs
echo ========================================================

set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
) else if exist "%USERPROFILE%\AppData\Local\Python\bin\python.exe" (
    set "PY_CMD=%USERPROFILE%\AppData\Local\Python\bin\python.exe"
)

"%PY_CMD%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
