@echo off
setlocal
cd /d "%~dp0.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
set NO_ALBUMENTATIONS_UPDATE=1
set HF_HUB_OFFLINE=1
echo Starting local API. Keep this window open. Stop with Ctrl+C.
echo After startup: http://127.0.0.1:8000/docs
.venv\Scripts\python.exe -m uvicorn bonescope.xray_api:app --host 127.0.0.1 --port 8000 --workers 1
set "RUN_CODE=%ERRORLEVEL%"
pause
exit /b %RUN_CODE%

:missing
echo Python environment not found in BONESCOPE. Run scripts\01_setup.bat first.
pause
exit /b 1
