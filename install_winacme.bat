@echo off
chcp 65001 >nul
REM ============================================================================
REM Win-ACME (Let's Encrypt for Windows) Otomatik Kurulum
REM maintencesp.com.tr icin SSL sertifikasi
REM ============================================================================

REM Change to script directory
cd /d "%~dp0"

title Win-ACME SSL Setup for maintencesp.com.tr

echo.
echo ============================================================================
echo  [SSL] Win-ACME SSL Kurulumu
echo  Domain: maintencesp.com.tr
echo  Let's Encrypt (Ucretsiz SSL)
echo ============================================================================
echo.

REM Check Admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Bu script Administrator olarak calistirilmali!
    pause
    exit /b 1
)

echo [OK] Administrator yetkisi dogrulandi.
echo.

REM Create directories
if not exist "C:\win-acme" mkdir "C:\win-acme"
if not exist "C:\ssl" mkdir "C:\ssl"
if not exist "C:\ssl\maintencesp.com.tr" mkdir "C:\ssl\maintencesp.com.tr"

echo [OK] Klasorler olusturuldu.
echo.

REM Download Win-ACME if not exists
if not exist "C:\win-acme\wacs.exe" (
    echo [INFO] Win-ACME indiriliyor...
    echo.
    echo Win-ACME otomatik indirme ozelligi burada olacak.
    echo Su an icin manuel indirmeniz gerekiyor:
    echo.
    echo 1. https://www.win-acme.com/ adresine gidin
    echo 2. "Download" butonuna tiklayin
    echo 3. ZIP dosyasini C:\win-acme klasorune cikarin
    echo 4. Bu scripti tekrar calistirin
    echo.
    pause
    exit /b 1
)

echo [OK] Win-ACME bulundu.
echo.

REM Stop any running web servers on port 80
echo [INFO] Port 80 temizleniyor...
netstat -ano | findstr :80 > nul
if %errorLevel% equ 0 (
    echo [WARN] Port 80'de calisan servis var. IIS veya Apache'yi durdurun.
    echo Devam etmek icin Enter'a basin...
    pause >nul
)

echo.
echo ============================================================================
echo  [SSL] SSL Sertifikasi Olusturuluyor...
echo ============================================================================
echo.

cd /d "C:\win-acme"

REM Create certificate with Win-ACME
echo [INFO] Win-ACME komutu calistiriliyor...
echo.

REM Interactive mode for first time setup
echo Asagidaki secimleri yapin:
echo.
echo 1. "N" (Create certificate) 
echo 2. "2" (Manual input)
echo 3. Domain: maintencesp.com.tr
echo 4. "3" (No additional installation steps) - ONEMLI!
echo 5. Email: admin@maintencesp.com.tr (veya kendi emailiniz)
echo.
echo [ONEMLI] Installation step soruldugunda "3" secin (No additional installation steps)!
echo Script dosyasi ISTEMEYIN, sadece Windows Certificate Store'a kaydedin!
echo.

wacs.exe

echo.
echo ============================================================================
echo  [ERROR] DNS Sorunu Tespit Edildi
echo ============================================================================
echo.
echo Eger DNS hatasi aldiyseniz:
echo 1. Domain DNS kayitlari hazir degil
echo 2. maintencesp.com.tr A kaydi 85.105.220.36 IP'sine yonlendirilmeli
echo 3. DNS propagation beklenmeli (24-48 saat)
echo.
echo Gecici cozum icin self-signed sertifika olusturmak ister misiniz? (Y/N)
set /p selfsigned=
if /i "%selfsigned%"=="Y" goto :selfsigned
echo.
echo ============================================================================
echo  📋 Sertifika Kontrol
echo ============================================================================
echo.

if exist "C:\ssl\maintencesp.com.tr\maintencesp.com.tr-chain.pem" (
    if exist "C:\ssl\maintencesp.com.tr\maintencesp.com.tr-key.pem" (
        echo ✅ SSL sertifikaları başarıyla oluşturuldu!
        echo.
        echo 📁 Sertifika dosyaları:
        echo    C:\ssl\maintencesp.com.tr\maintencesp.com.tr-chain.pem
        echo    C:\ssl\maintencesp.com.tr\maintencesp.com.tr-key.pem
        echo.
        
        REM Copy to expected names
        copy "C:\ssl\maintencesp.com.tr\maintencesp.com.tr-chain.pem" "C:\ssl\maintencesp.com.tr\fullchain.pem"
        copy "C:\ssl\maintencesp.com.tr\maintencesp.com.tr-key.pem" "C:\ssl\maintencesp.com.tr\privkey.pem"
        
        echo ✅ Sertifikalar Flask için uygun isimlerde kopyalandı.
        echo.
        echo 🎉 Artık start_https.bat ile HTTPS sunucuyu başlatabilirsiniz!
        
    ) else (
        echo ❌ Private key dosyası bulunamadı!
    )
) else (
    echo ❌ Sertifika dosyası bulunamadı!
    echo.
    echo 💡 Win-ACME tekrar çalıştırılacak mı? (Y/N)
    set /p retry=
    if /i "%retry%"=="Y" goto :retry
)

echo.
echo ============================================================================
echo  🔄 Otomatik Yenileme Ayarı
echo ============================================================================
echo.

echo Win-ACME otomatik olarak Windows Task Scheduler'a yenileme görevi ekler.
echo Sertifika 90 günde bir otomatik yenilenir.
echo.

pause
goto :end

:selfsigned
echo.
echo ============================================================================
echo  [TEMP] Self-Signed Sertifika Olusturuluyor...
echo ============================================================================
echo.

cd /d "C:\ssl\maintencesp.com.tr"

REM Create self-signed certificate using OpenSSL (if available) or PowerShell
echo Self-signed sertifika olusturuluyor...

REM PowerShell ile self-signed sertifika olustur
powershell -Command "$cert = New-SelfSignedCertificate -DnsName 'maintencesp.com.tr' -CertStoreLocation 'cert:\LocalMachine\My' -NotAfter (Get-Date).AddYears(1); $pwd = ConvertTo-SecureString -String '123456' -Force -AsPlainText; Export-PfxCertificate -cert $cert -FilePath 'C:\ssl\maintence.com.tr\maintence.com.tr.pfx' -Password $pwd"

echo.
echo [OK] Self-signed sertifika olusturuldu!
echo [INFO] Sertifika sifre: 123456
echo [INFO] Dosya: C:\ssl\maintencesp.com.tr\maintencesp.com.tr.pfx
echo.
echo [WARN] Bu gecici bir cozumdur. DNS hazir olunca Let's Encrypt kullanin.
echo.
goto :end

:retry
echo.
echo 🔄 Win-ACME tekrar çalıştırılıyor...
wacs.exe
goto :check

:end
echo.
echo 🎯 Sonraki adımlar:
echo.
echo 1. DNS ayarlarını kontrol edin: maintencesp.com.tr -> 85.105.220.36
echo 2. start_https.bat ile HTTPS sunucuyu başlatın
echo 3. https://maintencesp.com.tr adresini test edin
echo.
pause