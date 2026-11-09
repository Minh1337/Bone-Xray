@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set NO_ALBUMENTATIONS_UPDATE=1
set HF_HUB_OFFLINE=1
if not exist .venv\Scripts\python.exe goto missing
if not exist rag\demo_api.py goto missing
echo Starting BoneScope Research Studio (Educational X-ray + 22 Metadata + RAG Chatbot)...
echo Open http://127.0.0.1:8765/ in your browser after startup completes.
echo Keep this window open. Stop with Ctrl+C.
.venv\Scripts\python.exe -m tools.run_chatbot --port 8765
set "CHATBOT_EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %CHATBOT_EXIT_CODE%
:missing
echo Virtual environment (.venv) or rag\demo_api.py not found. Run 01_setup.bat and 04_setup_api.bat first.
pause
exit /b 1
