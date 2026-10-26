@echo off
setlocal
echo ========================================================
echo Starting ProcureSense AI Frontend (React + Vite + TS)
echo URL: http://127.0.0.1:5173
echo ========================================================

set "PATH=C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback;%PATH%"
cd /d "%~dp0frontend"
pnpm run dev --host 127.0.0.1
