@echo off
setlocal
cd /d "%~dp0.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
if not exist logs mkdir logs
.venv\Scripts\python.exe -m pip freeze > logs\before_api_install.txt
echo Installing API packages. Details: logs\api_setup.log
.venv\Scripts\python.exe -m pip install -r requirements_api.txt > logs\api_setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip check >> logs\api_setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m unittest discover -s api_tests -v >> logs\api_setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip freeze > logs\after_api_install.txt
echo API setup and tests passed. Run scripts\05_start_api.bat.
pause
exit /b 0
:fail
type logs\api_setup.log
echo Send logs\api_setup.log for help.
pause
exit /b 1

:missing
echo Virtual environment not found in BONESCOPE. Run scripts\01_setup.bat first.
pause
exit /b 1
