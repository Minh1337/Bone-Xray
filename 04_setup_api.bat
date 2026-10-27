@echo off
setlocal
cd /d "%~dp0"
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
echo API setup and tests passed. Run 05_start_api.bat.
pause
exit /b 0
:fail
type logs\api_setup.log
echo Send logs\api_setup.log for help.
pause
exit /b 1

:missing
echo Copy these files INTO Bone_Xray_Local_Check next to the existing .venv folder.
pause
exit /b 1
