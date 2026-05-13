@echo off
setlocal

:: ============================================================
:: Proxima Briefing — wrapper al login (Task Scheduler)
:: Percorso base: C:\Users\valer\Desktop\Proxima\Rassegna Stampa
:: ============================================================

set BASE=C:\Users\valer\Desktop\Proxima\Rassegna Stampa
set PYTHON=%BASE%\.venv\Scripts\python.exe
set SCRIPT=%BASE%\code\briefing_pipeline.py
set ANTHROPIC_API_KEY=sk-ant-api03-TUACHIAVE

:: Data di oggi nel formato yyyy-MM-dd
for /f %%a in ('powershell -command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%a

echo [%DATE% %TIME%] Proxima Briefing avviato

:: --- Vale ---
if exist "%BASE%\briefings\%TODAY%-vale.html" (
    echo Vale: briefing gia presente per %TODAY%, skip.
) else (
    echo Vale: genero briefing...
    "%PYTHON%" "%SCRIPT%" --user vale >> "%BASE%\logs\vale.log" 2>&1
    echo Vale: done.
)

:: --- Alex ---
if exist "%BASE%\briefings\%TODAY%-alex.html" (
    echo Alex: briefing gia presente per %TODAY%, skip.
) else (
    echo Alex: genero briefing...
    "%PYTHON%" "%SCRIPT%" --user alex >> "%BASE%\logs\alex.log" 2>&1
    echo Alex: done.
)

echo [%DATE% %TIME%] Proxima Briefing completato.
endlocal
