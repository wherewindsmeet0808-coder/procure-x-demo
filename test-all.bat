@echo off
setlocal
echo ========================================================
echo Running ProcureSense Verification Suite
echo ========================================================

set "PATH=C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\ssant\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback;%PATH%"

echo.
echo [1/2] Running Backend Pytest Suite...
cd /d "%~dp0backend"
python -m pytest tests/test_direct.py -v
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Backend tests failed!
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Running Frontend TypeScript Typecheck and Build...
cd /d "%~dp0frontend"
pnpm run build
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Frontend build failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo [SUCCESS] All backend tests and frontend builds passed!
echo ========================================================
