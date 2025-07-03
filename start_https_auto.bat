@echo off
setlocal
call venv\Scripts\activate.bat
start "HTTPSServer" /B python run_ssl_server.py
timeout /t 8 /nobreak >nul
start "" "chrome.exe" https://maintencesp.com.tr
:waitLoop
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if %errorlevel%==0 (
    timeout /t 1 >nul
    goto :waitLoop
)
taskkill /FI "WINDOWTITLE eq HTTPSServer" /F >nul 2>&1
endlocal