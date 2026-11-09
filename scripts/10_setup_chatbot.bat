@echo off
setlocal
cd /d "%~dp0.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
if not exist logs mkdir logs
echo Installing chatbot dependencies. Details: logs\chatbot_setup.log
.venv\Scripts\python.exe -m pip install -r requirements_api.txt -r requirements_rag.txt > logs\chatbot_setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip check >> logs\chatbot_setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m tools.chatbot_doctor
if errorlevel 1 goto configuration
echo Chatbot dependencies are installed. Run scripts\08_start_chatbot.bat.
pause
exit /b 0
:configuration
echo Packages installed. Resolve the configuration or asset warning above, then run scripts\09_check_chatbot.bat.
pause
exit /b 1
:fail
type logs\chatbot_setup.log
echo Installation failed. Review logs\chatbot_setup.log.
pause
exit /b 1
:missing
echo Python environment not found. Run scripts\01_setup.bat first.
pause
exit /b 1
