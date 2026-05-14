@echo off
REM aggiorna.bat - Scarica gli ultimi briefing e aggiornamenti dal repo GitHub
REM Doppio click per usarlo.

cd /d "%~dp0\.."

echo.
echo === Proxima - Aggiornamento in corso ===
echo.

git pull origin claude/financial-briefing-pipeline-aVCmh

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === Aggiornamento completato ===
    echo.
    echo Ultimi briefing in: docs\archivio\
) else (
    echo.
    echo === ERRORE durante l'aggiornamento ===
    echo Controlla la connessione internet o contatta Alex.
)

echo.
pause
