@echo off
title FinEasy AI - Mock Government API (Port 8001)
echo ========================================================
echo Starting Mock Government Tax Portal API on Port 8001...
echo Interactive Docs: http://127.0.0.1:8001/docs
echo ========================================================

set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
) else if exist "%USERPROFILE%\AppData\Local\Python\bin\python.exe" (
    set "PY_CMD=%USERPROFILE%\AppData\Local\Python\bin\python.exe"
)

"%PY_CMD%" -m uvicorn mock_government.main:app --host 127.0.0.1 --port 8001 --reload
pause
