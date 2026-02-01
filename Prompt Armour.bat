@echo off
TITLE Prompt-Armor Launcher
COLOR 0A

echo ==============================================================
echo      🛡️  LLM PROMPT-ARMOR SECURITY LAUNCHER (vasudj)  🛡️
echo ==============================================================
echo.

:: 1. KILL EXISTING PROCESSES (The Secret Fix)
echo [1/3] 🧹 Cleaning up background processes...
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM msedge.exe /T >nul 2>&1
taskkill /F /IM mitmweb.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1

:: 2. START THE PROXY SERVER
echo [2/3] 🚀 Starting Proxy Engine (mitmweb)...
:: Starts mitmweb in a new separate window so you can see logs
start "Prompt-Armor Logs" cmd /k "mitmweb -s proxy.py"

:: Wait 3 seconds for the proxy to wake up
timeout /t 3 /nobreak >nul

:: 3. LAUNCH SECURE CHROME
echo [3/3] 🌐 Launching Secure Browser...
echo.
echo NOTE: Do not close the Black Log Window!
echo.

:: Modify this path if your Chrome is installed somewhere else
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --disable-quic --proxy-server="127.0.0.1:8080" --ignore-certificate-errors
) else (
    echo ERROR: Chrome not found at default location.
    echo Please verify you have Google Chrome installed.
    pause
)