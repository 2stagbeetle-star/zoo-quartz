@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "LOGFILE=%~dp0_drafts\daily_run_log.txt"

echo ======================================================= >> "%LOGFILE%"
echo Zoo Knowledge Vault - Daily automation >> "%LOGFILE%"
echo Start: %date% %time% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

REM Resolve claude command path
where claude >nul 2>&1
if errorlevel 1 (
    set "CLAUDE_CMD="

    REM Windows Store package path (latest version folder)
    for /f "delims=" %%f in ('dir /b /ad /o-n "%USERPROFILE%\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\" 2^>nul') do (
        if not defined CLAUDE_CMD set "CLAUDE_CMD=%USERPROFILE%\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\%%f\claude.exe"
    )

    REM npm global install fallback
    if not defined CLAUDE_CMD (
        if exist "%USERPROFILE%\AppData\Roaming\npm\claude.cmd" (
            set "CLAUDE_CMD=%USERPROFILE%\AppData\Roaming\npm\claude.cmd"
        )
    )

    if not defined CLAUDE_CMD (
        echo [ERROR] claude command not found. >> "%LOGFILE%"
        exit /b 1
    )
) else (
    set "CLAUDE_CMD=claude"
)

echo [INFO] claude command: %CLAUDE_CMD% >> "%LOGFILE%"
echo [INFO] working directory: %cd% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo --- [1/5] Daily topic research --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/daily-topic-researcher" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo --- [2/5] Job listing collection --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/job-listing-collector" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo --- [3/5] Paper collection --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/paper-collector" >> "%LOGFILE%" 2>&1

REM Weekly tasks (Monday only)
for /f %%d in ('powershell -NoProfile -Command "(Get-Date).DayOfWeek"') do set "DOW=%%d"
echo. >> "%LOGFILE%"
if /I "%DOW%"=="Monday" (
    echo --- [4/5] Weekly event collection (Monday) --- >> "%LOGFILE%"
    %CLAUDE_CMD% -p "/weekly-event-collector" >> "%LOGFILE%" 2>&1

    echo. >> "%LOGFILE%"
    echo --- [5/5] Weekly article generation (Monday) --- >> "%LOGFILE%"
    %CLAUDE_CMD% -p "/weekly-article-generator" >> "%LOGFILE%" 2>&1
) else (
    echo [INFO] Weekly tasks skipped (today: %DOW%). >> "%LOGFILE%"
)

echo. >> "%LOGFILE%"
echo End: %date% %time% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo. >> "%LOGFILE%"

exit /b 0
