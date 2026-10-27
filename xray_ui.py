"""Serve the local UI alongside the already validated API."""
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from xray_api import app
from case_api import router as case_router
import database as db

# Initialise database on startup
db.init_db()

# Register case management routes
app.include_router(case_router)

WEB = Path(__file__).resolve().parent / 'xray_web'
app.mount('/ui-assets', StaticFiles(directory=WEB), name='xray-ui-assets')

@app.get('/', include_in_schema=False)
def index():
    return FileResponse(WEB / 'index.html', headers={'Cache-Control': 'no-store'})

@app.get('/history', include_in_schema=False)
def history_page():
    return FileResponse(WEB / 'history.html', headers={'Cache-Control': 'no-store'})

@app.get('/dashboard', include_in_schema=False)
def dashboard_page():
    return FileResponse(WEB / 'dashboard.html', headers={'Cache-Control': 'no-store'})

@app.get('/case/{case_id}', include_in_schema=False)
def case_detail_page(case_id: str):
    return FileResponse(WEB / 'case_detail.html', headers={'Cache-Control': 'no-store'})
