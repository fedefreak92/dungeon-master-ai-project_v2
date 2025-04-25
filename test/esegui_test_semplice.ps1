# Script PowerShell semplificato per eseguire i test
Write-Host "==============================================="
Write-Host "Test Gioco RPG - Esecuzione Semplice"
Write-Host "==============================================="
Write-Host ""

# Imposta la directory corrente alla cartella dei test
Set-Location -Path $PSScriptRoot

# Esegui i test unitari
Write-Host "Esecuzione test unitari..." -ForegroundColor Yellow
python -m pytest unitari -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "Test unitari completati con successo!" -ForegroundColor Green
} else {
    Write-Host "Test unitari falliti!" -ForegroundColor Red
}

# Esegui i test server/routes
Write-Host "Esecuzione test server/routes..." -ForegroundColor Yellow
python -m pytest server/routes -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "Test server/routes completati con successo!" -ForegroundColor Green
} else {
    Write-Host "Test server/routes falliti!" -ForegroundColor Red
}

# Esegui i test server/security
Write-Host "Esecuzione test server/security..." -ForegroundColor Yellow
python -m pytest server/security -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "Test server/security completati con successo!" -ForegroundColor Green
} else {
    Write-Host "Test server/security falliti!" -ForegroundColor Red
}

Write-Host "Test completati."
Write-Host "Premi un tasto per terminare..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 