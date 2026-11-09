@echo off
setlocal
cd /d "%~dp0.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
.venv\Scripts\python.exe -m tools.chatbot_doctor
set "CHECK_EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %CHECK_EXIT_CODE%
:missing
echo Python environment not found. Run scripts\01_setup.bat first.
pause
exit /b 1
