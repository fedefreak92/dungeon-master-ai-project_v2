@echo off
echo Avvio del gioco RPG...

rem Salvo la directory corrente
set "DIRECTORY_ORIGINALE=%CD%"

echo Attivazione dell'ambiente virtuale Python...
cd "%DIRECTORY_ORIGINALE%\gioco_rpg"
call .venv\Scripts\activate

echo Avvio del server backend...
start cmd /k python main.py

echo Avvio del frontend React...
cd "%DIRECTORY_ORIGINALE%\gioco_rpg\frontend"
start cmd /k npm start

echo Gioco avviato! Accedi a http://localhost:3000 nel tuo browser.

rem Torno alla directory originale
cd "%DIRECTORY_ORIGINALE%" 