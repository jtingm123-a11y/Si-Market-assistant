@echo off
setlocal
cd /d "%~dp0"

if not exist "runtime\python.exe" (
    echo Portable Python runtime is missing. Re-download and extract the complete ZIP package.
    pause
    exit /b 1
)

echo Starting A-Share Research Assistant...
"runtime\python.exe" -m streamlit run "%~dp0app.py" --server.address 127.0.0.1 --server.headless false
if errorlevel 1 (
    echo.
    echo The application stopped with an error. Copy the message above when asking for help.
    pause
)
