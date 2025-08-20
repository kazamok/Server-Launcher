@echo off
echo Installing/Updating required packages...
pip install -r "C:\WISE\Server-Launcher\requirements.txt" --upgrade
echo.

echo Launching Server Launcher...
start /b python C:\WISE\Server-Launcher\server_launcher.py
pause
