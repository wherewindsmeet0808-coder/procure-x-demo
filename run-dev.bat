@echo off
setlocal
echo ========================================================
echo Launching ProcureSense AI Prototype (Backend + Frontend)
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo ========================================================

start "ProcureSense Backend [8000]" cmd /k "%~dp0run-backend.bat"
timeout /t 2 >nul
start "ProcureSense Frontend [5173]" cmd /k "%~dp0run-frontend.bat"

echo.
echo Both servers launched in dedicated windows.
echo Open http://127.0.0.1:5173 in your browser to interact with the prototype.
