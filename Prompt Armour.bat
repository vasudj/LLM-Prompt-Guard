@echo off
TITLE Prompt-Armor Hackathon Launcher
COLOR 0A

cd /d "%~dp0"

echo ==================================================
echo        🛡️  PROMPT-ARMOR FULL STACK LAUNCHER
echo ==================================================
echo.

:: ================= CLEANUP =================

echo [1/6] Cleaning old processes...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM mitmdump.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8082') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1

timeout /t 1 >nul

:: ================= ACTIVATE VENV =================

echo [2/6] Activating Virtual Environment...
call venv\Scripts\activate.bat

:: ================= START FASTAPI =================

echo [3/6] Starting Dashboard Backend (Uvicorn)...
start "Prompt-Armor API" cmd /k "uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 >nul

:: ================= START MITMPROXY =================

echo [4/6] Starting Proxy Engine...
start "Prompt-Armor Proxy" cmd /k "mitmdump -s proxy.py -p 8082"

timeout /t 3 >nul

:: ================= START ISOLATED CHROME =================

echo [5/6] Launching Secure Chrome...

set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

if exist %CHROME_PATH% (
    start "" %CHROME_PATH% ^
    --proxy-server=127.0.0.1:8082 ^
    --ignore-certificate-errors ^
    --user-data-dir="%cd%\chrome-proxy-profile" ^
    http://127.0.0.1:8000
) else (
    echo Chrome not found at default location.
    pause
)

echo.
echo [6/6] System Ready.
echo.
echo Open ChatGPT in this Chrome window.
echo Dashboard is already opened.
echo.
echo DO NOT CLOSE the API or Proxy windows.
echo.
pause