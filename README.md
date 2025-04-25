# Gioco RPG Backend

Backend per un gioco RPG basato su architettura ECS (Entity Component System).

## Struttura del progetto

La nuova struttura del server è organizzata nei seguenti moduli:

- `server/app.py` - Inizializzazione dell'app Flask e funzioni principali
- `server/routes/base_routes.py` - Route base (GET /, ping, ecc.)
- `server/routes/game_routes.py` - Route di gioco (inizia_sessione, salvataggi, ecc.)
- `server/routes/assets_routes.py` - Route per risorse e asset
- `server/websocket/handlers.py` - Gestione WebSocket
- `server/utils/session.py` - Funzioni per gestione sessioni

Il file `server.py` originale è stato mantenuto per compatibilità ma non dovrebbe essere usato direttamente.

## Requisiti

- Python 3.8 o superiore
- Flask e altre dipendenze elencate in `requirements.txt`

## Installazione

1. Clona il repository
2. Installa le dipendenze:

```
pip install -r requirements.txt
```

## Avvio del server

Per avviare il server:

```
python main.py
```

Il server sarà disponibile all'indirizzo `http://localhost:5000`.

## Recenti miglioramenti (Giugno 2024)

Nel recente aggiornamento sono state apportate importanti correzioni che migliorano significativamente la stabilità e le prestazioni del frontend:

### 🔧 Ottimizzazioni React Hooks
- **Corretti errori Hook**: Risolti problemi legati alla regola "React Hook cannot be called inside a callback"
- **Gestione Context**: Migliorata l'estrazione delle funzioni dai context Socket.IO
- **Dependency Arrays**: Corrette le dipendenze negli useEffect per prevenire cicli di rendering infiniti

### ⚡ Miglioramenti WebSocket
- **Lifecycle Management**: Perfezionata la gestione del ciclo di vita delle connessioni socket
- **Event Handling**: Migliorato il sistema di gestione degli eventi con correzioni ai listener map_change_complete
- **Context Distribution**: Ottimizzato l'uso del context Socket.IO in tutta l'applicazione  

### 📋 File corretti
- **App.jsx**: Corretta l'implementazione di useSocket per rispettare le regole dei React Hooks
- **MapSelectState.jsx**: Rimosse variabili non utilizzate dal destructuring di useSocket
- **MapContainer.jsx**: Rimosso useMemo dall'import e ottimizzato l'uso di emitWithAck

### 📊 Vantaggi
- **Stabilità**: Eliminati errori console e warnings ESLint
- **Performance**: Ridotto il rischio di memory leaks e re-rendering non necessari
- **Manutenibilità**: Codice più pulito e conforme alle best practices di React
- **Compatibilità**: Migliore supporto a future versioni di React con strict mode

## API Endpoints

- `GET /` - Informazioni sull'API
- `GET /ping` - Verifica connessione
- `GET /salvataggi` - Ottieni lista salvataggi
- `POST /elimina_salvataggio` - Elimina un salvataggio
- `GET /assets/info` - Ottieni informazioni sugli asset disponibili
- `POST /assets/update` - Aggiorna le informazioni sugli asset
- `GET /assets/file/<path:asset_path>` - Ottiene un file asset specifico

## WebSocket Events

- `connect` - Connessione WebSocket
- `disconnect` - Disconnessione WebSocket
- `join_game` - Partecipa a una sessione di gioco
- `game_event` - Invia un evento di gioco
- `request_map_data` - Richiedi dati mappa

## Configurazione

1. Assicurati di avere Python installato (Python 3.6+)
2. Installa le dipendenze necessarie:
   ```
   pip install flask
   ```
3. Avvia il server:
   ```
   python server.py
   ```
4. Il server sarà in esecuzione su `http://localhost:5000`

## Endpoints

### `GET /`
Mostra informazioni generali sul server e gli endpoints disponibili.

### `POST /inizia`
Crea una nuova partita.

**Parametri (JSON):**
- `nome` (opzionale): Nome del personaggio (default: "Avventuriero")
- `classe` (opzionale): Classe del personaggio (default: "guerriero")

**Esempio di richiesta:**
```json
{
  "nome": "Thorin",
  "classe": "guerriero"
}
```

**Risposta:**
```json
{
  "id_sessione": "550e8400-e29b-41d4-a716-446655440000",
  "messaggio": "Gioco iniziato",
  "stato": {
    "nome": "Thorin",
    "classe": "guerriero",
    "hp": 25,
    "max_hp": 25,
    "stato": "TavernaState",
    "output": "Benvenuto alla taverna...",
    "posizione": {
      "mappa": "taverna",
      "x": 5,
      "y": 5
    },
    "inventario": ["Spada corta", "Pozione di cura"]
  }
}
```

### `POST /comando`
Invia un comando alla partita.

**Parametri (JSON):**
- `id_sessione` (obbligatorio): ID della sessione di gioco
- `comando` (obbligatorio): Comando da eseguire

**Esempio di richiesta:**
```json
{
  "id_sessione": "550e8400-e29b-41d4-a716-446655440000",
  "comando": "guarda"
}
```

**Risposta:**
```json
{
  "output": "Ti trovi in una taverna affollata...",
  "stato": {
    "nome": "Thorin",
    "classe": "guerriero",
    "hp": 25,
    "max_hp": 25,
    "stato": "TavernaState",
    "output": "Ti trovi in una taverna affollata...",
    "posizione": {
      "mappa": "taverna",
      "x": 5,
      "y": 5
    },
    "inventario": ["Spada corta", "Pozione di cura"]
  }
}
```

### `GET /stato`
Ottiene lo stato attuale della partita.

**Parametri (query string):**
- `id_sessione` (obbligatorio): ID della sessione di gioco

**Esempio di richiesta:**
```
GET /stato?id_sessione=550e8400-e29b-41d4-a716-446655440000
```

**Risposta:**
```json
{
  "nome": "Thorin",
  "classe": "guerriero",
  "hp": 25,
  "max_hp": 25,
  "stato": "TavernaState",
  "output": "Ti trovi in una taverna affollata...",
  "posizione": {
    "mappa": "taverna",
    "x": 5,
    "y": 5
  },
  "inventario": ["Spada corta", "Pozione di cura"]
}
```

### `POST /salva`
Salva la partita corrente.

**Parametri (JSON):**
- `id_sessione` (obbligatorio): ID della sessione di gioco
- `nome_file` (opzionale): Nome del file di salvataggio (default: "salvataggio.json")

**Esempio di richiesta:**
```json
{
  "id_sessione": "550e8400-e29b-41d4-a716-446655440000",
  "nome_file": "partita_thorin.json"
}
```

**Risposta:**
```json
{
  "messaggio": "Partita salvata in partita_thorin.json"
}
```

### `POST /carica`
Carica una partita esistente.

**Parametri (JSON):**
- `nome_file` (opzionale): Nome del file di salvataggio (default: "salvataggio.json")

**Esempio di richiesta:**
```json
{
  "nome_file": "partita_thorin.json"
}
```

**Risposta:**
```json
{
  "id_sessione": "660f8500-e29b-41d4-a716-446655440001",
  "messaggio": "Partita caricata da partita_thorin.json",
  "stato": {
    "nome": "Thorin",
    "classe": "guerriero",
    "hp": 25,
    "max_hp": 25,
    "stato": "TavernaState",
    "output": "Ti trovi in una taverna affollata...",
    "posizione": {
      "mappa": "taverna",
      "x": 5,
      "y": 5
    },
    "inventario": ["Spada corta", "Pozione di cura"]
  }
}
```

### `GET /mappa`
Ottiene informazioni sulla mappa attuale.

**Parametri (query string):**
- `id_sessione` (obbligatorio): ID della sessione di gioco

**Esempio di richiesta:**
```
GET /mappa?id_sessione=550e8400-e29b-41d4-a716-446655440000
```

**Risposta:**
```json
{
  "mappa": "taverna",
  "x": 5,
  "y": 5,
  "oggetti_vicini": {
    "pozione": {
      "x": 6,
      "y": 5,
      "nome": "Pozione di cura"
    }
  },
  "npg_vicini": {
    "oste": {
      "x": 4,
      "y": 5,
      "nome": "Oste"
    }
  }
}
```

### `POST /muovi`
Muove il giocatore nella direzione specificata.

**Parametri (JSON):**
- `id_sessione` (obbligatorio): ID della sessione di gioco
- `direzione` (obbligatorio): Una delle direzioni "nord", "sud", "est", "ovest"

**Esempio di richiesta:**
```json
{
  "id_sessione": "550e8400-e29b-41d4-a716-446655440000",
  "direzione": "nord"
}
```

**Risposta:**
```json
{
  "spostamento": true,
  "stato": {
    "nome": "Thorin",
    "classe": "guerriero",
    "hp": 25,
    "max_hp": 25,
    "stato": "TavernaState",
    "output": "Ti sposti verso nord.",
    "posizione": {
      "mappa": "taverna",
      "x": 5,
      "y": 4
    },
    "inventario": ["Spada corta", "Pozione di cura"]
  }
}
```

## Note sulla sicurezza

- Le sessioni vengono salvate sul server in formato pickle. In un ambiente di produzione, considerare soluzioni più sicure.
- L'API non implementa autenticazione. Aggiungere un sistema di autenticazione per un utilizzo in produzione.

## Persistenza dati

Le sessioni vengono salvate in due modi:
1. In memoria (durante l'esecuzione del server)
2. Su disco nella cartella "sessioni" (per persistenza tra riavvii del server)

Inoltre, è possibile salvare l'intera partita in un file JSON tramite l'endpoint `/salva`.

## Nuove funzionalità

### Output strutturato per la GUI web

Per preparare il backend all'interfaccia web con Flask + HTMX, sono state aggiunte nuove funzionalità di output strutturato:

1. Ogni messaggio visibile al giocatore passa attraverso `gioco.io.mostra_messaggio()` 
2. L'output è organizzato in modo chiaro e separato (senza newline a caso)
3. È stato aggiunto un helper `get_output_structured()` che restituisce una lista di messaggi nel formato:

```python
[
    {"tipo": "sistema", "testo": "Hai aperto il forziere"},
    {"tipo": "narrativo", "testo": "Dentro trovi una pergamena"}
]
```

Questa funzionalità è disponibile sia nella classe `TerminalIO` che in `GameIOWeb`, permettendo così di supportare entrambe le interfacce.

#### Utilizzo dell'output strutturato

```python
# Esempio di utilizzo con TerminalIO
from core.io_interface import TerminalIO
from core.game import Game

io_handler = TerminalIO()
# Creazione oggetto temporaneo gioco
gioco = Game(None, None, io_handler, e_temporaneo=True)
gioco.io.mostra_messaggio("Benvenuto avventuriero!")
gioco.io.messaggio_sistema("Nuova partita iniziata")

# Ottieni tutti i messaggi in formato strutturato
messaggi = gioco.io.get_output_structured()
```

```python
# Esempio di utilizzo con GameIOWeb (per interfaccia web)
from core.stato_gioco import GameIOWeb, StatoGioco
from entities.giocatore import Giocatore
from states.taverna import TavernaState

# Crea un giocatore e uno stato di gioco
giocatore = Giocatore("Avventuriero", "guerriero")
stato_gioco = StatoGioco(giocatore, TavernaState())

# Elabora un comando
stato_gioco.processa_comando("guarda")

# Ottieni i messaggi in formato strutturato
messaggi = stato_gioco.io_buffer.get_output_structured()
```

Questa funzionalità facilita l'integrazione con framework web come Flask + HTMX, permettendo di formattare facilmente i messaggi per l'interfaccia utente.

## Architettura del Progetto

Il progetto è strutturato secondo i seguenti principi:

- Architettura basata su stati (pattern State)
- Sistema Entity-Component-System (ECS)
- API RESTful con Flask
- WebSocket per comunicazioni in tempo reale
- Gestione mappe, oggetti interattivi e NPG

### Modularizzazione e Ristrutturazione

Per migliorare la manutenibilità e la scalabilità del codice, abbiamo adottato un approccio di modularizzazione per i file più grandi. Un esempio è il modulo `mercato`, che è stato ristrutturato come segue:

#### Modulo Mercato

Il file originale `states/mercato.py` (1201 righe) è stato suddiviso in moduli più piccoli e gestibili:

- **states/mercato/mercato_state.py** - Classe principale che integra tutti gli altri componenti
- **states/mercato/oggetti_interattivi.py** - Definizione degli oggetti interattivi presenti nel mercato
- **states/mercato/menu_handlers.py** - Gestione dei menu e delle opzioni di interazione
- **states/mercato/ui_handlers.py** - Gestione degli eventi dell'interfaccia utente
- **states/mercato/movimento.py** - Gestione del movimento del giocatore all'interno del mercato
- **states/mercato/dialogo.py** - Gestione delle conversazioni con gli NPC del mercato

Questa modularizzazione offre diversi vantaggi:
1. **Responsabilità singola**: Ogni file ha una sola responsabilità
2. **Facilità di manutenzione**: Più facile trovare e modificare il codice
3. **Coesione elevata**: Il codice correlato è organizzato insieme
4. **Estensibilità**: È più facile aggiungere nuove funzionalità

Per ulteriori dettagli sull'utilizzo del modulo mercato, consultare il file `states/mercato/README.md`.

## Sistema di Combattimento

Il sistema di combattimento implementa un meccanismo a turni per gestire i combattimenti tra giocatori e nemici, supportando diverse azioni e abilità.

### API per il Combattimento

#### Endpoints HTTP

- **POST /combattimento/inizia**: Inizia un nuovo combattimento.
  - Parametri: `id_sessione`, `nemici_ids` (opzionale), `tipo_incontro` (casuale, imboscata, preparato)
  - Risposta: Informazioni sui partecipanti e sullo stato iniziale del combattimento

- **GET /combattimento/stato**: Ottiene lo stato attuale del combattimento.
  - Parametri: `id_sessione`
  - Risposta: Stato dettagliato del combattimento in corso (turno, partecipanti, HP, ecc.)

- **POST /combattimento/azione**: Esegue un'azione durante il combattimento.
  - Parametri: `id_sessione`, `tipo_azione` (attacco, incantesimo, oggetto, movimento, passa), `parametri`
  - Risposta: Risultato dell'azione e stato aggiornato del combattimento

- **GET /combattimento/azioni_disponibili**: Ottiene le azioni disponibili per un'entità.
  - Parametri: `id_sessione`, `entita_id`
  - Risposta: Lista delle azioni che l'entità può eseguire

- **POST /combattimento/termina**: Termina un combattimento in corso.
  - Parametri: `id_sessione`, `forzato` (opzionale)
  - Risposta: Conferma della terminazione del combattimento

- **GET /combattimento/nemici_vicini**: Ottiene la lista dei nemici nelle vicinanze.
  - Parametri: `id_sessione`
  - Risposta: Lista di nemici che potrebbero essere coinvolti in un combattimento

#### Eventi WebSocket

- **combattimento_inizia**: Inizia un nuovo combattimento.
  - Parametri: `id_sessione`, `nemici_ids`, `tipo_incontro`
  - Eventi emessi: `combattimento_iniziato`

- **combattimento_azione**: Esegue un'azione generica durante il combattimento.
  - Parametri: `id_sessione`, `tipo_azione`, `parametri`
  - Eventi emessi: `combattimento_azione_eseguita`

- **combattimento_seleziona_bersaglio**: Seleziona un bersaglio per un'azione.
  - Parametri: `id_sessione`, `attaccante_id`, `target_id`
  - Eventi emessi: `combattimento_bersaglio_selezionato`

- **combattimento_usa_abilita**: Usa un'abilità durante il combattimento.
  - Parametri: `id_sessione`, `entita_id`, `abilita`, `target_ids`
  - Eventi emessi: `combattimento_abilita_usata`

- **combattimento_usa_oggetto**: Usa un oggetto durante il combattimento.
  - Parametri: `id_sessione`, `entita_id`, `oggetto`, `target_ids`
  - Eventi emessi: `combattimento_oggetto_usato`

- **combattimento_passa_turno**: Passa il turno a un'altra entità.
  - Parametri: `id_sessione`, `entita_id`
  - Eventi emessi: `combattimento_turno_passato`

### Eventi emessi dal server

- **combattimento_iniziato**: Emesso quando un combattimento inizia.
- **combattimento_azione_eseguita**: Emesso quando un'azione viene eseguita.
- **combattimento_bersaglio_selezionato**: Emesso quando un bersaglio viene selezionato.
- **combattimento_abilita_usata**: Emesso quando un'abilità viene usata.
- **combattimento_oggetto_usato**: Emesso quando un oggetto viene usato.
- **combattimento_turno_passato**: Emesso quando un turno viene passato.
- **combattimento_aggiornamento**: Emesso periodicamente con aggiornamenti sullo stato del combattimento.
- **combattimento_terminato**: Emesso quando un combattimento termina.

### Utilizzo del Sistema di Combattimento

```python
# Esempio: Inizia un combattimento
response = requests.post("http://localhost:5000/combattimento/inizia", json={
    "id_sessione": "sessione-123",
    "tipo_incontro": "casuale"
})

# Ottieni lo stato del combattimento
response = requests.get("http://localhost:5000/combattimento/stato?id_sessione=sessione-123")
stato = response.json()

# Esegui un'azione di attacco
response = requests.post("http://localhost:5000/combattimento/azione", json={
    "id_sessione": "sessione-123",
    "tipo_azione": "attacco",
    "parametri": {
        "attaccante_id": stato["turno_di"],
        "target_id": stato["partecipanti"][1]["id"],
        "arma": "spada"
    }
})

# Termina il combattimento
requests.post("http://localhost:5000/combattimento/termina", json={
    "id_sessione": "sessione-123",
    "forzato": True
})
```

### Flusso di un Combattimento Tipico

1. **Inizializzazione**:
   - Il client richiede l'inizio di un combattimento tramite `/combattimento/inizia`
   - Il server genera o usa i nemici specificati
   - Il server calcola l'iniziativa per determinare l'ordine dei turni
   - Il server emette l'evento `combattimento_iniziato`

2. **Turni di Combattimento**:
   - Il server determina di chi è il turno corrente
   - Il client richiede le azioni disponibili con `/combattimento/azioni_disponibili`
   - Il client esegue un'azione usando `/combattimento/azione`
   - Il server elabora l'azione e i suoi effetti
   - Il server emette eventi come `combattimento_azione_eseguita`
   - Se è il turno di un nemico, il server determina ed esegue automaticamente l'azione

3. **Fine del Combattimento**:
   - Il combattimento termina quando tutti i nemici sono sconfitti o il giocatore fugge/viene sconfitto
   - Il server emette l'evento `combattimento_terminato`
   - Il client viene informato dell'esito e delle ricompense 

## Ottimizzazioni e miglioramenti

### WebSocket ottimizzati
- Configurazione aggiornata per utilizzare Eventlet come backend per WebSocket
- Parametri ping/pong configurati correttamente per evitare timeout di connessione
- Gestione migliorata della riconnessione client per maggiore stabilità
- Riduzione del sovraccarico nella trasmissione dati

### Sistema di sprite sheet
- Implementato un sistema completo di sprite sheet per ridurre le richieste HTTP
- Gestore dedicato per la generazione e il caricamento dinamico degli sprite sheet
- API per la generazione degli sprite sheet al volo
- Ottimizzazione del rendering lato client grazie al consolidamento delle immagini

### Serializzazione MessagePack
- Supporto migliorato per MessagePack in tutte le classi principali
- Sistema di sessione configurato per utilizzare MessagePack di default
- Riduzione della dimensione dei payload trasmessi tra client e server
- Miglioramento della velocità di serializzazione/deserializzazione

### API di diagnostica
- Nuovi endpoint per monitorare le risorse del server
- API per la generazione e la gestione degli sprite sheet
- Strumenti di diagnostica per ottimizzare le prestazioni
- Supporto per il debug delle comunicazioni WebSocket

### Vantaggi delle ottimizzazioni
- **Performance**: Caricamento più veloce grazie alla riduzione delle richieste HTTP
- **Stabilità**: Connessioni WebSocket più affidabili con gestione corretta di ping/pong
- **Efficienza**: Riduzione della banda utilizzata grazie a MessagePack
- **Manutenibilità**: Migliore diagnostica e monitoraggio del sistema

Per utilizzare queste nuove funzionalità, consultare la documentazione specifica nelle rispettive sezioni.

## Contribuire al Progetto

Se desideri contribuire, segui questi passaggi:

1. Fai un fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome-feature`)
3. Effettua i tuoi cambiamenti
4. Esegui i test
5. Fai commit dei tuoi cambiamenti (`git commit -m 'Aggiunge nuova feature'`)
6. Effettua il push sul branch (`git push origin feature/nome-feature`)
7. Apri una Pull Request

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

## Sistema di Prove di Abilità

Il sistema implementa un meccanismo completo per eseguire prove di abilità, sia per il giocatore che per gli NPC, supportando anche confronti diretti tra entità.

### API per Prove di Abilità

#### Endpoints HTTP

- **POST /prova_abilita/inizia**: Inizia una nuova prova di abilità.
  - Parametri: `id_sessione`, `tipo_prova` (giocatore, npg, confronto)
  - Risposta: Stato iniziale della prova

- **GET /prova_abilita/abilita_disponibili**: Ottiene le abilità disponibili per un'entità.
  - Parametri: `id_sessione`, `entita_id` (opzionale, default: giocatore)
  - Risposta: Lista delle abilità disponibili

- **POST /prova_abilita/esegui**: Esegue una prova di abilità.
  - Parametri: `id_sessione`, `modalita` (semplice, avanzata), `abilita`, `entita_id`, `target_id`, `difficolta`
  - Risposta: Risultato dettagliato della prova

- **GET /prova_abilita/npg_vicini**: Ottiene la lista degli NPG vicini al giocatore.
  - Parametri: `id_sessione`
  - Risposta: Lista di NPG nelle vicinanze

- **POST /prova_abilita/termina**: Termina una prova di abilità in corso.
  - Parametri: `id_sessione`
  - Risposta: Conferma di terminazione

#### Eventi WebSocket

- **prova_abilita_input**: Gestisce gli input dell'utente durante una prova.
  - Parametri: `id_sessione`, `tipo_input`, `dati_input`
  - Eventi emessi: `prova_abilita_update`

- **prova_abilita_select_npc**: Seleziona un NPG per una prova.
  - Parametri: `id_sessione`, `npg_id`
  - Eventi emessi: `prova_abilita_update`

- **prova_abilita_select_oggetto**: Seleziona un oggetto per interazione.
  - Parametri: `id_sessione`, `oggetto_id`
  - Eventi emessi: `prova_abilita_update`

- **prova_abilita_imposta_difficolta**: Imposta la difficoltà di una prova.
  - Parametri: `id_sessione`, `difficolta`
  - Eventi emessi: `prova_abilita_update`, `prova_abilita_risultato`

### Estensioni di Entity e World

- La classe `Entity` è stata estesa per supportare abilità tramite il dizionario `abilita`.
- I metodi `get_abilita()`, `get_bonus_abilita()`, `aggiungi_abilita()` e `rimuovi_abilita()` consentono di gestire le abilità delle entità.
- La classe `World` ora supporta stati temporanei con i metodi `get_temporary_state()`, `set_temporary_state()` e `remove_temporary_state()`, utili per mantenere lo stato delle prove di abilità.

### Uso del Sistema di Prove

```python
# Esempio: Inizia una prova di abilità per il giocatore
response = requests.post("http://localhost:5000/prova_abilita/inizia", json={
    "id_sessione": "sessione-123",
    "tipo_prova": "giocatore"
})

# Verifica le abilità disponibili
response = requests.get("http://localhost:5000/prova_abilita/abilita_disponibili?id_sessione=sessione-123")
abilita = response.json()["abilita"]

# Esegui una prova di abilità
response = requests.post("http://localhost:5000/prova_abilita/esegui", json={
    "id_sessione": "sessione-123",
    "modalita": "avanzata",
    "abilita": "forza",
    "difficolta": 15
})

# Ottieni il risultato
risultato = response.json()
print(f"Risultato: {risultato['risultato_finale']}, Successo: {risultato['esito'] == 'successo'}")

# Termina la prova
requests.post("http://localhost:5000/prova_abilita/termina", json={"id_sessione": "sessione-123"})
``` 