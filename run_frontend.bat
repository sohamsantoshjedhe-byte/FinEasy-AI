@echo off
title FinEasy AI - Web Frontend (Port 3000)
echo ========================================================
echo Starting FinEasy AI Web Frontend on Port 3000...
echo URL: http://127.0.0.1:3000
echo ========================================================
cd /d "%~dp0"

set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
) else if exist "%USERPROFILE%\AppData\Local\Python\bin\python.exe" (
    set "PY_CMD=%USERPROFILE%\AppData\Local\Python\bin\python.exe"
)

"%PY_CMD%" -m http.server 3000 --directory frontend
pause
