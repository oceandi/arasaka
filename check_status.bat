@echo off
REM Server durumunu kontrol et

echo.
echo 🔍 Server Durumu Kontrol Ediliyor...
echo.

REM Port 443 dinleniyor mu?
netstat -an | findstr :443 | findstr LISTENING >nul
if %errorlevel%==0 (
    echo ✅ HTTPS Server ÇALIŞIYOR (Port 443)
) else (
    echo ❌ HTTPS Server ÇALIŞMIYOR
)

echo.
echo 📊 Port Detayları:
netstat -an | findstr :443

echo.
echo 🌐 Site Erişim Testi...
curl -k -s -o nul -w "HTTP Status: %%{http_code}\n" https://localhost

echo.
pause