@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe goto missing
set NO_ALBUMENTATIONS_UPDATE=1
set HF_HUB_OFFLINE=1
echo Starting local API. Keep this window open. Stop with Ctrl+C.
echo After startup: http://127.0.0.1:8000/docs
.venv\Scripts\python.exe -m uvicorn xray_api:app --host 127.0.0.1 --port 8000 --workers 1
pause
exit /b 0

:missing
echo Copy these files INTO Bone_Xray_Local_Check next to the existing .venv folder.
pause
exit /b 1
