@echo off
setlocal
cd /d "%~dp0.."
set PYTHONUTF8=1
set NO_ALBUMENTATIONS_UPDATE=1
set HF_HUB_OFFLINE=1
if not exist .venv\Scripts\python.exe goto missing
if not exist bonescope\xray_api.py goto missing
if not exist bonescope\xray_ui.py goto missing
.venv\Scripts\python.exe -m unittest discover -s ui_tests -p "test_ui_routes.py" -v
if errorlevel 1 goto failed
echo Stop the old API window with Ctrl+C before starting this server.
echo After Application startup complete, open http://127.0.0.1:8000/
echo Keep this window open. Stop with Ctrl+C.
.venv\Scripts\python.exe -m uvicorn bonescope.xray_ui:app --host 127.0.0.1 --port 8000 --workers 1
set "RUN_CODE=%ERRORLEVEL%"
pause
exit /b %RUN_CODE%
:missing
echo BoneScope environment or application package is missing. Run scripts\01_setup.bat first.
pause
exit /b 1
:failed
echo UI route tests failed. Send this console output for help.
pause
exit /b 1
