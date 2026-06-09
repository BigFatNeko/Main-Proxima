@echo off
cd /d "%~dp0"
echo Avvio Proxima Funnel Model...
start "" python -m http.server 8000
timeout /t 2 >nul
start http://localhost:8000
echo.
echo Server attivo su http://localhost:8000
echo Chiudi questa finestra per fermare il server.
pause >nul
