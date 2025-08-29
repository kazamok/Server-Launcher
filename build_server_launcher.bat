@echo off
echo Building Server Launcher...

REM Change to the script's directory
pushd "%~dp0"

echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in the PATH. Opening Python download page...
    start "" "https://www.python.org/downloads/"
    popd
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Aborting.
    popd
    pause
    exit /b %errorlevel%
)

echo.
echo Cleaning up previous build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo Running PyInstaller to build the executable...
python -m PyInstaller server_launcher.py --onefile --windowed > build.log 2>&1

REM Check if build was successful
if exist "dist\server_launcher.exe" (
    echo.
    echo Build successful! Executable is in dist\server_launcher.exe
    echo.
    echo Copying config file to dist folder...
    copy "server_config.json" "dist\server_config.json"
) else (
    echo.
    echo Build failed! Check the output above for errors.
)

popd
pause


