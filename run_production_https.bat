@echo off
REM ============================================================================
REM Production HTTPS Runner with Auto-Restart
REM maintencesp.com.tr - Takılma durumunda otomatik yeniden başlatma
REM ============================================================================

title M.S.P Production HTTPS Server

echo.
echo ============================================================================
echo  🚀 M.S.P Production HTTPS Server
echo  Domain: https://maintencesp.com.tr
echo  Auto-restart enabled
echo ============================================================================
echo.

REM Admin kontrolü
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Administrator olarak çalıştırın!
    pause
    exit /b 1
)

REM Virtual environment
call venv\Scripts\activate.bat

REM Waitress kur (daha stabil)
pip install waitress pyopenssl --quiet

:restart_loop
echo.
echo [%date% %time%] 🔄 Server başlatılıyor...
echo.

REM Waitress ile çalıştır (daha stabil)
python -c "from waitress import serve; from app import app; import ssl; context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(r'C:\ssl\maintencesp.com.tr\fullchain.pem', r'C:\ssl\maintencesp.com.tr\privkey.pem'); serve(app, host='0.0.0.0', port=443, url_scheme='https', ident='MSP', threads=4)"

echo.
echo [%date% %time%] ⚠️ Server durdu, 5 saniye sonra yeniden başlatılacak...
timeout /t 5 /nobreak >nul

goto :restart_loop