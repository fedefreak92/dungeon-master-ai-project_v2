@echo off
:: Script batch per eseguire i test del gioco RPG su Windows

echo ===============================================
echo Test del Gioco RPG
echo ===============================================

:: Imposta la directory corrente al percorso dello script
cd /d %~dp0

:: Verifica se è stato installato pytest
python -c "import pytest" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Installazione delle dipendenze necessarie...
    python -m pip install pytest locust selenium
)

:: Verifica se è specificato un tipo di test
if "%1"=="" (
    echo Esecuzione di tutti i test...
    python run_all_tests.py
) else (
    echo Esecuzione dei test '%1'...
    python run_all_tests.py --type %1
)

:: Mostra un messaggio di riepilogo
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Test completati con successo!
) else (
    echo.
    echo Alcuni test sono falliti. Controlla i log per i dettagli.
)

echo.
echo ===============================================

:: Pausa per consentire all'utente di vedere i risultati
pause 