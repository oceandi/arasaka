@echo off
REM ============================================================================
REM Quick Development Start (HTTP - No SSL needed)
REM Test amaçlı hızlı başlatma
REM ============================================================================

title M.S.P - Development Mode (HTTP)

echo.
echo ============================================================================
echo  🚀 M.S.P Development Server Starting...
echo  Mode: HTTP (No SSL)
echo ============================================================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment aktif
) else (
    echo ❌ Virtual environment bulunamadı!
    echo Önce windows_ssl_setup.bat çalıştırın.
    pause
    exit /b 1
)

REM Set development environment
set FLASK_ENV=development
set FLASK_APP=app.py
set FLASK_DEBUG=1

echo ✅ Development mode aktif
echo.
echo 🌐 HTTP Server başlatılıyor...
echo.
echo ============================================================================
echo  📡 Erişim Bilgileri:
echo  - Local: http://127.0.0.1:5001
echo  - Network: http://85.105.220.36:5000 (port forwarding gerekli)
echo  - Domain: http://maintence.com.tr (DNS ayarları sonrası)
echo ============================================================================
echo.
echo ⚠️  Durdurmak için CTRL+C
echo.

REM Start Flask development server
python app.py

echo.
echo 🛑 Development Server durduruldu.
pause