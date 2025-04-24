# Test del Gioco RPG

Questa directory contiene tutti i test per il progetto di gioco RPG. I test sono organizzati per tipologia in diverse cartelle.

## Struttura dei Test

- **unitari**: Test delle singole componenti del gioco in isolamento
- **integrazione**: Test dell'interazione tra più componenti
- **regressione**: Test per verificare che nuove funzionalità non rompano il codice esistente
- **e2e**: Test end-to-end che verificano flussi di gioco completi
- **carico**: Test di performance sotto carico
- **ui**: Test dell'interfaccia utente
- **manuali**: Test che richiedono intervento umano per la verifica

## Configurazione

Il file `conftest.py` contiene fixture e configurazioni comuni utilizzate da tutti i test. Queste fixture permettono:
- Creazione di oggetti mock per test unitari
- Prevenzione di accesso a file reali durante i test
- Configurazione di ambienti di test standardizzati

## Come Eseguire i Test

### Eseguire Tutti i Test

```bash
python run_all_tests.py
```

oppure:

```bash
.\run_tests.bat
```

### Eseguire un Tipo Specifico di Test

```bash
python run_all_tests.py --type unitari
```

oppure:

```bash
.\run_tests.bat unitari
```

### Eseguire un Test Specifico

Con unittest:

```bash
python -m unittest test.unitari.test_game
```

Con pytest:

```bash
python -m pytest unitari/test_game.py -v
```

## Buone Pratiche

1. **Isolamento**: I test unitari devono essere indipendenti da altri componenti e dai file reali
2. **Mock**: Utilizzare mock per sostituire dipendenze esterne nei test unitari
3. **Pulizia**: Ogni test deve ripulire dopo di sé e non influenzare altri test
4. **Chiarezza**: Ogni test deve testare un singolo comportamento e avere un nome descrittivo

## Dipendenze

I test utilizzano le seguenti librerie:
- pytest: framework di test principale
- unittest: libreria di test standard di Python
- Mock: per creare oggetti fittizi
- Locust: per test di carico
- Selenium: per test dell'interfaccia utente 

## Test Server

La suite di test include ora test dedicati per i componenti server dell'applicazione:

### 1. Test API REST

I test per le API REST si trovano nella cartella `test/server/routes` e verificano il corretto funzionamento delle route del server:

- `test_save_routes.py`: Verifica le API di salvataggio/caricamento
- `test_combat_routes.py`: Verifica le API di combattimento
- `test_session_routes.py`: Verifica le API di gestione sessione
- ...

Per eseguire solo i test delle route:

```bash
python -m pytest test/server/routes
```

### 2. Test WebSocket

I test per le comunicazioni WebSocket si trovano nella cartella `test/server/websocket` e verificano la corretta gestione degli eventi in tempo reale:

- `test_combattimento_socket.py`: Verifica gli eventi WebSocket del combattimento
- `test_dialogo_socket.py`: Verifica gli eventi WebSocket del dialogo
- ...

Per eseguire solo i test WebSocket:

```bash
python -m pytest test/server/websocket
```

### 3. Test End-to-End Server

La cartella `test/e2e` contiene ora test che verificano il flusso completo del server:

- `test_server_flow.py`: Verifica un flusso completo di interazione con il server

### 4. Test di Sicurezza

La cartella `test/server/security` contiene test dedicati alla sicurezza del server:

- `test_input_validation.py`: Verifica la corretta validazione degli input

### Esecuzione e Problematiche Note

Per eseguire tutti i test del server:

```bash
python -m pytest test/server
```

**Requisiti per l'esecuzione dei test**:
1. Il server deve essere in esecuzione su `http://localhost:5000`
2. Assicurati di avere installato le dipendenze: `pytest`, `requests`, `python-socketio`

**Note sui test**:
- Alcuni test usano `pytest.xfail()` quando rilevano problemi nel server (es. risposte 500 per input non validi). Questi test sono contrassegnati come "attesi al fallimento" e indicano aree da migliorare nella gestione degli errori del server.
- I test sono stati progettati per essere flessibili rispetto alle risposte API effettive del server (es. accettano sia 400 che 404 per errori di validazione).

**Problematiche Note e Miglioramenti Futuri**:
1. Gestione degli errori: Il server restituisce 500 per alcuni input non validi anziché gestire correttamente l'errore
2. Validazione input: Migliorare la validazione per gestire stringhe troppo lunghe, tipi errati, e input potenzialmente pericolosi
3. Formato JSON: Standardizzare il formato delle risposte JSON (es. includere sempre un campo "successo" o equivalente) 