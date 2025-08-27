@echo off

echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in the PATH. Opening Python download page...
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

echo Launching Server Launcher...
start /b python C:\WISE\Server-Launcher\server_launcher.py
pause
