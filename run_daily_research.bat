@echo off
chcp 65001 > nul
cd /d "%~dp0"

set LOGFILE=%~dp0_drafts\実行ログ.txt

echo ======================================================= >> "%LOGFILE%"
echo Zoo Knowledge Vault - 日次自動実行（リサーチ・求人・論文） >> "%LOGFILE%"
echo 実行開始: %date% %time% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

REM claude コマンドのパスを解決（タスクスケジューラ経由では PATH が通らない場合がある）
where claude >nul 2>&1
if %ERRORLEVEL% neq 0 (
    REM Windows Store パッケージ内の最新バージョンを動的に検出
    set CLAUDE_CMD=
    for /f "delims=" %%f in ('dir /b /ad /o-n "%USERPROFILE%\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\" 2^>nul') do (
        if not defined CLAUDE_CMD set CLAUDE_CMD=%USERPROFILE%\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude-code\%%f\claude.exe
    )
    REM npm グローバルインストールのフォールバック
    if not defined CLAUDE_CMD (
        if exist "%USERPROFILE%\AppData\Roaming\npm\claude.cmd" (
            set CLAUDE_CMD=%USERPROFILE%\AppData\Roaming\npm\claude.cmd
        )
    )
    if not defined CLAUDE_CMD (
        echo [ERROR] claude コマンドが見つかりません >> "%LOGFILE%"
        exit /b 1
    )
) else (
    set CLAUDE_CMD=claude
)

echo [INFO] claude コマンド: %CLAUDE_CMD% >> "%LOGFILE%"
echo [INFO] 作業ディレクトリ: %cd% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo --- [1/4] 日次トピックリサーチ --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/daily-topic-researcher" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo --- [2/4] 求人情報収集 --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/job-listing-collector" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo --- [3/4] 学術論文収集 --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/paper-collector" >> "%LOGFILE%" 2>&1

REM 曜日判定: 月曜日なら週次記事生成も実行
for /f %%d in ('powershell -NoProfile -Command "(Get-Date).DayOfWeek"') do set DOW=%%d
echo. >> "%LOGFILE%"
if "%DOW%"=="Monday" (
    echo --- [4/4] 週次記事生成（月曜日のみ自動実行） --- >> "%LOGFILE%"
    %CLAUDE_CMD% -p "/weekly-article-generator" >> "%LOGFILE%" 2>&1
) else (
    echo [INFO] 本日は%DOW%のため週次記事生成をスキップ >> "%LOGFILE%"
)

echo. >> "%LOGFILE%"
echo 終了: %date% %time% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo. >> "%LOGFILE%"
