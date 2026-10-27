@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set NO_ALBUMENTATIONS_UPDATE=1
set HF_HUB_OFFLINE=1
if not exist .venv\Scripts\python.exe goto missing
if not exist logs mkdir logs
.venv\Scripts\python.exe check_model.py --device auto > logs\last_run_console.txt 2>&1
set RUN_CODE=%ERRORLEVEL%
type logs\last_run_console.txt
pause
exit /b %RUN_CODE%
:missing
echo Run 01_setup.bat first.
pause
exit /b 1
