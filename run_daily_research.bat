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
    set CLAUDE_CMD=%USERPROFILE%\AppData\Roaming\npm\claude.cmd
) else (
    set CLAUDE_CMD=claude
)

echo [INFO] claude コマンド: %CLAUDE_CMD% >> "%LOGFILE%"
echo [INFO] 作業ディレクトリ: %cd% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo --- [1/3] 日次トピックリサーチ --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/daily-topic-researcher" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo --- [2/3] 求人情報収集 --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/job-listing-collector" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo --- [3/3] 学術論文収集 --- >> "%LOGFILE%"
%CLAUDE_CMD% -p "/paper-collector" >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo 終了: %date% %time% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo. >> "%LOGFILE%"
