@echo off
rem Double-click to start the Regulatory Knowledgebase web UI and open it in the browser.
rem Close this window (or press Ctrl+C) to stop the server.
title Regulatory Knowledgebase
cd /d "%~dp0"

set "URL=http://127.0.0.1:8001"
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

rem Already running? Just open the browser.
powershell -NoProfile -Command "try { Invoke-WebRequest '%URL%' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel%==0 (
    start "" "%URL%"
    exit /b 0
)

rem Open the browser as soon as the server answers (gives up after 60 seconds).
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for ($i = 0; $i -lt 60; $i++) { try { Invoke-WebRequest '%URL%' -UseBasicParsing -TimeoutSec 2 | Out-Null; Start-Process '%URL%'; break } catch { Start-Sleep 1 } }"

echo Starting Regulatory Knowledgebase at %URL% ...
echo Close this window to stop the server.
echo.
"%PY%" ui\app.py

rem Keep the window open if the server exits with an error, so the message can be read.
if errorlevel 1 pause
