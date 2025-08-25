@echo off
echo Launching Server Launcher...

REM Change to the script's directory
pushd "%~dp0"

if exist "dist\server_launcher.exe" (
    start "" "dist\server_launcher.exe"
) else (
    echo Executable not found. Please run the build script first.
)

popd
pause