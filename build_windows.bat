@echo off
setlocal EnableExtensions

title VietZIP - Windows Build

echo ========================================================
echo          VietZIP - Windows Build Script
echo ========================================================
echo.

echo [1/4] Checking environment and installing dependencies...
python -m pip install --upgrade -r requirements.txt pyinstaller

if errorlevel 1 (
    echo [ERROR] Failed to install required dependencies.
    pause
    exit /b 1
)

echo.
echo [2/4] Running automated tests...
python -m pytest tests/

if errorlevel 1 (
    echo [ERROR] Tests failed. Build cancelled.
    pause
    exit /b 1
)

echo.
echo [3/4] Building VietZIP application...
python -m PyInstaller VietZIP.spec --noconfirm --clean

if errorlevel 1 (
    echo [ERROR] VietZIP application build failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Building VietZIP Setup Wizard...
python -c "import shutil; shutil.make_archive('payload', 'zip', 'dist/VietZIP')"

python -m PyInstaller VietZIP_Setup.spec --noconfirm

if errorlevel 1 (
    echo [WARNING] Setup Wizard build failed.
)

if exist payload.zip (
    del /f /q payload.zip >nul 2>&1
)

where iscc.exe >nul 2>&1

if not errorlevel 1 (
    echo.
    echo [EXTRA] Inno Setup detected.
    echo Building installer.iss...
    iscc.exe installer.iss

    if errorlevel 1 (
        echo [WARNING] Inno Setup compilation failed.
    )
)

echo.
echo ========================================================
echo [DONE] Build completed.
echo.
echo   1. Portable application:
echo      dist\VietZIP\VietZIP.exe
echo.
echo   2. Setup Wizard:
echo      dist\VietZIP_Setup.exe
echo ========================================================
echo.

pause
endlocal
