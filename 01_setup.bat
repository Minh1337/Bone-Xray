@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
py -3.11 -c "import sys,struct; assert struct.calcsize('P') == 8" > logs\setup.log 2>&1
if errorlevel 1 goto python_missing
if not exist .venv\Scripts\python.exe py -3.11 -m venv .venv >> logs\setup.log 2>&1
if errorlevel 1 goto fail
echo Installing packages. Please wait; details are in logs\setup.log.
.venv\Scripts\python.exe -m pip install --upgrade pip >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124 >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip check >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip freeze > logs\installed_versions.txt
.venv\Scripts\python.exe -m unittest discover -s tests >> logs\setup.log 2>&1
if errorlevel 1 goto fail
echo Setup complete. Add best_model.pt and fill cases.json before running 02_run_check.bat.
pause
exit /b 0
:python_missing
echo Install Python 3.11 64-bit with Python Launcher. See README_VI.md.
pause
exit /b 1
:fail
echo Setup failed. Send logs\setup.log for troubleshooting.
pause
exit /b 1
