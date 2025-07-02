@echo off
REM ============================================================================
REM Windows HTTPS Production Setup for maintence.com.tr
REM M.S.P - Maintenance Solution Partner
REM ============================================================================

echo.
echo ============================================================================
echo  🚀 M.S.P HTTPS Production Setup for Windows Server
echo  Domain: maintence.com.tr
echo  IP: 85.105.220.36
echo ============================================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Bu script Administrator olarak çalıştırılmalı!
    echo Sağ tık yapıp "Administrator olarak çalıştır" seçin.
    pause
    exit /b 1
)

echo ✅ Administrator yetkisi doğrulandı.
echo.

REM Create SSL directory
echo 📁 SSL klasörü oluşturuluyor...
if not exist "C:\ssl" mkdir "C:\ssl"
if not exist "C:\ssl\maintence.com.tr" mkdir "C:\ssl\maintence.com.tr"
echo ✅ SSL klasörleri oluşturuldu: C:\ssl\maintence.com.tr\
echo.

REM Check if Python is installed
echo 🐍 Python kontrolü...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python bulunamadı! Python 3.12+ yükleyin.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python bulundu.

REM Check if we're in the correct directory
if not exist "app.py" (
    echo ❌ Yanlış klasör! Bu scripti arasaka klasöründe çalıştırın.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Virtual environment aktifleştiriliyor...
if not exist "venv" (
    echo ⚠️  Virtual environment bulunamadı, oluşturuluyor...
    python -m venv venv
)

call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo ❌ Virtual environment aktifleştirilemedi!
    pause
    exit /b 1
)
echo ✅ Virtual environment aktif.

REM Install/upgrade required packages
echo 📦 Gerekli paketler yükleniyor...
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-migrate flask-login
pip install pandas openpyxl simplekml xlsxwriter
pip install gunicorn
pip install requests
echo ✅ Tüm paketler yüklendi.

REM Initialize database if needed
echo 🗄️  Database kontrolü...
if not exist "fiberariza.db" (
    echo ⚠️  Database bulunamadı, oluşturuluyor...
    python init_users.py
    echo ✅ Database ve kullanıcılar oluşturuldu.
) else (
    echo ✅ Database mevcut.
)

REM Firewall rules
echo 🔥 Windows Firewall kuralları ekleniyor...
netsh advfirewall firewall add rule name="Flask HTTPS" dir=in action=allow protocol=TCP localport=443 >nul 2>&1
netsh advfirewall firewall add rule name="Flask HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
netsh advfirewall firewall add rule name="Flask Dev" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
echo ✅ Firewall kuralları eklendi (port 80, 443, 5000).

echo.
echo ============================================================================
echo  SSL Sertifikası Kurulumu
echo ============================================================================
echo.

echo SSL sertifikası için 3 seçeneğiniz var:
echo.
echo 1. 🔧 Win-ACME (Let's Encrypt için Windows) - ÖNERİLEN
echo 2. 📄 Mevcut sertifikayı kullan (zaten varsa)
echo 3. 🚀 Geliştirme modunda başlat (HTTP, SSL yok)
echo.
set /p ssl_choice=Seçiminizi yapın (1/2/3): 

if "%ssl_choice%"=="1" goto :win_acme
if "%ssl_choice%"=="2" goto :existing_cert
if "%ssl_choice%"=="3" goto :dev_mode

echo ❌ Geçersiz seçim!
pause
exit /b 1

:win_acme
echo.
echo 📋 Win-ACME (Let's Encrypt) Kurulumu:
echo.
echo 1. https://www.win-acme.com/ adresinden Win-ACME indirin
echo 2. wacs.exe yi Administrator olarak çalıştırın
echo 3. "N" (Create certificate) seçin
echo 4. "1" (Single binding of an IIS site) veya "4" (Manually input host names) seçin
echo 5. Domain: maintence.com.tr
echo 6. Sertifika C:\ssl\maintence.com.tr\ klasörüne kopyalanacak
echo.
echo Win-ACME kurulumu tamamlandıktan sonra bu scripti tekrar çalıştırın.
echo.
pause
exit /b 0

:existing_cert
echo.
echo 📄 Mevcut Sertifika Kontrolü:
if exist "C:\ssl\maintence.com.tr\fullchain.pem" (
    if exist "C:\ssl\maintence.com.tr\privkey.pem" (
        echo ✅ SSL sertifikaları bulundu!
        goto :start_production
    )
)
echo ❌ SSL sertifikaları bulunamadı!
echo Sertifika dosyalarını şu konuma kopyalayın:
echo   C:\ssl\maintence.com.tr\fullchain.pem
echo   C:\ssl\maintence.com.tr\privkey.pem
echo.
pause
exit /b 1

:dev_mode
echo.
echo 🚀 Geliştirme modunda başlatılıyor (HTTP - Port 5000)...
echo.

REM Set environment variables for development
set FLASK_ENV=development
set FLASK_APP=app.py

echo ⚡ Flask uygulaması başlatılıyor...
echo.
echo ============================================================================
echo  🌐 Uygulama Erişim Bilgileri:
echo  - Local: http://127.0.0.1:5001
echo  - Network: http://85.105.220.36:5000
echo  - Domain: http://maintence.com.tr (DNS ayarları sonrası)
echo ============================================================================
echo.
echo ⚠️  CTRL+C ile durdurmak için
echo.

python app.py
goto :end

:start_production
echo.
echo 🚀 Production modunda başlatılıyor (HTTPS - Port 443)...
echo.

REM Set environment variables
set FLASK_ENV=production
set FLASK_APP=app.py
set SSL_CERT_PATH=C:\ssl\maintence.com.tr\fullchain.pem
set SSL_KEY_PATH=C:\ssl\maintence.com.tr\privkey.pem
set PORT=443
set HOST=0.0.0.0

echo ⚡ Gunicorn ile başlatılıyor...
echo.
echo ============================================================================
echo  🌐 HTTPS Uygulama Erişim Bilgileri:
echo  - HTTPS: https://maintence.com.tr
echo  - IP: https://85.105.220.36
echo  - SSL: Let's Encrypt (Otomatik yenileme)
echo ============================================================================
echo.
echo ⚠️  CTRL+C ile durdurmak için
echo.

gunicorn --bind 0.0.0.0:443 --workers 2 --worker-class sync --timeout 30 --keep-alive 2 --certfile="%SSL_CERT_PATH%" --keyfile="%SSL_KEY_PATH%" --ssl-version TLSv1_2 app:app

:end
echo.
echo 🎉 M.S.P uygulaması durduruldu.
pause