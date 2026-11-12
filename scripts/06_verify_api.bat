@echo off
setlocal
cd /d "%~dp0.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
.venv\Scripts\python.exe -m bonescope.verify_api
set RUN_CODE=%ERRORLEVEL%
pause
exit /b %RUN_CODE%

:missing
echo Python environment not found in BONESCOPE. Run scripts\01_setup.bat first.
pause
exit /b 1
