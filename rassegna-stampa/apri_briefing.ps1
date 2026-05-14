# apri_briefing.ps1 — Apre il briefing di oggi nel browser (Vale)
# Usa come shortcut sul desktop: tasto destro → "Esegui con PowerShell"

$BASE     = "C:\Users\valer\Desktop\Proxima\Rassegna Stampa"
$BRIEFINGS = "$BASE\briefings"
$TODAY    = Get-Date -Format "yyyy-MM-dd"
$HTML     = "$BRIEFINGS\$TODAY-vale.html"

if (Test-Path $HTML) {
    Start-Process $HTML
} else {
    # Apri l'ultimo disponibile se oggi non c'è ancora
    $latest = Get-ChildItem "$BRIEFINGS\*-vale.html" -ErrorAction SilentlyContinue |
              Sort-Object Name -Descending |
              Select-Object -First 1
    if ($latest) {
        Write-Host "Briefing di oggi non trovato. Apro l'ultimo: $($latest.Name)"
        Start-Process $latest.FullName
    } else {
        Write-Host "Nessun briefing trovato in $BRIEFINGS"
        Read-Host "Premi Invio per uscire"
    }
}
