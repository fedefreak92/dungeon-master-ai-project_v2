# Documentazione della Struttura del Progetto RPG

## 🎮 Panoramica Generale
Questo progetto è un gioco di ruolo (RPG) basato su un'architettura client-server con un backend Python (Flask/Socket.IO) e un frontend React/Pixi.js. L'architettura del gioco utilizza un pattern di Macchina a Stati Finiti (FSM) per gestire i diversi stati di gioco.

## 📂 Struttura delle Directory

### 📁 Root del Progetto
- `start_gioco.bat` - Script batch per avviare sia il backend che il frontend del gioco
- `package.json` - File di configurazione per le dipendenze npm del progetto root
- `README.md` - Documentazione principale del progetto
- `LICENSE` - Licenza del progetto
- `player.png` - Immagine del personaggio giocatore
- `Image.png` - Immagine generica del progetto

### 📁 gioco_rpg (Directory Principale)
Directory principale che contiene l'intero progetto RPG.

#### 🔹 File di Configurazione e Avvio
- `main.py` - Script principale per avviare il backend del gioco, inizializza il sistema di logging e avvia il server Flask
- `server.py` - File per l'avvio del server di gioco, effettua il monkey patching di eventlet per le operazioni asincrone
- `requirements.txt` - Elenco delle dipendenze Python per il backend
- `__init__.py` - File vuoto che marca la directory come un pacchetto Python
- `run_tests.bat` - Script batch per eseguire i test del progetto
- `.gitignore` - File che specifica quali file e directory devono essere ignorati dal controllo versione

#### 📁 core (Nucleo del Gioco)
Contiene la logica di gioco principale e il motore di gioco.

- `game.py` - Implementazione della classe principale del gioco che gestisce tutto il flusso di gioco
- `io_interface.py` - Interfaccia per gestire l'input/output tra il gioco e l'utente
- `graphics_renderer.py` - Sistema di rendering grafico per la visualizzazione del gioco
- `stato_gioco.py` - Gestisce lo stato globale del gioco e la sua serializzazione/deserializzazione
- `ecs/` - Implementazione del sistema Entity-Component-System per la gestione delle entità di gioco

#### 📁 states (Stati del Gioco)
Implementa la macchina a stati finiti (FSM) che gestisce i diversi stati di gioco.

- `__init__.py` - Esporta gli stati disponibili nel gioco
- `base_state.py` - Classe base per tutti gli stati di gioco
- `menu.py` - Implementazione dello stato di menu principale
- `scelta_mappa_state.py` - Stato per la selezione della mappa di gioco
- `stato_esempio_grafico.py` - Esempio di stato con elementi grafici

Sottodirectory specializzate per gli stati:
- `mappa/` - Stati relativi alla navigazione sulla mappa di gioco
- `combattimento/` - Stati per il sistema di combattimento
- `dialogo/` - Stati per la gestione dei dialoghi con NPC
- `taverna/` - Stati per le interazioni nella taverna
- `mercato/` - Stati per il sistema di mercato e commercio
- `inventario/` - Stati per la gestione dell'inventario
- `prova_abilita/` - Stati per le prove di abilità del personaggio
- `base/` - Altri stati di base per il gioco

#### 📁 server (Backend)
Contiene l'implementazione del server backend.

- `__init__.py` - Inizializza e esporta le componenti del server
- `app.py` - Implementazione principale dell'applicazione Flask e configurazione di Socket.IO
- `routes/` - Definizioni delle rotte API REST
- `websocket/` - Gestione delle connessioni e degli eventi WebSocket
- `utils/` - Utilità specifiche per il server
- `init/` - Script di inizializzazione del server

#### 📁 entities (Entità di Gioco)
Definizioni delle entità che popolano il mondo di gioco.

#### 📁 items (Oggetti di Gioco)
Definizioni degli oggetti che possono essere raccolti, equipaggiati o utilizzati.

#### 📁 world (Mondo di Gioco)
Logica per la generazione e gestione del mondo di gioco.

#### 📁 data (Dati di Gioco)
Contiene dati statici e configurazioni per diverse parti del gioco.

- `mappe/` - Definizioni delle mappe di gioco
- `npc/` - Definizioni dei personaggi non giocanti
- `monsters/` - Definizioni dei mostri e nemici
- `items/` - Definizioni degli oggetti di gioco
- `classes/` - Definizioni delle classi dei personaggi
- `world_state/` - Stati predefiniti del mondo di gioco
- `achievements/` - Definizioni degli obiettivi e trofei
- `assets_info/` - Informazioni sugli asset grafici
- `tutorials/` - Dati per i tutorial in-game

#### 📁 frontend (Client)
Contiene l'implementazione del client frontend in React e Pixi.js.

- `public/` - File statici accessibili pubblicamente
- `src/` - Codice sorgente del frontend
  - `App.jsx` - Componente principale dell'applicazione React
  - `App.css` - Stili CSS per l'applicazione principale
  - `index.js` - Punto di ingresso del frontend
  - `components/` - Componenti React riutilizzabili
  - `game/` - Logica di gioco specifica per il frontend
  - `api/` - Client API per comunicare con il backend
  - `pixi/` - Implementazioni specifiche per Pixi.js
  - `contexts/` - Definizioni dei contesti React per la gestione dello stato
  - `hooks/` - Hook React personalizzati
  - `styles/` - File di stile CSS aggiuntivi

#### 📁 util (Utilità)
Funzioni e classi di utilità generica.

- `logging_config.py` - Configurazione del sistema di logging

#### 📁 assets (Risorse)
Contiene asset visivi e audio per il gioco.

#### 📁 salvataggi (Salvataggi di Gioco)
Directory dove vengono memorizzati i salvataggi dei giocatori.

#### 📁 sessioni (Sessioni di Gioco)
Contiene dati relativi alle sessioni di gioco attive.

#### 📁 logs (Log)
Directory per i file di log del sistema.

#### 📁 test e tests (Test)
Contiene i test automatizzati per il progetto.

## 🔄 Flusso di Funzionamento

1. L'utente avvia il gioco tramite `start_gioco.bat`
2. Il backend Flask/Socket.IO viene inizializzato tramite `main.py`
3. Il frontend React viene caricato nel browser dell'utente
4. Il client si connette al server tramite Socket.IO e API REST
5. La macchina a stati finiti (FSM) gestisce i vari stati del gioco
6. I dati vengono scambiati tra client e server tramite eventi Socket.IO e chiamate API
7. Lo stato del gioco viene persistito nella directory `salvataggi`

## 🧩 Architettura Principale

Il progetto utilizza un'architettura a strati:
- **Presentazione**: Frontend React/Pixi.js
- **Comunicazione**: Socket.IO e REST API
- **Logica di Gioco**: Core game engine basato su FSM
- **Persistenza**: File JSON per salvataggi e configurazioni

L'architettura FSM garantisce transizioni fluide tra i diversi stati di gioco (menu, mappa, combattimento, dialogo, ecc.) mantenendo la coerenza dello stato. 

## 🚀 Ottimizzazioni e Miglioramenti Tecnici

### ⚡ WebSocket Ottimizzati
- **Backend Eventlet**: Configurazione aggiornata per utilizzare Eventlet come backend WebSocket
- **Parametri Ping/Pong**: Impostazione corretta dei parametri per evitare disconnessioni
- **Gestione Connessione**: Meccanismi migliorati per la riconnessione e gestione client
- **Directory**: `server/websocket/` 

### 🖼️ Sistema di Sprite Sheet
- **Consolidamento Immagini**: Riduzione delle richieste HTTP tramite l'uso di sprite sheet
- **Generazione Dinamica**: Generazione e gestione automatica delle sprite sheet
- **API Dedicata**: Endpoint per la creazione e il recupero dei dati delle sprite sheet
- **File Principali**: `util/sprite_sheet_manager.py` e `server/routes/assets_routes.py`

### 📦 Serializzazione MessagePack
- **Formato Compatto**: Utilizzo di MessagePack per ridurre la dimensione dei dati trasmessi
- **Integrazione Nativa**: Supporto migliorato in tutte le classi principali del gioco
- **Sistema di Sessione**: Configurazione del sistema di sessione per l'uso di MessagePack
- **File Rilevanti**: `server/utils/session.py` e classi con supporto alla serializzazione

### 🛠️ API di Diagnostica
- **Monitoraggio Risorse**: Endpoint per monitorare lo stato e le risorse del server
- **Strumenti Analisi**: API per analizzare l'utilizzo delle risorse e ottimizzare le prestazioni
- **Debug WebSocket**: Supporto al debug delle comunicazioni WebSocket
- **File Rilevanti**: Nuovi endpoint nelle route del server

### 📊 Vantaggi delle Ottimizzazioni
- **Performance**: Riduzione significativa dei tempi di caricamento
- **Stabilità**: Connessioni WebSocket più affidabili
- **Efficienza**: Riduzione della banda utilizzata e dei tempi di risposta
- **Manutenibilità**: Maggiore facilità di debug e monitoraggio 