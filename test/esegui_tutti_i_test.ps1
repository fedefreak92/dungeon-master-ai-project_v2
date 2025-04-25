# Script PowerShell per eseguire tutti i test del gioco RPG su Windows
# Questo script è specifico per Windows e utilizza il PowerShell per eseguire i test

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Test Completi del Gioco RPG" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Funzione per eseguire un test e mostrare il risultato
function Esegui-Test {
    param (
        [string]$Nome,
        [string]$Comando
    )
    
    Write-Host "Esecuzione test '$Nome'..." -ForegroundColor Yellow
    Write-Host "Comando: $Comando" -ForegroundColor Gray
    
    try {
        Invoke-Expression $Comando
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "✓ Test '$Nome' completati con successo!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Test '$Nome' falliti con codice $exitCode" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Errore durante l'esecuzione dei test '$Nome': $_" -ForegroundColor Red
        return $false
    }
}

# Imposta la directory corrente alla cartella dei test
Set-Location -Path $PSScriptRoot

# Assicurati che il server sia in esecuzione (lo faremo manualmente prima)
Write-Host "IMPORTANTE: Assicurati che il server sia già in esecuzione in un altro terminale!" -ForegroundColor Magenta
Write-Host "Se non l'hai già fatto, avvia il server con: python -m gioco_rpg.server.app" -ForegroundColor Magenta
Write-Host ""

$totale = 0
$successi = 0

# Installa le dipendenze necessarie se non esistono
try {
    $null = python -c "import pytest, socketio, requests, selenium, locust"
    Write-Host "Tutte le dipendenze sono già installate." -ForegroundColor Green
} catch {
    Write-Host "Installazione delle dipendenze mancanti..." -ForegroundColor Yellow
    python -m pip install pytest socketio python-socketio requests selenium locust flask-socketio
}

# 1. Esegui i test unitari
if (Esegui-Test -Nome "unitari" -Comando "python -m pytest unitari -v") {
    $totale++
    $successi++
}

# 2. Esegui i test di integrazione
if (Esegui-Test -Nome "integrazione" -Comando "python -m pytest integrazione -v") {
    $totale++
    $successi++
}

# 3. Esegui i test di regressione
if (Esegui-Test -Nome "regressione" -Comando "python -m pytest regressione -v") {
    $totale++
    $successi++
}

# 4. Esegui i test UI
if (Esegui-Test -Nome "ui" -Comando "python -m pytest ui -v") {
    $totale++
    $successi++
}

# 5. Esegui i test server (routes)
if (Esegui-Test -Nome "server/routes" -Comando "python -m pytest server/routes -v") {
    $totale++
    $successi++
}

# 6. Esegui i test server (security)
if (Esegui-Test -Nome "server/security" -Comando "python -m pytest server/security -v") {
    $totale++
    $successi++
}

# 7. Esegui i test server (websocket)
if (Esegui-Test -Nome "server/websocket" -Comando "python -m pytest server/websocket -v") {
    $totale++
    $successi++
}

# 8. Esegui i test end-to-end
if (Esegui-Test -Nome "e2e" -Comando "python -m pytest e2e -v") {
    $totale++
    $successi++
}

# 9. Esegui i test di carico (opzionali, potrebbero richiedere molto tempo)
$eseguiCarico = $false
if ($eseguiCarico) {
    if (Esegui-Test -Nome "carico" -Comando "python -m pytest carico -v") {
        $totale++
        $successi++
    }
}

# Mostra il riepilogo dei test
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "RIEPILOGO TEST" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Categorie di test eseguite: $totale" -ForegroundColor White
Write-Host "Categorie di test con successo: $successi" -ForegroundColor Green
Write-Host "Categorie di test fallite: $($totale - $successi)" -ForegroundColor Red

if ($successi -eq $totale) {
    Write-Host ""
    Write-Host "TUTTI I TEST COMPLETATI CON SUCCESSO!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ATTENZIONE: Alcuni test sono falliti!" -ForegroundColor Red
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan

# Pausa per consentire all'utente di vedere i risultati
Write-Host "Premi un tasto per terminare..." -ForegroundColor Gray
$null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 