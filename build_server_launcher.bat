@echo off
REM ================================================================================
REM 이 스크립트는 PyInstaller를 사용하여 WoWLauncher.exe를 빌드합니다.
REM
REM 만약 "'pyinstaller'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는
REM 배치 파일이 아닙니다."와 같은 오류가 발생하면, 이는 PyInstaller 실행 파일이
REM 시스템의 PATH 환경 변수에 없기 때문입니다.
REM
REM 이 문제를 해결하려면 pyinstaller.exe가 있는 디렉토리(일반적으로
REM C:\Users\UUUUU\AppData\Roaming\Python\Python313\Scripts)를 시스템의 PATH에
REM 추가해야 합니다.
REM
REM PATH에 추가하는 방법 (Windows):
REM 1. 시작 메뉴를 열고 "환경 변수 편집"을 검색하여 엽니다.
REM 2. "환경 변수" 버튼을 클릭합니다.
REM 3. "시스템 변수" 섹션에서 "Path" 변수를 찾아 선택한 다음 "편집"을 클릭합니다.
REM 4. "새로 만들기"를 클릭하고 다음 경로를 추가합니다:
REM    C:\Users\UUUUU\AppData\Roaming\Python\Python313\Scripts
REM 5. 모든 열려 있는 창에서 "확인"을 클릭하여 변경 사항을 저장합니다.
REM 6. 변경 사항을 적용하려면 열려 있는 모든 명령 프롬프트 또는 PowerShell 창을 다시 시작해야 합니다.
REM ================================================================================

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

