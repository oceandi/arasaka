@echo off
chcp 65001 >nul
REM ============================================================================
REM Windows HTTPS Production Setup for maintence.com.tr
REM M.S.P - Maintenance Solution Partner
REM ============================================================================

REM Change to script directory
cd /d "%~dp0"

echo.
echo ============================================================================
echo   M.S.P HTTPS Production Setup for Windows Server
echo   Domain: maintence.com.tr
echo   IP: 85.105.220.36
echo ============================================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Bu script Administrator olarak calistirilmali!
    echo Sag tik yapip "Administrator olarak calistir" secin.
    pause
    exit /b 1
)

echo [OK] Administrator yetkisi dogrulandi.
echo.

REM Create SSL directory
echo [INFO] SSL klasoru olusturuluyor...
if not exist "C:\ssl" mkdir "C:\ssl"
if not exist "C:\ssl\maintence.com.tr" mkdir "C:\ssl\maintence.com.tr"
echo [OK] SSL klasorleri olusturuldu: C:\ssl\maintence.com.tr\
echo.

REM Show current directory
echo [INFO] Mevcut klasor: %CD%
echo [INFO] Bu klasordeki dosyalar:
dir /b *.py 2>nul
echo.

REM Check if Python is installed
echo [INFO] Python kontrolu...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python bulunamadi! Python 3.12+ yukleyin.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python bulundu.

REM Check if we're in the correct directory
if not exist "app.py" (
    echo [ERROR] app.py bulunamadi!
    echo [INFO] Bu scripti proje klasorunde calistirin.
    echo [INFO] Proje klasorunde su dosyalar olmali: app.py, init_users.py
    echo.
    echo Devam etmek icin proje klasorune gidin ve scripti tekrar calistirin.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Virtual environment aktifleştiriliyor...
if not exist "venv" (
    echo [WARN] Virtual environment bulunamadi, olusturuluyor...
    python -m venv venv
)

call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [ERROR] Virtual environment aktiflestirilemedi!
    pause
    exit /b 1
)
echo [OK] Virtual environment aktif.

REM Install/upgrade required packages
echo [INFO] Gerekli paketler yukleniyor...
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-migrate flask-login
pip install pandas openpyxl simplekml xlsxwriter
pip install gunicorn
pip install requests
echo [OK] Tum paketler yuklendi.

REM Initialize database if needed
echo [INFO] Database kontrolu...
if not exist "fiberariza.db" (
    echo [WARN] Database bulunamadi, olusturuluyor...
    python init_users.py
    echo [OK] Database ve kullanicilar olusturuldu.
) else (
    echo [OK] Database mevcut.
)

REM Firewall rules
echo [INFO] Windows Firewall kurallari ekleniyor...
netsh advfirewall firewall add rule name="Flask HTTPS" dir=in action=allow protocol=TCP localport=443 >nul 2>&1
netsh advfirewall firewall add rule name="Flask HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
netsh advfirewall firewall add rule name="Flask Dev" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
echo [OK] Firewall kurallari eklendi (port 80, 443, 5000).

echo.
echo ============================================================================
echo  SSL Sertifikası Kurulumu
echo ============================================================================
echo.

echo SSL sertifikasi icin 3 seceneginiz var:
echo.
echo 1. [TOOL] Win-ACME (Let's Encrypt icin Windows) - ONERILEN
echo 2. [FILE] Mevcut sertifikayi kullan (zaten varsa)
echo 3. [DEV] Gelistirme modunda baslat (HTTP, SSL yok)
echo.
set /p ssl_choice=Seciminizi yapin (1/2/3): 

if "%ssl_choice%"=="1" goto :win_acme
if "%ssl_choice%"=="2" goto :existing_cert
if "%ssl_choice%"=="3" goto :dev_mode

echo [ERROR] Gecersiz secim!
pause
exit /b 1

:win_acme
echo.
echo [INFO] Win-ACME (Let's Encrypt) Kurulumu:
echo.
echo 1. https://www.win-acme.com/ adresinden Win-ACME indirin
echo 2. wacs.exe yi Administrator olarak calistirin
echo 3. "N" (Create certificate) secin
echo 4. "1" (Single binding of an IIS site) veya "4" (Manually input host names) secin
echo 5. Domain: maintence.com.tr
echo 6. Sertifika C:\ssl\maintence.com.tr\ klasorune kopyalanacak
echo.
echo Win-ACME kurulumu tamamlandiktan sonra bu scripti tekrar calistirin.
echo.
pause
exit /b 0

:existing_cert
echo.
echo [INFO] Mevcut Sertifika Kontrolu:
if exist "C:\ssl\maintence.com.tr\fullchain.pem" (
    if exist "C:\ssl\maintence.com.tr\privkey.pem" (
        echo [OK] SSL sertifikalari bulundu!
        goto :start_production
    )
)
echo [ERROR] SSL sertifikalari bulunamadi!
echo Sertifika dosyalarini su konuma kopyalayin:
echo   C:\ssl\maintence.com.tr\fullchain.pem
echo   C:\ssl\maintence.com.tr\privkey.pem
echo.
pause
exit /b 1

:dev_mode
echo.
echo [DEV] Gelistirme modunda baslatiliyor (HTTP - Port 5000)...
echo.

REM Set environment variables for development
set FLASK_ENV=development
set FLASK_APP=app.py

echo [INFO] Flask uygulamasi baslatiliyor...
echo.
echo ============================================================================
echo  [WEB] Uygulama Erisim Bilgileri:
echo  - Local: http://127.0.0.1:5001
echo  - Network: http://85.105.220.36:5000
echo  - Domain: http://maintence.com.tr (DNS ayarlari sonrasi)
echo ============================================================================
echo.
echo [WARN] CTRL+C ile durdurmak icin
echo.

python app.py
goto :end

:start_production
echo.
echo [PROD] Production modunda baslatiliyor (HTTPS - Port 443)...
echo.

REM Set environment variables
set FLASK_ENV=production
set FLASK_APP=app.py
set SSL_CERT_PATH=C:\ssl\maintence.com.tr\fullchain.pem
set SSL_KEY_PATH=C:\ssl\maintence.com.tr\privkey.pem
set PORT=443
set HOST=0.0.0.0

echo [INFO] Gunicorn ile baslatiliyor...
echo.
echo ============================================================================
echo  [HTTPS] HTTPS Uygulama Erisim Bilgileri:
echo  - HTTPS: https://maintence.com.tr
echo  - IP: https://85.105.220.36
echo  - SSL: Let's Encrypt (Otomatik yenileme)
echo ============================================================================
echo.
echo [WARN] CTRL+C ile durdurmak icin
echo.

gunicorn --bind 0.0.0.0:443 --workers 2 --worker-class sync --timeout 30 --keep-alive 2 --certfile="%SSL_CERT_PATH%" --keyfile="%SSL_KEY_PATH%" --ssl-version TLSv1_2 app:app

:end
echo.
echo [INFO] M.S.P uygulamasi durduruldu.
pause