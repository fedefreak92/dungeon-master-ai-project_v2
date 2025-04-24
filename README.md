# Dungeon Master AI – Motore di Gioco RPG in Python

![Logo del gioco](Image.png)

## 📜 Panoramica del Progetto

Questo repository contiene un motore di gioco di ruolo (RPG) sviluppato in Python, progettato con un'architettura orientata agli oggetti e basata su una macchina a stati finiti (FSM) a stack. Il progetto mira a evolversi in un sistema RPG guidato dall'intelligenza artificiale con narrazione ricca, dove un Dungeon Master virtuale potenziato da GPT migliora l'immersione del giocatore.

L'applicazione è divisa in due componenti principali:
- **Backend**: Core del motore di gioco in Python, gestisce tutta la logica di gioco
- **Frontend**: Interfaccia utente React con Pixi.js per la visualizzazione grafica

## 🏗️ Architettura del Progetto

Il progetto è organizzato in moduli ben definiti:

```
gioco_rpg/
├── main.py                 # Punto di ingresso del server
├── server.py               # Script di compatibilità per il server
├── server/                 # Modulo server Flask/SocketIO
│   ├── app.py              # Configurazione dell'app Flask
│   ├── routes/             # Endpoint API REST
│   └── websocket/          # Gestori WebSocket
├── core/                   # Logica principale del gioco
│   ├── game.py             # Loop di gioco e gestione stati
│   ├── io_interface.py     # Interfaccia I/O astratta
│   ├── stato_gioco.py      # Gestione dello stato globale
│   └── graphics_renderer.py # Rendering grafico
├── entities/               # Entità di gioco
│   ├── giocatore.py        # Classe del giocatore
│   ├── entita.py           # Classe base per le entità
│   ├── nemico.py           # Sistema di nemici
│   └── npg.py              # Personaggi non giocanti
├── states/                 # Stati di gioco (FSM)
│   ├── base/               # Stati base
│   ├── mappa/              # Esplorazione mappa
│   ├── combattimento/      # Sistema di combattimento
│   ├── inventario/         # Gestione inventario
│   ├── dialogo/            # Sistema di dialogo
│   └── mercato/            # Sistema di commercio
├── world/                  # Sistema mondo e mappe
│   ├── mappa.py            # Definizione mappa
│   ├── controller_mappa.py # Controllore delle mappe
│   └── gestore_mappe.py    # Gestione delle mappe di gioco
├── items/                  # Oggetti e elementi interattivi
├── util/                   # Funzioni di utilità
├── data/                   # Dati di gioco in formato JSON
│   ├── mappe/              # Definizioni mappe
│   ├── monsters/           # Dati dei mostri
│   ├── npc/                # Dati dei PNG
│   ├── items/              # Definizioni oggetti
│   └── classes/            # Classi di personaggio
├── frontend/               # Interfaccia utente React
│   ├── src/                # Codice sorgente React
│   ├── public/             # Asset pubblici
│   └── package.json        # Dipendenze frontend
└── assets/                 # Risorse grafiche e audio
```

Il gioco utilizza una **macchina a stati finiti a stack** (`BaseState`) per gestire le diverse fasi di gioco (esplorazione della mappa, combattimento, dialoghi, gestione dell'inventario), consentendo transizioni fluide e interazioni stratificate (ad esempio, l'apertura di un forziere mette in pausa l'esplorazione e attiva uno stato di dialogo o di bottino).

## 🔮 Caratteristiche

- **Architettura modulare** pronta per l'estensione
- **Logica di gioco completa** (movimento, combattimento, dialoghi, inventario)
- **Sistema di mappe basato su ASCII** con controller di tile
- **Sistema factory per entità** per la generazione dinamica di contenuti
- **Completa separazione** della logica di gioco dall'interfaccia utente (pronto per future integrazioni web/GUI/AI)
- **Backend completamente testabile** 
- **Sistema centralizzato di caricamento dati** tramite file JSON
- **Sistema di combattimento avanzato** con selezione del tipo di mostro e livelli di difficoltà
- **Sistema di navigazione della mappa** con selezione della destinazione
- **Interazione migliorata** con pozioni e oggetti dell'inventario
- **Posizionamento migliorato** di PNG e oggetti interattivi sulle mappe
- **Interfaccia web** basata su React e Socket.IO
- **Visualizzazione grafica** tramite Pixi.js

## 🔧 Tecnologie Utilizzate

### Backend
- **Python 3.10+**
- **Flask** - Framework web
- **Flask-SocketIO** - Comunicazione real-time
- **JSON** - Formato dati

### Frontend
- **React 18** - Framework UI
- **Pixi.js** - Rendering grafico 2D
- **Socket.IO Client** - Comunicazione real-time con il server
- **Axios** - Richieste HTTP

## 🚀 Roadmap Attuale

✅ Sistema centralizzato di caricamento dati tramite data_manager.py utilizzando il formato JSON  
✅ Sistema di combattimento con mostri migliorato:  
   - Selezione specifica del tipo di mostro  
   - Livelli di difficoltà personalizzabili  
   - Ricompense e punti esperienza proporzionali alla difficoltà  
✅ Navigazione della mappa migliorata:  
   - Stato dedicato alla selezione della mappa  
   - Possibilità di scegliere la destinazione all'inizio del gioco  
   - Eliminazione del reindirizzamento automatico alla taverna  
✅ Miglioramento dell'interazione con oggetti e pozioni:  
   - Interfaccia utente più intuitiva per l'uso degli oggetti  
   - Effetti pozione ottimizzati  
   - Gestione avanzata dell'inventario  
✅ Miglioramento del posizionamento di PNG e oggetti interattivi sulle mappe:  
   - Posizioni predefinite precise per migliorare l'esperienza di gioco  
   - Sistema di posizionamento alternativo quando le posizioni principali sono occupate  
✅ Interfaccia web React funzionante con comunicazione real-time  
⬜ Implementare il Dungeon Master AI utilizzando GPT  
⬜ Miglioramento e aderenza alle regole ufficiali D&D  
⬜ Implementazione del sistema di magia e incantesimi  
⬜ Implementazione di combattimenti multipli (più nemici/alleati)  
⬜ Implementazione multiplayer online  
⬜ Implementazione di scenari di gioco generati dall'IA e volti realistici dei PNG  
⬜ Implementazione di scene di gioco generate dall'IA  
⬜ Integrazione della sintesi vocale AI per la narrazione del DM  

## 🚨 Problemi Attuali e Sviluppi in Corso

### Frontend React
- **Warning ESLint**: Numerosi componenti React contengono variabili non utilizzate e warning che necessitano di essere risolti
  ```
  GameMapScreen.jsx:
  - 'useMemo', 'dispatch', 'selectedTile', 'tileSize' sono definiti ma mai utilizzati
  - 'handleTileClick', 'clearTileHighlight' sono definiti ma mai utilizzati
  - React Hook useCallback ha dipendenze mancanti (highlightTile)
  ```
- **Export anonimi**: In `socketService.js` e altri servizi ci sono export anonimi che generano warning
  ```
  Line 176:1: Assign instance to a variable before exporting as module default
  ```

### Backend Flask
- **Gestione risorse**: Il sistema carica molte risorse con pattern di fallback quando non trova le immagini originali:
  ```
  Richiesta asset: tiles/floor.png, cercando in ...
  Richiesta asset: fallback/tiles/floor.png, cercando in ...
  ```
- **Serializzazione**: Errori durante la serializzazione di oggetti complessi:
  ```
  Attributo io presente nel World, escluso dalla serializzazione
  ```
- **Performance**: Il server genera un volume significativo di log durante l'esecuzione, potenzialmente impattando le performance

### Integrazione e Ottimizzazione
- **Caricamento risorse**: L'applicazione effettua numerose richieste HTTP per caricare gli asset grafici (più di 30 richieste all'avvio)
- **WebSocket e gestione sessioni**: Il sistema di connessione tramite WebSocket e gestione delle sessioni funziona, ma potrebbe essere ottimizzato

### Piano di Miglioramento
1. **Pulizia del codice React**:
   - Rimuovere variabili e import non utilizzati
   - Risolvere warning ESLint e problemi di dipendenze nei hooks
   - Ottimizzare la struttura dei componenti

2. **Ottimizzazione delle risorse**:
   - Implementare un sistema di sprite sheet per ridurre le richieste HTTP
   - Migliorare il sistema di caricamento assets con precaricamento
   - Ottimizzare dimensioni e formati immagini

3. **Miglioramento backend**:
   - Ottimizzare logging per ridurre impatto sulle performance
   - Migliorare sistema di serializzazione
   - Implementare caching per le richieste più frequenti

4. **Documentazione**:
   - Migliorare documenti tecnici per ogni modulo
   - Annotare meglio il codice per lo sviluppo futuro

## 🧠 Visione Futura: Dungeon Master AI

Questo progetto servirà come base per un'esperienza narrativa guidata dall'IA. Le integrazioni pianificate includono:

- **Dungeon Master potenziato da GPT** che reagisce agli eventi di gioco e genera descrizioni o dialoghi dinamici
- **Analisi del linguaggio naturale** per i comandi
- **Mappatura della generazione narrativa** agli alberi decisionali
- **Integrazione vocale** per la narrazione del DM

## 🎮 Installazione e Avvio

### Prerequisiti
- Python 3.10 o superiore
- Node.js 16 o superiore
- npm

### Installazione

1. Clona il repository:
```
git clone https://github.com/tuousername/gioco_rpg.git
cd gioco_rpg
```

2. Configura l'ambiente virtuale Python:
```
cd gioco_rpg
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Installa le dipendenze frontend:
```
cd frontend
npm install
```

### Avvio

Per avviare il gioco con una singola azione, utilizza lo script batch fornito:
```
start_gioco.bat
```

Altrimenti, avvia manualmente i componenti:

1. Avvia il backend:
```
cd gioco_rpg
.venv\Scripts\activate
python main.py
```

2. Avvia il frontend:
```
cd gioco_rpg\frontend
npm start
```

3. Accedi all'applicazione:
   - Apri il browser e vai a `http://localhost:3000`

## 📋 Requisiti

### Backend
- Python 3.10+
- Flask
- Flask-SocketIO
- Flask-CORS

### Frontend
- Node.js 16+
- React 18
- Pixi.js
- Socket.IO Client

## 👥 Contribuisci

Sto cercando collaboratori che vogliano aiutare a costruire:

- Miglioramenti all'interfaccia web
- Motore narrativo basato su IA (GPT)
- Trama e world-building
- Feedback UI/UX o playtesting

Sentiti libero di aprire issues, fork o contattarmi direttamente.

## 📜 Licenza

Questo progetto è distribuito con licenza MIT. Vedi il file `LICENSE` per ulteriori dettagli.

# Implementazione MessagePack per Gioco RPG

Questo documento descrive l'implementazione di MessagePack come formato di serializzazione per il gioco RPG.

## Cos'è MessagePack

MessagePack è un formato di serializzazione binario che permette scambi di dati tra diversi linguaggi di programmazione. È simile a JSON ma con una rappresentazione più compatta e prestazioni migliori sia in termini di velocità di serializzazione/deserializzazione che di dimensione dei dati.

## Vantaggi di MessagePack

- **Prestazioni**: Fino a 5 volte più veloce di JSON per la serializzazione/deserializzazione
- **Dimensione**: Occupa circa il 30-50% in meno rispetto a JSON
- **Compatibilità**: Supporta gli stessi tipi di dati di JSON
- **Facilità di utilizzo**: API simile a JSON, facilmente adottabile

## Implementazione nel Gioco RPG

MessagePack è stato implementato in diversi componenti del sistema:

1. **Classe `OggettoInterattivo`**:
   - Aggiunto metodo `to_msgpack()` per serializzare oggetti in formato MessagePack
   - Aggiunto metodo statico `from_msgpack()` per deserializzare oggetti

2. **Classe `World`**:
   - Aggiunto metodo `serialize_msgpack()` per serializzare il mondo di gioco
   - Aggiunto metodo statico `deserialize_msgpack()` per deserializzare il mondo

3. **Funzioni di gestione sessione**:
   - Modificata `salva_sessione()` per salvare utilizzando MessagePack
   - Modificata `carica_sessione()` per caricare utilizzando MessagePack con fallback su JSON

## Come funziona

Il sistema tenta sempre prima di utilizzare MessagePack per la serializzazione e deserializzazione. In caso di errori, il sistema esegue un fallback su JSON per garantire la robustezza.

I file serializzati con MessagePack hanno l'estensione `.msgpack` e vengono salvati nella stessa directory dei file JSON, ma occupano meno spazio e sono più veloci da leggere/scrivere.

## Dipendenze

Per utilizzare MessagePack è necessaria la libreria Python `msgpack`. È stata aggiunta a `requirements.txt`:

```
msgpack==1.0.5
```

## Impatto sulle prestazioni

L'utilizzo di MessagePack migliora significativamente le prestazioni del gioco:

- Riduce il tempo di salvataggio e caricamento delle sessioni
- Risolve i problemi di serializzazione per oggetti complessi
- Diminuisce l'utilizzo della memoria e dello spazio su disco

## Compatibilità

L'implementazione è retrocompatibile con il formato JSON precedente. Il sistema verificherà prima la presenza di file MessagePack e, se non presenti, tenterà di caricare i file JSON.


