@echo off
chcp 65001 >nul
REM ============================================================================
REM Windows HTTPS Production Setup for maintence.com.tr
REM M.S.P - Maintenance Solution Partner
REM ============================================================================

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

REM Show current directory and files
echo [INFO] Mevcut klasor: %CD%
echo [INFO] Bu klasordeki Python dosyalari:
dir /b *.py 2>nul
echo.

REM Check if we're in the correct directory FIRST
if not exist "app.py" (
    echo [ERROR] app.py bulunamadi!
    echo [INFO] Bu scripti proje klasorunde calistirin.
    echo [INFO] Proje klasorunde su dosyalar olmali: app.py, init_users.py
    echo.
    echo Cozum:
    echo 1. Proje klasorune gidin (app.py dosyasinin oldugu klasor)
    echo 2. Bu scripti o klasorde calistirin
    echo.
    pause
    exit /b 1
)

echo [OK] Proje dosyalari bulundu.
echo.

REM Create SSL directory
echo [INFO] SSL klasoru olusturuluyor...
if not exist "C:\ssl" mkdir "C:\ssl"
if not exist "C:\ssl\maintence.com.tr" mkdir "C:\ssl\maintence.com.tr"
echo [OK] SSL klasorleri olusturuldu: C:\ssl\maintence.com.tr\
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

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python bulundu: %PYTHON_VERSION%
echo.

REM Activate virtual environment
echo [INFO] Virtual environment kontrol ediliyor...
if not exist "venv" (
    echo [INFO] Virtual environment bulunamadi, olusturuluyor...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo [ERROR] Virtual environment olusturulamadi!
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [ERROR] Virtual environment aktiflestirilemiyor!
    echo [INFO] venv\Scripts\activate.bat dosyasi var mi kontrol edin.
    pause
    exit /b 1
)
echo [OK] Virtual environment aktif.
echo.

REM Install/upgrade required packages
echo [INFO] Gerekli paketler yukleniyor...
echo [INFO] Bu islem birkaç dakika surebilir...
pip install --upgrade pip --quiet
pip install flask flask-sqlalchemy flask-migrate flask-login --quiet
pip install pandas openpyxl simplekml xlsxwriter --quiet
pip install gunicorn --quiet
pip install requests --quiet
echo [OK] Tum paketler yuklendi.
echo.

REM Initialize database if needed
echo [INFO] Database kontrolu...
if not exist "fiberariza.db" (
    if not exist "instance\fiberariza.db" (
        echo [INFO] Database bulunamadi, olusturuluyor...
        python init_users.py
        if %errorLevel% neq 0 (
            echo [WARNING] init_users.py calistirilmadi, manuel olarak calistirin.
        ) else (
            echo [OK] Database ve kullanicilar olusturuldu.
        )
    ) else (
        echo [OK] Database mevcut (instance\fiberariza.db).
    )
) else (
    echo [OK] Database mevcut (fiberariza.db).
)
echo.

REM Firewall rules
echo [INFO] Windows Firewall kurallari ekleniyor...
netsh advfirewall firewall add rule name="MSP Flask HTTPS" dir=in action=allow protocol=TCP localport=443 >nul 2>&1
netsh advfirewall firewall add rule name="MSP Flask HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
netsh advfirewall firewall add rule name="MSP Flask Dev" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
netsh advfirewall firewall add rule name="MSP Flask Dev2" dir=in action=allow protocol=TCP localport=5001 >nul 2>&1
echo [OK] Firewall kurallari eklendi (port 80, 443, 5000, 5001).
echo.

echo ============================================================================
echo  SSL Sertifikasi Kurulumu
echo ============================================================================
echo.

echo SSL sertifikasi icin 3 seceneginiz var:
echo.
echo 1. Win-ACME (Let's Encrypt icin Windows) - ONERILEN
echo 2. Mevcut sertifikayi kullan (zaten varsa)
echo 3. Gelistirme modunda baslat (HTTP, SSL yok)
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
echo Adimlar:
echo 1. https://www.win-acme.com/ adresinden Win-ACME indirin
echo 2. wacs.exe yi Administrator olarak calistirin
echo 3. "N" (Create certificate) secin
echo 4. "4" (Manually input host names) secin
echo 5. Domain: maintence.com.tr
echo 6. Sertifika C:\ssl\maintence.com.tr\ klasorune kopyalanacak
echo.
echo Win-ACME kurulumu tamamlandiktan sonra start_https.bat calistirin.
echo.
pause
goto :end

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
goto :end

:dev_mode
echo.
echo [INFO] Gelistirme modunda baslatiliyor (HTTP - Port 5001)...
echo.

REM Set environment variables for development
set FLASK_ENV=development
set FLASK_APP=app.py

echo [INFO] Flask uygulamasi baslatiliyor...
echo.
echo ============================================================================
echo  Uygulama Erisim Bilgileri:
echo  - Local: http://127.0.0.1:5001
echo  - Network: http://85.105.220.36:5001 (port forwarding gerekli)
echo  - Domain: http://maintence.com.tr (DNS ayarlari sonrasi)
echo ============================================================================
echo.
echo [INFO] Durdurmak icin CTRL+C
echo.

python app.py
goto :end

:start_production
echo.
echo [INFO] Production modunda baslatiliyor (HTTPS - Port 443)...
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
echo  HTTPS Uygulama Erisim Bilgileri:
echo  - HTTPS: https://maintence.com.tr
echo  - IP: https://85.105.220.36
echo  - SSL: Let's Encrypt (Otomatik yenileme)
echo ============================================================================
echo.
echo [INFO] Durdurmak icin CTRL+C
echo.

gunicorn --bind 0.0.0.0:443 --workers 2 --worker-class sync --timeout 30 --keep-alive 2 --certfile="%SSL_CERT_PATH%" --keyfile="%SSL_KEY_PATH%" --ssl-version TLSv1_2 app:app

:end
echo.
echo [INFO] M.S.P uygulamasi durduruldu.
echo.
echo Diger scriptler:
echo - start_https.bat  : HTTPS production mode
echo - start_dev.bat    : HTTP development mode  
echo - install_winacme.bat : SSL sertifika kurulumu
echo.
pause