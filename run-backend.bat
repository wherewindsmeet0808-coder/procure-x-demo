@echo off
setlocal
echo ========================================================
echo Starting ProcureSense AI Backend (FastAPI + SQLite)
echo URL: http://127.0.0.1:8000
echo OpenAPI Docs: http://127.0.0.1:8000/docs
echo ========================================================

set "PATH=C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts;%PATH%"
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
