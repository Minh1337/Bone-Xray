@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
.venv\Scripts\python.exe verify_api.py
set RUN_CODE=%ERRORLEVEL%
pause
exit /b %RUN_CODE%

:missing
echo Copy these files INTO Bone_Xray_Local_Check next to the existing .venv folder.
pause
exit /b 1
