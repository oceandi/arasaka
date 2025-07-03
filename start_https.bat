@echo off
REM ============================================================================
REM Quick HTTPS Start for maintencesp.com.tr
REM Bu dosyayı SSL sertifikası kurduktan sonra kullanın
REM ============================================================================

title M.S.P - Maintenance Solution Partner (HTTPS)

echo.
echo ============================================================================
echo  🚀 M.S.P HTTPS Server Starting...
echo  Domain: maintencesp.com.tr
echo ============================================================================
echo.

REM Check Admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Administrator olarak çalıştırın!
    pause
    exit /b 1
)

REM Check SSL certificates - DÜZELTILDI!
if not exist "C:\ssl\maintencesp.com.tr\fullchain.pem" (
    echo ❌ SSL sertifikası bulunamadı!
    echo Beklenen: C:\ssl\maintencesp.com.tr\fullchain.pem
    pause
    exit /b 1
)

if not exist "C:\ssl\maintencesp.com.tr\privkey.pem" (
    echo ❌ SSL private key bulunamadı!
    echo Beklenen: C:\ssl\maintencesp.com.tr\privkey.pem
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set production environment - DÜZELTILDI!
set FLASK_ENV=production
set FLASK_APP=app.py
set SSL_CERT_PATH=C:\ssl\maintencesp.com.tr\fullchain.pem
set SSL_KEY_PATH=C:\ssl\maintencesp.com.tr\privkey.pem
set PORT=443
set HOST=0.0.0.0

echo ✅ SSL sertifikaları bulundu
echo ✅ Virtual environment aktif
echo ✅ Production mode aktif
echo.
echo 🌐 HTTPS Server başlatılıyor...
echo.
echo ============================================================================
echo  📡 Erişim Bilgileri:
echo  - HTTPS: https://maintencesp.com.tr
echo  - IP: https://85.105.220.36
echo  - Port: 443 (HTTPS)
echo ============================================================================
echo.
echo ⚠️  Durdurmak için CTRL+C
echo.

REM Create logs directory if not exists
if not exist "logs" mkdir "logs"

REM Start with Gunicorn
gunicorn --bind 0.0.0.0:443 ^
         --workers 2 ^
         --worker-class sync ^
         --timeout 30 ^
         --keep-alive 2 ^
         --max-requests 1000 ^
         --certfile="%SSL_CERT_PATH%" ^
         --keyfile="%SSL_KEY_PATH%" ^
         --ssl-version TLSv1_2 ^
         --access-logfile logs\access.log ^
         --error-logfile logs\error.log ^
         --log-level info ^
         app:app

echo.
echo 🛑 HTTPS Server durduruldu.
pause