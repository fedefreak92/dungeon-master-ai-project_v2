# Test Frontend del Gioco RPG

Questa directory contiene i test per l'interfaccia utente e i componenti frontend del gioco RPG.

## Struttura dei Test Frontend

- **test_frontend_components.py**: Test di base per i componenti React
- **test_socket_service.py**: Test per il servizio WebSocket utilizzato nella comunicazione client-server
- **test_game_canvas.py** (da implementare): Test per il rendering grafico con Pixi.js

Inoltre, nella directory `test/e2e/` sono disponibili test end-to-end per l'interfaccia utente:

- **test_game_interface.py**: Test e2e dell'interfaccia di gioco utilizzando Selenium

## Prerequisiti per i Test Frontend

1. **Per test unitari dei componenti React**:
   - Jest (da implementare)
   - React Testing Library (da implementare)

2. **Per test Socket.IO**:
   - Python con unittest/pytest
   - Mock appropriati per simulare Socket.IO

3. **Per test e2e con Selenium**:
   - Selenium WebDriver
   - Chrome/Firefox WebDriver installato e configurato
   - Server di gioco in esecuzione su localhost:5000

## Come Eseguire i Test Frontend

### Eseguire i Test Unitari Socket.IO

```bash
python -m pytest test/ui/test_socket_service.py -v
```

### Eseguire i Test dei Componenti Frontend Base

```bash
python -m pytest test/ui/test_frontend_components.py -v
```

### Eseguire i Test e2e dell'Interfaccia (richiede Selenium configurato)

```bash
python -m pytest test/e2e/test_game_interface.py -v
```

## Miglioramenti Futuri

1. **Aggiungere test Jest per React**: Implementare test Jest per i componenti React
2. **Aumentare copertura test**: Aggiungere test per più componenti e interazioni
3. **Mocking WebSocket avanzato**: Migliorare la simulazione dei messaggi Socket.IO
4. **Test di performance frontend**: Implementare test di performance per il frontend
5. **Screenshot automatici**: Catturare screenshot automatici durante i test e2e

## Note sull'Implementazione

- I test attuali usano unittest/pytest con mock per Socket.IO
- Per una soluzione completa, il frontend React dovrebbe avere anche test Jest
- I test e2e richiedono un server di test in esecuzione 