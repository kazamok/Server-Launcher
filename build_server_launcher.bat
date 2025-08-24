@echo off
echo Building Server Launcher...

REM Change to the script's directory
pushd "%~dp0"

echo Installing dependencies...
pip install customtkinter psutil CTkMessagebox pyinstaller
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
REM if exist "server_launcher.spec" del "server_launcher.spec"


echo.
echo Running PyInstaller to build the executable...
pyinstaller server_launcher.py --onefile --windowed > build.log 2>&1

REM Check if build was successful
if exist "dist\server_launcher.exe" (
    echo.
    echo Build successful! Executable is in dist\server_launcher.exe
) else (
    echo.
    echo Build failed! Check the output above for errors.
)

popd
pause
