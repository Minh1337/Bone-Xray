@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set NO_ALBUMENTATIONS_UPDATE=1
set HF_HUB_OFFLINE=1
if not exist .venv\Scripts\python.exe goto missing
if not exist xray_api.py goto missing
.venv\Scripts\python.exe -m unittest discover -s ui_tests -v
if errorlevel 1 goto failed
echo Stop the old API window with Ctrl+C before starting this server.
echo After Application startup complete, open http://127.0.0.1:8000/
echo Keep this window open. Stop with Ctrl+C.
.venv\Scripts\python.exe -m uvicorn xray_ui:app --host 127.0.0.1 --port 8000 --workers 1
pause
exit /b 0
:missing
echo Copy the UI addon into Bone_Xray_Local_Check, next to .venv and xray_api.py.
pause
exit /b 1
:failed
echo UI route tests failed. Send this console output for help.
pause
exit /b 1
