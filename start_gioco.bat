@echo off
TITLE Avvio Gioco RPG

:: Impostazioni colori per la console
color 0A

echo =======================================
echo       AVVIO DEL GIOCO RPG
echo =======================================
echo.

:: Crea directory logs se non esiste
if not exist "logs" mkdir logs

:: Controlla se Python è installato
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRORE: Python non trovato. Installare Python 3.8+ e riprovare.
    pause
    exit /b 1
)

:: Controlla se Node.js è installato
node --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRORE: Node.js non trovato. Installare Node.js e riprovare.
    pause
    exit /b 1
)

echo [INFO] Verifica delle dipendenze Python...
:: Verifica che l'ambiente virtuale esista, altrimenti lo crea
if not exist .venv (
    echo [INFO] Creazione ambiente virtuale Python...
    python -m venv .venv
)

:: Attiva l'ambiente virtuale
call .venv\Scripts\activate.bat

:: Installa le dipendenze Python
echo [INFO] Installazione dipendenze Python...
pip install -r requirements.txt

:: Vai nella directory client e installa le dipendenze npm
echo [INFO] Installazione dipendenze NPM...
cd gioco_rpg\client
if not exist node_modules (
    npm install
)
cd ..\..

:: Apri due finestre cmd, una per il frontend e una per il backend
echo [INFO] Avvio del server backend...
start cmd.exe /k "call .venv\Scripts\activate.bat && cd gioco_rpg && python -m server.main"

:: Attendi un po' per dare tempo al backend di avviarsi
timeout /t 3 > nul

echo [INFO] Avvio del client frontend...
start cmd.exe /k "cd gioco_rpg\client && npm start"

echo.
echo [SUCCESSO] Gioco avviato correttamente!
echo - Server backend in esecuzione... (non chiudere la finestra del terminale)
echo - Client frontend in avvio... (si aprirà automaticamente nel browser)
echo.
echo Per terminare l'esecuzione, chiudere entrambe le finestre dei terminali.
echo.

pause 