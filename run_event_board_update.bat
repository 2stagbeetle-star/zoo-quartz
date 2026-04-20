@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python command not found.
    exit /b 1
)

python automation\update-event-board.py %*
exit /b %ERRORLEVEL%
