@echo off
setlocal

:: ============================================================
:: Proxima Briefing — wrapper al login (Task Scheduler)
:: Dispositivo: PC Windows di Vale
:: Genera solo il briefing di Vale.
:: ============================================================

set BASE=C:\Users\valer\Desktop\Proxima\Rassegna Stampa
set PYTHON=%BASE%\.venv\Scripts\python.exe
set SCRIPT=%BASE%\code\briefing_pipeline.py
set ANTHROPIC_API_KEY=sk-ant-api03-TUACHIAVE

for /f %%a in ('powershell -command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%a

echo [%DATE% %TIME%] Proxima Briefing (Vale) avviato

if exist "%BASE%\briefings\%TODAY%-vale.html" (
    echo Vale: briefing gia presente per %TODAY%, skip.
) else (
    echo Vale: genero briefing...
    mkdir "%BASE%\logs" 2>nul
    "%PYTHON%" "%SCRIPT%" --user vale >> "%BASE%\logs\vale.log" 2>&1
    echo Vale: done.
)

echo [%DATE% %TIME%] Completato.
endlocal
