# Script PowerShell per eseguire i test del gioco RPG su Windows

Write-Host "==============================================="
Write-Host "Test del Gioco RPG"
Write-Host "==============================================="

# Imposta la directory corrente al percorso dello script
Set-Location -Path $PSScriptRoot

# Verifica se è stato installato pytest
try {
    $null = python -c "import pytest"
} catch {
    Write-Host "Installazione delle dipendenze necessarie..."
    python -m pip install pytest locust selenium
}

# Verifica se è specificato un tipo di test
if ($args.Count -eq 0) {
    Write-Host "Esecuzione di tutti i test..."
    python run_all_tests.py
} else {
    Write-Host "Esecuzione dei test '$($args[0])'..."
    python run_all_tests.py --type $args[0]
}

# Mostra un messaggio di riepilogo
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Test completati con successo!"
} else {
    Write-Host ""
    Write-Host "Alcuni test sono falliti. Controlla i log per i dettagli."
}

Write-Host ""
Write-Host "==============================================="

# Pausa per consentire all'utente di vedere i risultati
Write-Host "Premi un tasto per continuare..."
$null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 