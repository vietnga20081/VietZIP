@echo off
chcp 65001 > nul
echo ========================================================
echo        VietZIP - Script đóng gói Windows (PyInstaller)
echo ========================================================
echo.

echo [1/4] Đang kiểm tra môi trường và cài đặt dependencies...
python -m pip install --upgrade -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [LỖI] Không thể cài đặt các thư viện cần thiết.
    pause
    exit /b 1
)

echo.
echo [2/4] Đang chạy kiểm thử tự động (pytest)...
python -m pytest tests/
if errorlevel 1 (
    echo [CẢNH BÁO] Kiểm thử không đạt, dừng đóng gói.
    pause
    exit /b 1
)

echo.
echo [3/4] Đang đóng gói ứng dụng chính VietZIP...
python -m PyInstaller VietZIP.spec --noconfirm --clean
if errorlevel 1 (
    echo [LỖI] Đóng gói ứng dụng chính thất bại.
    pause
    exit /b 1
)

echo.
echo [4/4] Đang đóng gói bộ cài đặt Setup Wizard (VietZIP_Setup.exe)...
python -c "import shutil; shutil.make_archive('payload', 'zip', 'dist/VietZIP')"
python -m PyInstaller VietZIP_Setup.spec --noconfirm
if errorlevel 1 (
    echo [CẢNH BÁO] Không thể tạo file Setup EXE.
)

:: Xóa file zip tạm
if exist payload.zip del /f /q payload.zip >nul 2>&1

:: Kiểm tra Inno Setup nếu có
where iscc.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [BỔ SUNG] Phát hiện Inno Setup Compiler, đang biên dịch installer.iss...
    iscc.exe installer.iss
)

echo.
echo ========================================================
echo [HOÀN TẤT] Các bản dựng đã được tạo thành công:
echo   1. Ứng dụng độc lập: dist\VietZIP\VietZIP.exe
echo   2. Bộ cài đặt Wizard: dist\VietZIP_Setup.exe
echo ========================================================
echo.
pause
